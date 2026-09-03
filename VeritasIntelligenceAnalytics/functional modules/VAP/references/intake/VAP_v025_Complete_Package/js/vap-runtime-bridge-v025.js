(function (root, factory) {
  const api = factory(root);
  if (typeof module === 'object' && module.exports) module.exports = api;
  root.VAPRuntimeBridge = Object.freeze(api);
})(typeof globalThis !== 'undefined' ? globalThis : this, function (root) {
  'use strict';
  // def 01 PARAMETERS
  const VERSION = 'v025';
  const SCHEMA = 'VIA-VAP-RUNTIME-BRIDGE/1.0';
  const DEFAULT_ENDPOINT = 'http://127.0.0.1:8765';
  function def_endpoint(value) {
    const candidate = String(value || '').trim() || ((root.location && /^https?:$/.test(root.location.protocol)) ? root.location.origin : DEFAULT_ENDPOINT);
    const parsed = new URL(candidate, DEFAULT_ENDPOINT);
    if (!/^https?:$/.test(parsed.protocol) || !['127.0.0.1', 'localhost', '::1', '[::1]'].includes(parsed.hostname)) throw new Error('RUNTIME_ENDPOINT_MUST_BE_LOOPBACK');
    return parsed.origin;
  }
  async function def_request(path, options) {
    const settings = options || {};
    const controller = new AbortController();
    const timeout = root.setTimeout(() => controller.abort(), Number(settings.timeoutMs || 20000));
    try {
      const response = await root.fetch(def_endpoint(settings.endpoint) + path, {
        method: settings.method || 'GET',
        headers: settings.body ? { 'Content-Type': 'application/json' } : undefined,
        body: settings.body ? JSON.stringify(settings.body) : undefined,
        credentials: 'omit', cache: 'no-store', redirect: 'error', signal: controller.signal
      });
      const payload = await response.json();
      if (!response.ok) throw new Error((payload && (payload.code || payload.message)) || ('HTTP_' + response.status));
      return payload;
    } finally { root.clearTimeout(timeout); }
  }
  async function def_health(endpoint) { return def_request('/api/health', { endpoint, timeoutMs: 5000 }); }
  async function def_catalog(endpoint) { return def_request('/api/catalog', { endpoint }); }
  async function def_refresh(request, endpoint) {
    const payload = await def_request('/api/refresh', { method: 'POST', body: request, endpoint });
    if (root.dispatchEvent && root.CustomEvent) root.dispatchEvent(new root.CustomEvent('vap:catalog', { detail: payload }));
    return payload;
  }
  async function def_save_image(snapshot, endpoint) { return def_request('/api/images', { method: 'POST', body: snapshot, endpoint }); }
  async function def_images(endpoint) { return def_request('/api/images', { endpoint }); }
  function def_self_test() {
    const checks = { loopbackDefault: def_endpoint(DEFAULT_ENDPOINT) === DEFAULT_ENDPOINT, remoteRejected: false };
    try { def_endpoint('https://example.com'); } catch (error) { checks.remoteRejected = error.message === 'RUNTIME_ENDPOINT_MUST_BE_LOOPBACK'; }
    return { schema: SCHEMA, version: VERSION, status: Object.values(checks).every(Boolean) ? 'PASS' : 'FAIL', checks };
  }
  return { VERSION, SCHEMA, DEFAULT_ENDPOINT, endpoint: def_endpoint, request: def_request, health: def_health, catalog: def_catalog, refresh: def_refresh, saveImage: def_save_image, images: def_images, selfTest: def_self_test };
});
