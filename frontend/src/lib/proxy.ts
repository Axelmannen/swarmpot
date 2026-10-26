import { fromBase64, toBase64Url } from './base64'

export const METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE'] as const
export type Method = (typeof METHODS)[number]

/** Headers the proxy forwards to the target. Mirrors ALLOWED_HEADERS in proxy_request.py. */
export const ALLOWED_HEADERS = ['Accept', 'Accept-Language', 'Authorization', 'Content-Type', 'User-Agent']

/** Many servers and CDNs reject longer URLs. */
export const URL_LENGTH_WARNING = 8000

export type ProxyFields = {
  url: string
  payment: string
  method: Method
  body: string
  headers: string // JSON object, as typed by the user
  /** receipt=body: everything comes back as JSON with status 200, for clients that can't read headers. */
  receiptInBody: boolean
}

/** Builds the GET /api/proxy URL for `fields`. Throws an Error naming the field that is invalid. */
export function buildProxyUrl(origin: string, fields: ProxyFields): string {
  const params = new URLSearchParams({ url: fields.url.trim() })
  if (fields.payment.trim()) params.set('payment', fields.payment.trim())
  if (fields.method !== 'GET') params.set('method', fields.method)
  if (fields.method !== 'GET' && fields.body) params.set('body', toBase64Url(fields.body))
  if (fields.headers.trim()) params.set('headers', toBase64Url(JSON.stringify(parseHeaders(fields.headers))))
  if (fields.receiptInBody) params.set('receipt', 'body')
  return `${origin}/api/proxy?${params}`
}

function parseHeaders(text: string): Record<string, string> {
  let parsed: unknown
  try {
    parsed = JSON.parse(text)
  } catch {
    throw new Error('Headers must be a JSON object, like {"Content-Type": "application/json"}.')
  }
  if (typeof parsed !== 'object' || parsed === null || Array.isArray(parsed)) throw new Error('Headers must be a JSON object.')
  for (const [name, value] of Object.entries(parsed)) {
    if (typeof value !== 'string') throw new Error(`Header ${name} must be a string.`)
    if (!ALLOWED_HEADERS.some((allowed) => allowed.toLowerCase() === name.toLowerCase()))
      throw new Error(`Header ${name} is not forwarded. Allowed: ${ALLOWED_HEADERS.join(', ')}.`)
  }
  return parsed as Record<string, string>
}

export type ProxyResult = {
  status: number
  contentType: string | null
  body: string
  /** Decoded PAYMENT-RESPONSE (or X-PAYMENT-RESPONSE): the settlement receipt. */
  receipt?: Record<string, unknown>
  /** Why a 402 rejected the payment, from PAYMENT-REQUIRED or the body. */
  rejection?: string
  /** The proxy's own error, for 403/422/502. */
  proxyError?: string
}

/** The JSON a receipt=body response carries. Mirrors WrappedResponse in the backend. */
type WrappedResponse = {
  status: number
  content_type: string | null
  receipt: Record<string, unknown> | null
  payment_required: Record<string, any> | null
  body: string
  body_encoding: 'text' | 'base64'
}

/** Sends a built proxy URL. Same origin, so all response headers are readable. */
export async function sendThroughProxy(url: string): Promise<ProxyResult> {
  const response = await fetch(url)
  const body = await response.text()
  if (response.ok && new URL(url).searchParams.get('receipt') === 'body') return unwrap(JSON.parse(body))
  const result: ProxyResult = { status: response.status, contentType: response.headers.get('Content-Type'), body }

  const receipt = response.headers.get('PAYMENT-RESPONSE') ?? response.headers.get('X-PAYMENT-RESPONSE')
  if (receipt) result.receipt = decodeJson(receipt)

  if (response.status === 402) {
    const required = response.headers.get('PAYMENT-REQUIRED')
    result.rejection = (required ? decodeJson(required)?.error : undefined) ?? parseJson(body)?.error ?? undefined
  } else if ([403, 422, 502].includes(response.status) && !response.headers.has('Referrer-Policy')) {
    // Pass-through responses carry Referrer-Policy; the proxy's own errors do not.
    result.proxyError = describeProxyError(parseJson(body)?.detail)
  }
  return result
}

function unwrap(wrapped: WrappedResponse): ProxyResult {
  const result: ProxyResult = {
    status: wrapped.status,
    contentType: wrapped.content_type,
    body: wrapped.body_encoding === 'base64' ? `(binary, ${wrapped.body.length} base64 chars)` : wrapped.body,
  }
  if (wrapped.receipt) result.receipt = wrapped.receipt
  if (wrapped.status === 402) result.rejection = wrapped.payment_required?.error ?? parseJson(wrapped.body)?.error ?? undefined
  return result
}

function describeProxyError(detail: unknown): string | undefined {
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail))
    return detail.map((e) => `${(e.loc ?? []).slice(1).join('.') || 'request'}: ${String(e.msg).replace(/^Value error, /, '')}`).join('; ')
  return undefined
}

function decodeJson(value: string): Record<string, any> | undefined {
  try {
    return JSON.parse(fromBase64(value))
  } catch {
    return undefined
  }
}

function parseJson(text: string): Record<string, any> | undefined {
  try {
    return JSON.parse(text)
  } catch {
    return undefined
  }
}
