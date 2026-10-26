<script lang="ts">
  import { explorerUrl, formatAmount, networkName, shortAddress, timeAgo } from '../format'
  import type { SettledPayment } from '../ledger'

  let { payments }: { payments: SettledPayment[] } = $props()
</script>

<section>
  <h2>Latest payments</h2>
  <div class="card table">
    {#each payments as payment (payment.transaction)}
      {@const href = explorerUrl(payment.network, payment.transaction)}
      <div class="row">
        <span class="host">{payment.host}</span>
        <span class="amount">{formatAmount(payment.amount, payment.asset ?? undefined)}</span>
        <span class="tx">
          {#if href}
            <a {href} target="_blank" rel="noreferrer">{shortAddress(payment.transaction)}</a>
          {:else}
            <code title={networkName(payment.network)}>{shortAddress(payment.transaction)}</code>
          {/if}
        </span>
        <span class="when">{timeAgo(payment.settled_at)}</span>
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
    grid-template-columns: minmax(0, 2fr) minmax(0, 1.2fr) 130px 100px;
    gap: 16px;
    align-items: baseline;
    padding: 12px 0;
    font-size: 0.95rem;
  }

  .row + .row {
    border-top: var(--stroke);
  }

  .host {
    font-weight: 600;
    overflow-wrap: anywhere;
  }

  .amount {
    text-align: right;
    font-family: var(--font-mono);
    font-size: 0.875rem;
    overflow-wrap: anywhere;
  }

  .tx {
    font-family: var(--font-mono);
    font-size: 0.85rem;
  }

  .when {
    text-align: right;
    color: var(--muted);
  }

  @media (max-width: 600px) {
    .row {
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 2px 12px;
    }
  }
</style>
