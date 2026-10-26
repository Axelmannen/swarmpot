/** UTF-8 text as unpadded base64url, the encoding the proxy expects for `body` and `headers`. */
export function toBase64Url(text: string): string {
  let binary = ''
  for (const byte of new TextEncoder().encode(text)) binary += String.fromCharCode(byte)
  return btoa(binary).replaceAll('+', '-').replaceAll('/', '_').replace(/=+$/, '')
}

/** Decodes standard or URL-safe base64, padded or not, to UTF-8 text. Throws on invalid input. */
export function fromBase64(value: string): string {
  const normalized = value.trim().replaceAll(' ', '+').replaceAll('-', '+').replaceAll('_', '/')
  const binary = atob(normalized + '='.repeat((4 - (normalized.length % 4)) % 4))
  return new TextDecoder().decode(Uint8Array.from(binary, (char) => char.charCodeAt(0)))
}
