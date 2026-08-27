/* Design layer viewer.
   Spec: docs/design/design-layer-viewer/SPEC.md.

   Two product rules shape everything here:
   the answer comes first and the reasoning is opt-in; and evaluate and
   transform are different acts, so transform sits behind a gate the writer
   has to pass deliberately. The engine enforces the second independently —
   mode "auto" never selects transform — so this file cannot get it wrong by
   accident.

   No framework and no build step, matching main.js. State goes in one
   object, render() rebuilds the body from it, and every handler is delegated
   from a single click listener so re-rendering never orphans a binding. */

import { escapeHtml } from './markdown.js';
import { runDesign, engineFields, engineStatus, onEngineReady, startEngine } from './engine.js';

/* The reference implementation's draft, kept as the example: it carries one
   of every marker kind and a protected span that blocks an edit. */
const EXAMPLE_DRAFT = `Subject: Approving the Pyodide bundle for the public viewer

We need a decision on whether the public viewer ships the full Pyodide runtime or a trimmed build. The full runtime is 7 MB and downloads once; the trimmed build is 2.4 MB but drops three stdlib modules the engine imports, which would mean maintaining a shim.

Engineering prefers the full runtime. It costs nothing to maintain and the download is cached after first load. The trimmed build saves 4.6 MB on a cold visit, which matters on mobile.

I'd like to go with the full runtime unless someone objects by Friday.

Happy to talk it through if that's easier.`;

const app = document.getElementById('app');
const modeLabel = document.getElementById('mode-label');
const themeBtn = document.getElementById('theme-btn');
const resetBtn = document.getElementById('reset-btn');

const state = {
  stage: 'empty',              // empty | evaluated | transformed
  draft: '',
  stated: {},                  // field name -> value the writer stated
  result: null,                // the last design() result
  transform: null,             // the last transform-mode result
  open: { why: false, score: false, contract: false },
  editing: null,               // contract field name whose picker is open
  sel: null,                   // selected change id, shared by both panes
  draftView: 'marked',         // marked | original
  stopped: false,
  busy: false,
  notice: null,                // a rejection to show the writer
  theme: 'light',
};

/* ── theme ──────────────────────────────────────────────────────────── */

function applyTheme() {
  const root = document.documentElement;
  if (state.theme === 'dark') root.setAttribute('data-dlv-theme', 'dark');
  else root.removeAttribute('data-dlv-theme');
  themeBtn.textContent = state.theme === 'dark' ? 'Dark' : 'Light';
}

/* ── engine ─────────────────────────────────────────────────────────── */

async function evaluate(mode = 'auto') {
  state.busy = true;
  state.notice = null;
  render();
  const result = await runDesign({ draft: state.draft, stated: state.stated, mode });
  state.busy = false;
  if (result.rejected) {
    state.notice = result.rejected;
    render();
    return null;
  }
  // Transform mode returns the whole evaluation *plus* a `transform`
  // sub-object. Keep both: the depth map still reads the evaluation.
  if (mode === 'transform') { state.result = result; state.transform = result.transform; }
  else { state.result = result; state.transform = null; }
  render();
  return result;
}

/* ── data helpers ───────────────────────────────────────────────────── */

/** Group the contract by the engine's own sections, in FIELDS order. The
    groups hold 3/4/5/3/2/2/2 fields, so the grid must ragged-bottom. */
function contractGroups() {
  const contract = (state.result && state.result.contract) || {};
  const sections = contract.sections || {};
  const provenance = contract.provenance || {};
  const groups = new Map();
  for (const field of engineFields()) {
    if (!groups.has(field.section)) groups.set(field.section, []);
    const value = (sections[field.section] || {})[field.name];
    groups.get(field.section).push({
      name: field.name,
      question: field.question,
      options: field.options || [],
      value: value == null || value === '' ? '—' : String(value),
      // Absent is not inferred: a field praxis has said nothing about shows
      // neither dot filled nor a guess italicised as though it had one.
      provenance: provenance[field.name] || null,
      known: value != null && value !== '',
    });
  }
  return [...groups].map(([section, fields]) => ({ section, fields }));
}

