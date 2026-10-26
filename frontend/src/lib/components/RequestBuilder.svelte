<script lang="ts">
  import { inspectPayment, samplePayment, type PaymentSummary } from '../payment'
  import { ALLOWED_HEADERS, buildProxyUrl, METHODS, URL_LENGTH_WARNING, type ProxyFields, type ProxyResult } from '../proxy'
  import CopyButton from './CopyButton.svelte'
  import PaymentDetails from './PaymentDetails.svelte'
  import ProxyResponse from './ProxyResponse.svelte'

  let { origin, onsend }: { origin: string; onsend: (url: string) => Promise<ProxyResult> } = $props()

  let fields = $state<ProxyFields>({ url: '', payment: '', method: 'GET', body: '', headers: '', receiptInBody: false })
  let now = $state(Date.now() / 1000)
  let sending = $state(false)
  let result = $state<ProxyResult | null>(null)
  let sendError = $state<string | null>(null)

  $effect(() => {
    const timer = setInterval(() => (now = Date.now() / 1000), 1000)
    return () => clearInterval(timer)
  })

  const payment = $derived.by((): { summary?: PaymentSummary; error?: string } => {
    if (!fields.payment.trim()) return {}
    try {
      return { summary: inspectPayment(fields.payment) }
    } catch (e) {
      return { error: (e as Error).message }
    }
  })

  const built = $derived.by((): { url?: string; error?: string } => {
    if (!fields.url.trim()) return {}
    if (!/^https?:\/\/[^/]/i.test(fields.url.trim())) return { error: 'Target URL must start with http:// or https://.' }
    if (payment.error) return { error: payment.error }
    try {
      return { url: buildProxyUrl(origin, fields) }
    } catch (e) {
      return { error: (e as Error).message }
    }
  })

  const curl = $derived(built.url ? `curl -i '${built.url}'` : '')

  function loadSample() {
    fields = {
      url: 'https://api.example.com/generate',
      payment: samplePayment(),
      method: 'POST',
      body: '{"prompt": "hello"}',
      headers: '{"Content-Type": "application/json"}',
      receiptInBody: false,
    }
    result = null
  }

  async function send() {
    if (!built.url) return
    sending = true
    sendError = null
    result = null
    try {
      result = await onsend(built.url)
    } catch (e) {
      sendError = e instanceof Error ? e.message : String(e)
    } finally {
      sending = false
    }
  }
</script>

