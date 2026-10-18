import { useId, useState, type DragEvent, type ChangeEvent } from 'react'
import { HugeiconsIcon } from '@hugeicons/react'
import { Upload01Icon, Video01Icon } from '@/icons'

interface VideoDropzoneProps {
  file: File | null
  onFileChange: (file: File | null) => void
  disabled?: boolean
}

function formatBytes(size: number) {
  if (size < 1024 * 1024) return `${Math.max(1, Math.round(size / 1024))} KB`
  return `${(size / (1024 * 1024)).toFixed(1)} MB`
}

export function VideoDropzone({
  file,
  onFileChange,
  disabled = false,
}: VideoDropzoneProps) {
  const inputId = useId()
  const [dragging, setDragging] = useState(false)

  function handleFiles(files: FileList | null) {
    const next = files?.[0] ?? null
    onFileChange(next)
  }

  function handleDragOver(event: DragEvent<HTMLLabelElement>) {
    event.preventDefault()
    if (!disabled) setDragging(true)
  }

  function handleDragLeave() {
    setDragging(false)
  }

  function handleDrop(event: DragEvent<HTMLLabelElement>) {
    event.preventDefault()
    setDragging(false)
    if (disabled) return
    handleFiles(event.dataTransfer.files)
  }

  function handleChange(event: ChangeEvent<HTMLInputElement>) {
    handleFiles(event.target.files)
  }

  return (
    <div className="relative z-10 space-y-3">
      <label
        htmlFor={inputId}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        data-active={dragging ? 'true' : 'false'}
        data-filled={file ? 'true' : 'false'}
        className={`dropzone-court flex min-h-[13.5rem] cursor-pointer flex-col items-center justify-center px-6 py-12 text-center ${
          disabled ? 'cursor-not-allowed opacity-60' : ''
        }`}
      >
        <span className="relative z-[1] mb-4 inline-flex h-12 w-12 items-center justify-center rounded-full bg-[var(--color-ink)] text-white">
          <HugeiconsIcon
            icon={file ? Video01Icon : Upload01Icon}
            size={22}
            strokeWidth={1.8}
          />
        </span>
        <span className="relative z-[1] max-w-md text-balance font-[family-name:var(--font-display)] text-2xl font-semibold leading-tight text-[var(--color-ink)]">
          {file ? file.name : 'Drop your rally clip here'}
        </span>
        <span className="relative z-[1] mt-2 max-w-sm text-sm leading-relaxed text-[var(--color-muted)]">
          {file
            ? `${formatBytes(file.size)} · ready for the coach`
            : 'Or click to browse · MP4 or MOV · up to 100 MB · under 30 seconds'}
        </span>
        <input
          id={inputId}
          type="file"
          accept=".mp4,.mov,video/mp4,video/quicktime"
          className="sr-only"
          disabled={disabled}
          onChange={handleChange}
        />
      </label>
      {file ? (
        <button
          type="button"
          className="text-sm font-medium text-[var(--color-accent)] underline-offset-4 hover:underline"
          onClick={() => onFileChange(null)}
          disabled={disabled}
        >
          Choose a different clip
        </button>
      ) : null}
    </div>
  )
}
