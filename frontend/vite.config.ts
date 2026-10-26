import { svelte } from '@sveltejs/vite-plugin-svelte'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [svelte()],
  build: {
    // Two pages: the explainer at / and the public payments record at /payments/.
    rollupOptions: { input: { main: 'index.html', payments: 'payments/index.html' } },
  },
  server: {
    // FastAPI runs on :8765 in dev (`uv run fastapi dev --port 8765`).
    proxy: { '/api': 'http://127.0.0.1:8765' },
  },
})
