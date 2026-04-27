import { i18n } from '../i18n'
import { useAuth } from '../composables/useAuth'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''

type ErrorResponse = {
  detail?: unknown
  message?: unknown
  error?: unknown
  errors?: Array<{ message?: unknown }>
}

async function handleResponse<T>(response: Response): Promise<T> {
  const contentType = response.headers.get('content-type') ?? ''
  const t = i18n.global.t

  if (response.status === 204) {
    return undefined as T
  }

  if (!response.ok) {
    const bodyText = await response.text().catch(() => '')

    let errorMessage = t('errors.requestFailed', { status: response.status }) as string

    if (contentType.includes('application/json') && bodyText) {
      try {
        const parsed = JSON.parse(bodyText) as ErrorResponse
        if (parsed && typeof parsed === 'object') {
          const candidate = parsed.detail ?? parsed.message ?? parsed.error ?? parsed.errors?.[0]?.message

          if (candidate) {
            errorMessage = String(candidate)
          } else {
            errorMessage = bodyText
          }
        }
      } catch {
        errorMessage = bodyText
      }
    } else if (bodyText) {
      const trimmedText = bodyText.trim()
      if (contentType.includes('text/html') || /^<!doctype html>/i.test(trimmedText)) {
        errorMessage = t('errors.serverUnavailable') as string
      } else {
        errorMessage = trimmedText || errorMessage
      }
    }

    throw new Error(errorMessage)
  }

  if (contentType.includes('application/json')) {
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

  let response: Response

  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      headers,
    })
  } catch (error) {
    throw new Error(i18n.global.t('errors.network') as string)
  }

  if (response.status === 401) {
    auth.clearCredentials()
    throw new Error(i18n.global.t('errors.authenticationRequired') as string)
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
