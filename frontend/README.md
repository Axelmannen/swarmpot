# swarmpot frontend

Svelte 5 + Vite + TypeScript. Two pages: the explainer (`index.html`, `src/App.svelte`) and the public payments page (`payments/index.html`, `src/Payments.svelte`).

```sh
npm install
npm run dev     # http://localhost:5173, proxies /api to FastAPI on :8765
npm run check   # svelte-check + tsc
npm run build   # to dist/, which FastAPI serves
```

See [AGENTS.md](../AGENTS.md) for the conventions.
