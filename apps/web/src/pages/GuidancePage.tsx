import { Link } from 'react-router-dom'
import { HugeiconsIcon } from '@hugeicons/react'
import { ArrowDown01Icon } from '@hugeicons/core-free-icons'
import { BrandErrorBoundary } from '@/components/BrandErrorBoundary'
import GridMotion from '@/components/GridMotion'
import ScrollFloat from '@/components/ScrollFloat'
import TrueFocus from '@/components/TrueFocus'
import { TipsList } from '@/components/TipsList'
import { RECORDING_TIPS } from '@/sports/config'

const HERO_TITLE = 'Record one clip. Get coaching you can use.'

/** Local heroes + Unsplash competitive badminton action shots. */
const GRID_ITEMS = [
  '/images/hero-badminton.jpg',
  '/images/hero-court.jpg',
  'https://images.unsplash.com/photo-1626224583764-f87db24ac4ea?w=640&q=75&auto=format&fit=crop',
  'https://images.unsplash.com/photo-1722087642932-9b070e9a066e?w=640&q=75&auto=format&fit=crop',
  'https://images.unsplash.com/photo-1599391398131-cd12dfc6c24e?w=640&q=75&auto=format&fit=crop',
  'https://images.unsplash.com/photo-1595220427358-8cf2ce3d7f89?w=640&q=75&auto=format&fit=crop',
  'https://images.unsplash.com/photo-1729166241032-5b339506a0d7?w=640&q=75&auto=format&fit=crop',
  'https://images.unsplash.com/photo-1733141731875-8e33d5f2bd36?w=640&q=75&auto=format&fit=crop',
  'https://images.unsplash.com/photo-1720515226352-b0b1dec6813b?w=640&q=75&auto=format&fit=crop',
  'https://images.unsplash.com/photo-1758798474157-99bd084de57f?w=640&q=75&auto=format&fit=crop',
  'https://images.unsplash.com/photo-1633313236093-beebdd1a5e80?w=640&q=75&auto=format&fit=crop',
  'https://images.unsplash.com/photo-1521537634581-0dced2fee2ef?w=640&q=75&auto=format&fit=crop',
]

export function GuidancePage() {
  return (
    <div>
      <section className="relative flex min-h-[100svh] flex-col overflow-hidden bg-[var(--color-ink)]">
        <div className="pointer-events-none absolute inset-0 z-0" aria-hidden="true">
          <GridMotion
            items={GRID_ITEMS}
            rows={4}
            aspectRatio={1.33}
            gap={14}
            radius={12}
            angle={-10}
            tilt={0}
            speed={22}
            direction="alternate"
            parallax={0.45}
            spotlight={0.55}
            dim={0.45}
            fade={0.55}
            grayscale={false}
            theme="dark"
            tileColor="#242e2d"
          />
        </div>

        <div
          className="absolute inset-0 z-[1] bg-gradient-to-r from-[var(--color-ink)]/88 via-[var(--color-ink)]/55 to-[var(--color-ink)]/30"
          aria-hidden="true"
        />
        <div
          className="absolute inset-0 z-[1] bg-gradient-to-t from-[var(--color-ink)]/85 via-transparent to-[var(--color-ink)]/45"
          aria-hidden="true"
        />

        <div className="relative z-10 flex w-full flex-1 flex-col justify-end px-5 pb-8 pt-28 sm:px-8 sm:pb-10">
          <div className="mx-auto w-full max-w-3xl space-y-5">
            <h1 className="hero-enter-delay font-[family-name:var(--font-display)] text-4xl font-semibold leading-[1.05] text-white sm:text-5xl md:text-6xl">
              <BrandErrorBoundary fallback={HERO_TITLE}>
                <TrueFocus
                  className="focus-hero"
                  sentence={HERO_TITLE}
                  manualMode
                  focusStyle="brackets"
                  easing="smooth"
                  blurAmount={3}
                  focusScale={1.04}
                  unfocusedOpacity={0.7}
                  borderColor="#ffffff"
                  glowColor="rgba(255,255,255,0.35)"
                  cornerSize={14}
                  borderWidth={2}
                  animationDuration={0.35}
                />
              </BrandErrorBoundary>
            </h1>
            <div className="hero-enter-delay-2 max-w-xl text-base text-white/75 sm:text-lg">
              <ScrollFloat
                containerClassName="text-base font-normal leading-relaxed text-white/75 sm:text-lg"
                textClassName="text-left"
                effect="float"
                splitBy="words"
                direction="up"
                order="start"
                fromColor="#ae3121"
                animationDuration={1}
                ease="power3.out"
                scrollStart="top bottom+=20%"
                scrollEnd="center center"
                stagger={0.04}
                distance={80}
                stretch={1.4}
                smoothing={0.2}
              >
                Upload a short clip of a shot and FormCheck returns technique
                notes, drills, and cited coaching guidance.
              </ScrollFloat>
            </div>
            <div className="hero-enter-delay-2 pt-2">
              <Link to="/upload" className="btn-primary">
                Continue to upload
              </Link>
            </div>
          </div>

          <a
            href="#recording-tips"
            onClick={(event) => {
              event.preventDefault()
              const target = document.getElementById('recording-tips')
              if (!target) return
              const reduceMotion = window.matchMedia(
                '(prefers-reduced-motion: reduce)',
              ).matches
              target.scrollIntoView({
                behavior: reduceMotion ? 'auto' : 'smooth',
                block: 'start',
              })
              window.history.replaceState(null, '', '#recording-tips')
            }}
            className="hero-enter-delay-2 mx-auto mt-10 flex flex-col items-center gap-1.5 text-white/75 no-underline transition-colors hover:text-white"
          >
            <span className="text-xs uppercase tracking-[0.18em]">
              Recording tips below
            </span>
            <span className="scroll-cue-bounce inline-flex" aria-hidden="true">
              <HugeiconsIcon icon={ArrowDown01Icon} size={28} strokeWidth={2} />
            </span>
            <span className="sr-only">Scroll down to video recording instructions</span>
          </a>
        </div>
      </section>

      <section
        id="recording-tips"
        className="mx-auto w-full max-w-3xl scroll-mt-8 space-y-8 px-5 py-12 sm:px-8"
      >
        <div className="grid gap-8 sm:grid-cols-[1fr_0.85fr] sm:items-start">
          <TipsList tips={RECORDING_TIPS} />
          <aside className="overflow-hidden rounded-sm">
            <img
              src="/images/hero-court.jpg"
              alt="Player preparing a badminton shot indoors"
              className="aspect-[4/3] w-full object-cover"
              loading="lazy"
            />
          </aside>
        </div>

        <div className="border-l-2 border-[var(--color-accent)] pl-4 text-sm text-[var(--color-muted)]">
          <ScrollFloat
            containerClassName="text-sm font-normal leading-relaxed text-[var(--color-muted)]"
            textClassName="text-left"
            effect="float"
            splitBy="words"
            direction="up"
            order="start"
            fromColor="var(--color-ink)"
            animationDuration={0.95}
            ease="power3.out"
            scrollStart="top bottom-=5%"
            scrollEnd="top center+=15%"
            stagger={0.035}
            distance={85}
            stretch={1.35}
            smoothing={0.25}
          >
            FormCheck provides technique guidance only. It is not medical advice
            and does not diagnose injury. Analyses expire after 24 hours.
          </ScrollFloat>
        </div>
      </section>
    </div>
  )
}