function statedCount() {
  const provenance = ((state.result && state.result.contract) || {}).provenance || {};
  return Object.values(provenance).filter((p) => p === 'stated').length;
}

function dimensions() {
  return (state.result && state.result.evaluation && state.result.evaluation.dimensions) || [];
}

function verdictCounts() {
  const counts = { pass: 0, gap: 0, unknown: 0 };
  for (const d of dimensions()) if (counts[d.status] != null) counts[d.status] += 1;
  return counts;
}

/** A dimension name as a title a person reads: outcome_clarity → Outcome clarity. */
function humanise(name) {
  const words = String(name).replace(/_/g, ' ');
  return words.charAt(0).toUpperCase() + words.slice(1);
}

function edits() {
  return (state.transform && state.transform.edits) || [];
}

/** Where an edit sits in the draft. Inserts carry `at`; everything that
    changes existing words carries a `where` span. */
function editSpan(edit) {
  if (edit.where && edit.where.start != null) {
    return { start: edit.where.start, end: edit.where.end, text: edit.where.text || '' };
  }
  return { start: edit.at, end: edit.at, text: '' };
}

/** gap name -> the edit it folded into. */
function foldedInto() {
  return (state.transform && state.transform.folded_into) || {};
}

function noEditFor() {
  return (state.transform && state.transform.no_edit_for) || [];
}

/** Which gaps folded into this edit, by its dimension. */
function foldsFor(dimension) {
  return Object.entries(foldedInto())
    .filter(([, target]) => target === dimension)
    .map(([gap]) => gap);
}

function editKind(edit) {
  // blocked_by is a list of protected spans, empty when nothing collided.
  if (edit.blocked_by && edit.blocked_by.length) return 'blocked';
  return String(edit.kind || 'revise').toLowerCase();
}

function offsetLabel(edit) {
  const { start, end } = editSpan(edit);
  if (start == null) return '';
  if (end == null || end === start) return `char ${start}`;
  return `chars ${start}–${end}`;
}

/* ── render ─────────────────────────────────────────────────────────── */

function render() {
  modeLabel.textContent =
    state.stage === 'empty' ? 'Compose' : state.stage === 'transformed' ? 'Transform' : 'Evaluate';
  app.innerHTML = state.stage === 'empty' ? composeView() : evaluatedView();
}

function composeView() {
  const engine = engineStatus();
  const words = state.draft.trim() ? state.draft.trim().split(/\s+/).length : 0;
  const stated = Object.keys(state.stated).length;
  const total = engineFields().length || 21;
  const outstanding = state.result ? state.result.questions_outstanding : null;

  return `
  <div class="compose">
    <div class="mono">Compose · nothing written yet</div>
    <h1>Tell me who reads this and what they have to do, and I will tell you what shape it wants — before you write a word.</h1>
    <p class="lede">The decision comes before the sentences. Nothing here needs your draft;
    it comes from what you have already told me, and it runs entirely in this page.</p>

    <div class="stats">
      <div>
        <div class="mono">Stated</div>
        <div class="stat-value">${stated} of ${total} fields</div>
      </div>
      <div>
        <div class="mono">Could still change this</div>
        <div class="stat-value live">${outstanding == null ? 'Not asked yet' : `${outstanding} question${outstanding === 1 ? '' : 's'}`}</div>
      </div>
      <div>
        <div class="mono">Draft</div>
        <div class="stat-value idle">${words ? `${words} words` : 'Not needed yet'}</div>
      </div>
    </div>

    <div class="draft-box">
      <div class="mono">When you have a draft</div>
      <textarea id="draft-input" placeholder="Paste it here. Nothing leaves this page.">${escapeHtml(state.draft)}</textarea>
      <div class="draft-actions">
        <button class="btn btn-primary" data-act="evaluate" type="button"${engine.status === 'ready' ? '' : ' disabled'}>Evaluate this draft</button>
        <button class="btn btn-ghost" data-act="example" type="button"${engine.status === 'ready' ? '' : ' disabled'}>Load an example</button>
        <span class="mono-plain">${engineNote(engine, words)}</span>
      </div>
    </div>
    ${state.notice ? `<div class="notice">${escapeHtml(state.notice)}</div>` : ''}
  </div>`;
}

