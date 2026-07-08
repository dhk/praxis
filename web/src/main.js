import { startEngine, onEngineReady, engineStatus, enginePacks, runPipeline, downloadTrailZip } from './engine.js';
import { renderMarkdown, escapeHtml } from './markdown.js';

/* ── State ─────────────────────────────────────────── */

const DEFAULT_PACK = 'concise_scientific_writing';

const state = {
  source: '',
  trail: null,        // last completed run's artifact trail
  runSource: '',      // the source that produced `trail`
  runPack: '',        // the pack that produced `trail`
  stale: false,       // input or pack changed since last run
  step: 1,
  selectedObs: null,
  transformTab: 'diff',
  reportTab: null,
  compareView: 'raw', // 'raw' | 'rendered'
  running: false,
  error: null,
  packId: DEFAULT_PACK,
};

const EXAMPLES = [
  { id: 'technical-note', label: 'Technical note (repo example)', pack: DEFAULT_PACK },
  { id: 'hotaling-2020', label: 'Concise writing — after Hotaling (2020)', pack: DEFAULT_PACK },
  { id: 'drift-study', label: 'Model drift study', pack: DEFAULT_PACK },
  { id: 'claude-skill', label: 'Claude skill (SKILL.md)', pack: 'claude_skill_authoring' },
  { id: 'resume', label: 'Resume', pack: 'resume_writing' },
];

const SAFETY_LABEL = { safe: 'SAFE', low_risk: 'LOW RISK', review: 'REVIEW' };

const STALE_NOTE = '<div class="stale-note">Input changed since the last run — steps 2–6 are disabled until you re-run.</div>';

const STEPS = [
  { n: 1, name: 'Input' },
  { n: 2, name: 'Observe' },
  { n: 3, name: 'Recommend' },
  { n: 4, name: 'Transform' },
  { n: 5, name: 'Validate' },
  { n: 6, name: 'Report' },
  { n: 7, name: 'Compare' },
];

const stepperEl = document.getElementById('stepper');
const panelEl = document.getElementById('panel');

/* ── Live input metrics (display only; the artifacts use metrics.py) ── */

function liveMetrics(text) {
  const words = text.match(/\b\w+\b/g) || [];
  const sentences = text.match(/[^.!?]+[.!?]/g) || [];
  const avg = sentences.length ? Math.round((words.length / sentences.length) * 100) / 100 : 0;
  return { characters: text.length, words: words.length, sentences: sentences.length, average_sentence_words: avg };
}

/* ── Stepper (Zone A) ─────────────────────────────── */

function badgeFor(step) {
  if (!state.trail || state.stale) return '';
  const t = state.trail;
  switch (step) {
    case 1: return `${t.metrics.before.words.toLocaleString()} words`;
    case 2: return `${t.observations.length} observation${t.observations.length === 1 ? '' : 's'}`;
    case 3: return `${t.recommendations.length} proposed`;
    case 4: {
      const applied = t.transformations.filter((x) => x.applied).length;
      const flagged = t.transformations.length - applied;
      return `${applied} applied / ${flagged} flagged`;
    }
    case 5: return t.validation.status;
    case 6: return 'ready';
    case 7: return `${t.metrics.before.words} → ${t.metrics.after.words} words`;
    default: return '';
  }
}

function renderStepper() {
  const runComplete = state.trail && !state.stale;
  stepperEl.innerHTML = STEPS.map(({ n, name }) => {
    const enabled = n === 1 || runComplete;
    const current = state.step === n ? ' aria-current="step"' : '';
    return `<button class="step" data-step="${n}"${current} ${enabled ? '' : 'disabled'}>
      <span class="step-name"><span class="step-num">${n}</span> ${name}</span>
      <span class="step-badge">${escapeHtml(badgeFor(n))}</span>
    </button>`;
  }).join('');
}

stepperEl.addEventListener('click', (e) => {
  const btn = e.target.closest('.step');
  if (!btn || btn.disabled) return;
  state.step = Number(btn.dataset.step);
  render();
});

/* ── Panel chrome ─────────────────────────────────── */

