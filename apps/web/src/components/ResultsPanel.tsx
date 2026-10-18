import type { AnalysisResult } from '@/api/types'
import { formatConfidence } from '@/lib/videoValidation'

interface ResultsPanelProps {
  result: AnalysisResult
}

export function ResultsPanel({ result }: ResultsPanelProps) {
  const overallPercent = Math.round(result.quality.overall * 100)

  return (
    <div className="space-y-8">
      {result.feedback.summary ? (
        <p className="text-[var(--color-ink)]">{result.feedback.summary}</p>
      ) : null}

      <section className="space-y-2">
        <h2 className="font-[family-name:var(--font-display)] text-xl font-medium">
          Video quality
        </h2>
        <p className="text-[var(--color-muted)]">
          Overall:{' '}
          <span className="text-[var(--color-ink)]">{overallPercent}%</span>
        </p>
        {result.quality.warnings.length > 0 ? (
          <ul className="list-disc space-y-1 pl-5 text-[var(--color-muted)]">
            {result.quality.warnings.map((warning) => (
              <li key={warning}>{warning}</li>
            ))}
          </ul>
        ) : null}
        {result.stroke.confidence != null ? (
          <p className="text-sm text-[var(--color-muted)]">
            Stroke detection: {formatConfidence(result.stroke.confidence)}.
          </p>
        ) : null}
      </section>

      <section className="space-y-3">
        <h2 className="font-[family-name:var(--font-display)] text-xl font-medium">
          What to work on
        </h2>
        {result.findings.length === 0 ? (
          <p className="text-[var(--color-muted)]">No supported fault detected.</p>
        ) : (
          <ul className="space-y-4">
            {result.findings.slice(0, 3).map((finding) => (
              <li
                key={finding.rule_id}
                className="border-l-2 border-[var(--color-accent)] bg-[var(--color-surface)] px-4 py-3"
              >
                <div className="flex flex-wrap items-baseline justify-between gap-2">
                  <h3 className="font-medium">{finding.label}</h3>
                  <span className="text-sm text-[var(--color-muted)]">
                    Severity: {finding.severity} · {formatConfidence(finding.confidence)}
                  </span>
                </div>
                <ul className="mt-2 space-y-1 text-[var(--color-muted)]">
                  {finding.evidence.map((item) => (
                    <li key={`${finding.rule_id}-${item.feature}`}>
                      {item.feature}: {item.value} {item.unit}
                    </li>
                  ))}
                </ul>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="space-y-3">
        <h2 className="font-[family-name:var(--font-display)] text-xl font-medium">
          Coaching suggestions
        </h2>
        {result.feedback.tips.length === 0 ? (
          <p className="text-[var(--color-muted)]">No coaching suggestions for this clip.</p>
        ) : (
          <ul className="space-y-4">
            {result.feedback.tips.map((tip) => (
              <li
                key={tip.finding_id}
                className="border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-3"
              >
                <h3 className="font-medium">{tip.title}</h3>
                <p className="mt-2 text-[var(--color-muted)]">{tip.explanation}</p>
                <p className="mt-2 text-sm text-[var(--color-ink)]">
                  <span className="font-medium">Try this: </span>
                  {tip.practice_cue}
                </p>
                {tip.citations.length > 0 ? (
                  <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-[var(--color-muted)]">
                    {tip.citations.map((cite) => (
                      <li key={`${cite.source_id}:${cite.chunk_id}`}>
                        {cite.source_id} — {cite.locator}
                      </li>
                    ))}
                  </ul>
                ) : null}
              </li>
            ))}
          </ul>
        )}
      </section>

      {result.feedback.limitations.length > 0 ? (
        <section className="space-y-2">
          <h2 className="font-[family-name:var(--font-display)] text-xl font-medium">
            Limitations
          </h2>
          <ul className="list-disc space-y-1 pl-5 text-sm text-[var(--color-muted)]">
            {result.feedback.limitations.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </section>
      ) : null}
    </div>
  )
}
