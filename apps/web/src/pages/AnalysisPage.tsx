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
import { StatusBanner } from '@/components/StatusBanner'

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
      setDeleted(true)
      setConfirmDelete(false)
    },
  })

  if (!analysisId) {
    return (
      <StatusBanner tone="danger" title="Missing analysis" role="alert">
        <Link to="/upload" className="underline">
          Start a new upload
        </Link>
      </StatusBanner>
    )
  }

  if (!token) {
    return (
      <div className="space-y-4">
        <StatusBanner tone="warning" title="Session credentials missing" role="alert">
          This browser no longer has access to this analysis. Upload again to
          continue.
        </StatusBanner>
        <Link to="/upload" className="text-[var(--color-accent)] underline">
          Go to upload
        </Link>
      </div>
    )
  }

  if (deleted) {
    return (
      <div className="space-y-4">
        <StatusBanner tone="neutral" title="Analysis deleted">
          Your video and results for this analysis have been removed.
        </StatusBanner>
        <Link to="/upload" className="btn-primary">
          Analyze another clip
        </Link>
      </div>
    )
  }

  if (progressQuery.isError) {
    return (
      <StatusBanner tone="danger" title="Could not load analysis" role="alert">
        <Link to="/upload" className="underline">
          Try uploading again
        </Link>
      </StatusBanner>
    )
  }

  if (!status || !isTerminalStatus(status)) {
    return (
      <div className="space-y-6" aria-busy="true">
        <StatusBanner tone="neutral" title="Analyzing your clip…">
          <p>
            This usually takes a short while. You can leave this page open —
            processing continues even if you close the tab, but you will need
            this browser session to view results.
          </p>
          <p className="mt-2 font-mono text-xs">ID: {analysisId}</p>
        </StatusBanner>
        <div
          className="h-1 w-full overflow-hidden rounded bg-[var(--color-border)]"
          aria-hidden="true"
        >
          <div className="h-full w-1/3 animate-pulse bg-[var(--color-accent)]" />
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
      <StatusBanner tone="neutral" title="Loading results…">
        Almost ready.
      </StatusBanner>
    )
  }

  if (resultQuery.isError || !resultQuery.data) {
    return (
      <StatusBanner tone="danger" title="Results unavailable" role="alert">
        <Link to="/upload" className="underline">
          Start over
        </Link>
      </StatusBanner>
    )
  }

  const result = resultQuery.data

  return (
    <div className="space-y-8">
      <TerminalHeader status={result.status} analysisId={analysisId} />

      {result.status === 'completed' ? <ResultsPanel result={result} /> : null}

      {result.status === 'inconclusive' ? (
        <div className="space-y-4">
          <StatusBanner tone="warning" title="Could not analyze this clip safely">
            {result.error?.safe_message}
          </StatusBanner>
          {result.quality.warnings.length > 0 ? (
            <ul className="list-disc space-y-1 pl-5 text-[var(--color-muted)]">
              {result.quality.warnings.map((warning) => (
                <li key={warning}>{warning}</li>
              ))}
            </ul>
          ) : null}
          {result.error && result.error.remediation.length > 0 ? (
            <div className="space-y-2">
              <h2 className="font-[family-name:var(--font-display)] text-xl font-medium">
                How to re-record
              </h2>
              <ul className="list-disc space-y-1 pl-5 text-[var(--color-muted)]">
                {result.error.remediation.map((tip) => (
                  <li key={tip}>{tip}</li>
                ))}
              </ul>
            </div>
          ) : null}
          <Link to="/upload" className="btn-primary">
            Try another recording
          </Link>
        </div>
      ) : null}

      {result.status === 'failed' && result.error ? (
        <div className="space-y-4">
          <StatusBanner tone="danger" title="Analysis failed" role="alert">
            <p>{result.error.safe_message}</p>
            <p className="mt-2">
              {result.error.retryable
                ? 'Retrying with the same video may work.'
                : 'A new recording is recommended.'}
            </p>
            {result.error.remediation.length > 0 ? (
              <ul className="mt-2 list-disc space-y-1 pl-5">
                {result.error.remediation.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            ) : null}
            <p className="mt-2 font-mono text-xs">
              Support ID: {result.error.correlation_id}
            </p>
          </StatusBanner>
          <Link to="/upload" className="text-[var(--color-accent)] underline">
            Upload again
          </Link>
        </div>
      ) : null}

      {result.status === 'expired' ? (
        <div className="space-y-4">
          <StatusBanner tone="warning" title="This analysis has expired">
            {result.error?.safe_message ??
              'Results are removed after 24 hours. Upload a new clip to continue.'}
          </StatusBanner>
          <Link to="/upload" className="btn-primary">
            Start a new analysis
          </Link>
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
    completed: 'Your coaching feedback',
    inconclusive: 'Inconclusive result',
    failed: 'Something went wrong',
    expired: 'Expired analysis',
  }

  return (
    <div className="space-y-1">
      <h1 className="font-[family-name:var(--font-display)] text-3xl font-semibold">
        {titles[status] ?? 'Analysis'}
      </h1>
      <p className="font-mono text-xs text-[var(--color-muted)]">ID: {analysisId}</p>
    </div>
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
      <button
        type="button"
        className="text-sm text-[var(--color-danger)] underline"
        onClick={() => setConfirmDelete(true)}
      >
        Delete this analysis
      </button>
    )
  }

  return (
    <div
      role="group"
      aria-label="Confirm deletion"
      className="rounded-lg border border-[var(--color-danger)] bg-[var(--color-danger-soft)] px-4 py-3 space-y-3"
    >
      <p className="text-sm">
        Delete this analysis and all related video data? This cannot be undone.
      </p>
      <div className="flex flex-wrap gap-3">
        <button
          type="button"
          className="rounded-sm bg-[var(--color-accent-deep)] px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-[var(--color-accent)] disabled:opacity-60"
          disabled={isPending}
          onClick={onDelete}
        >
          {isPending ? 'Deleting…' : 'Confirm delete'}
        </button>
        <button
          type="button"
          className="text-sm underline"
          disabled={isPending}
          onClick={() => setConfirmDelete(false)}
        >
          Cancel
        </button>
      </div>
    </div>
  )
}
