const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8765'
const ANALYSIS_TIMEOUT_MS = 10 * 60 * 1000

async function request(path, options = {}) {
  const controller = new AbortController()
  const timeout = window.setTimeout(() => controller.abort(), ANALYSIS_TIMEOUT_MS)

  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    })
    const body = await response.json()
    if (!response.ok) {
      throw new Error(body.detail || `Request failed with status ${response.status}`)
    }
    return body
  } catch (error) {
    if (error.name === 'AbortError') {
      throw new Error(
        'The analysis exceeded 10 minutes. The first run may still be loading ML models; check the API terminal for details.',
      )
    }
    if (error instanceof TypeError) {
      throw new Error(`Cannot reach the API at ${API_BASE_URL}. Start the FastAPI server first.`)
    }
    throw error
  } finally {
    window.clearTimeout(timeout)
  }
}

export function fetchChangeRequests() {
  return request('/api/change-requests')
}

export function analyzeChange(changeId) {
  return request(`/api/analyze/${encodeURIComponent(changeId)}`, { method: 'POST' })
}
