/* Offline support: precache the app shell, then cache everything else
   (including the Pyodide runtime and Google Fonts) as it is first fetched.
   After one full load the site works with no network.

   Fetch strategy is stale-while-revalidate, not cache-first: every request
   is answered from cache immediately (so offline and repeat loads stay
   fast), but a network fetch always runs in the background and refreshes
   the cache for next time. Without this, a returning visitor would keep
   seeing whatever was cached on their first visit forever — the service
   worker only re-precaches when this file's bytes change, so a deploy that
   touches index.html/styles.css/etc. but not sw.js would otherwise never
   reach anyone who had already visited. */

const CACHE = 'praxis-viewer-v5';

const SHELL = [
  './',
  './index.html',
  './styles.css',
  './src/main.js',
  './src/engine.js',
  './src/worker.js',
  './src/markdown.js',
  './examples/technical-note.md',
  './examples/hotaling-2020.md',
  './examples/drift-study.md',
  './examples/claude-skill.md',
  './examples/resume.md',
  './py/manifest.json',
  './vendor/pyodide/pyodide.js',
  './vendor/pyodide/pyodide.asm.js',
  './vendor/pyodide/pyodide.asm.wasm',
  './vendor/pyodide/python_stdlib.zip',
  './vendor/pyodide/pyodide-lock.json',
];

self.addEventListener('install', (event) => {
  event.waitUntil((async () => {
    const cache = await caches.open(CACHE);
    await cache.addAll(SHELL);
    const manifest = await (await fetch('./py/manifest.json')).json();
    await cache.addAll(manifest.files.map((f) => `./py/praxis/${f}`));
    await self.skipWaiting();
  })());
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim()),
  );
});

self.addEventListener('fetch', (event) => {
  const { request } = event;
  if (request.method !== 'GET') return;

  const revalidate = fetch(request).then((response) => {
    if (response.ok || response.type === 'opaque') {
      const copy = response.clone();
      caches.open(CACHE).then((cache) => cache.put(request, copy));
    }
    return response;
  });

  event.respondWith(
    caches.match(request).then((cached) => cached || revalidate),
  );
  // Keep refreshing the cache even when `cached` already answered the page,
  // and swallow offline rejections here so they don't surface as unhandled.
  event.waitUntil(revalidate.catch(() => {}));
});
