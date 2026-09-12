import { defineConfig, loadEnv } from 'vite';

export default defineConfig(({ mode }) => {
  // Load environment variables based on current mode (e.g. .env file)
  const env = loadEnv(mode, process.cwd(), '');

  const targetUrl = (env.VITE_BACKEND_API_URL || env.VITE_API_BASE_URL || '').trim().replace(/\/+$/, '');

  const proxyConfig = targetUrl
    ? {
        target: targetUrl,
        changeOrigin: true,
        secure: false,
        headers: {
          'ngrok-skip-browser-warning': 'true',
        },
      }
    : undefined;

  return {
    server: {
      host: '0.0.0.0',
      port: 5173,
      strictPort: false,
      allowedHosts: true,
      proxy: proxyConfig
        ? {
            '/api': proxyConfig,
            '/featured-videos': proxyConfig,
            '/playlists': proxyConfig,
          }
        : undefined,
    },
    preview: {
      host: '0.0.0.0',
      port: 5173,
      proxy: proxyConfig
        ? {
            '/api': proxyConfig,
            '/featured-videos': proxyConfig,
            '/playlists': proxyConfig,
          }
        : undefined,
    },
  };
});
