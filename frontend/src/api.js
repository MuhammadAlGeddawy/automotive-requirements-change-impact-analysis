const API_BASE_URL = import.meta.env.PROD
  ? '/api'
  : (import.meta.env.VITE_API_BASE_URL || '')
const ANALYSIS_TIMEOUT_MS = 30 * 1000

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
    const responseText = await response.text()
    let body
    try {
      body = responseText ? JSON.parse(responseText) : {}
    } catch {
      throw new Error(
        `API returned a non-JSON response (status ${response.status}). Check the deployed API service route.`,
      )
    }
    if (!response.ok) {
      throw new Error(body.detail || `Request failed with status ${response.status}`)
    }
    return body
  } catch (error) {
    if (error.name === 'AbortError') {
      throw new Error(
        'The API request exceeded 30 seconds. Check that the selected local API server is running.',
      )
    }
    if (error instanceof TypeError) {
      throw new Error(`Cannot reach the API at ${API_BASE_URL || 'the local proxy'}.`)
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
