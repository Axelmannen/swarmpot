/** Client code shown on the page. Both are run against a real x402 server before they change. */

export const typescriptExample = (origin: string) => `// npm install @x402/core @x402/evm viem
import { x402Client, x402HTTPClient } from '@x402/core/client'
import { ExactEvmScheme } from '@x402/evm/exact/client'
import { privateKeyToAccount } from 'viem/accounts'

const SWARMPOT = '${origin}'
const target = 'https://api.example.com/generate'
const account = privateKeyToAccount(process.env.PRIVATE_KEY as \`0x\${string}\`)

// Register the network the target charges on (here Base Sepolia).
const x402 = new x402HTTPClient(new x402Client().register('eip155:84532', new ExactEvmScheme(account)))
const b64url = (text: string) => btoa(text).replaceAll('+', '-').replaceAll('/', '_').replace(/=+$/, '')

// 1. Ask the target for its price.
const challenge = await fetch(target, { method: 'POST' })
const required = x402.getPaymentRequiredResponse((name) => challenge.headers.get(name), await challenge.json())

// 2. Sign the payment locally. Nothing is sent yet.
const payload = await x402.createPaymentPayload(required)
const [payment] = Object.values(x402.encodePaymentSignatureHeader(payload))

// 3. One GET through swarmpot.
const url = new URL('/api/proxy', SWARMPOT)
url.search = new URLSearchParams({
  url: target,
  payment,
  method: 'POST',
  body: b64url(JSON.stringify({ prompt: 'hello' })),
  headers: b64url(JSON.stringify({ 'Content-Type': 'application/json' })),
}).toString()
const response = await fetch(url)
console.log(response.status, await response.text())
`

export const pythonExample = (origin: string) => `# uv add httpx "x402[evm]"
import asyncio
import base64
import json
import os

import httpx
from eth_account import Account
from x402 import x402Client
from x402.http.utils import decode_payment_required_header, encode_payment_signature_header
from x402.mechanisms.evm import EthAccountSigner
from x402.mechanisms.evm.exact import ExactEvmClientScheme

SWARMPOT = "${origin}"
TARGET = "https://api.example.com/generate"


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


async def main() -> None:
    # Register the network the target charges on (here Base Sepolia).
    signer = EthAccountSigner(Account.from_key(os.environ["PRIVATE_KEY"]))
    client = x402Client().register("eip155:84532", ExactEvmClientScheme(signer=signer))

    # 1. Ask the target for its price.
    challenge = httpx.post(TARGET)
    required = decode_payment_required_header(challenge.headers["PAYMENT-REQUIRED"])

    # 2. Sign the payment locally. Nothing is sent yet.
    payment = encode_payment_signature_header(await client.create_payment_payload(required))

    # 3. One GET through swarmpot.
    response = httpx.get(
        f"{SWARMPOT}/api/proxy",
        params={
            "url": TARGET,
            "payment": payment,
            "method": "POST",
            "body": b64url(json.dumps({"prompt": "hello"}).encode()),
            "headers": b64url(json.dumps({"Content-Type": "application/json"}).encode()),
        },
        timeout=60,
    )
    print(response.status_code, response.text)


asyncio.run(main())
`
