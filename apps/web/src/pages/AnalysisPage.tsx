import { useMutation, useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getAnalysisApi } from '@/api'
import {
  clearCapabilityToken,
  getCapabilityToken,
} from '@/api/session'
import { isTerminalStatus, type AnalysisStatus } from '@/api/types'
import { ResultsPanel } from '@/components/ResultsPanel'
import SpecularButton, {
  specularDangerProps,
  specularGhostLightProps,
  specularPrimaryProps,
} from '@/components/SpecularButton'
import { StatusBanner } from '@/components/StatusBanner'
import { clearAnalysisClip, getAnalysisClip } from '@/lib/clipSession'

export function AnalysisPage() {
  const { analysisId = '' } = useParams()
  const token = getCapabilityToken(analysisId)
  const [confirmDelete, setConfirmDelete] = useState(false)
  const [deleted, setDeleted] = useState(false)

  const progressQuery = useQuery({
    queryKey: ['analysis', analysisId],
    enabled: Boolean(analysisId && token && !deleted),
    queryFn: () => getAnalysisApi().getAnalysis(analysisId, token!),
    refetchInterval: (query) => {
      const status = query.state.data?.status
      if (!status || isTerminalStatus(status)) return false
      return 600
    },
  })

  const status = progressQuery.data?.status
  const readyForResult =
    status === 'completed' ||
    status === 'inconclusive' ||
    status === 'failed' ||
    status === 'expired'

  const resultQuery = useQuery({
    queryKey: ['analysis-result', analysisId],
    enabled: Boolean(analysisId && token && readyForResult && !deleted),
    queryFn: () => getAnalysisApi().getResult(analysisId, token!),
  })

  const deleteMutation = useMutation({
    mutationFn: async () => {
      await getAnalysisApi().deleteAnalysis(analysisId, token!)
    },
    onSuccess: () => {
      clearCapabilityToken(analysisId)
      clearAnalysisClip(analysisId)
      setDeleted(true)
      setConfirmDelete(false)
    },
  })

  if (!analysisId) {
    return (
      <StatusBanner tone="danger" title="Missing analysis" role="alert">
        <Link to="/upload" className="font-medium text-[var(--color-accent)] underline-offset-4 hover:underline">
          Start a new upload
        </Link>
      </StatusBanner>
    )
  }

  if (!token) {
    return (
      <div className="space-y-5">
        <StatusBanner tone="warning" title="Session credentials missing" role="alert">
          This browser no longer has access to this analysis. Upload again to
          continue.
        </StatusBanner>
        <SpecularButton to="/upload" {...specularPrimaryProps}>
          Go to upload
        </SpecularButton>
      </div>
    )
  }

  if (deleted) {
    return (
      <div className="space-y-5">
        <StatusBanner tone="neutral" title="Analysis deleted">
          Your video and results for this analysis have been removed.
        </StatusBanner>
        <SpecularButton to="/upload" {...specularPrimaryProps}>
          Analyze another clip
        </SpecularButton>
      </div>
    )
  }

  if (progressQuery.isError) {
    return (
      <StatusBanner tone="danger" title="Could not load analysis" role="alert">
        <Link to="/upload" className="font-medium text-[var(--color-accent)] underline-offset-4 hover:underline">
          Try uploading again
        </Link>
      </StatusBanner>
    )
  }

  if (!status || !isTerminalStatus(status)) {
    return (
      <div className="space-y-8" aria-busy="true">
        <header className="max-w-2xl space-y-3">
          <h1 className="font-[family-name:var(--font-display)] text-4xl font-semibold leading-[1.08] tracking-[-0.02em] text-[var(--color-ink)] text-balance sm:text-5xl">
            Reading your swing
          </h1>
          <p className="max-w-xl text-base leading-relaxed text-[var(--color-muted)] sm:text-lg">
            The coach is checking pose, timing, and technique. Stay on this page —
            processing continues if you leave, but you need this browser session
            to open the results.
          </p>
        </header>

        <div className="coach-panel space-y-5 p-5 sm:p-6">
          <StatusBanner tone="neutral" title="Analyzing your clip…">
            <p className="font-mono text-xs tracking-wide text-[var(--color-muted)]">
              ID: {analysisId}
            </p>
          </StatusBanner>
          <div className="coach-progress" aria-hidden="true">
            <div className="coach-progress__bar" />
          </div>
        </div>

        <DeleteControls
          confirmDelete={confirmDelete}
          setConfirmDelete={setConfirmDelete}
          onDelete={() => deleteMutation.mutate()}
          isPending={deleteMutation.isPending}
        />
      </div>
    )
  }

  if (resultQuery.isLoading) {
    return (
      <div className="coach-panel p-5 sm:p-6">
        <StatusBanner tone="neutral" title="Loading results…">
          Almost ready.
        </StatusBanner>
      </div>
    )
  }

  if (resultQuery.isError || !resultQuery.data) {
    return (
      <StatusBanner tone="danger" title="Results unavailable" role="alert">
        <Link to="/upload" className="font-medium text-[var(--color-accent)] underline-offset-4 hover:underline">
          Start over
        </Link>
      </StatusBanner>
    )
  }

  const result = resultQuery.data

  return (
    <div className="space-y-10">
      <TerminalHeader status={result.status} analysisId={analysisId} />

      {result.status === 'completed' ? (
        <ResultsPanel
          result={result}
          yourClipUrl={getAnalysisClip(analysisId)}
        />
      ) : null}

      {result.status === 'inconclusive' ? (
        <div className="space-y-6">
          <StatusBanner tone="warning" title="Could not analyze this clip safely">
            {result.error?.safe_message}
          </StatusBanner>
          {result.quality.warnings.length > 0 ? (
            <ul className="m-0 space-y-2 p-0 text-[var(--color-muted)]">
              {result.quality.warnings.map((warning) => (
                <li key={warning} className="list-none text-sm leading-relaxed">
                  {warning}
                </li>
              ))}
            </ul>
          ) : null}
          {result.error && result.error.remediation.length > 0 ? (
            <div className="coach-panel space-y-3 p-5 sm:p-6">
              <h2 className="font-[family-name:var(--font-display)] text-2xl font-semibold text-[var(--color-ink)]">
                How to re-record
              </h2>
              <ul className="m-0 space-y-2 p-0 text-[var(--color-muted)]">
                {result.error.remediation.map((tip) => (
                  <li key={tip} className="list-none text-sm leading-relaxed">
                    {tip}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
          <SpecularButton to="/upload" {...specularPrimaryProps}>
            Try another recording
          </SpecularButton>
        </div>
      ) : null}

      {result.status === 'failed' && result.error ? (
        <div className="space-y-5">
          <StatusBanner tone="danger" title="Analysis failed" role="alert">
            <p>{result.error.safe_message}</p>
            <p className="mt-2">
              {result.error.retryable
                ? 'Retrying with the same video may work.'
                : 'A new recording is recommended.'}
            </p>
            {result.error.remediation.length > 0 ? (
              <ul className="mt-3 space-y-1.5">
                {result.error.remediation.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            ) : null}
            <p className="mt-3 font-mono text-xs">
              Support ID: {result.error.correlation_id}
            </p>
          </StatusBanner>
          <SpecularButton to="/upload" {...specularPrimaryProps}>
            Upload again
          </SpecularButton>
        </div>
      ) : null}

      {result.status === 'expired' ? (
        <div className="space-y-5">
          <StatusBanner tone="warning" title="This analysis has expired">
            {result.error?.safe_message ??
              'Results are removed after 24 hours. Upload a new clip to continue.'}
          </StatusBanner>
          <SpecularButton to="/upload" {...specularPrimaryProps}>
            Start a new analysis
          </SpecularButton>
        </div>
      ) : null}

      {result.status !== 'expired' ? (
        <DeleteControls
          confirmDelete={confirmDelete}
          setConfirmDelete={setConfirmDelete}
          onDelete={() => deleteMutation.mutate()}
          isPending={deleteMutation.isPending}
        />
      ) : null}
    </div>
  )
}

function TerminalHeader({
  status,
  analysisId,
}: {
  status: AnalysisStatus
  analysisId: string
}) {
  const titles: Partial<Record<AnalysisStatus, string>> = {
    completed: 'Coach debrief',
    inconclusive: 'Inconclusive result',
    failed: 'Something went wrong',
    expired: 'Expired analysis',
  }

  const leads: Partial<Record<AnalysisStatus, string>> = {
    completed: 'Here is what to carry into your next session.',
    inconclusive: 'The clip was not clear enough for safe coaching.',
    failed: 'The analysis could not finish.',
    expired: 'This session is no longer available.',
  }

  return (
    <header className="max-w-2xl space-y-3">
      <h1 className="font-[family-name:var(--font-display)] text-4xl font-semibold leading-[1.08] tracking-[-0.02em] text-[var(--color-ink)] text-balance sm:text-5xl">
        {titles[status] ?? 'Analysis'}
      </h1>
      {leads[status] ? (
        <p className="text-base leading-relaxed text-[var(--color-muted)] sm:text-lg">
          {leads[status]}
        </p>
      ) : null}
      <p className="font-mono text-xs tracking-wide text-[var(--color-muted)]">
        ID: {analysisId}
      </p>
    </header>
  )
}

function DeleteControls({
  confirmDelete,
  setConfirmDelete,
  onDelete,
  isPending,
}: {
  confirmDelete: boolean
  setConfirmDelete: (value: boolean) => void
  onDelete: () => void
  isPending: boolean
}) {
  if (!confirmDelete) {
    return (
      <SpecularButton
        type="button"
        onClick={() => setConfirmDelete(true)}
        {...specularPrimaryProps}
      >
        Delete this analysis
      </SpecularButton>
    )
  }

  return (
    <div
      role="group"
      aria-label="Confirm deletion"
      className="coach-panel space-y-3 border-[var(--color-danger)] bg-[var(--color-danger-soft)] px-5 py-4"
    >
      <p className="text-sm leading-relaxed text-[var(--color-ink)]">
        Delete this analysis and all related video data? This cannot be undone.
      </p>
      <div className="flex flex-wrap gap-3">
        <SpecularButton
          type="button"
          disabled={isPending}
          onClick={onDelete}
          {...specularDangerProps}
        >
          {isPending ? 'Deleting…' : 'Confirm delete'}
        </SpecularButton>
        <SpecularButton
          type="button"
          disabled={isPending}
          onClick={() => setConfirmDelete(false)}
          {...specularGhostLightProps}
        >
          Cancel
        </SpecularButton>
      </div>
    </div>
  )
}
