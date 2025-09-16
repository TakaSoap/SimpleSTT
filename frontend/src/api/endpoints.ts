import { apiRequest, apiStream } from './client'
import type {
  AnalyzeFileResponse,
  OptionsResponse,
  ProviderConfig,
  StreamEvent,
  TranscriptionRequest,
  TranscriptionResponse,
  ValidateKeyResponse,
} from '../types/api'

export async function login(): Promise<{ status: string }> {
  return apiRequest('/api/auth/login', { method: 'POST' })
}

export async function fetchOptions(): Promise<OptionsResponse> {
  return apiRequest('/api/options', { method: 'GET' })
}

export async function validateKey(provider: ProviderConfig): Promise<ValidateKeyResponse> {
  return apiRequest('/api/keys/validate', {
    method: 'POST',
    body: JSON.stringify({ provider }),
  })
}

export async function analyzeFile(file: File, model: string): Promise<AnalyzeFileResponse> {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('model', model)

  return apiRequest('/api/files/analyze', {
    method: 'POST',
    body: formData,
  })
}

export async function deleteFile(fileId: string): Promise<void> {
  await apiRequest(`/api/files/${fileId}`, { method: 'DELETE' })
}

export async function transcribe(payload: TranscriptionRequest): Promise<TranscriptionResponse> {
  return apiRequest('/api/transcriptions', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function* streamTranscription(
  payload: TranscriptionRequest
): AsyncGenerator<StreamEvent> {
  const response = await apiStream('/api/transcriptions/stream', {
    method: 'POST',
    body: JSON.stringify(payload),
    headers: { 'Content-Type': 'application/json' },
  })

  if (!response.body) {
    throw new Error('Streaming not supported in this environment')
  }

  if (!response.ok) {
    const message = await response.text()
    throw new Error(message || 'Failed to start stream')
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let buffer = ''

  while (true) {
    const { value, done } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })

    let separatorIndex = buffer.indexOf('\n\n')
    while (separatorIndex !== -1) {
      const rawEvent = buffer.slice(0, separatorIndex)
      buffer = buffer.slice(separatorIndex + 2)
      const dataLine = rawEvent
        .split('\n')
        .map((line) => line.trim())
        .find((line) => line.startsWith('data:'))

      if (dataLine) {
        const jsonPayload = dataLine.replace('data:', '').trim()
        try {
          const event = JSON.parse(jsonPayload) as StreamEvent
          yield event
        } catch (error) {
          console.error('Failed to parse stream event', error, jsonPayload)
        }
      }
      separatorIndex = buffer.indexOf('\n\n')
    }
  }
}
