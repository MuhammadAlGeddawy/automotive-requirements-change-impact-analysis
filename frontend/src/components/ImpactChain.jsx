import { ArrowRight } from 'lucide-react'
import { useState } from 'react'

function ImpactChain({ impactChain, artifacts }) {
  const [selectedArtifactId, setSelectedArtifactId] = useState(artifacts[0]?.artifactId || '')
  const selectedArtifact = artifacts.find((artifact) => artifact.artifactId === selectedArtifactId)
  const selectedPath = selectedArtifact?.traceabilityPaths?.[0] || []
  const displayedPath = selectedPath.length > 0
    ? selectedPath
    : impactChain

  return (
    <section aria-labelledby="impact-chain-title">
      <div className="mb-4">
        <p className="text-[11px] font-semibold uppercase tracking-[0.05em] text-muted">
          Traceability
        </p>
        <h2 id="impact-chain-title" className="mt-1 text-xl font-bold text-heading">
          Impact chain
        </h2>
      </div>
      <label className="mb-4 flex max-w-md items-center gap-3 text-sm text-body">
        <span className="shrink-0 text-xs font-semibold uppercase tracking-[0.05em] text-muted">
          Show path for
        </span>
        <select
          value={selectedArtifactId}
          onChange={(event) => setSelectedArtifactId(event.target.value)}
          className="min-w-0 flex-1 rounded-nasaq-sm border border-brand-dark/15 bg-white/70 px-3 py-2 font-mono text-xs text-heading outline-none focus:border-accent"
        >
          {artifacts.map((artifact) => (
            <option key={artifact.artifactId} value={artifact.artifactId}>
              {artifact.artifactId}
            </option>
          ))}
        </select>
      </label>
      {selectedPath.length === 0 && (
        <p className="mb-3 text-xs text-muted">
          No formal traceability path exists for this artifact.
        </p>
      )}
      <div className="flex items-stretch gap-2 overflow-x-auto pb-2">
        {displayedPath.map((artifact, index) => (
          <div key={artifact.id} className="flex shrink-0 items-center gap-2">
            <article className={`glass-surface w-44 p-4 ${
              artifact.id === selectedArtifactId ? 'ring-2 ring-accent/60' : ''
            }`}>
              <p className="font-mono text-sm font-semibold text-heading">{artifact.id}</p>
              <p className="mt-2 text-xs leading-4 text-muted">{artifact.type}</p>
            </article>
            {index < impactChain.length - 1 && (
              <ArrowRight size={18} className="shrink-0 text-accent" aria-hidden="true" />
            )}
          </div>
        ))}
      </div>
    </section>
  )
}

export default ImpactChain