function passHead(n, title, desc) {
  return `<div class="pass-head"><span class="pass-num">${n}</span><h2>${title}</h2></div>
    <p class="pass-desc">${desc}</p>`;
}

/* ── 1 · Input ────────────────────────────────────── */

function renderInput() {
  const m = liveMetrics(state.source);
  const eng = engineStatus();
  const engChip = eng.status === 'ready'
    ? '<span class="engine-chip mono ready">engine ready</span>'
    : eng.status === 'error'
      ? '<span class="engine-chip mono error">engine failed to load</span>'
      : '<span class="engine-chip mono">loading engine…</span>';
  const runLabel = state.running ? 'Running…' : eng.status === 'loading' ? 'Loading engine…' : 'Run pipeline';
  const canRun = eng.status === 'ready' && !state.running && state.source.trim().length > 0;
  const packs = enginePacks();
  const selected = packs.find((p) => p.id === state.packId);
  const packOptions = packs.length
    ? packs.map((p) => `<option value="${p.id}"${p.id === state.packId ? ' selected' : ''}>${escapeHtml(p.title)}</option>`).join('')
    : `<option value="${DEFAULT_PACK}" selected>${DEFAULT_PACK}</option>`;
  const packDetail = selected ? ` · v${selected.version} · ${selected.transformations} transformations` : '';
  const exampleOptions = EXAMPLES.map((e) => `<option value="${e.id}">${escapeHtml(e.label)}</option>`).join('');

  panelEl.innerHTML = `
    ${passHead(1, 'Input', 'Paste or upload the source, watch live metrics, confirm the pack in effect, then run. The pipeline runs once, in your browser — the document never leaves it.')}
    ${state.error ? `<div class="error-note">${escapeHtml(state.error)}</div>` : ''}
    <div id="stale-slot">${state.stale && state.trail ? STALE_NOTE : ''}</div>
    <div class="card">
      <div class="input-actions">
        <button class="btn" id="upload-btn">Upload file</button>
        <input type="file" id="file-input" accept=".md,.txt,text/markdown,text/plain" hidden>
        <label class="select-wrap"><span class="label">Example</span>
          <select id="example-select" class="select">
            <option value="" selected disabled>Load example…</option>
            ${exampleOptions}
          </select></label>
        ${engChip}
      </div>
      <textarea id="source" class="source-input" spellcheck="false"
        placeholder="Paste Markdown source, or drag a .md / .txt file here…">${escapeHtml(state.source)}</textarea>
      <div class="metrics-row" id="metrics-row">
        <span class="metric">${m.characters.toLocaleString()} chars</span>
        <span class="metric">${m.words.toLocaleString()} words</span>
        <span class="metric">${m.sentences.toLocaleString()} sentences</span>
        <span class="metric">avg ${m.average_sentence_words} words/sentence</span>
      </div>
      <div class="run-row">
        <span class="pack-line">Pack
          <select id="pack-select" class="select" ${packs.length ? '' : 'disabled'}>${packOptions}</select>
          <span class="pack-detail mono">${packDetail}</span>
        </span>
        <button class="btn primary" id="run-btn" ${canRun ? '' : 'disabled'}>${runLabel}</button>
      </div>
    </div>`;

  const textarea = document.getElementById('source');
  textarea.addEventListener('input', () => {
    state.source = textarea.value;
    const nowStale = Boolean(state.trail) && (state.source !== state.runSource || state.packId !== state.runPack);
    if (nowStale !== state.stale) {
      state.stale = nowStale;   // greys out / re-enables steps 2–6
      renderStepper();
      const slot = document.getElementById('stale-slot');
      if (slot) slot.innerHTML = state.stale ? STALE_NOTE : '';
    }
    updateMetricsRow();
    updateRunButton();
  });

  textarea.addEventListener('dragover', (e) => { e.preventDefault(); textarea.classList.add('dragover'); });
  textarea.addEventListener('dragleave', () => textarea.classList.remove('dragover'));
  textarea.addEventListener('drop', async (e) => {
    e.preventDefault();
    textarea.classList.remove('dragover');
    const file = e.dataTransfer.files && e.dataTransfer.files[0];
    if (file) setSource(await file.text());
  });

  document.getElementById('upload-btn').addEventListener('click', () =>
    document.getElementById('file-input').click());
  document.getElementById('file-input').addEventListener('change', async (e) => {
    const file = e.target.files && e.target.files[0];
    if (file) setSource(await file.text());
  });
  document.getElementById('example-select').addEventListener('change', async (e) => {
    const example = EXAMPLES.find((x) => x.id === e.target.value);
    if (!example) return;
    const res = await fetch(new URL(`../examples/${example.id}.md`, import.meta.url));
    state.packId = example.pack;   // an example selects its matching pack
    setSource(await res.text());
  });
  document.getElementById('pack-select').addEventListener('change', (e) => {
    state.packId = e.target.value;
    state.stale = Boolean(state.trail) && (state.source !== state.runSource || state.packId !== state.runPack);
    render();
  });
  document.getElementById('run-btn').addEventListener('click', run);
}

