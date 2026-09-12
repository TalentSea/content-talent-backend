import { defineConfig, loadEnv } from 'vite';

export default defineConfig(({ mode }) => {
  // Load environment variables based on current mode (e.g. .env file)
  const env = loadEnv(mode, process.cwd(), '');

  return {
    server: {
      host: '0.0.0.0',
      port: 5173,
      strictPort: false,
      allowedHosts: true,
      proxy: {
        '/api': {
          target: env.VITE_BACKEND_API_URL || env.VITE_API_BASE_URL,
          changeOrigin: true,
        },
      },
    },
  };
});
