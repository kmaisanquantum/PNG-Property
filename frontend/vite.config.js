import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')

  return {
    plugins: [react()],

    // Dev server — proxies /api to local FastAPI backend
    server: {
      host: true,
      port: 3000,
      proxy: {
        '/api': {
          target: env.VITE_API_URL || 'http://127.0.0.1:8000',
          changeOrigin: true,
          // Strip /api prefix when proxying (FastAPI routes start with /api)
          rewrite: (path) => path,
        }
      }
    },

    // Production build
    build: {
      outDir: 'dist',
      emptyOutDir: true,
      sourcemap: false,
      rollupOptions: {
        input: {
          main: 'index.html',
        },
        output: {
          // Split React into its own chunk for better caching
          manualChunks: {
            vendor: ['react', 'react-dom'],
          }
        }
      }
    },

    // Preview server (npm run preview)
    preview: {
      host: true,
      port: 4173,
    }
  }
})