function engineNote(engine, words) {
  if (engine.status === 'loading') return 'Starting the engine…';
  if (engine.status === 'error') return `Engine failed to start: ${engine.error || 'unknown'}`;
  if (state.busy) return 'Reading…';
  return words ? `${words} words · never leaves this page` : 'Nothing leaves this page';
}

function evaluatedView() {
  const r = state.result;
  if (!r) return '';
  const ui = r.ui || {};
  const outstanding = r.questions_outstanding || 0;

  return `
  <div class="wide evaluated">
    <section class="answer">
      <div class="mono">The answer</div>
      <h1>${escapeHtml(ui.answer || '')}</h1>
      ${r.strategy && r.strategy.summary ? `<p class="answer-body">${escapeHtml(r.strategy.summary)}</p>` : ''}
      <div class="answer-foot">
        <span class="mono-plain">${escapeHtml(ui.progress || '')}</span>
        ${outstanding > 0 ? '<a href="#questions" class="mono-plain">Answer them →</a>' : ''}
      </div>
    </section>

    ${depthMap(r)}
    ${state.open.why ? depthWhy(ui) : ''}
    ${state.open.score ? depthScore() : ''}
    ${state.open.contract ? depthContract() : ''}
    ${questionCard(ui, outstanding)}
    ${state.stage === 'evaluated' ? gate() : ''}
    ${state.stage === 'transformed' ? transformView() : ''}
    ${state.notice ? `<div class="notice" style="margin-top:32px;">${escapeHtml(state.notice)}</div>` : ''}
  </div>`;
}

// The row counts reasons, and `because` is capped — so it must count the
// total, not the rows on screen. Reporting the cap as the count is the
// failure #48 names, and a summary row is where it would be least visible.
function reasonCount(r) {
  const shown = (r.strategy && r.strategy.because) ? r.strategy.because.length : 0;
  const total = (r.strategy && r.strategy.because_total != null)
    ? r.strategy.because_total : shown;
  return total > shown ? `${shown} of ${total} reasons` : `${total} reasons`;
}

function depthMap(r) {
  const counts = verdictCounts();
  const total = dimensions().length;
  const fields = engineFields().length;
  const gated = state.stage === 'transformed';
  const changes = edits().length;

  const row = (num, label, meta, act) => `
    <button class="depth-row" data-act="${act}" type="button">
      <span class="depth-num">${num}</span>
      <span class="depth-label">${label}</span>
      <span class="depth-meta">${escapeHtml(meta)}</span>
    </button>`;

  return `
  <div class="depths">
    ${row('01', 'Why this shape', reasonCount(r), 'toggle-why')}
    ${row('02', 'What is missing', `${total} dimensions · ${counts.unknown} unknown`, 'toggle-score')}
    ${row('03', 'What praxis thinks you meant', `${fields} fields · ${statedCount()} stated`, 'toggle-contract')}
    ${gated
      ? row('04', 'What to change, and where', `${changes} located`, 'scroll-transform')
      : `<div class="depth-row locked">
           <span class="depth-num">04</span>
           <span class="depth-label">What to change, and where</span>
           <span class="depth-meta">You have not asked</span>
         </div>`}
  </div>`;
}

