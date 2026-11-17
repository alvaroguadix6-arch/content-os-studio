import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// base './' permite publicar en cualquier subruta (p. ej. GitHub Pages /content-os/)
export default defineConfig({
  base: './',
  plugins: [react()],
  optimizeDeps: { exclude: ['onnxruntime-web'] },
  build: { target: 'es2020', chunkSizeWarningLimit: 2000 },
  test: { include: ['tests/unit/**/*.test.js'], environment: 'node' },
});
