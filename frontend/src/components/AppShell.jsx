import { Menu, PanelLeftClose } from 'lucide-react'
import { useEffect, useState } from 'react'
import { fetchChangeRequests } from '../api'
import GradientMesh from './GradientMesh'
import ComparisonCards from './ComparisonCards'
import ImpactAnalysis from './ImpactAnalysis'
import Sidebar from './Sidebar'
import Stepper from './Stepper'

const isDesktopViewport = () =>
  typeof window !== 'undefined' && window.matchMedia('(min-width: 768px)').matches

function AppShell() {
  const [changeRequests, setChangeRequests] = useState([])
  const [selectedId, setSelectedId] = useState('')
  const [requestError, setRequestError] = useState('')
  const [analysisStep, setAnalysisStep] = useState(1)
  const [isSidebarOpen, setIsSidebarOpen] = useState(isDesktopViewport)

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

  const handleSelect = (id) => {
    setSelectedId(id)
    setAnalysisStep(1)
    if (!isDesktopViewport()) {
      setIsSidebarOpen(false)
    }
  }

  return (
    <div className="relative min-h-screen overflow-x-hidden bg-bg-cream">
      <GradientMesh />

      <div className="relative z-10 flex min-h-screen">
        {isSidebarOpen && (
          <button
            type="button"
            aria-label="Close menu"
            onClick={() => setIsSidebarOpen(false)}
            className="fixed inset-0 z-30 bg-brand-dark/40 backdrop-blur-[2px] md:hidden"
          />
        )}
        <Sidebar
          requests={changeRequests}
          selectedId={selectedId}
          onSelect={handleSelect}
          isOpen={isSidebarOpen}
          onClose={() => setIsSidebarOpen(false)}
        />

        <main className="min-w-0 flex-1">
          <header className="flex h-16 items-center border-b border-brand-dark/10 px-4 sm:h-20 sm:px-8">
            <button
              type="button"
              onClick={() => setIsSidebarOpen((open) => !open)}
              aria-label={isSidebarOpen ? 'Collapse menu' : 'Expand menu'}
              aria-expanded={isSidebarOpen}
              className="inline-flex h-9 w-9 items-center justify-center rounded-nasaq-sm text-heading transition-colors hover:bg-brand-dark/5"
            >
              {isSidebarOpen ? (
                <PanelLeftClose size={20} aria-hidden="true" />
              ) : (
                <Menu size={20} aria-hidden="true" />
              )}
            </button>
          </header>
          <div className="mx-auto max-w-6xl space-y-8 px-4 py-6 sm:px-8 sm:py-8">
            {requestError ? (
              <p role="alert" className="rounded-nasaq-sm border border-diff-prev-border bg-diff-prev-bg px-4 py-3 text-sm text-badge-high-text">
                Unable to load change requests — {requestError}
              </p>
            ) : selectedRequest ? (
              <>
                <Stepper currentStep={analysisStep} />
                <ComparisonCards request={selectedRequest} />
                <ImpactAnalysis
                  key={selectedId}
                  changeId={selectedId}
                  request={selectedRequest}
                  hasSelection
                  onStepChange={setAnalysisStep}
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
