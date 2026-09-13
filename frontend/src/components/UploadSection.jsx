import { FileUp } from 'lucide-react'

function UploadSection() {
  const handleUpload = () => {
    console.log('Upload interaction requested')
  }

  return (
    <section>
      <p className="mb-3 text-[11px] font-semibold uppercase tracking-[0.05em] text-sidebar-muted">
        Engineering artifacts
      </p>
      <button
        type="button"
        onClick={handleUpload}
        onDrop={handleUpload}
        className="flex w-full flex-col items-center gap-2 rounded-nasaq-sm border border-dashed border-sidebar-muted/60 px-4 py-6 text-center text-sm text-sidebar-text transition-colors hover:border-accent hover:bg-brand-dark-alt/60"
      >
        <FileUp size={20} strokeWidth={1.8} aria-hidden="true" />
        <span>Drop artifacts here or browse</span>
      </button>
    </section>
  )
}

export default UploadSection
