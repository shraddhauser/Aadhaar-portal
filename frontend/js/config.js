/**
 * Frontend configuration — the one place that says where the API lives.
 *
 * Default: the same origin as the page, because FastAPI serves both the
 * pages and the API (locally on :8000 and on Render). To point the pages at
 * a different backend, define window.APP_CONFIG = { API_BASE: 'https://…/api' }
 * in a script tag before this file.
 */
window.APP_CONFIG = Object.assign({ API_BASE: '/api' }, window.APP_CONFIG || {});
