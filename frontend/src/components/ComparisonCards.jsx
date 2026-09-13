import { ArrowRight } from 'lucide-react'

function HighlightedText({ text, changedValue }) {
  const valueStart = text.indexOf(changedValue)

  if (valueStart === -1) {
    return text
  }

  const valueEnd = valueStart + changedValue.length
  return (
    <>
      {text.slice(0, valueStart)}
      <strong className="rounded bg-black/5 px-1 font-semibold">{text.slice(valueStart, valueEnd)}</strong>
      {text.slice(valueEnd)}
    </>
  )
}

function ComparisonCard({ label, text, changedValue, variant }) {
  const isPrevious = variant === 'previous'

  return (
    <article
      className={`min-w-0 flex-1 rounded-nasaq border-l-4 p-6 shadow-sm ${
        isPrevious
          ? 'border-diff-prev-border bg-diff-prev-bg'
          : 'border-diff-next-border bg-diff-next-bg'
      }`}
    >
      <p className="mb-3 text-[11px] font-semibold uppercase tracking-[0.05em] text-muted">
        {label}
      </p>
      <p className="text-base leading-7 text-body">
        <HighlightedText text={text} changedValue={changedValue} />
      </p>
    </article>
  )
}

function ComparisonCards({ request }) {
  return (
    <section aria-labelledby="requirement-comparison">
      <div className="mb-4">
        <p className="text-[11px] font-semibold uppercase tracking-[0.05em] text-muted">
          Changed requirement
        </p>
        <h1 id="requirement-comparison" className="mt-1 text-2xl font-bold tracking-tight text-heading">
          Review requirement update
        </h1>
      </div>
      <div className="flex flex-col items-stretch gap-4 lg:flex-row lg:items-center">
        <ComparisonCard
          label="Previous requirement"
          text={request.oldText}
          changedValue={request.changedValueOld}
          variant="previous"
        />
        <ArrowRight className="hidden shrink-0 text-muted lg:block" size={22} aria-hidden="true" />
        <ComparisonCard
          label="Updated requirement"
          text={request.newText}
          changedValue={request.changedValueNew}
          variant="next"
        />
      </div>
      <p className="mt-4 text-sm text-muted">
        <span className="font-medium text-body">{request.changeType}</span>
        <span className="mx-2 text-muted/60">·</span>
        {request.description}
      </p>
    </section>
  )
}

export default ComparisonCards
