<script lang="ts">
  import type { ProxyResult } from '../proxy'

  let { result }: { result: ProxyResult } = $props()

  const ok = $derived(result.status < 400)
  const summary = $derived.by(() => {
    if (result.proxyError) return `refused: ${result.proxyError}`
    if (result.status === 402) return `payment rejected${result.rejection ? `: ${result.rejection}` : ''}`
    if (result.receipt) return 'paid'
    return ok ? 'ok' : 'error from site'
  })
  const preview = $derived(result.body.length > 4000 ? `${result.body.slice(0, 4000)}\n…` : result.body)
</script>

<div class="response" class:ok>
  <p class="summary"><span class="status tinted">{result.status}</span>{summary}</p>
  {#if result.receipt}
    <details open>
      <summary>receipt</summary>
      <pre>{JSON.stringify(result.receipt, null, 2)}</pre>
    </details>
  {/if}
  {#if result.body}
    <details open={ok}>
      <summary>body{result.contentType ? ` · ${result.contentType}` : ''}</summary>
      <pre>{preview}</pre>
    </details>
  {/if}
</div>

<style>
  .response {
    display: grid;
    gap: 10px;
    padding: 14px;
    border: var(--stroke);
    border-radius: 8px;
    background: var(--surface);
    border-left: 3px solid var(--pink);
  }

  .response.ok {
    border-left-color: var(--green);
  }

  .summary {
    display: flex;
    align-items: baseline;
    gap: 10px;
    font-weight: 500;
    overflow-wrap: anywhere;
  }

  .status {
    --accent: var(--pink);
    font-family: var(--font-mono);
    font-weight: 600;
  }

  .ok .status {
    --accent: var(--green);
  }

  summary {
    cursor: pointer;
    font-family: var(--font-mono);
    font-size: 0.8rem;
    color: var(--muted);
  }

  pre {
    margin: 8px 0 0;
    padding: 12px;
    border-radius: 6px;
    background: var(--code-bg);
    color: var(--code-text);
    max-height: 320px;
    overflow: auto;
    white-space: pre-wrap;
    overflow-wrap: anywhere;
  }
</style>
