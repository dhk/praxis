/* Pipeline worker: loads Pyodide, installs the praxis package source unchanged,
   and exposes run / zip operations. Runs off the main thread so a large
   document never freezes the UI. */

importScripts('../vendor/pyodide/pyodide.js');

const PY_SETUP = `
import io
import json
import re
import zipfile
import difflib

from praxis.pipeline import run_pipeline
from praxis.packs import list_packs
from praxis.validation import protected_tokens
from praxis.handoff import render_prompt

# The design layer. praxis/*.py is copied into the bundle whole, so these
# modules have always shipped to the browser — they were simply never
# imported. Nothing here reaches a model or the network: design() is the
# same pure function the CLI and the MCP server call, so a writer with no
# model at all still gets every decision praxis can make.
from praxis import brief
from praxis.design import design as run_design
from praxis.contract import build as build_contract, SELECTORS, FIELDS
from praxis.render import document

def _word_diff(a, b):
    """Word-level opcodes between two documents, whitespace preserved."""
    ta = re.findall(r"\\S+|\\s+", a)
    tb = re.findall(r"\\S+|\\s+", b)
    sm = difflib.SequenceMatcher(a=ta, b=tb, autojunk=False)
    return [
        {"op": tag, "a": "".join(ta[i1:i2]), "b": "".join(tb[j1:j2])}
        for tag, i1, i2, j1, j2 in sm.get_opcodes()
    ]

def run_json(source, pack_id):
    result = run_pipeline(source, pack_id)
    result["ui"] = {
        "protected_tokens": sorted(protected_tokens(source)),
        "diff": _word_diff(source, result["final"]),
        "prompt": render_prompt(result),
    }
    return json.dumps(result)

def field_catalogue():
    """The closed domains, so the UI can offer choices rather than a text box."""
    return [
        {"name": f.name, "section": f.section, "question": f.question,
         "options": list(f.domain) if f.domain else [],
         "note": f.note, "kind": f.kind}
        for f in FIELDS
    ]

def design_json(draft, stated_json, mode, voice_reference, variants_json):
    """One design() call, plus the renderings a UI needs, as JSON.

    Answer-first is the contract of every praxis surface, so the browser
    gets the same tiers the CLI prints and the MCP server returns — the
    answer alone by default, the reasoning only when asked for.
    """
    stated = json.loads(stated_json) if stated_json else {}
    variants = json.loads(variants_json) if variants_json else None
    try:
        contract = build_contract(stated)
        result = run_design(draft, contract, variants=variants, mode=mode,
                            voice_reference=voice_reference)
    except ValueError as exc:
        # ContractError subclasses ValueError, as does design()'s own mode
        # and empty-draft guard. A writer sees the sentence, not a traceback.
        return json.dumps({"error": str(exc)})
    result["ui"] = {
        "answer": brief.answer(result),
        "progress": brief.progress(result),
        "question": brief.next_question(result),
        "why": brief.why(result),
        "findings": brief.findings(result),
        "contract": brief.contract(result),
        "edits": brief.edits(result) if result["mode"] == "transform" else "",
        "unresolved": brief.unresolved_count(result),
        "settled": brief.settled_count(result),
        # The artifact page, so a browser-only writer can keep the record
        # of the decision and not just read it once.
        "html": document(result),
    }
    return json.dumps(result)

def make_zip(source, pack_id):
    """Zip of the six artifact files, byte-identical to a CLI run's output."""
    r = run_pipeline(source, pack_id)
    artifacts = [
        ("observations.json", json.dumps(r["observations"], indent=2)),
        ("recommendations.json", json.dumps(r["recommendations"], indent=2)),
        ("transformations.json", json.dumps(r["transformations"], indent=2)),
        ("validation.json", json.dumps(r["validation"], indent=2)),
        ("final.md", r["final"]),
        ("report.md", r["report"]),
    ]
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in artifacts:
            z.writestr(zipfile.ZipInfo(name, (2020, 1, 1, 0, 0, 0)), data)
    return buf.getvalue()
`;

const ready = (async () => {
  const base = new URL('..', self.location).href;
  const pyodide = await loadPyodide({ indexURL: base + 'vendor/pyodide/' });

  const manifest = await (await fetch(base + 'py/manifest.json')).json();
  pyodide.FS.mkdir('/app');
  pyodide.FS.mkdir('/app/praxis');
  for (const name of manifest.files) {
    const text = await (await fetch(`${base}py/praxis/${name}`)).text();
    pyodide.FS.writeFile(`/app/praxis/${name}`, text);
  }

  pyodide.runPython("import sys; sys.path.insert(0, '/app')");
  pyodide.runPython(PY_SETUP);
  return pyodide;
})();

ready.then(
  (pyodide) => self.postMessage({
    type: 'ready',
    packs: JSON.parse(pyodide.runPython('json.dumps(list_packs())')),
    // The contract's closed domains, so the design UI can offer the
    // options rather than ask a writer to guess the vocabulary.
    fields: JSON.parse(pyodide.runPython('json.dumps(field_catalogue())')),
    selectors: JSON.parse(pyodide.runPython('json.dumps(list(SELECTORS))')),
  }),
  (err) => self.postMessage({ type: 'init-error', message: String(err) }),
);

self.onmessage = async (event) => {
  const { id, op, source, pack, draft, stated, mode, voice, variants } = event.data;
  try {
    const pyodide = await ready;
    if (op === 'run' || op === 'zip') {
      pyodide.globals.set('_SOURCE', source);
      pyodide.globals.set('_PACK', pack);
    }
    if (op === 'run') {
      const json = pyodide.runPython('run_json(_SOURCE, _PACK)');
      self.postMessage({ type: 'result', id, result: JSON.parse(json) });
    } else if (op === 'zip') {
      const bytes = pyodide.runPython('make_zip(_SOURCE, _PACK)').toJs();
      self.postMessage({ type: 'zip', id, bytes }, [bytes.buffer]);
    } else if (op === 'design') {
      pyodide.globals.set('_DRAFT', draft ?? '');
      pyodide.globals.set('_STATED', JSON.stringify(stated ?? {}));
      pyodide.globals.set('_MODE', mode ?? 'auto');
      pyodide.globals.set('_VOICE', voice ?? '');
      pyodide.globals.set('_VARIANTS', variants ? JSON.stringify(variants) : '');
      const json = pyodide.runPython(
        'design_json(_DRAFT, _STATED, _MODE, _VOICE, _VARIANTS)',
      );
      const result = JSON.parse(json);
      // design() rejects an unknown mode and a transform with no draft.
      // Those are the writer's mistakes, not failures — they come back as
      // a sentence to show, not an exception to swallow.
      if (result.error) {
        self.postMessage({ type: 'design-rejected', id, message: result.error });
      } else {
        self.postMessage({ type: 'design', id, result });
      }
    } else {
      self.postMessage({ type: 'error', id, message: `Unknown operation ${op}` });
    }
  } catch (err) {
    self.postMessage({ type: 'error', id, message: String(err) });
  }
};
