<script lang="ts">
  import { fetchPayments } from './lib/ledger'
  import RecentPayments from './lib/components/RecentPayments.svelte'
  import SiteHeader from './lib/components/SiteHeader.svelte'
  import SiteTotalsTable from './lib/components/SiteTotalsTable.svelte'

  const overview = fetchPayments()
</script>

<div class="page">
  <SiteHeader />

  <main>
    <section class="intro">
      <h1>Paid through swarmpot</h1>
      <p>Sites that settled payments sent through the proxy, as their receipts reported. Check any transaction on the explorer.</p>
    </section>

    {#await overview}
      <p class="note">loading…</p>
    {:then { sites, recent }}
      {#if sites.length === 0}
        <p class="note">No settled payments yet.</p>
      {:else}
        <SiteTotalsTable {sites} />
        <RecentPayments payments={recent} />
      {/if}
    {:catch error}
      <p class="note error">{error.message}</p>
    {/await}
  </main>

  <footer>swarmpot · built on <a href="https://www.x402.org" target="_blank" rel="noreferrer">x402</a></footer>
</div>

<style>
  .page {
    max-width: 1120px;
    margin: 0 auto;
    padding: 0 16px 40px;
  }

  main {
    display: grid;
    gap: 56px;
    padding-top: 32px;
  }

  .intro {
    display: grid;
    gap: 12px;
  }

  h1 {
    font-size: clamp(2rem, 5vw, 3rem);
  }

  .intro p,
  .note {
    max-width: 60ch;
    color: var(--muted);
  }

  .error {
    color: var(--pink);
  }

  footer {
    margin-top: 96px;
    padding-top: 20px;
    border-top: var(--stroke);
    color: var(--muted);
    font-family: var(--font-mono);
    font-size: 0.8rem;
  }
</style>
