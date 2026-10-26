<script lang="ts">
  import { pythonExample, typescriptExample } from '../examples'
  import CopyButton from './CopyButton.svelte'

  let { origin }: { origin: string } = $props()

  const tabs = [
    { id: 'ts', label: 'TypeScript', code: () => typescriptExample(origin) },
    { id: 'py', label: 'Python', code: () => pythonExample(origin) },
  ]
  let active = $state('ts')
  const code = $derived(tabs.find((tab) => tab.id === active)!.code())
</script>

<section id="code">
  <div class="section-head">
    <h2>Code</h2>
  </div>

  <div class="card example">
    <div class="bar">
      <div class="tabs" role="tablist">
        {#each tabs as tab (tab.id)}
          <button type="button" role="tab" aria-selected={active === tab.id} onclick={() => (active = tab.id)}>
            {tab.label}
          </button>
        {/each}
      </div>
      <CopyButton text={code} />
    </div>
    <pre><code>{code}</code></pre>
  </div>
</section>

<style>
  section {
    display: grid;
    gap: 28px;
  }

  .example {
    overflow: hidden;
  }

  .bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    padding: 12px;
    border-bottom: var(--stroke);
  }

  .tabs {
    display: flex;
    gap: 8px;
  }

  [role='tab'] {
    padding: 6px 14px;
    border: 0;
    border-radius: 8px;
    background: transparent;
    font-weight: 700;
    font-size: 0.9rem;
    color: var(--muted);
  }

  [role='tab'][aria-selected='true'] {
    color: var(--text);
    background: var(--surface-2);
  }

  pre {
    margin: 0;
    padding: 20px;
    background: var(--code-bg);
    color: var(--code-text);
    line-height: 1.6;
    overflow-x: auto;
    max-height: 560px;
  }
</style>
