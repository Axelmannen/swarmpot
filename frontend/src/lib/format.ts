const NETWORKS: Record<string, string> = {
  'eip155:8453': 'Base',
  'eip155:84532': 'Base Sepolia (testnet)',
  base: 'Base',
  'base-sepolia': 'Base Sepolia (testnet)',
}

// USDC uses 6 decimals; amounts in other assets are shown in atomic units.
const USDC: Record<string, true> = {
  '0x833589fcd6edb6e08f4c7c32d4f71b54bda02913': true, // Base
  '0x036cbd53842c5426634e7929541ec2318f3dcf7e': true, // Base Sepolia
}

const EXPLORERS: Record<string, string> = {
  'eip155:8453': 'https://basescan.org/tx/',
  'eip155:84532': 'https://sepolia.basescan.org/tx/',
  base: 'https://basescan.org/tx/',
  'base-sepolia': 'https://sepolia.basescan.org/tx/',
}

export const networkName = (network: string) => NETWORKS[network] ?? network

/** A block explorer link for a transaction, when the network is one we know. */
export const explorerUrl = (network: string, transaction: string) =>
  EXPLORERS[network] && /^0x[0-9a-fA-F]{64}$/.test(transaction) ? EXPLORERS[network] + transaction : undefined

export function formatAmount(amount: string, asset?: string) {
  if (asset && USDC[asset.toLowerCase()]) return `${(Number(amount) / 1e6).toLocaleString('en-US', { maximumFractionDigits: 6 })} USDC`
  return asset ? `${amount} atomic units of ${shortAddress(asset)}` : `${amount} atomic units`
}

export const shortAddress = (address: string) =>
  address.length > 14 ? `${address.slice(0, 6)}…${address.slice(-4)}` : address

/** "expires in 4 min" / "expired 2 min ago", from a unix timestamp in seconds. */
export function expiry(validBefore: number, now = Date.now() / 1000) {
  const seconds = Math.round(validBefore - now)
  const span = (s: number) => (s < 90 ? `${s} s` : s < 5400 ? `${Math.round(s / 60)} min` : `${Math.round(s / 3600)} h`)
  return seconds > 0 ? `expires in ${span(seconds)}` : `expired ${span(-seconds)} ago`
}

/** "3 min ago" / "2 d ago", from an ISO timestamp. */
export function timeAgo(iso: string, now = Date.now()) {
  const s = Math.max(0, Math.round((now - Date.parse(iso)) / 1000))
  if (s < 60) return 'just now'
  if (s < 3600) return `${Math.round(s / 60)} min ago`
  if (s < 86400) return `${Math.round(s / 3600)} h ago`
  return `${Math.round(s / 86400)} d ago`
}
