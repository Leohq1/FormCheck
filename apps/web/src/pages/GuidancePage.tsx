import { Link } from 'react-router-dom'
import { TipsList } from '@/components/TipsList'
import { RECORDING_TIPS } from '@/sports/config'

export function GuidancePage() {
  return (
    <div>
      <section className="relative flex min-h-[100svh] items-end overflow-hidden bg-[var(--color-ink)]">
        <img
          src="/images/hero-badminton.jpg"
          alt=""
          className="absolute inset-0 h-full w-full object-cover"
          fetchPriority="high"
        />
        <div
          className="absolute inset-0 bg-gradient-to-r from-[var(--color-ink)]/90 via-[var(--color-ink)]/70 to-[var(--color-ink)]/35"
          aria-hidden="true"
        />
        <div
          className="absolute inset-0 bg-gradient-to-t from-[var(--color-ink)]/80 via-transparent to-[var(--color-ink)]/40"
          aria-hidden="true"
        />

        <p
          className="pointer-events-none absolute bottom-[-0.08em] left-0 right-0 select-none text-center font-[family-name:var(--font-display)] text-[clamp(4.5rem,22vw,14rem)] font-semibold leading-none tracking-tight text-white/[0.07]"
          aria-hidden="true"
        >
          CLEAR
        </p>

        <div className="relative z-10 w-full px-5 pb-16 pt-28 sm:px-8 sm:pb-20">
          <div className="mx-auto max-w-3xl space-y-5">
            <h1 className="hero-enter-delay font-[family-name:var(--font-display)] text-4xl font-semibold leading-[1.05] text-white sm:text-5xl md:text-6xl">
              Record one clip. Get coaching you can use.
            </h1>
            <p className="hero-enter-delay-2 max-w-xl text-base text-white/75 sm:text-lg">
              Upload a short clip of a shot and FormCheck returns technique
              notes, drills, and cited coaching guidance.
            </p>
            <div className="hero-enter-delay-2 pt-2">
              <Link to="/upload" className="btn-primary">
                Continue to upload
              </Link>
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto w-full max-w-3xl space-y-8 px-5 py-12 sm:px-8">
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

        <p className="border-l-2 border-[var(--color-accent)] pl-4 text-sm text-[var(--color-muted)]">
          FormCheck provides technique guidance only. It is not medical advice
          and does not diagnose injury. Analyses expire after 24 hours.
        </p>
      </section>
    </div>
  )
}
