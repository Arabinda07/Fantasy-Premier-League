/**
 * Vercel Serverless Function: Transparent FPL REST API CORS Proxy
 * 
 * Route: /api/fpl?path=bootstrap-static/
 *        /api/fpl?path=fixtures/
 *        /api/fpl?path=element-summary/123/
 */

const FPL_BASE_URL = 'https://fantasy.premierleague.com/api';

const DEFAULT_HEADERS = {
  'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
  'Accept': 'application/json',
};

export default async function handler(req, res) {
  // 1. CORS Headers
  res.setHeader('Access-Control-Allow-Credentials', 'true');
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,OPTIONS');
  res.setHeader(
    'Access-Control-Allow-Headers',
    'X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version, Authorization'
  );

  // Handle preflight OPTIONS request
  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  // 2. Extract target path
  const query = req.query || {};
  let path = query.path || '';

  if (!path && req.url && req.url.includes('?')) {
    const urlParams = new URLSearchParams(req.url.split('?')[1]);
    path = urlParams.get('path') || '';
  }

  if (!path) {
    res.status(400).json({
      success: false,
      error: 'MISSING_PATH',
      message: 'Parameter "path" is required (e.g. ?path=bootstrap-static/).',
    });
    return;
  }

  // Prevent path traversal
  const sanitizedPath = path.replace(/^\/+/, '');
  const targetUrl = `${FPL_BASE_URL}/${sanitizedPath}`;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 8000);

  try {
    const fplRes = await fetch(targetUrl, {
      headers: DEFAULT_HEADERS,
      signal: controller.signal,
    });

    if (fplRes.status === 503) {
      res.status(503).json({
        success: false,
        error: 'FPL_MAINTENANCE',
        message: 'The official FPL API is currently updating.',
      });
      return;
    }

    if (!fplRes.ok) {
      res.status(fplRes.status).json({
        success: false,
        error: `HTTP_${fplRes.status}`,
        message: `FPL endpoint returned status ${fplRes.status}.`,
      });
      return;
    }

    const data = await fplRes.json();
    res.status(200).json(data);
  } catch (err) {
    if (err.name === 'AbortError') {
      res.status(504).json({
        success: false,
        error: 'FPL_TIMEOUT',
        message: 'Request to FPL server timed out after 8s.',
      });
      return;
    }

    res.status(500).json({
      success: false,
      error: 'SERVER_ERROR',
      message: err.message || 'Internal proxy error.',
    });
  } finally {
    clearTimeout(timeoutId);
  }
}
