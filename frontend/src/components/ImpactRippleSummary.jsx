import { ArrowRight } from 'lucide-react'
import { IMPACT_STATUS } from '../lib/impactStatus'

function countByStatus(artifacts) {
  const counts = { DIRECT: 0, POTENTIAL: 0, NO_IMPACT: 0 }
  for (const artifact of artifacts) {
    if (counts[artifact.llmLabel] !== undefined) {
      counts[artifact.llmLabel] += 1
    }
  }
  return counts
}

function StatChip({ status, count }) {
  const meta = IMPACT_STATUS[status]
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full border border-brand-dark/10 bg-white/70 py-1 pl-1.5 pr-3 text-xs font-semibold text-body">
      <span className={`h-2 w-2 rounded-full ${meta.dot}`} aria-hidden="true" />
      {count} {meta.label.toLowerCase()}
    </span>
  )
}

function ImpactRippleSummary({ request, artifacts }) {
  const counts = countByStatus(artifacts)

  return (
    <section
      aria-label="Impact ripple summary"
      className="flex flex-wrap items-center justify-between gap-4 rounded-nasaq border border-brand-dark/10 bg-white/75 px-5 py-4 shadow-sm"
    >
      <div className="min-w-0">
        <p className="text-[11px] font-semibold uppercase tracking-[0.05em] text-muted">
          Impact ripple · {request?.requirementId}
        </p>
        {request && (
          <p className="mt-1 flex flex-wrap items-center gap-2 text-sm text-body">
            <span className="font-mono font-semibold text-heading">{request.changedValueOld}</span>
            <ArrowRight size={14} className="shrink-0 text-muted" aria-hidden="true" />
            <span className="font-mono font-semibold text-heading">{request.changedValueNew}</span>
          </p>
        )}
      </div>
      <div className="flex flex-wrap gap-2">
        <StatChip status="DIRECT" count={counts.DIRECT} />
        <StatChip status="POTENTIAL" count={counts.POTENTIAL} />
        <StatChip status="NO_IMPACT" count={counts.NO_IMPACT} />
      </div>
    </section>
  )
}

export default ImpactRippleSummary