function depthWhy(ui) {
  const lines = String(ui.why || '')
    .split('\n')
    .map((l) => l.trim())
    .filter(Boolean);
  return `
  <section class="section read">
    <div class="section-divider"><span>01 — Why this shape</span></div>
    <div class="reasons">
      ${lines.map((line) => `
        <div class="reason"><span class="arrow">→</span><p>${escapeHtml(line)}</p></div>`).join('')}
    </div>
  </section>`;
}

function depthScore() {
  const counts = verdictCounts();
  const cells = dimensions().map((d) => `
    <div class="cell${d.status === 'unknown' ? ' is-unknown' : ''}">
      <div class="cell-head">
        <span class="verdict ${d.status}">${d.status}</span>
        <span class="cell-title">${escapeHtml(humanise(d.dimension))}</span>
      </div>
      <p class="cell-body">${escapeHtml(d.finding || d.question || '')}</p>
      ${(d.evidence && d.evidence.length)
        ? `<p class="cell-evidence">${escapeHtml(d.evidence.join(' · '))}</p>`
        : ''}
    </div>`).join('');

  return `
  <section class="section">
    <div class="section-divider"><span>02 — What is missing</span></div>
    <div class="score-counts">${counts.pass} pass · ${counts.gap} gap · ${counts.unknown} unknown · no overall score, by design</div>
    <div class="scorecard">${cells}</div>
    <p class="score-note"><span class="tag">Unknown</span> is not a failure and not a loading
    state. It means the answer does not depend on it yet, or you have not said.</p>
  </section>`;
}

function depthContract() {
  const groups = contractGroups().map((g) => `
    <div>
      <div class="group-name">${escapeHtml(g.section)}</div>
      ${g.fields.map((f) => fieldRow(f)).join('')}
    </div>`).join('');

  return `
  <section class="section">
    <div class="section-divider"><span>03 — What praxis thinks you meant</span></div>
    <div class="legend-dots">
      <span class="legend-dot"><span class="dot-stated"></span>Stated</span>
      <span class="legend-dot"><span class="dot-inferred"></span>Inferred · click to correct</span>
    </div>
    <div class="contract-grid">${groups}</div>
  </section>`;
}

function fieldRow(f) {
  const inferred = f.known && f.provenance !== 'stated';
  const open = state.editing === f.name;
  const dot = inferred ? 'dot-inferred' : 'dot-stated';
  const row = `
    <button class="field-row${inferred ? ' inferred' : ''}" data-act="edit-field" data-field="${escapeHtml(f.name)}" type="button">
      <span class="field-key">${escapeHtml(f.name)}</span>
      <span class="field-value">${escapeHtml(f.value)}</span>
      <span style="flex:1"></span>
      ${f.options.length ? '' : '<span class="field-kind">free text</span>'}
      <span class="field-dot ${dot}"></span>
    </button>`;
  if (!open) return row;
  /* A field with no closed domain gets no picker — the eleven free-text
     fields are named as such rather than given a fake list to choose from. */
  const editor = f.options.length
    ? `<div class="picker">
         ${f.options.map((opt) => `
           <button class="picker-opt${state.stated[f.name] === opt ? ' on' : ''}" data-act="set-field" data-field="${escapeHtml(f.name)}" data-value="${escapeHtml(opt)}" type="button">${escapeHtml(opt)}</button>`).join('')}
       </div>`
    : `<div class="picker-note">${escapeHtml(f.question)} This field is free text —
       there is no list to choose from, and a free-text editor is not built yet.</div>`;
  return row + editor;
}

