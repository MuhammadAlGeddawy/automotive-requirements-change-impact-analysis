import { Check, LoaderCircle, Play } from 'lucide-react'
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

const agentSteps = [
  'Retrieving the most probable requirements and artifacts to be impacted...',
  'Tracing relationships across the requirement graph...',
  'Reasoning over the change request and candidate evidence...',
  'Finding the impact level for each artifact...',
  'Preparing the ranked impact summary...',
]

const wait = (duration) => new Promise((resolve) => window.setTimeout(resolve, duration))

function AgentActivity({ activeStep, isComplete }) {
  const visibleSteps = isComplete
    ? agentSteps
    : [agentSteps[Math.min(activeStep, agentSteps.length - 1)]]

  return (
    <div
      className="overflow-hidden rounded-nasaq-sm border border-brand-dark/10 bg-white/65 shadow-sm"
      aria-live="polite"
      aria-label="CIA agent activity"
    >
      <div className="flex items-center gap-3 border-b border-brand-dark/10 px-5 py-4">
        <span className="flex h-8 w-8 items-center justify-center rounded-full bg-accent/10 text-accent">
          {isComplete ? (
            <Check size={17} strokeWidth={3} aria-hidden="true" />
          ) : (
            <LoaderCircle size={17} className="animate-spin" aria-hidden="true" />
          )}
        </span>
        <div>
          <p className="text-sm font-semibold text-heading">
            {isComplete ? 'Analysis complete' : 'Change impact analysis running'}
          </p>
          <p className="text-xs text-muted">
            {isComplete ? 'Impact results are ready for review' : 'Reviewing the selected change request'}
          </p>
        </div>
      </div>
      <div className="space-y-3 px-5 py-4">
        {visibleSteps.map((step) => {
          const complete = isComplete
          const current = !isComplete
          return (
            <div
              key={step}
              className={`flex items-start gap-3 text-sm transition-opacity ${
                'opacity-100'
              }`}
            >
              <span className={`mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full ${
                complete
                  ? 'bg-accent text-white'
                  : current
                    ? 'border-2 border-accent text-accent'
                    : 'border border-brand-dark/20 text-muted'
              }`}>
                {complete ? (
                  <Check size={12} strokeWidth={3} aria-hidden="true" />
                ) : current ? (
                  <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-accent" />
                ) : (
                  <span className="h-1 w-1 rounded-full bg-current" />
                )}
              </span>
              <span className={current ? 'font-medium text-heading' : 'text-body'}>
                {step}
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}

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

function ImpactAnalysis({ changeId, hasSelection, onStepChange }) {
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [results, setResults] = useState(null)
  const [error, setError] = useState('')
  const [activeStep, setActiveStep] = useState(0)

  const handleAnalyze = async () => {
    if (!hasSelection || isAnalyzing) {
      return
    }

    setResults(null)
    setError('')
    setIsAnalyzing(true)
    setActiveStep(0)
    onStepChange?.(2)
    const startedAt = Date.now()
    const stepTimer = window.setInterval(() => {
      setActiveStep((step) => Math.min(step + 1, agentSteps.length - 1))
    }, 1800)
    try {
      const analysis = await analyzeChange(changeId)
      const minimumDuration = 9000
      await wait(Math.max(0, minimumDuration - (Date.now() - startedAt)))
      setActiveStep(agentSteps.length)
      setResults(analysis)
      onStepChange?.(3)
    } catch (requestError) {
      setError(requestError.message || 'Analysis failed. Check the backend and OpenRouter API key.')
    } finally {
      window.clearInterval(stepTimer)
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
      {(isAnalyzing || results) && (
        <AgentActivity
          activeStep={activeStep}
          isComplete={Boolean(results) && !isAnalyzing}
        />
      )}
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
