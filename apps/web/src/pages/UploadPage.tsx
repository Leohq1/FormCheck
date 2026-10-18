import { useMutation } from '@tanstack/react-query'
import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { getAnalysisApi } from '@/api'
import { storeCapabilityToken } from '@/api/session'
import GlideSelect from '@/components/GlideSelect'
import SpecularButton, {
  specularGhostDarkProps,
  specularPrimaryProps,
} from '@/components/SpecularButton'
import { VideoDropzone } from '@/components/VideoDropzone'
import { storeAnalysisClip } from '@/lib/clipSession'
import { validateVideoFile } from '@/lib/videoValidation'
import {
  MVP_STROKE,
  RECORDING_TIPS,
  STROKE_OPTIONS,
  type Handedness,
  type StrokeId,
  type ViewHint,
} from '@/sports/config'

const STROKE_SELECT_OPTIONS = STROKE_OPTIONS.map((option) => ({
  value: option.id,
  label: option.label,
}))

const HAND_OPTIONS = [
  { value: 'right', label: 'Right' },
  { value: 'left', label: 'Left' },
]

const VIEW_OPTIONS = [
  { value: 'side', label: 'Side', tag: 'Preferred' },
  { value: 'rear_three_quarter', label: 'Rear three-quarter' },
]

const SELECT_THEME = {
  accentColor: 'var(--color-accent)',
  surfaceColor: 'var(--color-surface)',
  highlightColor: 'var(--color-border)',
  textColor: 'var(--color-ink)',
  size: 'lg' as const,
  radius: 6,
  menuWidth: 220,
}

