import { useMutation } from '@tanstack/react-query'
import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { getAnalysisApi } from '@/api'
import { storeCapabilityToken } from '@/api/session'
import GlideSelect from '@/components/GlideSelect'
import { TipsList } from '@/components/TipsList'
import { VideoDropzone } from '@/components/VideoDropzone'
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
    <div className="space-y-8">
      <div className="space-y-2">
        <h1 className="font-[family-name:var(--font-display)] text-3xl font-semibold">
          Upload your clip
        </h1>
        <p className="text-[var(--color-muted)]">
          Choose the stroke in your clip, then upload for coaching feedback.
        </p>
      </div>

      <TipsList tips={RECORDING_TIPS.slice(0, 4)} title="Quick reminders" />

      <form className="space-y-6" onSubmit={handleSubmit} noValidate>
        <VideoDropzone
          file={file}
          onFileChange={setFile}
          disabled={uploadMutation.isPending}
        />

        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <span className="block text-sm font-medium">Stroke</span>
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
            <span className="block text-sm font-medium">Dominant hand</span>
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
            <span className="block text-sm font-medium">Camera view</span>
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

        <label className="flex items-start gap-3 text-sm">
          <input
            type="checkbox"
            className="mt-1"
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
          <div role="alert" className="space-y-1 text-sm text-[var(--color-danger)]">
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

        <div className="flex flex-wrap items-center gap-4">
          <button
            type="submit"
            disabled={uploadMutation.isPending}
            className="btn-primary"
          >
            {uploadMutation.isPending ? 'Uploading…' : 'Analyze clip'}
          </button>
          <Link to="/" className="text-sm text-[var(--color-muted)] underline">
            Back to recording tips
          </Link>
        </div>
      </form>
    </div>
  )
}
