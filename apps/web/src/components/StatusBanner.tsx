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
      className={`rounded-sm border px-4 py-3 ${toneStyles[tone]}`}
    >
      <p className="font-medium text-[var(--color-ink)]">{title}</p>
      {children ? (
        <div className="mt-1 text-sm text-[var(--color-muted)]">{children}</div>
      ) : null}
    </div>
  )
}
