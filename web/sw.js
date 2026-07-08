/* Offline support: precache the app shell, then cache everything else
   (including the Pyodide runtime and Google Fonts) as it is first fetched.
   After one full load the site works with no network. */

const CACHE = 'praxis-viewer-v3';

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
  event.respondWith(
    caches.match(request).then((cached) => {
      if (cached) return cached;
      return fetch(request).then((response) => {
        if (response.ok || response.type === 'opaque') {
          const copy = response.clone();
          caches.open(CACHE).then((c) => c.put(request, copy));
        }
        return response;
      });
    }),
  );
});
