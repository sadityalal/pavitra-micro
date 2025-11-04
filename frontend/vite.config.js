// vite.config.js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 3000,
    proxy: {
      // Proxy all /api calls to nginx
      '/api': {
        target: 'http://localhost', // Your nginx on port 80
        changeOrigin: true,
        secure: false,
      }
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true
      }
    },
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          router: ['react-router-dom'],
          ui: ['react-bootstrap', 'bootstrap'],
          http: ['axios']
        }
      }
    }
  },
  preview: {
    port: 3000,
    host: true
  },
  publicDir: 'public',
  base: './'
})