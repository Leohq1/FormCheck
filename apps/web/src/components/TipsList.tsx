import ScrollFloat from '@/components/ScrollFloat'

interface TipsListProps {
  tips: string[]
  title?: string
}

export function TipsList({ tips, title = 'Recording tips' }: TipsListProps) {
  return (
    <section aria-labelledby="tips-heading" className="space-y-5">
      <ScrollFloat
        id="tips-heading"
        containerClassName="font-[family-name:var(--font-display)] text-2xl font-semibold text-[var(--color-ink)]"
        textClassName="text-left"
        effect="float"
        splitBy="chars"
        direction="up"
        order="start"
        fromColor="var(--color-accent)"
        animationDuration={1}
        ease="back.inOut(2)"
        scrollStart="top bottom-=8%"
        scrollEnd="center center+=10%"
        stagger={0.035}
        distance={100}
        stretch={1.75}
        smoothing={0.3}
      >
        {title}
      </ScrollFloat>

      <ul className="space-y-3 pl-0 text-[var(--color-muted)]">
        {tips.map((tip, index) => (
          <li key={tip} className="list-none">
            <ScrollFloat
              containerClassName="text-base font-normal leading-relaxed text-[var(--color-muted)]"
              textClassName="text-left"
              effect="float"
              splitBy="words"
              direction="up"
              order="start"
              fromColor="var(--color-ink)"
              animationDuration={0.9}
              ease="power3.out"
              scrollStart="top bottom-=5%"
              scrollEnd="top center+=20%"
              stagger={0.045}
              distance={90}
              stretch={1.45}
              smoothing={0.25}
            >
              {`${index + 1}. ${tip}`}
            </ScrollFloat>
          </li>
        ))}
      </ul>
    </section>
  )
}
