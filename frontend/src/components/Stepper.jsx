import { Check } from 'lucide-react'

const steps = ['Select Change', 'Analyze Impact', 'Review Results']

function Stepper({ currentStep = 1 }) {
  const activeStep = Math.min(Math.max(currentStep, 1), steps.length)

  return (
    <nav aria-label="Analysis progress" className="flex items-center">
      {steps.map((label, index) => {
        const step = index + 1
        const isComplete = step < activeStep
        const isCurrent = step === activeStep

        return (
          <div key={label} className="flex min-w-0 flex-1 items-center last:flex-none">
            <div className="flex items-center gap-2">
              <span
                className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full border text-xs font-semibold ${
                  isComplete || isCurrent
                    ? 'border-accent bg-accent text-white'
                    : 'border-muted/40 bg-white/30 text-muted'
                }`}
              >
                {isComplete ? <Check size={14} strokeWidth={3} aria-hidden="true" /> : step}
              </span>
              <span
                className={`hidden text-xs font-semibold sm:inline ${
                  isCurrent ? 'text-accent' : isComplete ? 'text-heading' : 'text-muted'
                }`}
              >
                {label}
              </span>
            </div>
            {step < steps.length && (
              <span
                aria-hidden="true"
                className={`mx-2 h-px min-w-4 flex-1 sm:mx-4 ${
                  isComplete ? 'bg-accent/60' : 'bg-muted/25'
                }`}
              />
            )}
          </div>
        )
      })}
    </nav>
  )
}

export default Stepper
