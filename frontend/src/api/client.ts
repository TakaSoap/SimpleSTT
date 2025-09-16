import { useAuth } from '../composables/useAuth'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''

async function handleResponse<T>(response: Response): Promise<T> {
  if (response.status === 204) {
    return undefined as T
  }
  if (!response.ok) {
    const message = await response.text()
    throw new Error(message || `Request failed with status ${response.status}`)
  }
  const contentType = response.headers.get('content-type')
  if (contentType && contentType.includes('application/json')) {
    return (await response.json()) as T
  }
  return (await response.text()) as unknown as T
}

export async function apiRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  const auth = useAuth()
  const headers = new Headers(init.headers)
  const authHeaders = auth.getAuthHeaders()
  Object.entries(authHeaders).forEach(([key, value]) => headers.set(key, value))

  if (!(init.body instanceof FormData)) {
    headers.set('Accept', 'application/json')
    if (init.body && !headers.has('Content-Type')) {
      headers.set('Content-Type', 'application/json')
    }
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers,
  })

  if (response.status === 401) {
    auth.clearCredentials()
    throw new Error('Authentication required')
  }

  return handleResponse<T>(response)
}

export async function apiStream(path: string, init: RequestInit): Promise<Response> {
  const auth = useAuth()
  const headers = new Headers(init.headers)
  Object.entries(auth.getAuthHeaders()).forEach(([key, value]) => headers.set(key, value))
  headers.set('Accept', 'text/event-stream')

  return fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers,
  })
}
