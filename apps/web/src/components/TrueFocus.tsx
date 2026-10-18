import {
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
  type CSSProperties,
} from 'react'
import { motion, useReducedMotion } from 'motion/react'
import './TrueFocus.css'

const CORNERS = ['top-left', 'top-right', 'bottom-left', 'bottom-right'] as const
const FRAME_GAP = 8
const SMOOTH_EASE = [0.65, 0, 0.35, 1] as const
const SMOOTH_CSS = 'cubic-bezier(0.65, 0, 0.35, 1)'
const SPRING_CSS = 'cubic-bezier(0.34, 1.56, 0.64, 1)'

const useIsomorphicLayoutEffect =
  typeof window !== 'undefined' ? useLayoutEffect : useEffect

type FocusStyle = 'brackets' | 'box' | 'underline' | 'highlight'
type FocusRect = { x: number; y: number; width: number; height: number }

export interface TrueFocusProps {
  sentence?: string
  separator?: string
  manualMode?: boolean
  focusStyle?: FocusStyle
  order?: 'sequential' | 'random'
  easing?: 'smooth' | 'spring'
  blurAmount?: number
  focusScale?: number
  borderColor?: string
  highlightColor?: string
  glowColor?: string
  animationDuration?: number
  pauseBetweenAnimations?: number
  cornerSize?: number
  borderWidth?: number
  unfocusedOpacity?: number
  className?: string
}

