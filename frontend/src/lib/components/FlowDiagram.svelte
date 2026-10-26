<script lang="ts">
  type Lane = 0 | 1 | 2
  type Step =
    | { kind: 'phase'; label: string }
    | { kind: 'message'; from: Lane; to: Lane; label: string; detail: string }
    | { kind: 'local'; at: Lane; label: string; detail: string }

  const lanes = ['you', 'swarmpot', 'x402 site']

  const steps: Step[] = [
    { kind: 'phase', label: 'your side' },
    { kind: 'message', from: 0, to: 2, label: 'POST /generate', detail: 'no payment' },
    { kind: 'message', from: 2, to: 0, label: '402', detail: 'price + payee' },
    { kind: 'local', at: 0, label: 'sign', detail: 'exact amount, exact payee' },
    { kind: 'phase', label: 'one GET' },
    { kind: 'message', from: 0, to: 1, label: 'GET /api/proxy', detail: '?url&payment' },
    { kind: 'message', from: 1, to: 2, label: 'POST /generate', detail: '+ PAYMENT-SIGNATURE' },
    { kind: 'local', at: 2, label: 'settle', detail: 'onchain' },
    { kind: 'message', from: 2, to: 1, label: '200', detail: '+ receipt' },
    { kind: 'message', from: 1, to: 0, label: '200', detail: 'passed through' },
  ]

  let n = 0
  const numbered = steps.map((step) => ({ ...step, n: step.kind === 'phase' ? 0 : ++n }))
</script>

<figure class="card diagram" aria-label="Sequence of requests when paying through swarmpot">
  <div class="grid">
    {#each lanes as lane, i (lane)}
      <div class="lifeline" style:left="{((2 * i + 1) / 6) * 100}%"></div>
      <div class="lane" style:grid-column={i + 1}>{lane}</div>
    {/each}

    {#each numbered as step, i (i)}
      {#if step.kind === 'phase'}
        <div class="phase" style:grid-row={i + 2}>{step.label}</div>
      {:else if step.kind === 'local'}
        <div class="local" style:grid-row={i + 2} style:grid-column={step.at + 1}>
          <strong><span class="n">{step.n}</span>{step.label}</strong>
          <span>{step.detail}</span>
        </div>
      {:else}
        {@const start = Math.min(step.from, step.to)}
        {@const span = Math.abs(step.to - step.from) + 1}
        <div
          class="message"
          class:leftward={step.to < step.from}
          style:grid-row={i + 2}
          style:grid-column="{start + 1} / span {span}"
          style:--span={span}
        >
          <strong><span class="n">{step.n}</span>{step.label}</strong>
          <span class="arrow" aria-hidden="true"></span>
          <span class="detail">{step.detail}</span>
        </div>
      {/if}
    {/each}
  </div>
</figure>

<style>
  .diagram {
    margin: 0;
    padding: 22px 12px;
  }

  .grid {
    position: relative;
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    row-gap: 14px;
  }

  .lifeline {
    position: absolute;
    top: 36px;
    bottom: 0;
    width: 0;
    border-left: 1.5px dashed var(--border);
  }

  .lane {
    grid-row: 1;
    justify-self: center;
    position: relative;
    padding: 4px 14px;
    border-radius: 8px;
    font-weight: 700;
    font-size: 0.9rem;
    white-space: nowrap;
  }

  .phase {
    grid-column: 1 / -1;
    position: relative;
    margin-top: 12px;
    padding: 0 8px;
    justify-self: start;
    background: var(--surface);
    font-family: var(--font-mono);
    font-size: 0.75rem;
    color: var(--muted);
  }

  .phase::before {
    content: '// ';
  }

  .n {
    display: inline-grid;
    place-items: center;
    width: 20px;
    height: 20px;
    margin-right: 6px;
    border: 1px solid var(--muted);
    border-radius: 50%;
    font-family: var(--font-body);
    font-size: 0.7rem;
    vertical-align: 1px;
  }

  .message {
    /* From the middle of the first lane to the middle of the last: half a lane in from each side. */
    margin-inline: calc(100% / (2 * var(--span)));
    position: relative;
    display: grid;
    justify-items: center;
    text-align: center;
    gap: 3px;
    font-size: 0.85rem;
  }

  .message strong {
    font-family: var(--font-mono);
    font-weight: 600;
    background: var(--surface);
    padding: 0 6px;
  }

  .detail {
    color: var(--muted);
    font-family: var(--font-mono);
    font-size: 0.75rem;
    background: var(--surface);
    padding: 0 6px;
  }

  .arrow {
    position: relative;
    width: 100%;
    height: 1.5px;
    background: var(--line);
  }

  .arrow::after {
    content: '';
    position: absolute;
    top: -5px;
    right: -1px;
    border: 6px solid transparent;
    border-right: 0;
    border-left: 9px solid var(--line);
  }

  .leftward .arrow::after {
    right: auto;
    left: -1px;
    border-left: 0;
    border-right: 9px solid var(--line);
  }

  .local {
    position: relative;
    justify-self: center;
    display: grid;
    gap: 2px;
    max-width: 200px;
    background: var(--surface);
    padding: 8px 14px;
    border-radius: 8px;
    font-size: 0.8rem;
    text-align: center;
  }

  @media (max-width: 560px) {
    .diagram {
      padding: 18px 4px;
    }

    .lane {
      padding: 3px 9px;
      font-size: 0.8rem;
    }

    .message,
    .local {
      font-size: 0.75rem;
    }

    .detail {
      font-size: 0.68rem;
    }
  }
  .local > span {
    color: var(--muted);
  }
</style>