<section id="try">
  <div class="section-head">
    <h2>Try it</h2>
    <button type="button" class="btn btn-ghost" onclick={loadSample} title="Well-formed but unsigned: a real site rejects it">
      Load sample
    </button>
  </div>

  <div class="card builder">
    <form onsubmit={(e) => e.preventDefault()}>
      <div class="row">
        <label class="grow">
          <span>target url</span>
          <input type="url" bind:value={fields.url} placeholder="https://api.example.com/generate" spellcheck="false" />
        </label>
        <label>
          <span>method</span>
          <select bind:value={fields.method}>
            {#each METHODS as method (method)}
              <option>{method}</option>
            {/each}
          </select>
        </label>
      </div>

      <label>
        <span>signed payment <em>optional</em></span>
        <textarea bind:value={fields.payment} rows="3" placeholder="eyJ4NDAyVmVyc2lvbiI6Miwi…" spellcheck="false"></textarea>
      </label>

      {#if payment.summary}
        <PaymentDetails payment={payment.summary} {now} />
      {/if}

      {#if fields.method !== 'GET'}
        <label>
          <span>body</span>
          <textarea bind:value={fields.body} rows="2" placeholder={'{"prompt": "hello"}'} spellcheck="false"></textarea>
        </label>
      {/if}

      <label>
        <span>headers</span>
        <input
          bind:value={fields.headers}
          placeholder={'{"Content-Type": "application/json"}'}
          title={`Allowed: ${ALLOWED_HEADERS.join(', ')}`}
          spellcheck="false"
        />
      </label>

      <label class="check">
        <input type="checkbox" bind:checked={fields.receiptInBody} />
        <span>receipt in body <em>for fetch tools that hide headers</em></span>
      </label>
    </form>

    <div class="output">
      {#if built.error}
        <p class="error" role="alert">{built.error}</p>
      {:else if built.url}
        <pre class="url">{built.url}</pre>
        {#if built.url.length > URL_LENGTH_WARNING}
          <p class="warning">{built.url.length.toLocaleString()} chars: many servers reject URLs over ~8,000.</p>
        {/if}
        <div class="buttons">
          <button type="button" class="btn btn-primary" onclick={send} disabled={sending}>
            {sending ? 'Sending…' : 'Send'}
          </button>
          <CopyButton text={built.url} label="Copy URL" />
          <CopyButton text={curl} label="Copy curl" />
        </div>
        {#if fields.payment.trim()}
          <p class="hint">Sending spends the payment.</p>
        {/if}
        {#if sendError}
          <p class="error" role="alert">{sendError}</p>
        {/if}
        {#if result}
          <ProxyResponse {result} />
        {/if}
      {:else}
        <p class="placeholder">url (+ payment) → your link</p>
      {/if}
    </div>
  </div>
</section>

<style>
  section {
    display: grid;
    gap: 28px;
  }

  .builder {
    display: grid;
    grid-template-columns: 1fr 1fr;
    overflow: hidden;
  }

  form {
    display: grid;
    gap: 16px;
    align-content: start;
    padding: 22px;
  }

  .row {
    display: flex;
    gap: 12px;
  }

  .grow {
    flex: 1;
    min-width: 0;
  }

  label {
    display: grid;
    gap: 6px;
  }

  label > span {
    font-family: var(--font-mono);
    font-size: 0.8rem;
    color: var(--muted);
  }

  .check {
    display: flex;
    align-items: center;
    gap: 8px;
    cursor: pointer;
  }

  .check input {
    width: auto;
    margin: 0;
    accent-color: var(--primary);
  }

  label em {
    font-style: normal;
    opacity: 0.7;
  }

  input,
  select,
  textarea {
    width: 100%;
    padding: 10px 12px;
    border: var(--stroke);
    border-radius: 8px;
    background: var(--surface);
    font-family: var(--font-mono);
    font-size: 0.85rem;
  }

  select {
    font-family: var(--font-body);
    font-weight: 700;
  }

  textarea {
    resize: vertical;
    overflow-wrap: anywhere;
  }

  input:focus,
  select:focus,
  textarea:focus {
    outline: none;
    border-color: var(--primary);
    box-shadow: 0 0 0 3px color-mix(in srgb, var(--primary) 18%, transparent);
  }

  .output {
    display: grid;
    gap: 14px;
    align-content: start;
    padding: 22px;
    background: var(--surface-2);
    border-left: var(--stroke);
    min-width: 0;
  }

  .url {
    margin: 0;
    padding: 14px;
    border: var(--stroke);
    border-radius: 8px;
    background: var(--surface);
    color: var(--primary);
    white-space: pre-wrap;
    overflow-wrap: anywhere;
    max-height: 220px;
    overflow-y: auto;
  }

  .buttons {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
  }

  .hint,
  .placeholder {
    color: var(--muted);
    font-family: var(--font-mono);
    font-size: 0.8rem;
  }

  .placeholder {
    padding: 40px 0;
    text-align: center;
  }

  .error {
    color: var(--pink);
    font-weight: 500;
  }

  .warning {
    color: var(--yellow);
    font-size: 0.85rem;
  }

  @media (max-width: 860px) {
    .builder {
      grid-template-columns: 1fr;
    }

    .output {
      border-left: 0;
      border-top: var(--stroke);
    }
  }

  @media (max-width: 480px) {
    form,
    .output {
      padding: 16px;
    }

    .row {
      flex-direction: column;
    }
  }
</style>