export default function TrueFocus({
  sentence = 'True Focus',
  separator = ' ',
  manualMode = false,
  focusStyle = 'brackets',
  order = 'sequential',
  easing = 'smooth',
  blurAmount = 5,
  focusScale = 1,
  borderColor = 'green',
  highlightColor,
  glowColor = 'transparent',
  animationDuration = 0.5,
  pauseBetweenAnimations = 1,
  cornerSize = 16,
  borderWidth = 3,
  unfocusedOpacity = 1,
  className = '',
}: TrueFocusProps) {
  const words = sentence.split(separator).filter((word) => word.trim() !== '')
  const [currentIndex, setCurrentIndex] = useState(0)
  const [focusRect, setFocusRect] = useState<FocusRect | null>(null)
  const [hovered, setHovered] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)
  const wordRefs = useRef<Array<HTMLSpanElement | null>>([])
  const reduceMotion = useReducedMotion()
  const duration = reduceMotion ? 0 : animationDuration
  const activeIndex =
    words.length === 0
      ? -1
      : manualMode && !hovered
        ? -1
        : currentIndex % words.length
  const spring = easing === 'spring' && !reduceMotion
  const transition = spring
    ? { type: 'spring' as const, stiffness: 320, damping: 28, mass: 0.8 }
    : { duration, ease: SMOOTH_EASE }

  useEffect(() => {
    if (manualMode || words.length < 2) return undefined
    const interval = setInterval(
      () => {
        const roll = Math.random()
        setCurrentIndex((prev) => {
          const current = prev % words.length
          if (order !== 'random') return (current + 1) % words.length
          const next = Math.floor(roll * (words.length - 1))
          return next >= current ? next + 1 : next
        })
      },
      (animationDuration + pauseBetweenAnimations) * 1000,
    )
    return () => clearInterval(interval)
  }, [manualMode, animationDuration, pauseBetweenAnimations, words.length, order])

  useIsomorphicLayoutEffect(() => {
    const container = containerRef.current
    const word = activeIndex >= 0 ? wordRefs.current[activeIndex] : null
    if (!container || !word) {
      setFocusRect(null)
      return undefined
    }

    const measure = () => {
      const next = {
        x: word.offsetLeft,
        y: word.offsetTop,
        width: word.offsetWidth,
        height: word.offsetHeight,
      }
      setFocusRect((prev) =>
        prev &&
        prev.x === next.x &&
        prev.y === next.y &&
        prev.width === next.width &&
        prev.height === next.height
          ? prev
          : next,
      )
    }

    measure()
    if (typeof ResizeObserver === 'undefined') return undefined
    const observer = new ResizeObserver(measure)
    observer.observe(container)
    wordRefs.current.forEach((node) => {
      if (node) observer.observe(node)
    })
    return () => observer.disconnect()
  }, [activeIndex, sentence, separator])

  const frame =
    focusRect == null
      ? null
      : {
          x: focusRect.x - (focusRect.width * (focusScale - 1)) / 2,
          y: focusRect.y - (focusRect.height * (focusScale - 1)) / 2,
          width: focusRect.width * focusScale,
          height: focusRect.height * focusScale,
        }

  const corners =
    frame == null
      ? null
      : {
          'top-left': { left: frame.x - FRAME_GAP, top: frame.y - FRAME_GAP },
          'top-right': {
            left: frame.x + frame.width + FRAME_GAP - cornerSize,
            top: frame.y - FRAME_GAP,
          },
          'bottom-left': {
            left: frame.x - FRAME_GAP,
            top: frame.y + frame.height + FRAME_GAP - cornerSize,
          },
          'bottom-right': {
            left: frame.x + frame.width + FRAME_GAP - cornerSize,
            top: frame.y + frame.height + FRAME_GAP - cornerSize,
          },
        }

  const shapes =
    frame == null
      ? null
      : {
          box: {
            left: frame.x - FRAME_GAP,
            top: frame.y - FRAME_GAP,
            width: frame.width + FRAME_GAP * 2,
            height: frame.height + FRAME_GAP * 2,
          },
          underline: {
            left: frame.x,
            top: frame.y + frame.height + FRAME_GAP * 0.4,
            width: frame.width,
            height: borderWidth,
          },
          highlight: {
            left: frame.x - frame.height * 0.14,
            top: frame.y + frame.height * 0.04,
            width: frame.width + frame.height * 0.28,
            height: frame.height * 0.92,
          },
        }

  const frameStyle = {
    '--border-color': borderColor,
    '--highlight-color': `color-mix(in srgb, ${highlightColor ?? borderColor} 30%, transparent)`,
    '--glow-color': glowColor,
    '--corner-size': `${cornerSize}px`,
    '--border-width': `${borderWidth}px`,
  } as CSSProperties

  return (
    <div
      className={`focus-container${className ? ` ${className}` : ''}`}
      ref={containerRef}
      style={frameStyle}
      onMouseEnter={() => {
        if (!manualMode) return
        setHovered(true)
        setCurrentIndex(0)
      }}
      onMouseLeave={() => {
        if (manualMode) setHovered(false)
      }}
    >
      {focusStyle === 'highlight' && shapes ? (
        <motion.span
          className="focus-highlight"
          aria-hidden="true"
          initial={false}
          animate={{ ...shapes.highlight, opacity: 1 }}
          transition={transition}
        />
      ) : null}

      {words.map((word, index) => {
        const isActive = index === activeIndex
        const dimmed = activeIndex >= 0 && !isActive
        return (
          <span
            key={`${word}-${index}`}
            ref={(el) => {
              wordRefs.current[index] = el
            }}
            className={`focus-word${manualMode ? ' manual' : ''}${isActive && !manualMode ? ' active' : ''}`}
            style={{
              filter: dimmed ? `blur(${blurAmount}px)` : 'none',
              opacity: dimmed ? unfocusedOpacity : 1,
              transform:
                focusScale !== 1 && isActive ? `scale(${focusScale})` : undefined,
              transition: `filter ${duration}s ease, opacity ${duration}s ease, transform ${duration}s ${spring ? SPRING_CSS : SMOOTH_CSS}`,
            }}
            onMouseEnter={() => {
              if (!manualMode) return
              setHovered(true)
              setCurrentIndex(index)
            }}
          >
            {word}
          </span>
        )
      })}

      {shapes && corners && focusStyle !== 'highlight' ? (
        <div className="focus-frame" aria-hidden="true">
          {focusStyle === 'box' ? (
            <motion.span
              className="focus-box"
              initial={false}
              animate={{ ...shapes.box, opacity: 1 }}
              transition={transition}
            />
          ) : null}
          {focusStyle === 'underline' ? (
            <motion.span
              className="focus-underline"
              initial={false}
              animate={{ ...shapes.underline, opacity: 1 }}
              transition={transition}
            />
          ) : null}
          {focusStyle !== 'box' && focusStyle !== 'underline'
            ? CORNERS.map((corner) => (
                <motion.span
                  key={corner}
                  className={`corner ${corner}`}
                  initial={false}
                  animate={{ ...corners[corner], opacity: 1 }}
                  transition={transition}
                />
              ))
            : null}
        </div>
      ) : null}
    </div>
  )
}
