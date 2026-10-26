<script lang="ts">
  import { formatAmount, networkName, timeAgo } from '../format'
  import type { SiteTotals } from '../ledger'

  let { sites }: { sites: SiteTotals[] } = $props()
</script>

<section>
  <h2>Sites</h2>
  <div class="card table">
    <div class="row head">
      <span>site</span>
      <span class="num">payments</span>
      <span class="num">total</span>
      <span class="num">last</span>
    </div>
    {#each sites as site (`${site.host} ${site.network} ${site.asset}`)}
      <div class="row">
        <span class="host">
          {site.host}
          <small>{networkName(site.network)}</small>
        </span>
        <span class="num">{site.payments}</span>
        <span class="num total">{formatAmount(site.total, site.asset ?? undefined)}</span>
        <span class="num muted">{timeAgo(site.last_settled_at)}</span>
      </div>
    {/each}
  </div>
</section>

<style>
  section {
    display: grid;
    gap: 20px;
  }

  h2 {
    font-size: 1.5rem;
  }

  .table {
    padding: 4px 18px;
  }

  .row {
    display: grid;
    grid-template-columns: minmax(0, 2fr) 90px minmax(0, 1.2fr) 100px;
    gap: 16px;
    align-items: baseline;
    padding: 12px 0;
    font-size: 0.95rem;
  }

  .row + .row {
    border-top: var(--stroke);
  }

  .head {
    color: var(--muted);
    font-family: var(--font-mono);
    font-size: 0.75rem;
  }

  .host {
    display: grid;
    font-weight: 600;
    overflow-wrap: anywhere;
  }

  small {
    color: var(--muted);
    font-weight: 400;
    font-size: 0.8rem;
  }

  .num {
    text-align: right;
    font-variant-numeric: tabular-nums;
  }

  .total {
    font-family: var(--font-mono);
    font-size: 0.875rem;
    overflow-wrap: anywhere;
  }

  .muted {
    color: var(--muted);
  }

  @media (max-width: 600px) {
    .row {
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 2px 12px;
    }

    .head {
      display: none;
    }

    .row > :nth-child(2)::after {
      content: ' payments';
      color: var(--muted);
    }
  }
</style>
