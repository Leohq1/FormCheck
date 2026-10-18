import {
  isValidElement,
  useEffect,
  useMemo,
  useRef,
  useState,
  type CSSProperties,
  type ReactNode,
} from 'react'

import './GridMotion.css'

const THEMES = {
  dark: {
    tile: '#1b1922',
    text: 'rgba(255, 255, 255, 0.78)',
    border: 'rgba(255, 255, 255, 0.07)',
  },
  light: {
    tile: '#f4f4f5',
    text: '#3f3f46',
    border: 'rgba(24, 24, 27, 0.08)',
  },
} as const

const DIRECTIONS = ['alternate', 'left', 'right'] as const
const IMAGE =
  /^(https?:\/\/|\/\/|\/|\.\.?\/|data:image\/|blob:)|\.(avif|gif|jpe?g|png|svg|webp)(\?.*)?$/i
const INERTIA = [0.42, 0.32, 0.26, 0.22]
const PACE = [1, 0.86, 1.12, 0.94]

type Direction = (typeof DIRECTIONS)[number]
type ThemeName = keyof typeof THEMES

export type GridMotionItem =
  | string
  | ReactNode
  | { src: string; alt?: string }
  | null
  | undefined
  | false

type TileData =
  | { kind: 'empty' }
  | { kind: 'node'; node: ReactNode }
  | { kind: 'image'; src: string; alt: string }
  | { kind: 'text'; text: string }

export interface GridMotionProps {
  items?: GridMotionItem[]
  rows?: number
  aspectRatio?: number
  gap?: number
  radius?: number
  angle?: number
  tilt?: number
  speed?: number
  direction?: Direction
  parallax?: number
  spotlight?: number
  dim?: number
  grayscale?: boolean
  fade?: number
  tileColor?: string
  textColor?: string
  theme?: ThemeName
  className?: string
  style?: CSSProperties
}

const clamp = (value: number, min: number, max: number) =>
  Math.min(max, Math.max(min, value))
const wrap = (value: number, total: number) => ((value % total) + total) % total
const smoothstep = (edge0: number, edge1: number, value: number) => {
  const t = clamp((value - edge0) / (edge1 - edge0), 0, 1)
  return t * t * (3 - 2 * t)
}

const feather = (side: string, zone: number) => {
  const stops: string[] = []
  for (let i = 0; i <= 6; i++) {
    const t = i / 6
    const alpha = t * t * t * (t * (t * 6 - 15) + 10)
    stops.push(`rgba(0, 0, 0, ${alpha.toFixed(4)}) ${(t * zone).toFixed(2)}%`)
  }
  const mirrored = stops.map((_, i) => {
    const t = (6 - i) / 6
    const alpha = t * t * t * (t * (t * 6 - 15) + 10)
    return `rgba(0, 0, 0, ${alpha.toFixed(4)}) ${(100 - t * zone).toFixed(2)}%`
  })
  return `linear-gradient(${side}, ${stops.join(', ')}, ${mirrored.join(', ')})`
}

const toTile = (item: GridMotionItem): TileData => {
  if (item === null || item === undefined || item === false) return { kind: 'empty' }
  if (isValidElement(item)) return { kind: 'node', node: item }
  if (typeof item === 'object' && 'src' in item && typeof item.src === 'string') {
    return { kind: 'image', src: item.src, alt: item.alt ?? '' }
  }
  const text = String(item).trim()
  return IMAGE.test(text) ? { kind: 'image', src: text, alt: '' } : { kind: 'text', text }
}

const EMPTY: TileData = { kind: 'empty' }

function Tile({ tile }: { tile: TileData }) {
  return (
    <div className="grid-motion__tile">
      {tile.kind === 'image' && (
        <img src={tile.src} alt={tile.alt} draggable={false} decoding="async" />
      )}
      {tile.kind === 'text' && <span className="grid-motion__text">{tile.text}</span>}
      {tile.kind === 'node' && tile.node}
    </div>
  )
}

