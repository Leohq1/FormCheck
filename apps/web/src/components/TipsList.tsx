interface TipsListProps {
  tips: string[]
  title?: string
}

export function TipsList({ tips, title = 'Recording tips' }: TipsListProps) {
  return (
    <section aria-labelledby="tips-heading" className="space-y-3">
      <h2
        id="tips-heading"
        className="font-[family-name:var(--font-display)] text-2xl font-semibold"
      >
        {title}
      </h2>
      <ul className="tip-stagger list-disc space-y-2 pl-5 text-[var(--color-muted)]">
        {tips.map((tip) => (
          <li key={tip}>{tip}</li>
        ))}
      </ul>
    </section>
  )
}
