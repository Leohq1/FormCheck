import { afterEach, describe, expect, it, vi } from 'vitest'
import { createHttpClient } from '@/api/httpClient'

const created = {
  schema_version: '1',
  analysis_id: '11111111-1111-4111-8111-111111111111',
  capability_token: 'token',
  upload_url: 'http://storage.local/put',
  status: 'created',
}

describe('http client upload', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('puts the video bytes before completing the upload', async () => {
    const file = new File(['bytes'], 'overhead-clear.mp4', { type: 'video/mp4' })
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(new Response(JSON.stringify(created), { status: 201 }))
      .mockResolvedValueOnce(new Response(null, { status: 200 }))
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            schema_version: '1',
            analysis_id: created.analysis_id,
            status: 'queued',
          }),
          { status: 202 },
        ),
      )
    vi.stubGlobal('fetch', fetchMock)

    const api = createHttpClient('http://api.local')
    const response = await api.createAnalysis({
      stroke: 'overhead_clear',
      handedness: 'right',
      view_hint: 'side',
      consent: true,
      filename: file.name,
      content_type: 'video/mp4',
      byte_size: file.size,
    })
    await api.uploadFile(response.upload_url, file, 'video/mp4')
    await api.completeUpload(response.analysis_id, response.capability_token)

    expect(fetchMock).toHaveBeenCalledTimes(3)
    expect(fetchMock.mock.calls[1][0]).toBe('http://storage.local/put')
    expect(fetchMock.mock.calls[1][1]).toMatchObject({
      method: 'PUT',
      body: file,
      headers: { 'Content-Type': 'video/mp4' },
    })
    expect(String(fetchMock.mock.calls[2][0])).toContain('/complete-upload')
  })
})
