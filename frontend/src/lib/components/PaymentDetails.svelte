<script lang="ts">
  import { expiry, formatAmount, networkName, shortAddress } from '../format'
  import type { PaymentSummary } from '../payment'

  let { payment, now }: { payment: PaymentSummary; now: number } = $props()

  const expired = $derived(payment.validBefore !== undefined && payment.validBefore <= now)
</script>

<dl>
  <div>
    <dt>pays</dt>
    <dd class="amount">{payment.amount ? formatAmount(payment.amount, payment.asset) : '?'}</dd>
  </div>
  <div>
    <dt>to</dt>
    <dd><code title={payment.payTo}>{payment.payTo ? shortAddress(payment.payTo) : '?'}</code></dd>
  </div>
  <div>
    <dt>on</dt>
    <dd>{payment.network ? networkName(payment.network) : '?'}</dd>
  </div>
  {#if payment.validBefore !== undefined}
    <div>
      <dt>valid</dt>
      <dd class:expired>{expiry(payment.validBefore, now)}</dd>
    </div>
  {/if}
  <div>
    <dt>header</dt>
    <dd><code>{payment.header}</code></dd>
  </div>
</dl>

<style>
  dl {
    margin: 0;
    padding: 14px;
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
    gap: 10px 16px;
    border: var(--stroke);
    background: var(--surface-2);
    border-radius: 8px;
    font-size: 0.9rem;
  }

  dt {
    font-family: var(--font-mono);
    font-size: 0.75rem;
    color: var(--muted);
  }

  dd {
    margin: 0;
    overflow-wrap: anywhere;
  }

  .amount {
    color: var(--green);
    font-weight: 700;
  }

  .expired {
    color: var(--pink);
    font-weight: 700;
  }
</style>