function setSource(text) {
  state.source = text;
  state.stale = Boolean(state.trail) && (text !== state.runSource || state.packId !== state.runPack);
  state.error = null;
  render();
}

function updateMetricsRow() {
  const m = liveMetrics(state.source);
  document.getElementById('metrics-row').innerHTML = `
    <span class="metric">${m.characters.toLocaleString()} chars</span>
    <span class="metric">${m.words.toLocaleString()} words</span>
    <span class="metric">${m.sentences.toLocaleString()} sentences</span>
    <span class="metric">avg ${m.average_sentence_words} words/sentence</span>`;
}

function updateRunButton() {
  const btn = document.getElementById('run-btn');
  if (!btn) return;
  const eng = engineStatus();
  btn.disabled = !(eng.status === 'ready' && !state.running && state.source.trim().length > 0);
}

async function run() {
  state.running = true;
  state.error = null;
  render();
  try {
    state.trail = await runPipeline(state.source, state.packId);
    state.runSource = state.source;
    state.runPack = state.packId;
    state.stale = false;
    state.selectedObs = null;
    state.step = 2;
  } catch (err) {
    state.error = `Pipeline run failed: ${err.message}`;
  } finally {
    state.running = false;
    render();
  }
}

/* ── 2 · Observe ──────────────────────────────────── */

function observationRanges() {
  const text = state.runSource;
  const ranges = [];
  let cursor = 0;
  for (const obs of state.trail.observations) {
    const m = /^char:(\d+)-(\d+)$/.exec(obs.location);
    if (m) {
      ranges.push({ start: Number(m[1]), end: Number(m[2]), obs });
    } else {
      const at = text.indexOf(obs.evidence, cursor);
      if (at !== -1) { ranges.push({ start: at, end: at + obs.evidence.length, obs }); cursor = at; }
    }
  }
  return ranges;
}

function renderHighlightedSource(ranges) {
  const text = state.runSource;
  const points = new Set([0, text.length]);
  for (const r of ranges) { points.add(r.start); points.add(r.end); }
  const cuts = [...points].sort((a, b) => a - b);
  let html = '';
  for (let i = 0; i < cuts.length - 1; i += 1) {
    const [a, b] = [cuts[i], cuts[i + 1]];
    const covering = ranges.filter((r) => r.start <= a && r.end >= b);
    const chunk = escapeHtml(text.slice(a, b));
    if (!covering.length) { html += chunk; continue; }
    // innermost (shortest) range wins for click target and color
    covering.sort((x, y) => (x.end - x.start) - (y.end - y.start));
    const top = covering[0];
    const classes = ['hl', top.obs.safety];
    if (covering.some((r) => r.obs.id === state.selectedObs)) classes.push('selected');
    const title = `${top.obs.id} · ${SAFETY_LABEL[top.obs.safety] || top.obs.safety}`;
    html += `<span class="${classes.join(' ')}" data-obs="${top.obs.id}" title="${escapeHtml(title)}">${chunk}</span>`;
  }
  return html;
}

