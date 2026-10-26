<script lang="ts">
  import { sendThroughProxy } from './lib/proxy'
  import ApiReference from './lib/components/ApiReference.svelte'
  import ClientExamples from './lib/components/ClientExamples.svelte'
  import Hero from './lib/components/Hero.svelte'
  import HowItWorks from './lib/components/HowItWorks.svelte'
  import RequestBuilder from './lib/components/RequestBuilder.svelte'
  import SiteHeader from './lib/components/SiteHeader.svelte'

  const origin = window.location.origin
</script>

<div class="page">
  <SiteHeader />

  <main>
    <Hero />
    <HowItWorks />
    <RequestBuilder {origin} onsend={sendThroughProxy} />
    <ClientExamples {origin} />
    <ApiReference />
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
    gap: 104px;
  }

  footer {
    margin-top: 96px;
    padding-top: 20px;
    border-top: var(--stroke);
    color: var(--muted);
    font-family: var(--font-mono);
    font-size: 0.8rem;
  }

  @media (max-width: 600px) {
    main {
      gap: 72px;
    }
  }
</style>
