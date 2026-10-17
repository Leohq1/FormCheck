import type { AnalysisResult } from '@/api/types'
import { formatConfidence } from '@/lib/videoValidation'

interface ResultsPanelProps {
  result: AnalysisResult
}

export function ResultsPanel({ result }: ResultsPanelProps) {
  return (
    <div className="space-y-8">
      <section className="space-y-2">
        <h2 className="font-[family-name:var(--font-display)] text-xl font-medium">
          Video quality
        </h2>
        <p className="text-[var(--color-muted)]">
          Overall: <span className="text-[var(--color-ink)]">{result.quality.overall}</span>
        </p>
        {result.quality.notes.length > 0 ? (
          <ul className="list-disc space-y-1 pl-5 text-[var(--color-muted)]">
            {result.quality.notes.map((note) => (
              <li key={note}>{note}</li>
            ))}
          </ul>
        ) : null}
        {(result.stroke_confidence != null || result.phase_confidence != null) && (
          <p className="text-sm text-[var(--color-muted)]">
            {result.stroke_confidence != null
              ? `Stroke detection: ${formatConfidence(result.stroke_confidence)}. `
              : null}
            {result.phase_confidence != null
              ? `Phase detection: ${formatConfidence(result.phase_confidence)}.`
              : null}
          </p>
        )}
      </section>

      <section className="space-y-3">
        <h2 className="font-[family-name:var(--font-display)] text-xl font-medium">
          What to work on
        </h2>
        {result.findings.length === 0 ? (
          <p className="text-[var(--color-muted)]">No technique findings for this clip.</p>
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
                <p className="mt-2 text-[var(--color-muted)]">{finding.evidence}</p>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="space-y-3">
        <h2 className="font-[family-name:var(--font-display)] text-xl font-medium">
          Coaching suggestions
        </h2>
        {result.recommendations.length === 0 ? (
          <p className="text-[var(--color-muted)]">No recommendations available.</p>
        ) : (
          <ul className="space-y-4">
            {result.recommendations.map((rec) => (
              <li
                key={rec.title}
                className="border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-3"
              >
                <h3 className="font-medium">{rec.title}</h3>
                <p className="mt-2 text-[var(--color-muted)]">{rec.body}</p>
                {rec.exercise ? (
                  <p className="mt-2 text-sm text-[var(--color-ink)]">
                    <span className="font-medium">Try this: </span>
                    {rec.exercise}
                  </p>
                ) : null}
              </li>
            ))}
          </ul>
        )}
      </section>

      {result.citations.length > 0 ? (
        <section className="space-y-2">
          <h2 className="font-[family-name:var(--font-display)] text-xl font-medium">
            Sources
          </h2>
          <ul className="list-disc space-y-1 pl-5 text-sm text-[var(--color-muted)]">
            {result.citations.map((cite) => (
              <li key={cite.id}>
                {cite.title} — {cite.locator}
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {result.limitations.length > 0 ? (
        <section className="space-y-2">
          <h2 className="font-[family-name:var(--font-display)] text-xl font-medium">
            Limitations
          </h2>
          <ul className="list-disc space-y-1 pl-5 text-sm text-[var(--color-muted)]">
            {result.limitations.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </section>
      ) : null}
    </div>
  )
}