function renderObserve() {
  const t = state.trail;
  const ranges = observationRanges();

  const groups = new Map();
  for (const obs of t.observations) {
    const key = `${obs.rule_id} · ${obs.rule_title}`;
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(obs);
  }
  const sidebar = t.observations.length === 0
    ? '<div class="empty-note">No observations — the document already matches this pack\'s guidance.</div>'
    : [...groups.entries()].map(([key, list]) => `
        <div class="label obs-rule-head">Rule · ${escapeHtml(key)}</div>
        ${list.map((obs) => `
          <button class="obs-item${obs.id === state.selectedObs ? ' selected' : ''}" data-obs="${obs.id}" id="obs-item-${obs.id}">
            <span class="obs-meta"><span class="obs-id">${obs.id}</span>
              <span class="tag ${obs.safety}">${SAFETY_LABEL[obs.safety] || obs.safety}</span></span>
            <span class="obs-evidence">“${escapeHtml(obs.evidence.length > 120 ? obs.evidence.slice(0, 120) + '…' : obs.evidence)}”</span>
            <span class="obs-reason">${escapeHtml(obs.reason)}</span>
          </button>`).join('')}`).join('');

  panelEl.innerHTML = `
    ${passHead(2, 'Observe', 'Read-only source with each observation\'s evidence highlighted and colored by safety. Click a highlight or a list entry to select and scroll to its counterpart.')}
    <div class="observe-grid">
      <div class="source-view" id="source-view">${renderHighlightedSource(ranges)}</div>
      <div class="obs-list" id="obs-list">${sidebar}</div>
    </div>`;

  panelEl.querySelectorAll('[data-obs]').forEach((el) => {
    el.addEventListener('click', () => selectObservation(el.dataset.obs, el.classList.contains('hl') ? 'list' : 'source'));
  });

  if (state.selectedObs) scrollObservationIntoView('both');
}

function selectObservation(id, scrollTarget) {
  state.selectedObs = id;
  renderObserve();
  scrollObservationIntoView(scrollTarget);
}

function scrollObservationIntoView(which) {
  const item = document.getElementById(`obs-item-${state.selectedObs}`);
  const hl = document.querySelector(`.hl[data-obs="${state.selectedObs}"]`);
  if ((which === 'list' || which === 'both') && item) item.scrollIntoView({ block: 'nearest' });
  if ((which === 'source' || which === 'both') && hl) hl.scrollIntoView({ block: 'nearest' });
}

/* ── 3 · Recommend ────────────────────────────────── */

function renderRecommend() {
  const t = state.trail;
  const rows = t.recommendations.map((rec) => {
    const isReview = rec.safety === 'review';
    const beforeAfter = isReview
      ? '<span class="no-change">no text change proposed</span>'
      : `<span class="before-after"><code>${escapeHtml(rec.before)}</code><span class="arrow">→</span><code>${escapeHtml(rec.after) || '<em>∅</em>'}</code></span>`;
    return `<tr${isReview ? ' class="review-row"' : ''}>
      <td><span class="mono">${rec.id}</span><br>
        <button class="obs-link" data-goto-obs="${rec.observation_id}">↩ ${rec.observation_id}</button></td>
      <td><span class="action-name">${escapeHtml(rec.action)}</span></td>
      <td>${beforeAfter}</td>
      <td><span class="tag ${rec.safety}">${SAFETY_LABEL[rec.safety] || rec.safety}</span></td>
    </tr>`;
  }).join('');

  panelEl.innerHTML = `
    ${passHead(3, 'Recommend', 'Every recommendation links back to its observation. Review rows propose no text change — a human decides.')}
    ${t.recommendations.length === 0
      ? '<div class="empty-note">No recommendations — nothing to change.</div>'
      : `<div class="card"><div class="table-wrap"><table class="data">
          <thead><tr><th>Rec / Obs</th><th>Action</th><th>Before → After</th><th>Safety</th></tr></thead>
          <tbody>${rows}</tbody></table></div></div>`}`;

  panelEl.querySelectorAll('[data-goto-obs]').forEach((el) => {
    el.addEventListener('click', () => {
      state.step = 2;
      state.selectedObs = el.dataset.gotoObs;
      render();
    });
  });
}

