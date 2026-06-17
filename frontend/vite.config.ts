import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/auth': 'http://localhost:8000',
      '/puzzles': 'http://localhost:8000',
      '/matches': 'http://localhost:8000',
      '/lobbies': 'http://localhost:8000',
      '/users': 'http://localhost:8000',
      '/leaderboard': 'http://localhost:8000',
      '/ws': { target: 'ws://localhost:8000', ws: true },
    },
  },
})
