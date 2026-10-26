<header>
  <a class="brand" href="/">
    <img src="/favicon.svg" alt="" />
    swarmpot
  </a>
  <nav aria-label="Sections">
    <a href="/#how">how</a>
    <a href="/#try">try</a>
    <a href="/#code">code</a>
    <a href="/#reference">api</a>
    <a href="/payments/">payments</a>
  </nav>
</header>

<style>
  header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 12px 24px;
    padding: 24px 0;
  }

  .brand {
    display: flex;
    align-items: center;
    gap: 10px;
    font-family: var(--font-display);
    font-weight: 700;
    font-size: 1.4rem;
    letter-spacing: -0.02em;
    color: var(--text);
    text-decoration: none;
  }

  img {
    width: 30px;
    height: 30px;
  }

  nav {
    display: flex;
    gap: 6px;
  }

  nav a {
    padding: 4px 12px;
    border-radius: 999px;
    color: var(--muted);
    font-family: var(--font-mono);
    font-size: 0.85rem;
    text-decoration: none;
  }

  nav a:hover {
    background: var(--surface-2);
    color: var(--text);
  }
</style>
