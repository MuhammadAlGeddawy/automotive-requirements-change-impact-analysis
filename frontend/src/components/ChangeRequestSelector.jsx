import { Check, ChevronDown } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'

function ChangeRequestSelector({ requests, selectedId, onSelect }) {
  const [isOpen, setIsOpen] = useState(false)
  const selectorRef = useRef(null)
  const selectedRequest = requests.find((request) => request.id === selectedId)

  useEffect(() => {
    const handleOutsideClick = (event) => {
      if (!selectorRef.current?.contains(event.target)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleOutsideClick)
    return () => document.removeEventListener('mousedown', handleOutsideClick)
  }, [])

  const handleSelect = (request) => {
    onSelect(request.id)
    setIsOpen(false)
  }

  return (
    <section className="relative z-20">
      <p className="mb-3 text-[11px] font-semibold uppercase tracking-[0.05em] text-sidebar-muted">
        Change request
      </p>
      <div ref={selectorRef} className="relative">
        <button
          type="button"
          aria-expanded={isOpen}
          onClick={() => setIsOpen((open) => !open)}
          className="flex w-full items-center justify-between rounded-nasaq-sm border border-sidebar-muted/40 bg-brand-dark-alt/70 px-4 py-3 text-left text-sm text-sidebar-text transition-colors hover:border-sidebar-muted"
        >
          <span className="font-mono">{selectedRequest?.id || 'Select request'}</span>
          <ChevronDown size={16} className={isOpen ? 'rotate-180 transition-transform' : 'transition-transform'} aria-hidden="true" />
        </button>

        {isOpen && (
          <div className="glass-surface absolute left-0 right-0 top-full z-30 mt-2 overflow-hidden p-1">
            {requests.map((request) => (
              <button
                key={request.id}
                type="button"
                onClick={() => handleSelect(request)}
                className="flex w-full items-center justify-between rounded-lg px-3 py-2.5 text-left text-sm text-body transition-colors hover:bg-white/60"
              >
                <span>
                  <span className="font-mono font-semibold">{request.id}</span>
                  <span className="ml-2 text-xs text-muted">{request.requirementId}</span>
                </span>
                {request.id === selectedId && (
                  <Check size={16} className="text-accent" aria-label="Selected" />
                )}
              </button>
            ))}
          </div>
        )}
      </div>
    </section>
  )
}

export default ChangeRequestSelector
