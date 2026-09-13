import { useEffect, useState } from 'react'
import { fetchChangeRequests } from '../api'
import GradientMesh from './GradientMesh'
import ComparisonCards from './ComparisonCards'
import ImpactAnalysis from './ImpactAnalysis'
import Sidebar from './Sidebar'
import Stepper from './Stepper'

function AppShell() {
  const [changeRequests, setChangeRequests] = useState([])
  const [selectedId, setSelectedId] = useState('')
  const [requestError, setRequestError] = useState('')

  useEffect(() => {
    fetchChangeRequests()
      .then((requests) => {
        setChangeRequests(requests)
        setSelectedId(requests[0]?.id || '')
      })
      .catch((error) => {
        setRequestError(error.message || 'Unable to load change requests.')
      })
  }, [])

  const selectedRequest = changeRequests.find((request) => request.id === selectedId)

  return (
    <div className="relative min-h-screen overflow-x-hidden bg-bg-cream">
      <GradientMesh />

      <div className="relative z-10 flex min-h-screen">
        <Sidebar
          requests={changeRequests}
          selectedId={selectedId}
          onSelect={setSelectedId}
        />

        <main className="min-w-0 flex-1">
          <header className="h-20 border-b border-brand-dark/10 px-6 sm:px-8" />
          <div className="mx-auto max-w-6xl space-y-8 px-6 py-8 sm:px-8">
            {requestError ? (
              <p role="alert" className="rounded-nasaq-sm border border-diff-prev-border bg-diff-prev-bg px-4 py-3 text-sm text-badge-high-text">
                Unable to load change requests — {requestError}
              </p>
            ) : selectedRequest ? (
              <>
                <Stepper currentStep={1} />
                <ComparisonCards request={selectedRequest} />
                <ImpactAnalysis
                  key={selectedId}
                  changeId={selectedId}
                  hasSelection
                />
              </>
            ) : (
              <p className="text-sm text-muted">Loading change requests...</p>
            )}
          </div>
        </main>
      </div>
    </div>
  )
}

export default AppShell
