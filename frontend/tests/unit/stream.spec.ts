import { describe, expect, it, vi } from 'vitest'
import type { TranscriptionRequest } from '../../src/types/api'

const { mockStream } = vi.hoisted(() => ({
  mockStream: vi.fn()
}))

vi.mock('../../src/api/client', () => ({
  apiStream: mockStream
}))

import { streamTranscription } from '../../src/api/endpoints'

function createSSEStream(payload: string) {
  const encoder = new TextEncoder()
  return new ReadableStream<Uint8Array>({
    start(controller) {
      controller.enqueue(encoder.encode(payload))
      controller.close()
    }
  })
}

describe('streamTranscription parser', () => {
  it('yields parsed SSE events', async () => {
    const ssePayload =
      'data: {"type":"chunk","data":"hello"}\n\n' +
      'data: {"type":"complete","data":"done","download_url":"/api/transcriptions/123/download","transcript_id":"123"}\n\n'

    mockStream.mockResolvedValueOnce(
      new Response(createSSEStream(ssePayload), {
        headers: { 'content-type': 'text/event-stream' },
        status: 200
      })
    )

    const payload: TranscriptionRequest = {
      file_id: 'file123',
      model: 'gpt-4o-transcribe',
      format: 'text',
      language: null,
      prompt: null,
      provider: { provider: 'openai', api_key: 'test' },
      stream: true
    }

    const events = []
    for await (const event of streamTranscription(payload)) {
      events.push(event)
    }

    expect(events).toHaveLength(2)
    expect(events[0]).toMatchObject({ type: 'chunk', data: 'hello' })
    expect(events[1]).toMatchObject({ type: 'complete', download_url: '/api/transcriptions/123/download' })
  })
})
