interface LogoMarkProps {
  className?: string
  /** `dark` = charcoal mark for light pages; `light` = cream mark for the hero header */
  variant?: 'dark' | 'light'
}

export function LogoMark({ className, variant = 'dark' }: LogoMarkProps) {
  const src =
    variant === 'light' ? '/images/logo-mark-light.png' : '/images/logo-mark.png'

  return (
    <img
      src={src}
      alt=""
      width={36}
      height={36}
      className={className}
      decoding="async"
    />
  )
}
