import { Link, Outlet, useLocation } from 'react-router-dom'
import { LogoMark } from '@/components/LogoMark'

export function AppShell() {
  const { pathname } = useLocation()
  const isLanding = pathname === '/'

  return (
    <div
      className={
        isLanding
          ? 'flex min-h-screen w-full flex-col'
          : 'mx-auto flex min-h-screen w-full max-w-3xl flex-col px-5 py-8 sm:px-8'
      }
    >
      <header
        className={
          isLanding
            ? 'absolute inset-x-0 top-0 z-20 flex items-center justify-between gap-4 px-5 py-5 sm:px-8'
            : 'mb-10 flex items-center justify-between gap-4'
        }
      >
        <Link
          to="/"
          className={
            isLanding
              ? 'inline-flex items-center gap-2.5 font-[family-name:var(--font-display)] text-2xl font-semibold tracking-wide text-white no-underline sm:gap-3 sm:text-3xl'
              : 'inline-flex items-center gap-2.5 font-[family-name:var(--font-display)] text-3xl font-semibold tracking-tight text-[var(--color-ink)] no-underline'
          }
        >
          <LogoMark
            variant={isLanding ? 'light' : 'dark'}
            className="h-8 w-8 shrink-0 sm:h-9 sm:w-9"
          />
          FormCheck
        </Link>
        <p
          className={
            isLanding
              ? 'text-xs uppercase tracking-[0.18em] text-white/70 sm:text-sm'
              : 'text-sm text-[var(--color-muted)]'
          }
        >
          Badminton coaching
        </p>
      </header>

      <main className="flex-1">
        <Outlet />
      </main>

      {!isLanding ? (
        <footer className="mt-12 border-t border-[var(--color-border)] pt-4 text-sm text-[var(--color-muted)]">
          Technique guidance only — not medical advice. Analyses expire after 24
          hours.
        </footer>
      ) : null}
    </div>
  )
}
