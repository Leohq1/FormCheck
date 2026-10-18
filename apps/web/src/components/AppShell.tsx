import { Link, Outlet, useLocation } from 'react-router-dom'
import FloatingLines from '@/components/FloatingLines'
import { LogoMark } from '@/components/LogoMark'

export function AppShell() {
  const { pathname } = useLocation()
  const isLanding = pathname === '/'
  const isToolPage = pathname === '/upload' || pathname.startsWith('/analyses')

  return (
    <div
      className={
        isLanding
          ? 'flex min-h-screen w-full flex-col'
          : 'tool-shell relative flex min-h-screen w-full flex-col'
      }
    >
      {isToolPage ? (
        <div
          className="pointer-events-none absolute inset-0 z-0 min-h-[100svh] overflow-hidden"
          aria-hidden="true"
        >
          <FloatingLines
            className="h-full min-h-[100svh] w-full"
            style={{ width: '100%', height: '100%', minHeight: '100svh' }}
            linesGradient={['#ffffff', '#ffffff']}
            enabledWaves={['top', 'middle', 'bottom']}
            lineCount={13}
            lineDistance={30}
            bendStrength={-0.6}
            interactive
            clickSwirl
            lineWidth={4}
            glow={3}
            brightness={2}
            animationSpeed={0.8}
            amplitude={1.9}
            depthOfField={1}
            parallaxStrength={0.25}
          />
        </div>
      ) : null}

      <header
        className={
          isLanding
            ? 'absolute inset-x-0 top-0 z-20 flex items-center justify-between gap-4 px-5 py-5 sm:px-8'
            : 'tool-shell__header relative z-10 mx-auto flex w-full max-w-4xl items-center justify-between gap-4 px-5 pt-7 pb-6 sm:px-8'
        }
      >
        <Link
          to="/"
          className={
            isLanding || isToolPage
              ? 'inline-flex items-center gap-2.5 font-[family-name:var(--font-display)] text-2xl font-semibold tracking-tight text-white no-underline sm:gap-3 sm:text-3xl'
              : 'inline-flex items-center gap-2.5 font-[family-name:var(--font-display)] text-2xl font-semibold tracking-tight text-[var(--color-ink)] no-underline sm:text-3xl'
          }
        >
          <LogoMark
            variant={isLanding || isToolPage ? 'light' : 'dark'}
            className="h-8 w-8 shrink-0 sm:h-9 sm:w-9"
          />
          <span>FormCheck</span>
        </Link>
        <p
          className={
            isLanding || isToolPage
              ? 'text-xs uppercase tracking-[0.18em] text-white/70 sm:text-sm'
              : 'text-xs uppercase tracking-[0.16em] text-[var(--color-muted)] sm:text-sm'
          }
        >
          Badminton coaching
        </p>
      </header>

      <main
        className={
          isLanding
            ? 'flex-1'
            : 'tool-shell__main relative z-10 mx-auto w-full max-w-4xl flex-1 px-5 pb-10 sm:px-8'
        }
      >
        <Outlet />
      </main>

      {!isLanding ? (
        <footer className="tool-shell__footer relative z-10 mx-auto w-full max-w-4xl px-5 pb-8 pt-2 sm:px-8">
          <p className="text-sm text-[var(--color-muted)]">
            Technique guidance only — not medical advice. Analyses expire after
            24 hours.
          </p>
        </footer>
      ) : null}
    </div>
  )
}
