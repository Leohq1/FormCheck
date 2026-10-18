import type { ReactNode } from 'react'

interface StatusBannerProps {
  tone?: 'neutral' | 'warning' | 'danger' | 'success'
  title: string
  children?: ReactNode
  role?: 'status' | 'alert'
}

const toneStyles: Record<
  NonNullable<StatusBannerProps['tone']>,
  string
> = {
  neutral: 'bg-[var(--color-surface)] border-[var(--color-border)]',
  warning: 'bg-[var(--color-warning-soft)] border-[var(--color-warning)]',
  danger: 'bg-[var(--color-danger-soft)] border-[var(--color-danger)]',
  success: 'bg-[var(--color-accent-soft)] border-[var(--color-accent)]',
}

export function StatusBanner({
  tone = 'neutral',
  title,
  children,
  role = 'status',
}: StatusBannerProps) {
  return (
    <div
      role={role}
      className={`rounded-lg border px-5 py-4 ${toneStyles[tone]}`}
    >
      <p className="font-[family-name:var(--font-display)] text-xl font-semibold text-[var(--color-ink)]">
        {title}
      </p>
      {children ? (
        <div className="mt-2 text-sm leading-relaxed text-[var(--color-muted)]">
          {children}
        </div>
      ) : null}
    </div>
  )
}