function questionCard(ui, outstanding) {
  const q = ui.question;
  if (state.stopped && q) {
    return `
    <section class="questions" id="questions">
      <div class="qcard-flat">
        <span>Stopped with ${outstanding} question${outstanding === 1 ? '' : 's'} unanswered.
        The answer above still holds; it is just less certain.</span>
        <button class="qlink" data-act="resume" type="button">Ask me again →</button>
      </div>
    </section>`;
  }
  if (!q) {
    return `
    <section class="questions" id="questions">
      <div class="qcard done">
        <div class="mono-teal">Progress · complete</div>
        <h3>Nothing else you could tell me would change the answer.</h3>
        <p class="qdecides">${escapeHtml(ui.progress || '')}</p>
      </div>
    </section>`;
  }
  return `
  <section class="questions" id="questions">
    <div class="qcard">
      <div class="mono">One question · ${outstanding} of ${outstanding} left</div>
      <h3>${escapeHtml(q.ask || '')}</h3>
      <p class="qdecides">Decides between: ${escapeHtml(q.changes || '')}</p>
      <div class="qoptions">
        ${(q.options || []).map((opt) => `
          <button class="qoption" data-act="answer" data-field="${escapeHtml(q.field)}" data-value="${escapeHtml(opt)}" type="button">${escapeHtml(opt)}</button>`).join('')}
      </div>
      <button class="qlink" data-act="stop" type="button">I would rather stop here →</button>
    </div>
  </section>`;
}

function gate() {
  const gaps = verdictCounts().gap;
  const outstanding = (state.result && state.result.questions_outstanding) || 0;
  return `
  <section class="gate">
    <div class="section-divider"><span>04 — What to change, and where</span></div>
    <p>"What is wrong" and "what to change" are different questions. I have answered the
    first. The second rewrites your draft, so you have to ask for it.</p>
    <div class="gate-actions">
      <button class="btn btn-primary" data-act="transform" type="button">Show me the changes</button>
      <span class="mono-plain">${gaps
        ? `${gaps} gap${gaps === 1 ? '' : 's'} to locate · nothing is applied`
        : 'No gaps yet, so nothing to locate'}</span>
    </div>
    ${gaps ? '' : `
      <p class="gutter-note" style="margin-top:14px;max-width:640px;">I have found nothing to
      change, and that is a statement about what you have told me rather than about your
      draft. ${outstanding
        ? `<a href="#questions">Answering ${outstanding === 1 ? 'the question' : 'a question'} above</a>
           may give me the standard to hold it to.`
        : 'There is nothing further I could ask that would change it.'}</p>`}
  </section>`;
}

/* ── transform ──────────────────────────────────────────────────────── */

function transformView() {
  const list = edits();
  const blocked = list.filter((e) => e.blocked_by && e.blocked_by.length).length;
  if (!list.length) {
    /* Honest rather than empty: an engine that reports no gaps has nothing
       to locate, and saying so beats an empty two-pane that reads as broken. */
    return `
    <section class="transform" id="transform">
      <div class="section-divider"><span>04 — What to change, and where</span></div>
      <p class="notice">Nothing located. I found no gaps to fix against the situation as you
      have described it, so there is no change I can point at in your draft. Tell me more
      above and ask again — I will not invent an edit to fill the space.</p>
    </section>`;
  }
  return `
  <section class="transform" id="transform">
    <div class="section-divider"><span>04 — What to change, and where</span></div>
    <div class="marker-legend">
      <span class="legend-item"><span style="color:var(--accent);font-size:13px;">⌃</span>Insert</span>
      <span class="legend-item"><span class="rule-solid"></span>Revise</span>
      <span class="legend-item"><span style="color:var(--accent-purple);">⇅</span>Move</span>
      <span class="legend-item"><span class="rule-cut"></span>Cut</span>
      <span class="legend-item blocked"><span>⊘</span>Blocked</span>
    </div>
    <div class="two-pane">
      ${draftPane(list)}
      ${gutter(list, blocked)}
    </div>
  </section>`;
}

function draftPane(list) {
  const marked = state.draftView === 'marked';
  return `
  <div class="draft-card">
    <div class="draft-head">
      <div class="mono">Your draft</div>
      <div style="flex:1"></div>
      <button class="view-toggle${marked ? ' on' : ''}" data-act="view-marked" type="button">Marked up · ${list.length} change${list.length === 1 ? '' : 's'}</button>
      <span class="view-sep">|</span>
      <button class="view-toggle${marked ? '' : ' on'}" data-act="view-original" type="button">Original</button>
      <span class="view-label">${marked ? 'With changes in place' : 'As you wrote it'}</span>
    </div>
    ${marked
      ? `<div class="draft-prose">${markedDraft(list)}</div>`
      : `<pre class="draft-original">${escapeHtml(state.draft)}</pre>`}
  </div>`;
}

