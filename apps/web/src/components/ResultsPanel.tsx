import type { AnalysisResult, FeedbackTip } from '@/api/types'
import { SkeletonVideo } from '@/components/SkeletonVideo'
import { formatConfidence } from '@/lib/videoValidation'

const STROKE_LABELS: Record<string, string> = {
  overhead_clear: 'Overhead clear',
  smash: 'Smash',
  drop: 'Drop',
}

const PHASES = ['Prepare', 'Strike', 'Recover']

function phaseOf(tip: FeedbackTip, index: number): string {
  const citation = tip.citations[0]
  if (citation?.source_id === 'stroke-brief' && citation.locator) {
    return citation.locator
  }
  return PHASES[index] ?? 'Cue'
}

interface ResultsPanelProps {
  result: AnalysisResult
  /** Optional player clip URL (e.g. object URL of the upload). */
  yourClipUrl?: string | null
  /** Optional reference / model-form clip URL. */
  referenceClipUrl?: string | null
}

function VideoTape({
  label,
  src,
}: {
  label: string
  src?: string | null
}) {
  return (
    <figure className="video-tape m-0 min-w-0">
      <div className="video-tape__bezel">
        {src ? (
          <SkeletonVideo src={src} label={label} />
        ) : (
          <div
            className="video-tape__media video-tape__media--empty"
            role="img"
            aria-label={`${label} preview placeholder`}
          >
            <span className="video-tape__empty-label">Preview soon</span>
          </div>
        )}
      </div>
      <figcaption className="video-tape__caption">{label}</figcaption>
    </figure>
  )
}

export function ResultsPanel({
  result,
  yourClipUrl,
  referenceClipUrl,
}: ResultsPanelProps) {
  const overallPercent = Math.round(result.quality.overall * 100)
  const strokeLabel = STROKE_LABELS[result.stroke.type] ?? 'Selected shot'
  const tips = result.feedback.tips.slice(0, 3)

  return (
    <div className="space-y-10">
      {result.feedback.summary ? (
        <p className="max-w-3xl text-pretty font-[family-name:var(--font-display)] text-2xl font-medium leading-snug tracking-[-0.01em] text-[var(--color-ink)] sm:text-3xl">
          {result.feedback.summary}
        </p>
      ) : null}

      <section className="coach-panel space-y-4 p-5 sm:p-6" aria-labelledby="quality-heading">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <h2
            id="quality-heading"
            className="font-[family-name:var(--font-display)] text-2xl font-semibold text-[var(--color-ink)]"
          >
            Video quality
          </h2>
          <p className="text-sm text-[var(--color-muted)]">
            Overall{' '}
            <span className="font-medium tabular-nums text-[var(--color-ink)]">
              {overallPercent}%
            </span>
          </p>
        </div>
        <div
          className="coach-meter"
          role="meter"
          aria-valuenow={overallPercent}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label="Overall video quality"
        >
          <div
            className="coach-meter__fill"
            style={{ width: `${overallPercent}%` }}
          />
        </div>
        {result.quality.warnings.length > 0 ? (
          <ul className="m-0 space-y-2 p-0">
            {result.quality.warnings.map((warning) => (
              <li
                key={warning}
                className="list-none text-sm leading-relaxed text-[var(--color-muted)]"
              >
                {warning}
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-[var(--color-muted)]">
            Clean enough for reliable coaching.
          </p>
        )}
        {result.stroke.confidence != null ? (
          <p className="text-sm text-[var(--color-muted)]">
            Stroke detection:{' '}
            <span className="text-[var(--color-ink)]">
              {formatConfidence(result.stroke.confidence)}
            </span>
          </p>
        ) : null}
      </section>

      <section className="space-y-4" aria-labelledby="clips-heading">
        <div className="space-y-1">
          <h2
            id="clips-heading"
            className="font-[family-name:var(--font-display)] text-2xl font-semibold text-[var(--color-ink)]"
          >
            Form comparison
          </h2>
          <p className="text-sm text-[var(--color-muted)]">
            Your swing beside the reference swing, each with a MediaPipe skeleton.
          </p>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <VideoTape label="Your swing" src={yourClipUrl} />
          <VideoTape label={`Reference ${strokeLabel.toLowerCase()}`} src={referenceClipUrl} />
        </div>
      </section>

      <section className="space-y-5" aria-labelledby="coaching-heading">
        <div className="space-y-1">
          <p className="text-xs font-medium uppercase tracking-[0.16em] text-[var(--color-accent)]">
            {strokeLabel}
          </p>
          <h2
            id="coaching-heading"
            className="font-[family-name:var(--font-display)] text-2xl font-semibold text-[var(--color-ink)]"
          >
            Practice session
          </h2>
        </div>
        {tips.length === 0 ? (
          <p className="text-[var(--color-muted)]">
            Coaching for this shot did not come back. Run the analysis again.
          </p>
        ) : (
          <ol className="m-0 grid list-none gap-4 p-0 md:grid-cols-3">
            {tips.map((tip, index) => (
              <li
                key={`${tip.finding_id}-${index}`}
                className="coach-panel flex list-none flex-col gap-4 px-5 py-5"
              >
                <div className="flex items-baseline justify-between gap-3">
                  <span className="font-[family-name:var(--font-display)] text-sm font-semibold uppercase tracking-[0.14em] text-[var(--color-accent)]">
                    {phaseOf(tip, index)}
                  </span>
                  <span
                    className="font-[family-name:var(--font-display)] text-lg font-semibold tabular-nums text-[var(--color-ink)]/35"
                    aria-hidden="true"
                  >
                    {String(index + 1).padStart(2, '0')}
                  </span>
                </div>
                <h3 className="font-[family-name:var(--font-display)] text-xl font-semibold leading-tight text-[var(--color-ink)]">
                  {tip.title}
                </h3>
                <p className="flex-1 text-sm leading-relaxed text-[var(--color-muted)]">
                  {tip.explanation}
                </p>
                <p className="rounded-md bg-[var(--color-accent-soft)] px-4 py-3 text-sm leading-relaxed text-[var(--color-ink)]">
                  {tip.practice_cue}
                </p>
              </li>
            ))}
          </ol>
        )}
      </section>
    </div>
  )
}