export function UploadPage() {
  const navigate = useNavigate()
  const [file, setFile] = useState<File | null>(null)
  const [stroke, setStroke] = useState<StrokeId>(MVP_STROKE.id)
  const [handedness, setHandedness] = useState<Handedness>('right')
  const [viewHint, setViewHint] = useState<ViewHint>('side')
  const [consent, setConsent] = useState(false)
  const [formErrors, setFormErrors] = useState<string[]>([])

  const uploadMutation = useMutation({
    mutationFn: async () => {
      const validation = validateVideoFile(file)
      const errors = [...validation.errors]
      if (!consent) errors.push('Consent is required to process your video.')
      if (errors.length > 0) {
        setFormErrors(errors)
        throw new Error('Validation failed')
      }

      setFormErrors([])
      const api = getAnalysisApi()
      const created = await api.createAnalysis({
        stroke,
        handedness,
        view_hint: viewHint,
        consent: true,
        filename: file!.name,
        content_type: file!.type || 'video/mp4',
        byte_size: file!.size,
      })

      storeCapabilityToken(created.analysis_id, created.capability_token)
      storeAnalysisClip(created.analysis_id, file!)
      await api.uploadFile(
        created.analysis_id,
        created.capability_token,
        file!,
        file!.type || 'video/mp4',
      )
      await api.completeUpload(created.analysis_id, created.capability_token)
      return created.analysis_id
    },
    onSuccess: (analysisId) => {
      void navigate(`/analyses/${analysisId}`)
    },
  })

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    uploadMutation.mutate()
  }

  return (
    <div className="space-y-10">
      <header className="max-w-2xl space-y-3">
        <h1 className="text-balance font-[family-name:var(--font-display)] text-4xl font-semibold leading-[1.08] tracking-[-0.02em] text-[var(--color-ink)] sm:text-5xl">
          Send your clip to the coach
        </h1>
        <p className="max-w-xl text-base leading-relaxed text-[var(--color-muted)] sm:text-lg">
          Drop one clear, smash, or drop. Tell us the stroke setup, then FormCheck
          returns technique notes you can take back on court.
        </p>
      </header>

      <div className="grid gap-8 lg:grid-cols-[minmax(0,1.35fr)_minmax(16rem,0.85fr)] lg:items-start">
        <form className="space-y-8" onSubmit={handleSubmit} noValidate>
          <VideoDropzone
            file={file}
            onFileChange={setFile}
            disabled={uploadMutation.isPending}
          />

          <section className="coach-panel space-y-5 p-5 sm:p-6" aria-labelledby="setup-heading">
            <div className="space-y-1">
              <h2
                id="setup-heading"
                className="font-[family-name:var(--font-display)] text-2xl font-semibold text-[var(--color-ink)]"
              >
                Match setup
              </h2>
              <p className="text-sm text-[var(--color-muted)]">
                Helps the coach read your swing from the right angle.
              </p>
            </div>

            <div className="grid gap-5 sm:grid-cols-2">
              <div className="space-y-2 sm:col-span-2">
                <span className="block text-sm font-medium text-[var(--color-ink)]">
                  Stroke
                </span>
                <GlideSelect
                  className="w-full"
                  options={STROKE_SELECT_OPTIONS}
                  value={stroke}
                  disabled={uploadMutation.isPending}
                  ariaLabel="Stroke"
                  showTags
                  onChange={(next) => setStroke(next as StrokeId)}
                  {...SELECT_THEME}
                />
              </div>

              <div className="space-y-2">
                <span className="block text-sm font-medium text-[var(--color-ink)]">
                  Dominant hand
                </span>
                <GlideSelect
                  className="w-full"
                  options={HAND_OPTIONS}
                  value={handedness}
                  disabled={uploadMutation.isPending}
                  ariaLabel="Dominant hand"
                  showTags={false}
                  onChange={(next) => setHandedness(next as Handedness)}
                  {...SELECT_THEME}
                />
              </div>

              <div className="space-y-2">
                <span className="block text-sm font-medium text-[var(--color-ink)]">
                  Camera view
                </span>
                <GlideSelect
                  className="w-full"
                  options={VIEW_OPTIONS}
                  value={viewHint}
                  disabled={uploadMutation.isPending}
                  ariaLabel="Camera view"
                  showTags
                  onChange={(next) => setViewHint(next as ViewHint)}
                  {...SELECT_THEME}
                />
              </div>
            </div>
          </section>

          <label className="flex items-start gap-3 text-sm leading-relaxed text-[var(--color-ink)]">
            <input
              type="checkbox"
              className="mt-1 h-4 w-4 accent-[var(--color-accent)]"
              checked={consent}
              disabled={uploadMutation.isPending}
              onChange={(event) => setConsent(event.target.checked)}
            />
            <span>
              I consent to processing this video for technique analysis. Data is
              deleted within 24 hours or when I delete the analysis.
            </span>
          </label>

          {formErrors.length > 0 ? (
            <div
              role="alert"
              className="coach-panel space-y-1 border-[var(--color-danger)] bg-[var(--color-danger-soft)] px-4 py-3 text-sm text-[var(--color-danger)]"
            >
              {formErrors.map((error) => (
                <p key={error}>{error}</p>
              ))}
            </div>
          ) : null}

          {uploadMutation.isError && formErrors.length === 0 ? (
            <p role="alert" className="text-sm text-[var(--color-danger)]">
              Upload failed. Please try again.
            </p>
          ) : null}

          <div className="flex flex-wrap items-center gap-3">
            <SpecularButton
              type="submit"
              disabled={uploadMutation.isPending}
              {...specularPrimaryProps}
            >
              {uploadMutation.isPending ? 'Uploading…' : 'Analyze clip'}
            </SpecularButton>
            <SpecularButton
              to="/#recording-tips"
              {...specularGhostDarkProps}
            >
              Review recording tips
            </SpecularButton>
          </div>
        </form>

        <aside
          className="coach-panel space-y-4 p-5 sm:p-6 lg:sticky lg:top-6"
          aria-labelledby="reminders-heading"
        >
          <h2
            id="reminders-heading"
            className="font-[family-name:var(--font-display)] text-2xl font-semibold text-[var(--color-ink)]"
          >
            Before you hit record
          </h2>
          <ol className="m-0 space-y-3 p-0">
            {RECORDING_TIPS.slice(0, 4).map((tip, index) => (
              <li key={tip} className="flex list-none gap-3 text-sm leading-relaxed text-[var(--color-muted)]">
                <span
                  className="mt-0.5 inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-sm bg-[var(--color-ink)] font-[family-name:var(--font-display)] text-sm font-semibold text-white"
                  aria-hidden="true"
                >
                  {index + 1}
                </span>
                <span>{tip}</span>
              </li>
            ))}
          </ol>
        </aside>
      </div>
    </div>
  )
}
