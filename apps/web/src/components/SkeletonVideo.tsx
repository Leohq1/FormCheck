import { useEffect, useRef, useState } from 'react'
import { POSE_CONNECTIONS, createPoseClock, nextVideoTimestamp, objectFitCover } from '@/lib/poseGeometry'
import type { PosePoint } from '@/lib/poseTracker'

interface SkeletonVideoProps {
  src: string
  label: string
}

const MIN_VISIBILITY = 0.45
const INFER_EDGE = 256

function visible(point: PosePoint | undefined): point is PosePoint {
  if (!point) return false
  const score = point.visibility ?? point.presence ?? 1
  return score >= MIN_VISIBILITY
}

function clock(seconds: number): string {
  const total = Math.max(0, Math.floor(seconds))
  const minutes = Math.floor(total / 60)
  const remain = total % 60
  return `${minutes}:${String(remain).padStart(2, '0')}`
}

export function SkeletonVideo({ src, label }: SkeletonVideoProps) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [status, setStatus] = useState('Loading pose model…')
  const [paused, setPaused] = useState(true)
  const [time, setTime] = useState(0)
  const [duration, setDuration] = useState(0)

  useEffect(() => {
    const video = videoRef.current
    const canvas = canvasRef.current
    if (!video || !canvas) return undefined

    let stopped = false
    let frameHandle = 0
    let playbackGeneration = 0
    const clock = createPoseClock()
    let landmarks: PosePoint[] | null = null
    let usingVideoFrames = false
    type Landmarker = {
      detectForVideo: (frame: CanvasImageSource, timestamp: number) => { landmarks: PosePoint[][] }
      close: () => void
    }
    let landmarker: Landmarker | null = null
    let sparePromise: Promise<Landmarker> | null = null
    let replaying = false
    const loadLandmarker = () =>
      import('@/lib/poseTracker').then((module) => module.createPoseLandmarker())
    const warmSpare = () => {
      sparePromise ??= loadLandmarker()
    }
    const context = canvas.getContext('2d')
    const snapshot = document.createElement('canvas')
    const snapshotContext = snapshot.getContext('2d', { alpha: false })
    const inference = document.createElement('canvas')
    const inferenceContext = inference.getContext('2d', { alpha: false })
    if (!context || !snapshotContext || !inferenceContext) return undefined

    const landmarkerPromise = loadLandmarker()

    const paint = () => {
      const boxWidth = video.clientWidth
      const boxHeight = video.clientHeight
      if (!boxWidth || !boxHeight || snapshot.width === 0) return
      const ratio = window.devicePixelRatio || 1
      const pixelWidth = Math.round(boxWidth * ratio)
      const pixelHeight = Math.round(boxHeight * ratio)
      if (canvas.width !== pixelWidth || canvas.height !== pixelHeight) {
        canvas.width = pixelWidth
        canvas.height = pixelHeight
      }
      context.setTransform(ratio, 0, 0, ratio, 0, 0)
      const frame = objectFitCover(boxWidth, boxHeight, snapshot.width, snapshot.height)
      context.clearRect(0, 0, boxWidth, boxHeight)
      context.drawImage(
        snapshot,
        0,
        0,
        snapshot.width,
        snapshot.height,
        frame.offsetX,
        frame.offsetY,
        frame.drawWidth,
        frame.drawHeight,
      )
      if (!landmarks) return

      const pointAt = (index: number) => {
        const point = landmarks?.[index]
        if (!visible(point)) return null
        return {
          x: frame.offsetX + point.x * frame.drawWidth,
          y: frame.offsetY + point.y * frame.drawHeight,
        }
      }

      context.lineWidth = Math.max(2, boxWidth / 180)
      context.lineCap = 'round'
      context.strokeStyle = 'rgba(255, 255, 255, 0.92)'
      context.fillStyle = '#ae3121'
      context.beginPath()
      for (const [start, end] of POSE_CONNECTIONS) {
        const a = pointAt(start)
        const b = pointAt(end)
        if (!a || !b) continue
        context.moveTo(a.x, a.y)
        context.lineTo(b.x, b.y)
      }
      context.stroke()

      const joint = Math.max(2.5, boxWidth / 140)
      for (let index = 0; index < landmarks.length; index += 1) {
        const point = pointAt(index)
        if (!point) continue
        context.beginPath()
        context.arc(point.x, point.y, joint, 0, Math.PI * 2)
        context.fill()
      }
    }

    const beginReplay = () => {
      if (replaying) return
      replaying = true
      const pending = sparePromise ?? loadLandmarker()
      sparePromise = null
      warmSpare()
      Object.assign(clock, createPoseClock())
      landmarks = null
      const generation = playbackGeneration
      void pending
        .then((fresh) => {
          replaying = false
          if (stopped || generation !== playbackGeneration) {
            fresh.close()
            return
          }
          landmarker?.close()
          landmarker = fresh
          detect()
        })
        .catch(() => {
          replaying = false
        })
    }

    const detect = () => {
      if (stopped || replaying || !landmarker || video.readyState < 2) return
      const media = video.currentTime * 1000
      if (clock.lastMedia >= 0 && media + 5 < clock.lastMedia) {
        beginReplay()
        return
      }
      const mediaWidth = video.videoWidth
      const mediaHeight = video.videoHeight
      if (!mediaWidth || !mediaHeight) return
      if (snapshot.width !== mediaWidth || snapshot.height !== mediaHeight) {
        snapshot.width = mediaWidth
        snapshot.height = mediaHeight
      }
      snapshotContext.drawImage(video, 0, 0, mediaWidth, mediaHeight)
      const scale = INFER_EDGE / Math.max(mediaWidth, mediaHeight)
      const inferWidth = Math.max(1, Math.round(mediaWidth * scale))
      const inferHeight = Math.max(1, Math.round(mediaHeight * scale))
      if (inference.width !== inferWidth || inference.height !== inferHeight) {
        inference.width = inferWidth
        inference.height = inferHeight
      }
      inferenceContext.drawImage(snapshot, 0, 0, inferWidth, inferHeight)
      const timestamp = nextVideoTimestamp(video.currentTime * 1000, clock)
      const result = landmarker.detectForVideo(inference, timestamp)
      landmarks = result.landmarks[0] ?? null
      paint()
    }

    const cancelFrame = () => {
      if (usingVideoFrames && typeof video.cancelVideoFrameCallback === 'function') {
        video.cancelVideoFrameCallback(frameHandle)
      }
      cancelAnimationFrame(frameHandle)
      frameHandle = 0
    }

    const watch = (generation: number) => {
      if (stopped || generation !== playbackGeneration || video.paused || video.ended) return
      detect()
      if (stopped || generation !== playbackGeneration || video.paused || video.ended) return
      if (typeof video.requestVideoFrameCallback === 'function') {
        usingVideoFrames = true
        frameHandle = video.requestVideoFrameCallback(() => watch(generation))
      } else {
        usingVideoFrames = false
        frameHandle = requestAnimationFrame(() => watch(generation))
      }
    }

    const onPlay = () => {
      playbackGeneration += 1
      cancelFrame()
      setPaused(false)
      watch(playbackGeneration)
    }
    const onPause = () => {
      playbackGeneration += 1
      cancelFrame()
      setPaused(true)
      detect()
    }
    const onTime = () => {
      setTime(video.currentTime)
      if (Number.isFinite(video.duration)) setDuration(video.duration)
    }

    landmarkerPromise
      .then((created) => {
        landmarker = created
        warmSpare()
        if (!stopped) {
          setStatus('MediaPipe skeleton')
          detect()
        }
      })
      .catch(() => {
        if (!stopped) setStatus('Skeleton unavailable')
      })

    video.addEventListener('play', onPlay)
    video.addEventListener('pause', onPause)
    video.addEventListener('ended', onPause)
    video.addEventListener('loadeddata', detect)
    video.addEventListener('seeked', detect)
    video.addEventListener('timeupdate', onTime)
    video.addEventListener('durationchange', onTime)
    if (video.readyState >= 2) detect()

    return () => {
      stopped = true
      if (usingVideoFrames && typeof video.cancelVideoFrameCallback === 'function') {
        video.cancelVideoFrameCallback(frameHandle)
      }
      cancelAnimationFrame(frameHandle)
      video.removeEventListener('play', onPlay)
      video.removeEventListener('pause', onPause)
      video.removeEventListener('ended', onPause)
      video.removeEventListener('loadeddata', detect)
      video.removeEventListener('seeked', detect)
      video.removeEventListener('timeupdate', onTime)
      video.removeEventListener('durationchange', onTime)
      void landmarkerPromise.then((created) => created.close()).catch(() => undefined)
      void sparePromise?.then((created) => created.close()).catch(() => undefined)
    }
  }, [src])

  const toggle = () => {
    const video = videoRef.current
    if (!video) return
    if (video.paused) void video.play()
    else video.pause()
  }

  const seek = (next: number) => {
    const video = videoRef.current
    if (!video) return
    video.currentTime = next
    setTime(next)
  }

  return (
    <div className="video-tape__stage">
      <video
        ref={videoRef}
        className="video-tape__media"
        playsInline
        preload="auto"
        src={src}
        aria-label={label}
      >
        <track kind="captions" />
      </video>
      <canvas ref={canvasRef} className="video-tape__skeleton" aria-hidden="true" />
      <p className="video-tape__status">{status}</p>
      <div className="video-tape__controls">
        <button type="button" className="video-tape__play" onClick={toggle}>
          {paused ? 'Play' : 'Pause'}
        </button>
        <input
          className="video-tape__scrub"
          type="range"
          min={0}
          max={duration || 0}
          step={0.01}
          value={Math.min(time, duration || 0)}
          aria-label={`${label} playback position`}
          aria-valuetext={clock(time)}
          onChange={(event) => seek(Number(event.target.value))}
        />
        <span className="video-tape__time">
          {clock(time)} / {clock(duration)}
        </span>
      </div>
    </div>
  )
}
