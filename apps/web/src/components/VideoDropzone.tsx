import { useId, useState, type DragEvent, type ChangeEvent } from 'react'

interface VideoDropzoneProps {
  file: File | null
  onFileChange: (file: File | null) => void
  disabled?: boolean
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
    <div className="space-y-2">
      <label
        htmlFor={inputId}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`flex cursor-pointer flex-col items-center justify-center rounded-sm border-2 border-dashed px-6 py-10 text-center transition-colors ${
          dragging
            ? 'border-[var(--color-accent)] bg-[var(--color-accent-soft)]'
            : 'border-[var(--color-border)] bg-[var(--color-surface)] hover:border-[var(--color-accent)]'
        } ${disabled ? 'cursor-not-allowed opacity-60' : ''}`}
      >
        <span className="text-base font-medium text-[var(--color-ink)]">
          {file ? file.name : 'Drop your video here, or click to browse'}
        </span>
        <span className="mt-2 text-sm text-[var(--color-muted)]">
          MP4 or MOV, up to 100 MB
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
          className="text-sm text-[var(--color-accent)] underline"
          onClick={() => onFileChange(null)}
          disabled={disabled}
        >
          Clear file
        </button>
      ) : null}
    </div>
  )
}