/* ── 4 · Transform ────────────────────────────────── */

function normalize(s) {
  return s.replace(/\s+/g, ' ').trim().toLowerCase();
}

function safetyForSegment(a, b) {
  const na = normalize(a);
  const nb = normalize(b);
  for (const t of state.trail.transformations) {
    if (!t.applied) continue;
    const tb = normalize(t.before);
    const ta = normalize(t.after);
    if (na && (na === tb || na.includes(tb) || tb.includes(na))) return t.safety;
    if (nb && ta && (nb === ta || nb.includes(ta))) return t.safety;
  }
  return 'other';
}

function renderDiff() {
  const { diff } = state.trail.ui;
  let html = '';
  for (const seg of diff) {
    if (seg.op === 'equal') { html += escapeHtml(seg.a); continue; }
    const safety = safetyForSegment(seg.a, seg.b);
    if (seg.a) html += `<del class="${safety}">${escapeHtml(seg.a)}</del>`;
    if (seg.b) html += `<ins class="${safety}">${escapeHtml(seg.b)}</ins>`;
  }
  return html;
}

function renderTransform() {
  const t = state.trail;
  const applied = t.transformations.filter((x) => x.applied);
  const flagged = t.transformations.filter((x) => !x.applied);

  const logTable = (list) => `<div class="table-wrap"><table class="data">
    <thead><tr><th>ID</th><th>Rule</th><th>Before → After</th><th>Safety</th><th>Validation</th></tr></thead>
    <tbody>${list.map((x) => `<tr${x.safety === 'review' ? ' class="review-row"' : ''}>
      <td><span class="mono">${x.id}</span></td>
      <td><span class="mono">${x.rule_id}</span></td>
      <td>${x.applied
        ? `<span class="before-after"><code>${escapeHtml(x.before)}</code><span class="arrow">→</span><code>${escapeHtml(x.after) || '<em>∅</em>'}</code></span>`
        : `<span class="no-change">not applied — ${escapeHtml(x.reason)}</span>`}</td>
      <td><span class="tag ${x.safety}">${SAFETY_LABEL[x.safety] || x.safety}</span></td>
      <td><span class="mono">${escapeHtml(x.validation_status)}</span></td>
    </tr>`).join('')}</tbody></table></div>`;

  const tabContent = state.transformTab === 'diff'
    ? `<div class="diff-view">${renderDiff()}</div>
       <div class="legend">
         <span class="swatch"><span class="sq safe"></span> safe — applied</span>
         <span class="swatch"><span class="sq low_risk"></span> low risk — applied</span>
         <span class="swatch"><span class="sq review"></span> review — flagged only, never applied</span>
       </div>`
    : `${applied.length ? `<div class="label">Applied (${applied.length})</div>${logTable(applied)}` : '<div class="empty-note">No transformations applied.</div>'}
       ${flagged.length ? `<div class="label" style="margin-top:12px">Flagged for human review (${flagged.length})</div>${logTable(flagged)}` : ''}`;

  panelEl.innerHTML = `
    ${passHead(4, 'Transform', 'Original vs. transformed with a word-level inline diff, applied changes colored by safety. The log lists every transformation record; flagged entries were never applied.')}
    <div class="tabs" role="tablist">
      <button class="tab" role="tab" data-tab="diff" aria-selected="${state.transformTab === 'diff'}">Diff</button>
      <button class="tab" role="tab" data-tab="log" aria-selected="${state.transformTab === 'log'}">Log</button>
    </div>
    <div class="card">${tabContent}</div>`;

  panelEl.querySelectorAll('.tab').forEach((el) => {
    el.addEventListener('click', () => { state.transformTab = el.dataset.tab; render(); });
  });
}

/* ── 5 · Validate ─────────────────────────────────── */

