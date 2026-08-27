import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

const apiMiddleware = async (req, res, next) => {
  const url = req.url || '';
  if (url.startsWith('/api/sync')) {
    res.status = (code) => {
      res.statusCode = code;
      return res;
    };
    res.json = (data) => {
      res.setHeader('Content-Type', 'application/json');
      res.end(JSON.stringify(data));
      return res;
    };
    try {
      const { default: syncHandler } = await import('../api/sync.js');
      await syncHandler(req, res);
    } catch (err) {
      console.error('[Vite Dev /api/sync Error]:', err);
      res.statusCode = 500;
      res.setHeader('Content-Type', 'application/json');
      res.end(JSON.stringify({ success: false, error: 'SERVER_ERROR', message: err.message }));
    }
    return;
  }

  if (url.startsWith('/api/fpl')) {
    res.status = (code) => {
      res.statusCode = code;
      return res;
    };
    res.json = (data) => {
      res.setHeader('Content-Type', 'application/json');
      res.end(JSON.stringify(data));
      return res;
    };
    try {
      const { default: fplHandler } = await import('../api/fpl.js');
      await fplHandler(req, res);
    } catch (err) {
      console.error('[Vite Dev /api/fpl Error]:', err);
      res.statusCode = 500;
      res.setHeader('Content-Type', 'application/json');
      res.end(JSON.stringify({ success: false, error: 'SERVER_ERROR', message: err.message }));
    }
    return;
  }

  next();
};

function apiDevServerPlugin() {
  return {
    name: 'api-dev-server',
    configureServer(server) {
      server.middlewares.use(apiMiddleware);
    },
    configurePreviewServer(server) {
      server.middlewares.use(apiMiddleware);
    }
  };
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), apiDevServerPlugin()],
  base: './',
})
