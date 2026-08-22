"""Measuring whether a detector agrees with what praxis claims it means.

Every finding praxis reports rests on `signals.py`, and until now nothing
checked those patterns beyond the handful of strings whoever last edited
them happened to think of. Seven separate corrections this session came
from a reviewer noticing a detector firing on something it should not.

This scores the detectors against `corpus/detectors.jsonl` — examples
with known answers — and reports precision and recall per detector.

Two design choices carry most of the honesty:

* **Only labelled detectors are scored.** An example says which signals
  it is about; the rest are unlabelled and contribute nothing. Guessing a
  label to fill a matrix would manufacture agreement.
* **Results are split by where the example came from.** An example a
  reviewer found praxis failing on is evidence. One a language model
  wrote to order is a weaker thing, because the model that wrote the
  detectors and the model writing the examples share their blind spots.
  The headline figure counts human and review-sourced examples only.
"""

from __future__ import annotations

import json
from pathlib import Path

from . import signals

CORPUS = Path(__file__).resolve().parent.parent / "corpus" / "detectors.jsonl"

#: Sources whose labels are ground truth rather than another model's
#: opinion. See `corpus/README.md`.
TRUSTED = ("hand", "review")


def load(path: Path | None = None) -> list[dict]:
    """Read the corpus, rejecting labels that name no real detector."""
    lines = (path or CORPUS).read_text(encoding="utf-8").splitlines()
    examples = []
    for number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        record = json.loads(line)
        for name in list(record.get("present", [])) + list(record.get("absent", [])):
            if name not in signals.DETECTORS:
                raise ValueError(f"{path or CORPUS}:{number} labels unknown detector {name!r}")
        overlap = set(record.get("present", [])) & set(record.get("absent", []))
        if overlap:
            raise ValueError(f"{path or CORPUS}:{number} labels {overlap} both present and absent")
        examples.append(record)
    return examples


def score(examples: list[dict] | None = None, sources: tuple[str, ...] = TRUSTED) -> dict:
    """Precision, recall, and the examples each detector gets wrong.

    Counted per (example, detector) pair, only where the example carries a
    label for that detector.
    """
    chosen = [e for e in (examples if examples is not None else load())
              if e.get("source", "hand") in sources]
    tallies: dict[str, dict] = {}

    for example in chosen:
        found = {name for name in signals.DETECTORS if signals.find(name, example["text"])}
        for name in example.get("present", []):
            bucket = tallies.setdefault(name, _blank())
            if name in found:
                bucket["true_positive"] += 1
            else:
                bucket["false_negative"] += 1
                bucket["missed"].append(example["text"])
        for name in example.get("absent", []):
            bucket = tallies.setdefault(name, _blank())
            if name in found:
                bucket["false_positive"] += 1
                bucket["fired_wrongly"].append(example["text"])
            else:
                bucket["true_negative"] += 1

    for name, bucket in tallies.items():
        bucket["precision"] = _ratio(bucket["true_positive"],
                                     bucket["true_positive"] + bucket["false_positive"])
        bucket["recall"] = _ratio(bucket["true_positive"],
                                  bucket["true_positive"] + bucket["false_negative"])
        bucket["labelled"] = sum(bucket[k] for k in
                                 ("true_positive", "false_positive",
                                  "true_negative", "false_negative"))
    return {
        "detectors": dict(sorted(tallies.items())),
        "examples": len(chosen),
        "sources": list(sources),
        "unmeasured": sorted(set(signals.DETECTORS) - set(tallies)),
    }


def _blank() -> dict:
    return {"true_positive": 0, "false_positive": 0, "true_negative": 0,
            "false_negative": 0, "missed": [], "fired_wrongly": []}


def _ratio(numerator: int, denominator: int) -> float | None:
    """`None`, not zero, when nothing was measured.

    A detector with no labelled positives has not scored 0% precision; it
    has not been measured, and the two must not print the same.
    """
    return round(numerator / denominator, 3) if denominator else None


def report(result: dict | None = None) -> str:
    """The scores as a table, with what each detector still gets wrong."""
    result = result or score()
    lines = [f"{result['examples']} examples, sources: {', '.join(result['sources'])}",
             "",
             f"{'detector':18} {'precision':>10} {'recall':>8} {'labelled':>9}",
             "-" * 48]
    for name, bucket in result["detectors"].items():
        lines.append("{:18} {:>10} {:>8} {:>9}".format(
            name, _show(bucket["precision"]), _show(bucket["recall"]), bucket["labelled"]))
    for name, bucket in result["detectors"].items():
        for text in bucket["fired_wrongly"]:
            lines.append(f"  {name}: fired on {text!r}")
        for text in bucket["missed"]:
            lines.append(f"  {name}: missed {text!r}")
    if result["unmeasured"]:
        lines += ["", "no labelled example yet: " + ", ".join(result["unmeasured"])]
    return "\n".join(lines)


def _show(value: float | None) -> str:
    return "unmeasured" if value is None else f"{value:.3f}"