/** The draft with each located change marked where it sits.

    Edits are applied back-to-front so an earlier marker never shifts the
    offsets of a later one — the offsets are the engine's, and rewriting them
    here would be inventing a location. */
function markedDraft(list) {
  const ordered = [...list]
    .map((e, i) => ({ ...e, id: i, span: editSpan(e) }))
    .filter((e) => e.span.start != null)
    .sort((a, b) => b.span.start - a.span.start);

  const pieces = [];
  let cursor = state.draft.length;

  for (const edit of ordered) {
    const start = Math.max(0, Math.min(edit.span.start, state.draft.length));
    const end = Math.max(start, Math.min(edit.span.end == null ? start : edit.span.end, state.draft.length));
    pieces.unshift(escapeHtml(state.draft.slice(end, cursor)));
    pieces.unshift(marker(edit, state.draft.slice(start, end)));
    cursor = start;
  }
  pieces.unshift(escapeHtml(state.draft.slice(0, cursor)));

  return pieces.join('')
    .split(/\n{2,}/)
    .map((para) => `<p>${para.replace(/\n/g, '<br>')}</p>`)
    .join('');
}

function marker(edit, text) {
  const kind = editKind(edit);
  const id = edit.id;
  const open = state.sel === id;
  const ann = open ? annotation(edit, kind) : '';

  if (kind === 'blocked') return blockedBlock(edit) + ann;
  if (kind === 'insert') {
    return `<button class="mk mk-insert" data-act="sel" data-id="${id}" type="button">⌃ Insert here — ${escapeHtml(shortSummary(edit))}</button>${ann}`;
  }
  const cls = kind === 'move' ? 'mk-move' : kind === 'cut' ? 'mk-cut' : 'mk-revise';
  const prefix = kind === 'move' ? '⇅ ' : '';
  return `<button class="mk ${cls}" data-act="sel" data-id="${id}" type="button">${prefix}${escapeHtml(text || shortSummary(edit))}</button>${ann}`;
}

function annotation(edit, kind) {
  const folds = foldsFor(edit.dimension);
  const cls = kind === 'move' ? ' move' : kind === 'cut' ? ' cut' : '';
  return `
  <div class="annotation${cls}">
    <span class="ann-label">${escapeHtml(kind)} · ${escapeHtml(offsetLabel(edit))}</span>
    <div class="ann-body">${escapeHtml(edit.instruction || edit.summary || '')}</div>
    ${folds.map((gap) => `<span class="ann-also">Also covers · ${escapeHtml(humanise(gap))}</span>`).join('')}
  </div>`;
}

function blockedBlock(edit) {
  return `
  <div class="blocked-block">
    <div class="blocked-head">
      <span class="blocked-tag">⊘ Blocked</span>
      <span class="blocked-sub">Collides with content you protected</span>
    </div>
    <p>${escapeHtml(edit.instruction || edit.summary || '')}
    You protected <span class="blocked-span">${escapeHtml((edit.blocked_by || []).join(', '))}</span>,
    and the change cannot be made without touching it. I have not made it and I will not
    choose for you.</p>
    <div class="blocked-actions">
      <button class="btn btn-ghost" data-act="noop" type="button">Release the protection</button>
      <button class="btn btn-ghost" data-act="noop" type="button">Keep it as written</button>
    </div>
  </div>`;
}

function shortSummary(edit) {
  const text = edit.instruction || edit.summary || '';
  const stop = text.indexOf('.');
  return stop > 0 ? text.slice(0, stop) : text;
}

