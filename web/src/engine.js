/* Engine boundary: the UI calls runPipeline() and gets the whole trail back.
   Only this module knows Python exists. */

let worker = null;
let nextId = 1;
const pending = new Map();
const readyListeners = [];

let status = 'loading'; // 'loading' | 'ready' | 'error'
let initError = null;
let packs = [];
let fields = [];

export function engineStatus() {
  return { status, error: initError };
}

/** Pack metadata from the Python registry; empty until the engine is ready. */
export function enginePacks() {
  return packs;
}

/** Contract fields with their closed domains, for the design surface.
    `options` is empty for the eleven free-text fields — the picker and the
    free-text affordance are different, and a field with no domain must not
    be given a fake one. */
export function engineFields() {
  return fields;
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
      fields = msg.fields || [];
      readyListeners.splice(0).forEach((fn) => fn(status));
      return;
    }
    const entry = pending.get(msg.id);
    if (!entry) return;
    pending.delete(msg.id);
    if (msg.type === 'error') entry.reject(new Error(msg.message));
    else if (msg.type === 'result') entry.resolve(msg.result);
    else if (msg.type === 'zip') entry.resolve(msg.bytes);
    // A rejected design is the writer's mistake, not a failure: a mode that
    // needs a draft, or a value outside its domain. It resolves with the
    // sentence to show rather than rejecting with an exception to catch.
    else if (msg.type === 'design') entry.resolve(msg.result);
    else if (msg.type === 'design-rejected') entry.resolve({ rejected: msg.message });
  };
  worker.onerror = (event) => {
    if (status === 'loading') {
      status = 'error';
      initError = event.message || 'Worker failed to start';
      readyListeners.splice(0).forEach((fn) => fn(status));
    }
  };
}

function request(op, payload) {
  startEngine();
  const id = nextId++;
  return new Promise((resolve, reject) => {
    pending.set(id, { resolve, reject });
    worker.postMessage({ id, op, ...payload });
  });
}

/** Run the pipeline once; resolves with the full artifact trail. */
export function runPipeline(source, pack = 'concise_scientific_writing') {
  return request('run', { source, pack });
}

/** Zip of the six artifact files, byte-identical to a CLI run's output dir. */
export function downloadTrailZip(source, pack = 'concise_scientific_writing') {
  return request('zip', { source, pack });
}

/** The design layer's one entry point. `mode` is auto | compose | evaluate |
    transform; auto never selects transform, so the gate is the engine's rule
    and not the UI's. Resolves with `{ rejected }` when the writer's own input
    is the problem. */
export function runDesign({ draft = '', stated = {}, mode = 'auto', voice = '', variants = null } = {}) {
  return request('design', { draft, stated, mode, voice, variants });
}
