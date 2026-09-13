import AssessmentEngine from './AssessmentEngine'
import ChangeRequestSelector from './ChangeRequestSelector'
import RequestDetails from './RequestDetails'

function Sidebar({ requests, selectedId, onSelect }) {
  const selectedRequest = requests.find((request) => request.id === selectedId)

  return (
    <aside className="w-72 shrink-0 bg-gradient-to-b from-brand-dark to-brand-dark-alt text-sidebar-text">
      <div className="space-y-6 p-6">
        <div className="border-b border-sidebar-muted/20 pb-5">
          <p className="text-2xl font-bold tracking-[0.18em] text-sidebar-text">NASAQ</p>
          <p className="mt-1 text-[10px] font-medium uppercase tracking-[0.16em] text-accent-disabled">
            Change impact intelligence
          </p>
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
