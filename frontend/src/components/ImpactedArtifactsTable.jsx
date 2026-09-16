import { Link2, TriangleAlert } from 'lucide-react'
import { useState } from 'react'
import { IMPACT_STATUS, impactStatusOf } from '../lib/impactStatus'

function StatusBadge({ status }) {
  const meta = IMPACT_STATUS[status]
  return (
    <span className={`inline-flex shrink-0 items-center whitespace-nowrap rounded-full px-2.5 py-1 text-[11px] font-bold ${meta.badge}`}>
      {meta.label}
    </span>
  )
}

function ArtifactCard({ artifact, isExpanded, onToggle }) {
  const status = impactStatusOf(artifact.llmLabel)
  const meta = IMPACT_STATUS[status]
  const isUnlinked = artifact.traceability === 'graph_unlinked'

  return (
    <article
      className={`rounded-nasaq border bg-white/75 p-5 shadow-sm ${
        isUnlinked ? 'border-dashed border-flag-unlinked-border' : 'border-brand-dark/10'
      }`}
    >
      <header className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="truncate font-mono text-sm font-semibold text-heading">{artifact.artifactId}</p>
          <p className="text-xs text-muted">{artifact.artifactType.replace(/_/g, ' ')}</p>
        </div>
        <StatusBadge status={status} />
      </header>

      <div className="mt-3 flex items-end justify-between gap-4">
        <p className="text-sm leading-6 text-body">{artifact.reason || 'No rationale provided.'}</p>
        <div className="shrink-0 text-right">
          <p className="font-mono text-sm font-semibold text-heading">
            {Math.round(artifact.confidence * 100)}%
          </p>
          <p className="text-[10px] uppercase tracking-wide text-muted">confidence</p>
        </div>
      </div>

      {artifact.evidence?.length > 0 && (
        <div className={`mt-3 rounded-l-none rounded-r-nasaq-sm border-l-4 px-3 py-2 ${meta.border} ${meta.tint}`}>
          <p className="text-[10px] font-semibold uppercase tracking-wide text-muted">Evidence</p>
          <ul className="mt-1 space-y-1 text-xs text-body">
            {artifact.evidence.map((item, index) => (
              <li key={index}>{item}</li>
            ))}
          </ul>
        </div>
      )}

      <footer className="mt-3 flex items-center justify-between gap-3 border-t border-brand-dark/10 pt-3">
        {isUnlinked ? (
          <span className="inline-flex items-center gap-1.5 rounded-nasaq-sm border border-dashed border-flag-unlinked-border bg-flag-unlinked-bg px-2 py-1 text-[11px] font-semibold text-flag-unlinked-text">
            <TriangleAlert size={13} aria-hidden="true" />
            Not in traceability graph
          </span>
        ) : (
          <span className="inline-flex items-center gap-1.5 text-xs text-body">
            <Link2 size={14} className="text-accent" aria-hidden="true" />
            Linked
          </span>
        )}
      </footer>

      <div
        className="mt-3 cursor-pointer rounded-nasaq-sm border border-brand-dark/10 bg-bg-cream/60 px-3 py-2 transition-colors hover:border-brand-dark/20"
        aria-label={`Engineering content for ${artifact.artifactId}. Double-click to expand or collapse.`}
        title={isExpanded ? undefined : artifact.engineeringContent}
        onDoubleClick={onToggle}
      >
        <p className="text-[10px] font-semibold uppercase tracking-wide text-muted">Engineering content</p>
        <p className={`mt-1 text-xs leading-5 text-body ${isExpanded ? 'whitespace-normal' : 'line-clamp-2'}`}>
          {artifact.engineeringContent}
        </p>
      </div>
    </article>
  )
}

function ImpactedArtifactsTable({ artifacts }) {
  const [expandedArtifacts, setExpandedArtifacts] = useState(() => new Set())

  const toggleArtifactContent = (artifactId) => {
    setExpandedArtifacts((current) => {
      const next = new Set(current)
      if (next.has(artifactId)) {
        next.delete(artifactId)
      } else {
        next.add(artifactId)
      }
      return next
    })
  }

  return (
    <section aria-labelledby="impacted-artifacts-title">
      <div className="mb-4">
        <p className="text-[11px] font-semibold uppercase tracking-[0.05em] text-muted">
          Assessment output
        </p>
        <h2 id="impacted-artifacts-title" className="mt-1 text-xl font-bold text-heading">
          Impacted artifacts
        </h2>
        <p className="mt-1 text-xs text-muted">
          Double-click a card's engineering content to expand or collapse the full text.
        </p>
      </div>
      <div className="grid gap-4">
        {artifacts.map((artifact) => (
          <ArtifactCard
            key={artifact.artifactId}
            artifact={artifact}
            isExpanded={expandedArtifacts.has(artifact.artifactId)}
            onToggle={() => toggleArtifactContent(artifact.artifactId)}
          />
        ))}
      </div>
    </section>
  )
}

export default ImpactedArtifactsTable
