import { fromBase64, toBase64Url } from './base64'

/** What a signed x402 payment commits to, read from its payload. Fields are missing when the payload omits them. */
export type PaymentSummary = {
  version: 1 | 2
  header: 'PAYMENT-SIGNATURE' | 'X-PAYMENT'
  scheme?: string
  network?: string
  amount?: string
  asset?: string
  payTo?: string
  payer?: string
  validBefore?: number
}

type Authorization = { from?: string; to?: string; value?: string; validBefore?: string | number }

/** Reads a pasted payment the same way the proxy does. Throws an Error explaining what is wrong. */
export function inspectPayment(payment: string): PaymentSummary {
  let parsed: unknown
  try {
    parsed = JSON.parse(fromBase64(payment))
  } catch {
    throw new Error('Not an x402 payment: expected base64-encoded JSON.')
  }
  if (typeof parsed !== 'object' || parsed === null) throw new Error('Not an x402 payment: expected a JSON object.')

  const p = parsed as Record<string, any>
  const version = p.x402Version ?? 2
  if (version !== 1 && version !== 2) throw new Error(`Unsupported x402Version ${JSON.stringify(version)}.`)

  const auth: Authorization = p.payload?.authorization ?? {}
  const accepted = version === 2 ? (p.accepted ?? {}) : p
  return {
    version,
    header: version === 2 ? 'PAYMENT-SIGNATURE' : 'X-PAYMENT',
    scheme: accepted.scheme,
    network: accepted.network,
    amount: accepted.amount ?? auth.value,
    asset: accepted.asset,
    payTo: accepted.payTo ?? auth.to,
    payer: auth.from,
    validBefore: auth.validBefore === undefined ? undefined : Number(auth.validBefore),
  }
}

/** A well-formed but unsigned v2 payment, for trying the builder. A real target will reject it. */
export function samplePayment(): string {
  const validBefore = Math.floor(Date.now() / 1000) + 300
  const payload = {
    x402Version: 2,
    accepted: {
      scheme: 'exact',
      network: 'eip155:84532',
      amount: '10000',
      asset: '0x036CbD53842c5426634e7929541eC2318f3dCF7e',
      payTo: '0x209693Bc6afc0C5328bA36FaF03C514EF312287C',
      maxTimeoutSeconds: 300,
      extra: { name: 'USDC', version: '2' },
    },
    payload: {
      signature: `0x${'00'.repeat(65)}`,
      authorization: {
        from: '0x857b06519E91e3A54538791bDbb0E22373e36b66',
        to: '0x209693Bc6afc0C5328bA36FaF03C514EF312287C',
        value: '10000',
        validAfter: '0',
        validBefore: String(validBefore),
        nonce: `0x${'ab'.repeat(32)}`,
      },
    },
  }
  return toBase64Url(JSON.stringify(payload))
}
