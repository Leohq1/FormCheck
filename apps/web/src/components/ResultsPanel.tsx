import type { AnalysisFinding, AnalysisResult, FeedbackTip } from '@/api/types'
import { formatConfidence } from '@/lib/videoValidation'

interface ResultsPanelProps {
  result: AnalysisResult
  /** Optional player clip URL (e.g. object URL of the upload). */
  yourClipUrl?: string | null
  /** Optional reference / model-form clip URL. */
  referenceClipUrl?: string | null
}

interface CoachingItem {
  finding: AnalysisFinding
  tip: FeedbackTip | undefined
  index: number
}

function VideoTape({
  label,
  src,
  poster,
}: {
  label: string
  src?: string | null
  poster: string
}) {
  return (
    <figure className="video-tape m-0 min-w-0">
      <div className="video-tape__bezel">
        {src ? (
          <video
            className="video-tape__media"
            controls
            playsInline
            preload="metadata"
            poster={poster}
            src={src}
          >
            <track kind="captions" />
          </video>
        ) : (
          <div
            className="video-tape__media video-tape__media--empty"
            style={{ backgroundImage: `url(${poster})` }}
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

  const coachingItems: CoachingItem[] = result.findings
    .slice(0, 3)
    .map((finding, index) => ({
      finding,
      tip: result.feedback.tips.find((tip) => tip.finding_id === finding.rule_id),
      index,
    }))

  const orphanTips = result.feedback.tips.filter(
    (tip) => !result.findings.some((finding) => finding.rule_id === tip.finding_id),
  )

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
            Your swing beside a reference model of the same stroke.
          </p>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <VideoTape
            label="Your swing"
            src={yourClipUrl}
            poster="/images/hero-badminton.jpg"
          />
          <VideoTape
            label="Reference form"
            src={referenceClipUrl}
            poster="/images/hero-court.jpg"
          />
        </div>
      </section>

      <section className="space-y-4" aria-labelledby="coaching-heading">
        <h2
          id="coaching-heading"
          className="font-[family-name:var(--font-display)] text-2xl font-semibold text-[var(--color-ink)]"
        >
          Coaching suggestions
        </h2>
        {coachingItems.length === 0 && orphanTips.length === 0 ? (
          <p className="text-[var(--color-muted)]">
            No supported fault detected — nothing specific to work on for this
            clip.
          </p>
        ) : (
          <ul className="m-0 space-y-4 p-0">
            {coachingItems.map(({ finding, tip, index }) => (
              <li
                key={finding.rule_id}
                className="coach-panel list-none space-y-4 px-5 py-4 sm:px-6 sm:py-5"
              >
                <div className="flex flex-wrap items-baseline justify-between gap-2">
                  <div className="flex items-baseline gap-3">
                    <span
                      className="font-[family-name:var(--font-display)] text-lg font-semibold tabular-nums text-[var(--color-accent)]"
                      aria-hidden="true"
                    >
                      {String(index + 1).padStart(2, '0')}
                    </span>
                    <h3 className="text-base font-medium text-[var(--color-ink)] sm:text-lg">
                      {finding.label}
                    </h3>
                  </div>
                  <span className="text-sm text-[var(--color-muted)]">
                    {finding.severity} · {formatConfidence(finding.confidence)}
                  </span>
                </div>

                {finding.evidence.length > 0 ? (
                  <ul className="m-0 space-y-1.5 p-0 text-sm text-[var(--color-muted)]">
                    {finding.evidence.map((item) => (
                      <li
                        key={`${finding.rule_id}-${item.feature}`}
                        className="list-none"
                      >
                        <span className="font-mono text-xs text-[var(--color-ink)]">
                          {item.feature}
                        </span>
                        : {item.value} {item.unit}
                      </li>
                    ))}
                  </ul>
                ) : null}

                {tip ? (
                  <div className="space-y-3 border-t border-[color-mix(in_srgb,var(--color-border)_55%,transparent)] pt-4">
                    <h4 className="text-base font-medium text-[var(--color-ink)]">
                      {tip.title}
                    </h4>
                    <p className="max-w-3xl leading-relaxed text-[var(--color-muted)]">
                      {tip.explanation}
                    </p>
                    <p className="max-w-3xl rounded-md bg-[#efefed] px-4 py-3 text-sm leading-relaxed text-[#242e2d]">
                      <span className="font-medium text-[#242e2d]/70">
                        Try this —{' '}
                      </span>
                      {tip.practice_cue}
                    </p>
                    {tip.citations.length > 0 ? (
                      <ul className="m-0 space-y-1 p-0 text-sm text-[var(--color-muted)]">
                        {tip.citations.map((cite) => (
                          <li
                            key={`${cite.source_id}:${cite.chunk_id}`}
                            className="list-none"
                          >
                            {cite.source_id} — {cite.locator}
                          </li>
                        ))}
                      </ul>
                    ) : null}
                  </div>
                ) : null}
              </li>
            ))}

            {orphanTips.map((tip) => (
              <li
                key={tip.finding_id}
                className="coach-panel list-none space-y-3 px-5 py-4 sm:px-6 sm:py-5"
              >
                <h3 className="text-lg font-medium text-[var(--color-ink)]">
                  {tip.title}
                </h3>
                <p className="max-w-3xl leading-relaxed text-[var(--color-muted)]">
                  {tip.explanation}
                </p>
                <p className="max-w-3xl rounded-md bg-[#efefed] px-4 py-3 text-sm leading-relaxed text-[#242e2d]">
                  <span className="font-medium text-[#242e2d]/70">Try this — </span>
                  {tip.practice_cue}
                </p>
              </li>
            ))}
          </ul>
        )}
      </section>

      {result.feedback.limitations.length > 0 ? (
        <section className="space-y-2 border-t border-[color-mix(in_srgb,var(--color-border)_70%,transparent)] pt-6">
          <h2 className="font-[family-name:var(--font-display)] text-xl font-semibold text-[var(--color-ink)]">
            Limitations
          </h2>
          <ul className="m-0 space-y-1.5 p-0 text-sm leading-relaxed text-[var(--color-muted)]">
            {result.feedback.limitations.map((item) => (
              <li key={item} className="list-none">
                {item}
              </li>
            ))}
          </ul>
        </section>
      ) : null}
    </div>
  )
}
