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
  }),
  (err) => self.postMessage({ type: 'init-error', message: String(err) }),
);

self.onmessage = async (event) => {
  const { id, op, source, pack } = event.data;
  try {
    const pyodide = await ready;
    pyodide.globals.set('_SOURCE', source);
    pyodide.globals.set('_PACK', pack);
    if (op === 'run') {
      const json = pyodide.runPython('run_json(_SOURCE, _PACK)');
      self.postMessage({ type: 'result', id, result: JSON.parse(json) });
    } else if (op === 'zip') {
      const bytes = pyodide.runPython('make_zip(_SOURCE, _PACK)').toJs();
      self.postMessage({ type: 'zip', id, bytes }, [bytes.buffer]);
    }
  } catch (err) {
    self.postMessage({ type: 'error', id, message: String(err) });
  }
};
