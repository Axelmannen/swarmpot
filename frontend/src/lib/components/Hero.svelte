<script lang="ts">
  const parts = [
    { key: 'url', value: 'https://api.example.com/generate', note: 'the x402 site', color: 'var(--blue)' },
    { key: 'payment', value: 'eyJ4NDAyVmVyc2lvbiI6Miwi…', note: 'your signed payment (optional)', color: 'var(--yellow)' },
    { key: 'method', value: 'POST', note: 'optional', color: 'var(--violet)' },
    { key: 'body', value: 'eyJwcm9tcHQiOiJoaSJ9', note: 'optional, base64url', color: 'var(--pink)' },
  ]
</script>

<section class="hero">
  <div class="intro">
    <h1>Pay any <mark>x402</mark> API with one&nbsp;GET.</h1>
    <p class="lede">Sign a payment. Put it in a URL. swarmpot delivers it.</p>
    <div class="actions">
      <a class="btn btn-primary" href="#try">Try it</a>
      <a class="btn btn-ghost" href="#how">How it works</a>
    </div>
  </div>

  <figure class="card anatomy" aria-label="Anatomy of a swarmpot request">
    <pre><span class="verb">GET</span> /api/proxy{#each parts as part, i (part.key)}
  <span class="sep">{i === 0 ? '?' : '&'}</span><span class="key" style:--accent={part.color}>{part.key}</span>=<span class="value">{part.value}</span>{/each}</pre>
    <ul>
      {#each parts as part (part.key)}
        <li><span class="tag tinted" style:--accent={part.color}>{part.key}</span>{part.note}</li>
      {/each}
    </ul>
  </figure>
</section>

<style>
  .hero {
    display: grid;
    grid-template-columns: 1fr 1.05fr;
    gap: 48px;
    align-items: center;
    padding-top: 40px;
  }

  .intro {
    display: grid;
    gap: 20px;
  }

  h1 {
    font-size: clamp(2.6rem, 6vw, 4.2rem);
  }

  mark {
    background: none;
    color: var(--primary);
  }

  .lede {
    font-size: 1.15rem;
    color: var(--muted);
  }

  .actions {
    display: flex;
    flex-wrap: wrap;
    gap: 14px;
  }

  .anatomy {
    margin: 0;
    padding: 18px;
    display: grid;
    gap: 16px;
    min-width: 0;
  }

  pre {
    margin: 0;
    padding: 16px;
    border-radius: 8px;
    background: var(--code-bg);
    color: var(--code-text);
    line-height: 1.75;
    overflow-x: auto;
  }

  .key {
    color: color-mix(in srgb, var(--accent) 80%, black);
    font-weight: 600;
  }

  .verb {
    color: var(--green);
    font-weight: 600;
  }

  .sep {
    color: var(--code-muted);
  }

  .value {
    color: var(--code-muted);
  }

  ul {
    margin: 0;
    padding: 0;
    list-style: none;
    display: flex;
    flex-wrap: wrap;
    gap: 10px 18px;
    font-size: 0.9rem;
    color: var(--muted);
  }

  li {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .tag {
    font-family: var(--font-mono);
    font-size: 0.8rem;
    font-weight: 600;
  }

  @media (max-width: 860px) {
    .hero {
      grid-template-columns: 1fr;
      gap: 32px;
      padding-top: 16px;
    }
  }
</style>