function renderValidate() {
  const v = state.trail.validation;
  const tokens = state.trail.ui.protected_tokens;
  const missing = new Set(v.checks.missing_protected_tokens);
  const pass = v.status === 'pass';

  panelEl.innerHTML = `
    ${passHead(5, 'Validate', 'A conservative, evidence-based check: protected tokens — URLs, numbers, citations, bracketed references — must survive the transformation untouched.')}
    <div class="validation-banner ${pass ? 'pass' : 'fail'}">
      <span class="status-word">Validation ${escapeHtml(v.status)}</span>
      <span class="status-detail">${pass
        ? '— all protected tokens preserved'
        : `— ${missing.size} protected token${missing.size === 1 ? '' : 's'} missing from the final document`}</span>
    </div>
    <div class="card">
      <div class="label">Protected tokens · ${tokens.length} checked · ${missing.size} missing</div>
      ${tokens.length
        ? `<div class="token-list">${tokens.map((tok) =>
            `<span class="token${missing.has(tok) ? ' missing' : ''}">${escapeHtml(tok)}</span>`).join('')}</div>`
        : '<div class="empty-note">No protected tokens detected in this document.</div>'}
      ${missing.size ? `<div class="label" style="color:var(--danger)">Missing</div>
        <div class="token-list">${[...missing].map((tok) => `<span class="token missing">${escapeHtml(tok)}</span>`).join('')}</div>` : ''}
    </div>
    <p class="caveat">${escapeHtml(v.note)}</p>`;
}

/* ── 6 · Report ───────────────────────────────────── */

function download(name, blob) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 5000);
}

// The exact, fixed section titles report.py emits at the top level. Only
// these split into tabs — the "Final Document" section embeds the user's
// document verbatim, which may contain its own H2 headings (e.g. "##
// Experience" in a resume), and those must stay inside that one tab rather
// than being mistaken for new top-level sections.
const REPORT_SECTIONS = ['Metrics', 'Validation', 'Transformation Diff Log', 'Final Document'];

function splitReportSections(reportMd) {
  const lines = reportMd.split('\n');
  const sections = [];
  let current = null;
  for (const line of lines) {
    const h2 = /^##\s+(.*)$/.exec(line);
    if (h2 && REPORT_SECTIONS.includes(h2[1].trim())) {
      current = { title: h2[1].trim(), lines: [] };
      sections.push(current);
    } else if (current) {
      current.lines.push(line);
    }
    // Lines before the first known section (the H1 title) are dropped —
    // it's already shown in the pass head.
  }
  return sections.map((s) => ({ title: s.title, body: s.lines.join('\n').trim() }));
}

function renderReport() {
  const t = state.trail;
  const hasPrompt = Boolean(t.ui.prompt);
  const sections = splitReportSections(t.report);
  if (!sections.some((s) => s.title === state.reportTab)) {
    state.reportTab = sections[0]?.title;
  }
  const active = sections.find((s) => s.title === state.reportTab) || sections[0];

  panelEl.innerHTML = `
    ${passHead(6, 'Report', 'The rendered report: metrics before and after, the validation summary, the transformation log, and the final document.')}
    <div class="report-actions">
      <button class="btn" id="copy-final">Copy final document</button>
      <button class="btn" id="dl-final">Download final.md</button>
      ${hasPrompt ? '<button class="btn" id="copy-prompt" title="Markdown handoff of the flagged items, ready to paste into Claude">Copy review prompt</button>' : ''}
      <button class="btn primary" id="dl-trail">Download artifact trail</button>
    </div>
    ${hasPrompt ? '<p class="prompt-hint">The review prompt packages every flagged item — evidence, reasons, protected tokens, and the document — as Markdown for an LLM (or a colleague) to propose resolutions. The pipeline itself never calls one.</p>' : ''}
    <div class="tabs" role="tablist">
      ${sections.map((s) => `<button class="tab" role="tab" data-report-tab="${escapeHtml(s.title)}" aria-selected="${s.title === active.title}">${escapeHtml(s.title)}</button>`).join('')}
    </div>
    <div class="card"><div class="report-body">${renderMarkdown(active ? active.body : t.report)}</div></div>`;

  panelEl.querySelectorAll('[data-report-tab]').forEach((el) => {
    el.addEventListener('click', () => { state.reportTab = el.dataset.reportTab; render(); });
  });

  if (hasPrompt) {
    document.getElementById('copy-prompt').addEventListener('click', async (e) => {
      await navigator.clipboard.writeText(t.ui.prompt);
      e.target.textContent = 'Copied ✓';
      setTimeout(() => { const b = document.getElementById('copy-prompt'); if (b) b.textContent = 'Copy review prompt'; }, 1500);
    });
  }

  document.getElementById('copy-final').addEventListener('click', async (e) => {
    await navigator.clipboard.writeText(t.final);
    e.target.textContent = 'Copied ✓';
    setTimeout(() => { const b = document.getElementById('copy-final'); if (b) b.textContent = 'Copy final document'; }, 1500);
  });
  document.getElementById('dl-final').addEventListener('click', () =>
    download('final.md', new Blob([t.final], { type: 'text/markdown' })));
  document.getElementById('dl-trail').addEventListener('click', async (e) => {
    e.target.disabled = true;
    try {
      const bytes = await downloadTrailZip(state.runSource, state.runPack);
      download('praxis-artifact-trail.zip', new Blob([bytes], { type: 'application/zip' }));
    } finally {
      const b = document.getElementById('dl-trail');
      if (b) b.disabled = false;
    }
  });
}

