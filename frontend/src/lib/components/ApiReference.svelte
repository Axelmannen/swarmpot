<script lang="ts">
  import { ALLOWED_HEADERS } from '../proxy'

  const params = [
    ['url', 'required', 'target URL'],
    ['payment', '', 'signed x402 payload, base64 or base64url · leave out for a plain request'],
    ['method', 'GET', 'GET POST PUT PATCH DELETE'],
    ['body', '', 'base64url'],
    ['headers', '', `base64url JSON · ${ALLOWED_HEADERS.join(', ')}`],
    ['receipt', 'header', 'body: 200 + JSON {status, receipt, payment_required, body}, for fetch tools'],
  ]

  const statuses = [
    ['any', 'the site’s answer, passed through', 'var(--green)'],
    ['422', 'bad request, nothing sent', 'var(--yellow)'],
    ['403', 'private target', 'var(--violet)'],
    ['502', 'unreachable, >30 s or >10 MB', 'var(--pink)'],
  ]
</script>

<section id="reference">
  <div class="section-head">
    <h2><code>GET /api/proxy</code></h2>
    <a class="btn btn-ghost" href="/docs">/docs</a>
  </div>

  <div class="tables">
    <div class="card table params">
      {#each params as [name, flag, description] (name)}
        <div class="line">
          <code class="name">{name}</code>
          <span>{description}{#if flag}<em>{flag}</em>{/if}</span>
        </div>
      {/each}
    </div>

    <div class="card table statuses">
      {#each statuses as [status, description, color] (status)}
        <div class="line">
          <code class="status tinted" style:--accent={color}>{status}</code>
          <span>{description}</span>
        </div>
      {/each}
    </div>
  </div>
</section>

<style>
  section {
    display: grid;
    gap: 28px;
  }

  h2 code {
    font-size: 0.8em;
  }

  .tables {
    display: grid;
    grid-template-columns: 1.2fr 1fr;
    gap: 24px;
    align-items: start;
  }

  .table {
    padding: 8px 18px;
    min-width: 0;
  }

  .line {
    display: grid;
    grid-template-columns: 84px 1fr;
    gap: 12px;
    align-items: baseline;
    padding: 10px 0;
    font-size: 0.9rem;
    color: var(--muted);
    overflow-wrap: anywhere;
  }

  .line + .line {
    border-top: var(--stroke);
  }

  .name {
    color: var(--text);
    font-weight: 600;
  }

  em {
    margin-left: 8px;
    font-style: normal;
    font-family: var(--font-mono);
    font-size: 0.75rem;
    color: var(--yellow);
  }

  .status {
    justify-self: start;
    font-weight: 600;
  }

  @media (max-width: 860px) {
    .tables {
      grid-template-columns: 1fr;
    }
  }
</style>
