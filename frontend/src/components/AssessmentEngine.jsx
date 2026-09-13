import { CheckCircle2, Cpu } from 'lucide-react'

const ASSESSMENT_MODEL = 'nvidia/nemotron-3.5-lightning:free'

function AssessmentEngine() {
  return (
    <section>
      <p className="mb-3 text-[11px] font-semibold uppercase tracking-[0.05em] text-sidebar-muted">
        Assessment engine
      </p>
      <div className="rounded-nasaq-sm border border-sidebar-muted/30 bg-brand-dark-alt/50 px-3 py-3">
        <div className="flex items-center gap-2">
          <Cpu size={15} className="shrink-0 text-sidebar-muted" aria-hidden="true" />
          <p className="truncate font-mono text-xs text-sidebar-text" title={ASSESSMENT_MODEL}>
            {ASSESSMENT_MODEL}
          </p>
        </div>
        <div className="mt-2 flex items-center gap-1.5 text-xs text-accent-disabled">
          <CheckCircle2 size={14} aria-hidden="true" />
          <span>Review engine ready</span>
        </div>
      </div>
    </section>
  )
}

export default AssessmentEngine
