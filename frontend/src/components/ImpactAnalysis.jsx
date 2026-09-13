import { LoaderCircle, Play } from 'lucide-react'
import { useState } from 'react'
import { analyzeChange } from '../api'
import ImpactChain from './ImpactChain'
import ImpactedArtifactsTable from './ImpactedArtifactsTable'

const stats = [
  ['High Impact', 'highImpact', 'Directly affected', 'text-badge-high-text'],
  ['Medium Impact', 'mediumImpact', 'Requires review', 'text-badge-medium-text'],
  ['Low Impact', 'lowImpact', 'No impact identified', 'text-badge-low-text'],
  ['Total Affected', 'totalAffected', 'Ranked artifacts', 'text-heading'],
]

function KpiCards({ results }) {
  return (
    <section aria-label="Impact summary" className="grid animate-fade-in gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {stats.map(([label, field, caption, colorClass]) => (
        <article key={field} className="glass-surface p-5">
          <p className="text-[11px] font-semibold uppercase tracking-[0.05em] text-muted">
            {label}
          </p>
          <p className={`mt-3 text-4xl font-bold tracking-tight ${colorClass}`}>
            {results[field]}
          </p>
          <p className="mt-1 text-sm text-body">{caption}</p>
        </article>
      ))}
    </section>
  )
}

function ImpactAnalysis({ changeId, hasSelection }) {
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [results, setResults] = useState(null)
  const [error, setError] = useState('')

  const handleAnalyze = async () => {
    if (!hasSelection || isAnalyzing) {
      return
    }

    setResults(null)
    setError('')
    setIsAnalyzing(true)
    try {
      const analysis = await analyzeChange(changeId)
      setResults(analysis)
    } catch (requestError) {
      setError(requestError.message || 'Analysis failed. Check the backend and OpenRouter API key.')
    } finally {
      setIsAnalyzing(false)
    }
  }

  return (
    <section className="space-y-6">
      <button
        type="button"
        disabled={!hasSelection || isAnalyzing}
        onClick={handleAnalyze}
        className="flex w-full items-center justify-center gap-2 rounded-nasaq-sm bg-accent px-5 py-3.5 text-sm font-semibold text-white transition-colors hover:bg-accent-hover active:bg-accent-hover disabled:cursor-not-allowed disabled:bg-accent-disabled"
      >
        {isAnalyzing ? (
          <>
            <LoaderCircle size={18} className="animate-spin" aria-hidden="true" />
            Analyzing impact...
          </>
        ) : (
          <>
            <Play size={17} fill="currentColor" aria-hidden="true" />
            Analyze Impact
          </>
        )}
      </button>
      {error && (
        <p role="alert" className="rounded-nasaq-sm border border-diff-prev-border bg-diff-prev-bg px-4 py-3 text-sm text-badge-high-text">
          Analysis failed — {error}
        </p>
      )}
      {results && (
        <>
          <KpiCards results={results} />
          <ImpactChain
            impactChain={results.impactChain}
            artifacts={results.artifacts}
          />
          <ImpactedArtifactsTable artifacts={results.artifacts} />
        </>
      )}
    </section>
  )
}

export default ImpactAnalysis
