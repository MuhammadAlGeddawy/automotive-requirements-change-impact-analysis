import { Link2, TriangleAlert } from 'lucide-react'
import { useState } from 'react'

const tierStyles = {
  high: 'bg-badge-high-bg text-badge-high-text',
  medium: 'bg-badge-medium-bg text-badge-medium-text',
  low: 'bg-badge-low-bg text-badge-low-text',
}

function shortenAtWord(text, limit = 92) {
  if (text.length <= limit) {
    return text
  }

  const shortened = text.slice(0, limit).replace(/\s+\S*$/, '')
  return `${shortened}…`
}

function ImpactBadge({ tier, label }) {
  return (
    <span className={`inline-flex whitespace-nowrap rounded-full px-2.5 py-1 text-[11px] font-bold ${tierStyles[tier]}`}>
      {tier.toUpperCase()}
      <span className="mx-1 opacity-60">·</span>
      <span className="font-semibold">{label}</span>
    </span>
  )
}

function Confidence({ value }) {
  return (
    <div className="flex min-w-28 items-center justify-end gap-2">
      <span className="font-mono text-xs text-body">{value.toFixed(2)}</span>
      <span className="h-1.5 w-16 overflow-hidden rounded-full bg-brand-dark/10">
        <span className="block h-full rounded-full bg-accent" style={{ width: `${value * 100}%` }} />
      </span>
    </div>
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
          Double-click reason, evidence, or engineering content to expand or collapse the full text.
        </p>
      </div>
      <div className="overflow-x-auto rounded-nasaq bg-white/75 shadow-sm">
        <table className="w-full min-w-[1200px] border-collapse text-left">
          <thead className="sticky top-0 border-b border-brand-dark/10 bg-white/95 text-[11px] uppercase tracking-[0.05em] text-muted">
            <tr>
              <th className="px-4 py-3 font-semibold">Artifact</th>
              <th className="px-4 py-3 font-semibold">Type</th>
              <th className="px-4 py-3 font-semibold">Impact</th>
              <th className="px-4 py-3 text-right font-semibold">Confidence</th>
              <th className="px-4 py-3 font-semibold">Traceability</th>
              <th className="w-[320px] px-4 py-3 font-semibold">Reason &amp; evidence</th>
              <th className="w-[300px] px-4 py-3 font-semibold">Engineering content</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-brand-dark/10 text-sm">
            {artifacts.map((artifact) => (
              <tr key={artifact.artifactId} className="transition-colors hover:bg-bg-cream/70">
                <td className="whitespace-nowrap px-4 py-4 font-mono font-semibold text-heading">
                  {artifact.artifactId}
                </td>
                <td className="whitespace-nowrap px-4 py-4 text-muted">{artifact.artifactType}</td>
                <td className="px-4 py-4">
                  <ImpactBadge tier={artifact.impactTier} label={artifact.llmLabel} />
                </td>
                <td className="px-4 py-4">
                  <Confidence value={artifact.confidence} />
                </td>
                <td className="px-4 py-4">
                  {artifact.traceability === 'graph_unlinked' ? (
                    <span className="inline-flex whitespace-nowrap items-center gap-1.5 rounded-nasaq-sm border border-dashed border-flag-unlinked-border bg-flag-unlinked-bg px-2 py-1 text-[11px] font-semibold text-flag-unlinked-text">
                      <TriangleAlert size={13} aria-hidden="true" />
                      GRAPH-UNLINKED
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1.5 text-xs text-body">
                      <Link2 size={14} className="text-accent" aria-hidden="true" />
                      Linked
                    </span>
                  )}
                </td>
                <td
                  className={`max-w-[320px] cursor-pointer px-4 py-4 text-body ${
                    expandedArtifacts.has(artifact.artifactId) ? 'whitespace-normal' : ''
                  }`}
                  aria-label={`Reason and evidence for ${artifact.artifactId}. Double-click to expand or collapse.`}
                  title={artifact.reason}
                  onDoubleClick={() => toggleArtifactContent(artifact.artifactId)}
                >
                  {artifact.reason ? (
                    <>
                      <p>
                        {expandedArtifacts.has(artifact.artifactId)
                          ? artifact.reason
                          : shortenAtWord(artifact.reason)}
                      </p>
                      {artifact.evidence?.length > 0 && (
                        <ul className="mt-1.5 space-y-1 text-xs text-muted">
                          {(expandedArtifacts.has(artifact.artifactId)
                            ? artifact.evidence
                            : artifact.evidence.slice(0, 1)
                          ).map((item, index) => (
                            <li key={index} className="flex gap-1.5">
                              <span className="shrink-0 text-accent">•</span>
                              <span>
                                {expandedArtifacts.has(artifact.artifactId)
                                  ? item
                                  : shortenAtWord(item, 60)}
                              </span>
                            </li>
                          ))}
                        </ul>
                      )}
                    </>
                  ) : (
                    <span className="text-muted">—</span>
                  )}
                </td>
                <td
                  className={`max-w-[300px] cursor-pointer px-4 py-4 text-body ${
                    expandedArtifacts.has(artifact.artifactId) ? 'whitespace-normal' : ''
                  }`}
                  aria-label={`Engineering content for ${artifact.artifactId}. Double-click to expand or collapse.`}
                  title={artifact.engineeringContent}
                  onDoubleClick={() => toggleArtifactContent(artifact.artifactId)}
                >
                  {expandedArtifacts.has(artifact.artifactId)
                    ? artifact.engineeringContent
                    : shortenAtWord(artifact.engineeringContent)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}

export default ImpactedArtifactsTable