function gutter(list, blocked) {
  const rows = list.map((edit, id) => {
    const folds = foldsFor(edit.dimension).length;
    return `
    <button class="change-row${state.sel === id ? ' on' : ''}" data-act="sel" data-id="${id}" type="button">
      <span class="change-kind">${escapeHtml(editKind(edit))}</span>
      <span class="change-summary">${escapeHtml(shortSummary(edit))}${folds ? ` <span class="change-plus">+${folds}</span>` : ''}</span>
      <span class="change-at">${escapeHtml(offsetLabel(edit))}</span>
    </button>`;
  }).join('');

  const orphans = noEditFor();
  return `
  <div class="gutter">
    <div class="gutter-head">${list.length} change${list.length === 1 ? '' : 's'} · in draft order${blocked ? ` · ${blocked} blocked` : ''}</div>
    ${rows}
    <p class="gutter-note">Nothing has been applied. praxis locates changes; you make them.</p>
    ${orphans.length ? `
      <div class="no-edit">
        <div class="no-edit-label">Reported · no edit</div>
        ${orphans.map((gap) => `
          <p class="no-edit-row"><b>${escapeHtml(humanise(gap))}</b> — reported, and nothing in
          the draft is the place to change. Naming it is the whole of what I can do here.</p>`).join('')}
      </div>` : ''}
  </div>`;
}

/* ── events ─────────────────────────────────────────────────────────── */

app.addEventListener('input', (e) => {
  if (e.target.id === 'draft-input') state.draft = e.target.value;
});

app.addEventListener('click', async (e) => {
  const el = e.target.closest('[data-act]');
  if (!el) return;
  const act = el.dataset.act;

  if (act === 'evaluate' || act === 'example') {
    if (act === 'example') state.draft = EXAMPLE_DRAFT;
    else if (!state.draft.trim()) state.draft = EXAMPLE_DRAFT;
    const result = await evaluate('auto');
    if (result) { state.stage = 'evaluated'; render(); }
    return;
  }
  if (act === 'toggle-why') { state.open.why = !state.open.why; render(); return; }
  if (act === 'toggle-score') { state.open.score = !state.open.score; render(); return; }
  if (act === 'toggle-contract') { state.open.contract = !state.open.contract; render(); return; }
  if (act === 'scroll-transform') {
    document.getElementById('transform')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    return;
  }
  if (act === 'edit-field') {
    state.editing = state.editing === el.dataset.field ? null : el.dataset.field;
    render();
    return;
  }
  if (act === 'set-field' || act === 'answer') {
    state.stated[el.dataset.field] = el.dataset.value;
    state.editing = null;
    state.stopped = false;
    await evaluate('auto');
    if (state.stage === 'transformed') await evaluate('transform');
    return;
  }
  if (act === 'stop') { state.stopped = true; render(); return; }
  if (act === 'resume') { state.stopped = false; render(); return; }
  if (act === 'transform') {
    const result = await evaluate('transform');
    if (result) { state.stage = 'transformed'; state.sel = null; render(); }
    return;
  }
  if (act === 'sel') {
    const id = Number(el.dataset.id);
    state.sel = state.sel === id ? null : id;   // clicking the open one closes it
    render();
    return;
  }
  if (act === 'view-marked') { state.draftView = 'marked'; render(); return; }
  if (act === 'view-original') { state.draftView = 'original'; render(); return; }
  if (act === 'noop') return;
});

themeBtn.addEventListener('click', () => {
  state.theme = state.theme === 'dark' ? 'light' : 'dark';
  applyTheme();
});

resetBtn.addEventListener('click', () => {
  state.stage = 'empty';
  state.draft = '';
  state.stated = {};
  state.result = null;
  state.transform = null;
  state.open = { why: false, score: false, contract: false };
  state.editing = null;
  state.sel = null;
  state.stopped = false;
  state.notice = null;
  render();
});

applyTheme();
render();
startEngine();
onEngineReady(() => render());
