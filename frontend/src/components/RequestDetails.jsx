import { FileText, Hash, KeyRound, Tag } from 'lucide-react'

const detailItems = [
  ['Request ID', 'id', Hash],
  ['Requirement ID', 'requirementId', KeyRound],
  ['Change type', 'changeType', Tag],
]

function RequestDetails({ request }) {
  return (
    <section className="rounded-nasaq-sm bg-brand-dark-alt/80 p-4">
      <p className="mb-4 text-[11px] font-semibold uppercase tracking-[0.05em] text-sidebar-muted">
        Request details
      </p>
      <div className="space-y-3">
        {detailItems.map(([label, field, Icon]) => (
          <div key={field} className="flex items-start gap-2.5">
            <Icon size={15} className="mt-0.5 shrink-0 text-sidebar-muted" aria-hidden="true" />
            <div className="min-w-0">
              <p className="text-[11px] text-sidebar-muted">{label}</p>
              <p className={`truncate text-sm text-sidebar-text ${field !== 'changeType' ? 'font-mono' : ''}`}>
                {request[field]}
              </p>
            </div>
          </div>
        ))}
        <div className="flex items-start gap-2.5">
          <FileText size={15} className="mt-0.5 shrink-0 text-sidebar-muted" aria-hidden="true" />
          <div>
            <p className="text-[11px] text-sidebar-muted">Description</p>
            <p className="text-sm leading-5 text-sidebar-text">{request.description}</p>
          </div>
        </div>
      </div>
    </section>
  )
}

export default RequestDetails
