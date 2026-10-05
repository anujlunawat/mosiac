import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],

  // ── Fix: yjs, y-websocket, y-indexeddb use complex "exports" fields
  // that esbuild (Vite's pre-bundler) can't resolve automatically.
  // Listing them here forces Vite to pre-bundle them with the correct
  // browser ESM conditions.
  optimizeDeps: {
    include: [
      'yjs',
      'y-websocket',
      'y-indexeddb',
      'lib0/decoding',
      'lib0/encoding',
      'lib0/observable',
    ],
  },

  resolve: {
    // Prefer the browser-compatible build of packages that ship
    // both a Node.js and browser entry.
    conditions: ['browser', 'module', 'import', 'default'],
  },

  server: {
    port: 5173,
    proxy: {
      // Proxy REST calls: /api → http://localhost:8000
      // We strip the /api prefix since the backend routes don't use it.
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
      // Proxy auth calls: /auth → http://localhost:8000/auth
      '/auth': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      // Proxy WebSocket: /ws → ws://localhost:8000/ws
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
        changeOrigin: true,
      },
    },
  },
})
