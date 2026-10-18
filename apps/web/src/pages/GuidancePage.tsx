import { HugeiconsIcon } from '@hugeicons/react'
import { ArrowDown01Icon } from '@hugeicons/core-free-icons'
import { BiLogoVisualStudio } from 'react-icons/bi'
import {
  SiCursor,
  SiDocker,
  SiFastapi,
  SiFramer,
  SiGooglegemini,
  SiGsap,
  SiMediapipe,
  SiPostgresql,
  SiPython,
  SiReact,
  SiReactquery,
  SiReactrouter,
  SiTailwindcss,
  SiTypescript,
  SiUv,
  SiVite,
} from 'react-icons/si'
import AnimatedContent from '@/components/AnimatedContent'
import { BrandErrorBoundary } from '@/components/BrandErrorBoundary'
import GridMotion from '@/components/GridMotion'
import LogoLoop, { type LogoItem } from '@/components/LogoLoop'
import SpecularButton, {
  specularPrimaryProps,
} from '@/components/SpecularButton'
import TrueFocus from '@/components/TrueFocus'
import { RECORDING_TIPS } from '@/sports/config'

/** Stack reflected in apps/web, services/api, and the MediaPipe analysis worker. */
const TECH_LOGOS: LogoItem[] = [
  {
    node: <SiReact />,
    title: 'React',
    href: 'https://react.dev',
    hoverColor: '#61dafb',
  },
  {
    node: <SiTypescript />,
    title: 'TypeScript',
    href: 'https://www.typescriptlang.org',
    hoverColor: '#3178c6',
  },
  {
    node: <SiVite />,
    title: 'Vite',
    href: 'https://vite.dev',
    hoverColor: '#646cff',
  },
  {
    node: <SiTailwindcss />,
    title: 'Tailwind CSS',
    href: 'https://tailwindcss.com',
    hoverColor: '#38bdf8',
  },
  {
    node: <SiGsap />,
    title: 'GSAP',
    href: 'https://gsap.com',
    hoverColor: '#88ce02',
  },
  {
    node: <SiFramer />,
    title: 'Motion',
    href: 'https://motion.dev',
    hoverColor: '#ff0055',
  },
  {
    node: <SiReactrouter />,
    title: 'React Router',
    href: 'https://reactrouter.com',
    hoverColor: '#ca4245',
  },
  {
    node: <SiReactquery />,
    title: 'TanStack Query',
    href: 'https://tanstack.com/query',
    hoverColor: '#ff4154',
  },
  {
    node: <SiPython />,
    title: 'Python',
    href: 'https://www.python.org',
    hoverColor: '#3776ab',
  },
  {
    node: <SiFastapi />,
    title: 'FastAPI',
    href: 'https://fastapi.tiangolo.com',
    hoverColor: '#009688',
  },
  {
    node: <SiMediapipe />,
    title: 'MediaPipe',
    href: 'https://ai.google.dev/edge/mediapipe',
    hoverColor: '#0097a7',
  },
  {
    node: <SiPostgresql />,
    title: 'PostgreSQL',
    href: 'https://www.postgresql.org',
    hoverColor: '#4169e1',
  },
  {
    node: <SiDocker />,
    title: 'Docker',
    href: 'https://www.docker.com',
    hoverColor: '#2496ed',
  },
  {
    node: <SiUv />,
    title: 'uv',
    href: 'https://docs.astral.sh/uv',
    hoverColor: '#de5fe9',
  },
  {
    node: <SiGooglegemini />,
    title: 'Gemini',
    href: 'https://gemini.google.com',
    hoverColor: '#8e75b2',
  },
  {
    node: <SiCursor />,
    title: 'Cursor',
    href: 'https://cursor.com',
    hoverColor: '#ffffff',
  },
  {
    node: <BiLogoVisualStudio />,
    title: 'VS Code',
    href: 'https://code.visualstudio.com',
    hoverColor: '#007acc',
  },
]

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

function LandingBackdrop() {
  return (
    <>
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
    </>
  )
}