export default function GridMotion({
  items = [],
  rows = 4,
  aspectRatio = 1.33,
  gap = 16,
  radius = 14,
  angle = -12,
  tilt = 0,
  speed = 24,
  direction = 'alternate',
  parallax = 0.5,
  spotlight = 0.6,
  dim = 0.35,
  grayscale = false,
  fade = 0.5,
  tileColor,
  textColor,
  theme = 'dark',
  className = '',
  style,
}: GridMotionProps) {
  const rootRef = useRef<HTMLDivElement>(null)
  const planeRef = useRef<HTMLDivElement>(null)
  const [size, setSize] = useState({ width: 0, height: 0 })
  const palette = THEMES[theme] ?? THEMES.dark
  const settings = {
    rows: clamp(Math.round(rows), 1, 12),
    aspect: clamp(aspectRatio, 0.3, 4),
    gap: Math.max(0, gap),
    angle,
    tilt: clamp(tilt, 0, 75),
    speed,
    direction: DIRECTIONS.includes(direction) ? direction : 'alternate',
    parallax: clamp(parallax, 0, 1),
    spotlight: clamp(spotlight, 0, 1),
    dim: clamp(dim, 0, 1),
    fade: clamp(fade, 0, 1),
  }
  const settingsRef = useRef(settings)
  settingsRef.current = settings

  const layout = useMemo(() => {
    const { width, height } = size
    if (!width || !height) return null
    const turn = (settings.angle * Math.PI) / 180
    const lean = (settings.tilt * Math.PI) / 180
    const cos = Math.abs(Math.cos(turn))
    const sin = Math.abs(Math.sin(turn))
    const planeHeight =
      ((width * sin + height * cos) / Math.max(0.3, Math.cos(lean))) * 1.12
    const planeWidth =
      (width * cos + height * sin) * (1 + Math.sin(lean) * 0.9) * 1.12
    const tileHeight = Math.max(
      16,
      (planeHeight - settings.gap * (settings.rows - 1)) / settings.rows,
    )
    const tileWidth = tileHeight * settings.aspect
    const step = tileWidth + settings.gap
    const perRow = Math.ceil(planeWidth / step) + 1
    const period = perRow * step
    return {
      planeWidth,
      planeHeight,
      tileWidth,
      tileHeight,
      step,
      perRow,
      period,
      copies: Math.ceil(planeWidth / period) + 1,
      top: (planeHeight - settings.rows * tileHeight - (settings.rows - 1) * settings.gap) / 2,
      perspective: Math.max(width, height) * 1.5,
    }
  }, [size, settings.angle, settings.tilt, settings.rows, settings.gap, settings.aspect])

  const tiles = useMemo(() => items.map(toTile), [items])

  useEffect(() => {
    const root = rootRef.current
    if (!root) return undefined
    const observer = new ResizeObserver(() => {
      const width = Math.round(root.clientWidth)
      const height = Math.round(root.clientHeight)
      setSize((current) =>
        current.width === width && current.height === height
          ? current
          : { width, height },
      )
    })
    observer.observe(root)
    return () => observer.disconnect()
  }, [])

  useEffect(() => {
    const root = rootRef.current
    const plane = planeRef.current
    if (!root || !plane || !layout) return undefined

    const reduce =
      window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false
    const nudges = Array.from(
      plane.querySelectorAll<HTMLElement>('.grid-motion__nudge'),
    )
    const tileEls = nudges.map(
      (nudge) =>
        Array.from(
          nudge.querySelectorAll<HTMLElement>(':scope > .grid-motion__row > .grid-motion__tile'),
        ),
    )
    const spots = tileEls.map((list) => new Float32Array(list.length))
    const written = tileEls.map((list) => new Float32Array(list.length))
    const shifts = new Float32Array(nudges.length)
    let raf = 0
    let last = performance.now()
    let alive = true
    let visible = true
    let rect = root.getBoundingClientRect()
    const pointer = { x: 0, y: 0, inside: false }
    const started = performance.now()

    const play = (on: boolean) => {
      root.style.setProperty('--gm-play', on && !document.hidden ? 'running' : 'paused')
    }

    const rowX = (row: number, now: number, speed: number, direction: Direction) => {
      const drift = direction === 'left' ? -1 : direction === 'right' ? 1 : row % 2 ? 1 : -1
      const velocity = (reduce ? 0 : speed) * drift * PACE[row % PACE.length]
      const offset = row * layout.step * 0.37 + velocity * ((now - started) / 1000)
      return -layout.period + wrap(offset, layout.period)
    }

    const frame = (now: number) => {
      raf = 0
      if (!alive || !visible) return
      const s = settingsRef.current
      const dt = Math.min(0.05, Math.max(0.001, (now - last) / 1000))
      last = now

      const scale = rect.width ? root.clientWidth / rect.width : 1
      const halfWidth = root.clientWidth / 2 || 1
      const halfHeight = root.clientHeight / 2 || 1
      const px = (pointer.x - rect.left) * scale - halfWidth
      const py = (pointer.y - rect.top) * scale - halfHeight
      const inside =
        pointer.inside && Math.abs(px) <= halfWidth && Math.abs(py) <= halfHeight
      const lean = (s.tilt * Math.PI) / 180
      const turn = (s.angle * Math.PI) / 180
      const depth = layout.perspective
      let flatY = py
      let flatX = px
      if (lean > 0.0001) {
        flatY = (py * depth) / (depth * Math.cos(lean) + py * Math.sin(lean))
        flatX = (px * (depth - flatY * Math.sin(lean))) / depth
      }
      const planeX = flatX * Math.cos(turn) + flatY * Math.sin(turn)
      const planeY = -flatX * Math.sin(turn) + flatY * Math.cos(turn)
      const nudge = inside ? clamp(px / halfWidth, -1, 1) : 0
      const reach =
        (0.6 + 2.2 * s.spotlight) * Math.max(layout.tileWidth, layout.tileHeight)
      const settle = 1 - Math.exp(-dt / 0.22)
      let pending = false

      nudges.forEach((node, r) => {
        const target = reduce
          ? 0
          : s.parallax * layout.tileWidth * 1.2 * nudge * (r % 2 ? -1 : 1)
        shifts[r] += (target - shifts[r]) * (1 - Math.exp(-dt / INERTIA[r % INERTIA.length]))
        if (Math.abs(shifts[r]) < 0.05 && target === 0) shifts[r] = 0
        if (Math.abs(target - shifts[r]) > 0.05) pending = true
        node.style.transform =
          shifts[r] === 0 ? '' : `translate3d(${shifts[r].toFixed(2)}px, 0, 0)`

        const list = tileEls[r]
        const values = spots[r]
        const marks = written[r]
        if (!list || s.spotlight <= 0) return
        const x = rowX(r, now, s.speed, s.direction)
        const rowY =
          layout.top +
          r * (layout.tileHeight + s.gap) +
          layout.tileHeight / 2 -
          layout.planeHeight / 2
        const left = shifts[r] + x - layout.planeWidth / 2 + layout.tileWidth / 2
        const spotlightOn = inside
        const radius = Math.ceil(reach / layout.step) + 1
        const center = spotlightOn ? Math.round((planeX - left) / layout.step) : 0
        const from = spotlightOn ? Math.max(0, center - radius) : 0
        const to = spotlightOn ? Math.min(list.length - 1, center + radius) : -1
        for (let k = 0; k < list.length; k++) {
          const near = k >= from && k <= to
          if (!near && values[k] < 0.004) continue
          let wanted = 0
          if (near && spotlightOn) {
            const distance =
              Math.hypot(left + k * layout.step - planeX, rowY - planeY) / reach
            wanted = 1 - smoothstep(0.25, 1, distance)
          }
          values[k] += (wanted - values[k]) * settle
          if (Math.abs(wanted - values[k]) > 0.004) pending = true
          if (
            Math.abs(values[k] - marks[k]) > 0.004 ||
            (wanted === 0 && values[k] < 0.004 && marks[k] !== 0)
          ) {
            marks[k] = values[k] < 0.004 ? 0 : values[k]
            list[k].style.setProperty('--spot', marks[k].toFixed(3))
          }
        }
      })

      if (pending || inside) raf = requestAnimationFrame(frame)
    }

    const wake = () => {
      if (raf || !alive || !visible) return
      last = performance.now()
      raf = requestAnimationFrame(frame)
    }
    const onMove = (event: PointerEvent) => {
      pointer.x = event.clientX
      pointer.y = event.clientY
      pointer.inside = true
      rect = root.getBoundingClientRect()
      wake()
    }
    const onLeave = () => {
      pointer.inside = false
      wake()
    }
    const visibility = new IntersectionObserver(
      (entries) => {
        visible = entries.some((entry) => entry.isIntersecting && entry.intersectionRatio >= 0.08)
        play(visible)
        if (!visible && raf) {
          cancelAnimationFrame(raf)
          raf = 0
        }
      },
      { threshold: [0, 0.08] },
    )

    visibility.observe(root)
    root.addEventListener('pointermove', onMove, { passive: true })
    root.addEventListener('pointerleave', onLeave)
    const onHidden = () => play(visible)
    document.addEventListener('visibilitychange', onHidden)

    return () => {
      alive = false
      cancelAnimationFrame(raf)
      visibility.disconnect()
      root.removeEventListener('pointermove', onMove)
      root.removeEventListener('pointerleave', onLeave)
      document.removeEventListener('visibilitychange', onHidden)
    }
  }, [layout])

  const rowTiles = layout
    ? Array.from({ length: settings.rows }, (_, r) =>
        Array.from({ length: layout.perRow }, (_, j) =>
          tiles.length ? tiles[(r * layout.perRow + j) % tiles.length] : EMPTY,
        ),
      )
    : []
  const mask =
    settings.fade > 0
      ? `${feather('to right', settings.fade * 34)}, ${feather('to bottom', settings.fade * 44)}`
      : undefined

  return (
    <div
      ref={rootRef}
      className={`grid-motion${grayscale ? ' grid-motion--gray' : ''}${className ? ` ${className}` : ''}`}
      style={{
        '--gm-tile': tileColor ?? palette.tile,
        '--gm-text': textColor ?? palette.text,
        '--gm-border': palette.border,
        '--gm-radius': `${Math.max(0, radius)}px`,
        '--gm-dim': settings.dim,
        perspective: layout && settings.tilt > 0 ? `${layout.perspective}px` : undefined,
        '--gm-play': 'paused',
        maskImage: mask,
        WebkitMaskImage: mask,
        maskComposite: mask ? 'intersect' : undefined,
        WebkitMaskComposite: mask ? 'source-in' : undefined,
        ...style,
      } as CSSProperties}
    >
      {layout && (
        <div
          ref={planeRef}
          className="grid-motion__plane"
          aria-hidden="true"
          style={
            {
              width: layout.planeWidth,
              height: layout.planeHeight,
              transform: `translate(-50%, -50%) rotateX(${settings.tilt}deg) rotateZ(${settings.angle}deg)`,
              '--gm-gap': `${settings.gap}px`,
              '--gm-tile-w': `${layout.tileWidth}px`,
              '--gm-tile-h': `${layout.tileHeight}px`,
              '--gm-font': `${clamp(layout.tileHeight * 0.12, 12, 32)}px`,
            } as CSSProperties
          }
        >
          {rowTiles.map((sequence, r) => {
            const drift =
              settings.direction === 'left' ? -1 : settings.direction === 'right' ? 1 : r % 2 ? 1 : -1
            const velocity = Math.abs(settings.speed) * PACE[r % PACE.length]
            const duration = velocity > 0 ? layout.period / velocity : 0
            const phase = wrap(r * layout.step * 0.37, layout.period) / layout.period
            const delay =
              duration === 0 ? 0 : drift < 0 ? -(1 - phase) * duration : -phase * duration
            return (
              <div
                key={r}
                className="grid-motion__nudge"
                style={{ top: layout.top + r * (layout.tileHeight + settings.gap) }}
              >
                <div
                  className="grid-motion__row"
                  style={
                    {
                      '--gm-period': `${layout.period}px`,
                      animationName: drift < 0 ? 'grid-motion-left' : 'grid-motion-right',
                      animationDuration: `${duration}s`,
                      animationDelay: `${delay}s`,
                    } as CSSProperties
                  }
                >
                  {Array.from({ length: layout.copies * layout.perRow }, (_, k) => (
                    <Tile key={k} tile={sequence[k % layout.perRow]} />
                  ))}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
