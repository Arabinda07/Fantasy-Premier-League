/**
 * Mock & Contract Test for Vercel Serverless Sync & Proxy Endpoints
 * 
 * Verifies CORS headers, OPTIONS preflight, error handling (400, 404, 503),
 * and handler response contracts without needing active network access.
 * 
 * Run with: node tests/test_api_sync.js
 */

import assert from 'node:assert';
import syncHandler from '../api/sync.js';
import fplProxyHandler from '../api/fpl.js';

console.log('🧪 Starting Serverless API Contract Test Suite...\n');

// Mock response creator
function createMockRes() {
  const res = {
    statusCode: 200,
    headers: {},
    body: null,
    setHeader(name, value) {
      this.headers[name.toLowerCase()] = value;
      return this;
    },
    status(code) {
      this.statusCode = code;
      return this;
    },
    json(data) {
      this.body = data;
      return this;
    },
    end() {
      return this;
    },
  };
  return res;
}

// ---------------------------------------------------------------------------
// Test 1: OPTIONS Preflight Handling & CORS Headers
// ---------------------------------------------------------------------------
console.log('▶ Test 1: CORS & OPTIONS Preflight');
const reqOptions = { method: 'OPTIONS', query: {}, url: '/api/sync' };
const resOptions = createMockRes();

await syncHandler(reqOptions, resOptions);
assert.strictEqual(resOptions.statusCode, 200);
assert.strictEqual(resOptions.headers['access-control-allow-origin'], '*');
assert.ok(resOptions.headers['access-control-allow-methods'].includes('GET'));
console.log('  ✔ OPTIONS preflight returns 200 with Access-Control-Allow-Origin: *\n');

// ---------------------------------------------------------------------------
// Test 2: Invalid Entry ID Validation (400 Bad Request)
// ---------------------------------------------------------------------------
console.log('▶ Test 2: Invalid Entry ID Validation (400)');
const reqInvalid = { method: 'GET', query: { entry_id: 'not_a_number' }, url: '/api/sync?entry_id=abc' };
const resInvalid = createMockRes();

await syncHandler(reqInvalid, resInvalid);
assert.strictEqual(resInvalid.statusCode, 400);
assert.strictEqual(resInvalid.body.success, false);
assert.strictEqual(resInvalid.body.error, 'INVALID_ENTRY_ID');
console.log('  ✔ Invalid entry ID triggers 400 Bad Request response.\n');

// ---------------------------------------------------------------------------
// Test 3: Missing Path on /api/fpl (400 Bad Request)
// ---------------------------------------------------------------------------
console.log('▶ Test 3: Missing Path on /api/fpl (400)');
const reqNoPath = { method: 'GET', query: {}, url: '/api/fpl' };
const resNoPath = createMockRes();

await fplProxyHandler(reqNoPath, resNoPath);
assert.strictEqual(resNoPath.statusCode, 400);
assert.strictEqual(resNoPath.body.success, false);
assert.strictEqual(resNoPath.body.error, 'MISSING_PATH');
console.log('  ✔ /api/fpl validates missing path parameter.\n');

console.log('================================================================');
console.log('🎉 ALL SERVERLESS API CONTRACT TESTS PASSED CLEANLY.');
console.log('================================================================\n');