export function GuidancePage() {
  return (
    <div>
      <section className="relative flex min-h-[100svh] flex-col overflow-hidden bg-[var(--color-ink)]">
        <LandingBackdrop />

        <div className="relative z-10 flex w-full flex-1 flex-col justify-end px-5 pb-8 pt-28 sm:px-8 sm:pb-10">
          <AnimatedContent
            className="mx-auto flex w-full max-w-3xl flex-col gap-5"
            distance={100}
            direction="vertical"
            duration={0.8}
            ease="power3.out"
            blur={0}
            stagger={0.08}
            threshold={0.1}
            trigger="mount"
          >
            <h1 className="font-[family-name:var(--font-display)] text-4xl font-semibold leading-[1.05] text-white sm:text-5xl md:text-6xl">
              <BrandErrorBoundary fallback={HERO_TITLE}>
                <TrueFocus
                  className="focus-hero"
                  sentence={HERO_TITLE}
                  manualMode
                  focusStyle="brackets"
                  easing="smooth"
                  blurAmount={0}
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
            <p className="max-w-xl text-base leading-relaxed text-white/75 sm:text-lg">
              Upload a short clip of a shot and FormCheck returns technique
              notes, drills, and cited coaching guidance.
            </p>
            <div className="pt-2">
              <SpecularButton to="/upload" {...specularPrimaryProps}>
                Continue to upload
              </SpecularButton>
            </div>
          </AnimatedContent>

          <AnimatedContent
            distance={60}
            direction="vertical"
            duration={0.7}
            ease="power3.out"
            blur={0}
            delay={0.35}
            threshold={0.1}
            trigger="mount"
          >
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
              className="mx-auto mt-10 flex flex-col items-center gap-1.5 text-white/75 no-underline transition-colors hover:text-white"
            >
              <span className="text-xs uppercase tracking-[0.18em]">
                Recording tips below
              </span>
              <span className="scroll-cue-bounce inline-flex" aria-hidden="true">
                <HugeiconsIcon
                  icon={ArrowDown01Icon}
                  size={28}
                  strokeWidth={2}
                />
              </span>
              <span className="sr-only">
                Scroll down to video recording instructions
              </span>
            </a>
          </AnimatedContent>
        </div>
      </section>

      <section
        id="recording-tips"
        className="relative flex min-h-[100svh] scroll-mt-0 flex-col overflow-hidden bg-[var(--color-ink)]"
      >
        <LandingBackdrop />

        <div className="relative z-10 flex flex-1 flex-col justify-center px-5 py-24 sm:px-8 sm:py-28">
          <div className="fluid-glass mx-auto w-full max-w-4xl p-6 sm:p-8">
            <AnimatedContent
              className="fluid-glass-bento"
              distance={100}
              direction="vertical"
              duration={0.8}
              ease="power3.out"
              blur={0}
              stagger={0.08}
              threshold={0.1}
            >
              <div className="fluid-glass-bento__main space-y-6">
                <h2
                  id="tips-heading"
                  className="font-[family-name:var(--font-display)] text-3xl font-semibold text-white sm:text-4xl"
                >
                  Recording tips
                </h2>
                <ol className="m-0 space-y-3 p-0 text-base leading-relaxed text-white/80 sm:text-lg">
                  {RECORDING_TIPS.map((tip, index) => (
                    <li key={tip} className="flex list-none gap-3">
                      <span
                        className="mt-0.5 inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-sm bg-white/10 font-[family-name:var(--font-display)] text-sm font-semibold text-white"
                        aria-hidden="true"
                      >
                        {index + 1}
                      </span>
                      <span>{tip}</span>
                    </li>
                  ))}
                </ol>
              </div>

              <aside className="fluid-glass-bento__media overflow-hidden rounded-[1rem]">
                <img
                  src="/images/hero-court.jpg"
                  alt="Player preparing a badminton shot indoors"
                  className="aspect-[4/3] h-full w-full object-cover sm:aspect-auto sm:min-h-[16rem]"
                  loading="lazy"
                />
              </aside>

              <div className="fluid-glass-bento__note border-t border-white/15 pt-5 text-sm leading-relaxed text-white/65">
                FormCheck provides technique guidance only. It is not medical
                advice and does not diagnose injury. Analyses expire after 24
                hours.
              </div>

              <div className="fluid-glass-bento__cta">
                <SpecularButton to="/upload" {...specularPrimaryProps}>
                  Continue to upload
                </SpecularButton>
              </div>
            </AnimatedContent>
          </div>
        </div>
      </section>

      <section
        aria-labelledby="tech-stack-heading"
        className="relative overflow-hidden bg-[var(--color-ink)] px-5 py-16 sm:px-8 sm:py-20"
      >
        <div
          className="pointer-events-none absolute inset-0 bg-gradient-to-t from-[var(--color-ink)] via-[var(--color-ink)]/95 to-transparent"
          aria-hidden="true"
        />
        <div className="relative z-10 mx-auto w-full max-w-5xl space-y-8">
          <div className="space-y-2 text-center">
            <p className="text-xs uppercase tracking-[0.18em] text-white/50">
              Stack
            </p>
            <h2
              id="tech-stack-heading"
              className="font-[family-name:var(--font-display)] text-2xl font-semibold text-white sm:text-3xl"
            >
              Built with
            </h2>
          </div>
          <div className="relative text-white/80">
            {/* Logo-band fades only — keep hover names clear of the edge wash */}
            <div
              className="pointer-events-none absolute top-3 left-0 z-20 h-10 w-16 bg-gradient-to-r from-[var(--color-ink)] to-transparent sm:w-24"
              aria-hidden="true"
            />
            <div
              className="pointer-events-none absolute top-3 right-0 z-20 h-10 w-16 bg-gradient-to-l from-[var(--color-ink)] to-transparent sm:w-24"
              aria-hidden="true"
            />
            <div className="py-3">
              <LogoLoop
                logos={TECH_LOGOS}
                speed={100}
                direction="left"
                logoHeight={40}
                gap={56}
                hoverSpeed={0}
                scaleOnHover
                fadeOut={false}
                labels="hover"
                ariaLabel="FormCheck technology stack"
              />
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
