import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue' // OR '@vitejs/plugin-vue' if you use Vue
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  base: '/pytalk/',
  plugins: [vue()], // IMPORTANT: If you use Vue, change this to [vue()]
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
})