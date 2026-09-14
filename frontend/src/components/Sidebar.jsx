import { X } from 'lucide-react'
import AssessmentEngine from './AssessmentEngine'
import ChangeRequestSelector from './ChangeRequestSelector'
import RequestDetails from './RequestDetails'

function Sidebar({ requests, selectedId, onSelect, isOpen, onClose }) {
  const selectedRequest = requests.find((request) => request.id === selectedId)

  return (
    <aside
      aria-hidden={!isOpen}
      className={`fixed inset-y-0 left-0 z-40 w-72 shrink-0 overflow-hidden bg-gradient-to-b from-brand-dark to-brand-dark-alt text-sidebar-text transition-[transform,width] duration-200 ease-in-out md:static md:h-auto ${
        isOpen ? 'translate-x-0 md:w-72' : '-translate-x-full md:w-0 md:translate-x-0'
      }`}
    >
      <div className="h-full w-72 space-y-6 overflow-y-auto p-6">
        <div className="flex items-start justify-between gap-3 border-b border-sidebar-muted/20 pb-5">
          <div>
            <p className="text-2xl font-bold tracking-[0.18em] text-sidebar-text">NASAQ</p>
            <p className="mt-1 text-[10px] font-medium uppercase tracking-[0.16em] text-accent-disabled">
              Change impact intelligence
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close menu"
            className="shrink-0 rounded-nasaq-sm p-1.5 text-sidebar-muted transition-colors hover:bg-white/10 hover:text-sidebar-text md:hidden"
          >
            <X size={18} aria-hidden="true" />
          </button>
        </div>
        <ChangeRequestSelector
          requests={requests}
          selectedId={selectedId}
          onSelect={onSelect}
        />
        {selectedRequest && <RequestDetails request={selectedRequest} />}
        <AssessmentEngine />
      </div>
    </aside>
  )
}

export default Sidebar
