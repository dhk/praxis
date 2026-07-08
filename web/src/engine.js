/* Engine boundary: the UI calls runPipeline() and gets the whole trail back.
   Only this module knows Python exists. */

let worker = null;
let nextId = 1;
const pending = new Map();
const readyListeners = [];

let status = 'loading'; // 'loading' | 'ready' | 'error'
let initError = null;
let packs = [];

export function engineStatus() {
  return { status, error: initError };
}

/** Pack metadata from the Python registry; empty until the engine is ready. */
export function enginePacks() {
  return packs;
}

export function onEngineReady(fn) {
  if (status !== 'loading') fn(status);
  else readyListeners.push(fn);
}

export function startEngine() {
  if (worker) return;
  worker = new Worker(new URL('./worker.js', import.meta.url));
  worker.onmessage = (event) => {
    const msg = event.data;
    if (msg.type === 'ready' || msg.type === 'init-error') {
      status = msg.type === 'ready' ? 'ready' : 'error';
      initError = msg.message || null;
      packs = msg.packs || [];
      readyListeners.splice(0).forEach((fn) => fn(status));
      return;
    }
    const entry = pending.get(msg.id);
    if (!entry) return;
    pending.delete(msg.id);
    if (msg.type === 'error') entry.reject(new Error(msg.message));
    else if (msg.type === 'result') entry.resolve(msg.result);
    else if (msg.type === 'zip') entry.resolve(msg.bytes);
  };
  worker.onerror = (event) => {
    if (status === 'loading') {
      status = 'error';
      initError = event.message || 'Worker failed to start';
      readyListeners.splice(0).forEach((fn) => fn(status));
    }
  };
}

function request(op, source, pack) {
  startEngine();
  const id = nextId++;
  return new Promise((resolve, reject) => {
    pending.set(id, { resolve, reject });
    worker.postMessage({ id, op, source, pack });
  });
}

/** Run the pipeline once; resolves with the full artifact trail. */
export function runPipeline(source, pack = 'concise_scientific_writing') {
  return request('run', source, pack);
}

/** Zip of the six artifact files, byte-identical to a CLI run's output dir. */
export function downloadTrailZip(source, pack = 'concise_scientific_writing') {
  return request('zip', source, pack);
}
