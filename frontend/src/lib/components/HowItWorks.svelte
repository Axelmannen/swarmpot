<script lang="ts">
  import FlowDiagram from './FlowDiagram.svelte'

  const facts = [
    'never holds funds',
    "can't change the payee",
    'stateless',
    'payment optional: any request works',
    'receipt=body: receipt readable by fetch tools',
    'public targets only',
    'URL = cash until settled',
  ]
</script>

<section id="how">
  <div class="section-head">
    <h2>How it works</h2>
  </div>
  <FlowDiagram />
  <ul>
    {#each facts as fact (fact)}
      <li>{fact}</li>
    {/each}
  </ul>
</section>

<style>
  section {
    display: grid;
    gap: 28px;
    max-width: 860px;
  }

  ul {
    margin: 0;
    padding: 0;
    list-style: none;
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }

  li {
    padding: 4px 12px;
    border-radius: 999px;
    background: var(--surface-2);
    color: var(--muted);
    font-weight: 700;
    font-size: 0.9rem;
  }
</style>
