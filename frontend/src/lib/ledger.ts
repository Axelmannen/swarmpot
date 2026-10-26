/** Mirrors swarmpot.ledger.models. Amounts are atomic units, as strings. */
export type SiteTotals = {
  host: string
  network: string
  asset: string | null
  payments: number
  total: string
  last_settled_at: string
}

export type SettledPayment = {
  host: string
  network: string
  asset: string | null
  amount: string
  transaction: string
  settled_at: string
}

export type PaymentsOverview = { sites: SiteTotals[]; recent: SettledPayment[] }

export async function fetchPayments(): Promise<PaymentsOverview> {
  const response = await fetch('/api/payments')
  if (!response.ok) throw new Error(`Could not load payments (${response.status}).`)
  return response.json()
}