/* ── 7 · Compare ──────────────────────────────────── */

function syncScroll(a, b) {
  let lock = false;
  const follow = (from, to) => () => {
    if (lock) return;
    lock = true;
    const range = from.scrollHeight - from.clientHeight;
    const ratio = range > 0 ? from.scrollTop / range : 0;
    to.scrollTop = ratio * (to.scrollHeight - to.clientHeight);
    requestAnimationFrame(() => { lock = false; });
  };
  a.addEventListener('scroll', follow(a, b));
  b.addEventListener('scroll', follow(b, a));
}

function renderCompare() {
  const t = state.trail;
  const rendered = state.compareView === 'rendered';
  const pane = (text) => (rendered
    ? `<div class="report-body">${renderMarkdown(text)}</div>`
    : escapeHtml(text));
  const paneClass = rendered ? 'rendered-view compare-pane' : 'source-view compare-pane';

  panelEl.innerHTML = `
    ${passHead(7, 'Compare', 'Original and final documents side by side. Scrolling either pane scrolls the other proportionally.')}
    <div class="tabs" role="tablist">
      <button class="tab" role="tab" data-compare-view="raw" aria-selected="${!rendered}">Raw</button>
      <button class="tab" role="tab" data-compare-view="rendered" aria-selected="${rendered}">Rendered</button>
    </div>
    <div class="compare-grid">
      <div class="compare-col">
        <div class="label">Original · ${t.metrics.before.words} words</div>
        <div class="${paneClass}" id="cmp-original">${pane(state.runSource)}</div>
      </div>
      <div class="compare-col">
        <div class="label">Final · ${t.metrics.after.words} words</div>
        <div class="${paneClass}" id="cmp-final">${pane(t.final)}</div>
      </div>
    </div>`;

  panelEl.querySelectorAll('[data-compare-view]').forEach((el) => {
    el.addEventListener('click', () => { state.compareView = el.dataset.compareView; render(); });
  });
  syncScroll(document.getElementById('cmp-original'), document.getElementById('cmp-final'));
}

/* ── Render loop ──────────────────────────────────── */

function render() {
  if (state.step !== 1 && (!state.trail || state.stale)) state.step = 1;
  renderStepper();
  switch (state.step) {
    case 1: renderInput(); break;
    case 2: renderObserve(); break;
    case 3: renderRecommend(); break;
    case 4: renderTransform(); break;
    case 5: renderValidate(); break;
    case 6: renderReport(); break;
    case 7: renderCompare(); break;
    default: renderInput();
  }
}

/* ── Boot ─────────────────────────────────────────── */

startEngine();               // load Pyodide in the background while the user types
onEngineReady(() => { if (state.step === 1) render(); });   // also delivers pack metadata
render();

if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register(new URL('../sw.js', import.meta.url)).catch(() => {});
}
