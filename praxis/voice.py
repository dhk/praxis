"""Which of the writer's habits a rewrite kept, and which it dropped.

Deliberately *not* an authorship measure, and the difference matters.

The obvious design is stylometric: compare function-word frequencies
between the draft and the rewrite and report a similarity. That was
built, and then tested the only way worth testing it — against pairs of
texts whose answer is already known. Two halves of one document are the
same writer; two different documents are not. On the kind of text praxis
handles, a few hundred words, the two groups do not separate:

    same writer, cosine       0.712 … 0.977
    different writers, cosine 0.609 … 0.883

Same-author pairs scored *below* different-author pairs, so any threshold
drawn through that range decides authorship by coin flip. Stylometry
needs thousands of words per sample; an email is not that. The similarity
number was therefore removed rather than shipped behind a caveat, because
a number in a report gets read as a finding no matter what the caveat
says. The measurement is recorded in RFC-0004 so nobody re-adds it.

What survives is what was never inferential: **counts**. Whether a
rewrite kept the writer's semicolons, their sentence rhythm, their
contractions, their first-person voice. Those are directly observable,
checkable by the writer against the same text, and they are what people
actually mean when they say a rewrite stopped sounding like them.

So this module reports habits and never renders a verdict on identity.
"""

import re
from math import sqrt

#: Below this, a per-thousand rate is arithmetic on too little text: one
#: comma in an eighty-word note is 12.5 per thousand.
MINIMUM_WORDS = 80

WORD = re.compile(r"\b[\w']+\b")

#: Each habit: how to count it, and how far it may drift before it is
#: worth reporting. Rate tolerance is per thousand words; a habit must
#: also move by `least` occurrences, so a single token never trips it.
HABITS = {
    "sentence length": {"rate": 6.0, "least": 0, "unit": "words"},
    "sentence variation": {"rate": 6.0, "least": 0, "unit": "words"},
    "comma": {"rate": 12.0, "least": 2, "unit": "per 1000 words"},
    "semicolon": {"rate": 3.0, "least": 2, "unit": "per 1000 words"},
    "dash": {"rate": 5.0, "least": 2, "unit": "per 1000 words"},
    "colon": {"rate": 6.0, "least": 2, "unit": "per 1000 words"},
    "contraction": {"rate": 5.0, "least": 2, "unit": "per 1000 words"},
    "first person": {"rate": 10.0, "least": 2, "unit": "per 1000 words"},
    "paragraph length": {"rate": 25.0, "least": 0, "unit": "words"},
}


def fingerprint(text: str) -> dict:
    """The countable habits, as both raw counts and per-thousand rates."""
    words = WORD.findall(text)
    total = len(words)
    sentence_lengths = [len(WORD.findall(s))
                        for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    block_lengths = [len(WORD.findall(b))
                     for b in re.split(r"\n\s*\n", text) if b.strip()]

    counts = {
        "comma": text.count(","),
        "semicolon": text.count(";"),
        "dash": len(re.findall(r"—|--| - ", text)),
        "colon": text.count(":"),
        "contraction": len(re.findall(r"\b\w+'\w+", text)),
        "first person": len(re.findall(r"\b(?:I|we|my|our|me|us)\b", text, re.IGNORECASE)),
    }
    habits = {name: round(1000 * n / (total or 1), 2) for name, n in counts.items()}
    habits["sentence length"] = round(_mean(sentence_lengths), 2)
    habits["sentence variation"] = round(_spread(sentence_lengths), 2)
    habits["paragraph length"] = round(_mean(block_lengths), 2)
    return {"words": total, "habits": habits, "counts": counts}


def _mean(values: list[int]) -> float:
    return sum(values) / len(values) if values else 0.0


def _spread(values: list[int]) -> float:
    if len(values) < 2:
        return 0.0
    mean = _mean(values)
    return sqrt(sum((v - mean) ** 2 for v in values) / len(values))


def compare(reference: str, variant: str) -> dict:
    """Which of `reference`'s habits `variant` kept.

    The reference is normally the writer's own draft: in a transform, the
    voice being preserved is the voice of the text being transformed, so
    no external corpus is needed.

    Never returns a `gap`. A dropped habit is a fact about the rewrite,
    not a fault in it — a writer who asked for a scannable version *wants*
    shorter sentences, and reporting that as a failure would be praxis
    disagreeing with an instruction it was given.
    """
    ref, var = fingerprint(reference), fingerprint(variant)
    if ref["words"] < MINIMUM_WORDS or var["words"] < MINIMUM_WORDS:
        return {
            "status": "unknown",
            "finding": f"Habit rates need about {MINIMUM_WORDS} words to mean anything; "
                       f"these are {ref['words']} and {var['words']}.",
            "moved": [], "held": [],
        }

    moved, held = [], []
    for habit, rule in HABITS.items():
        before, after = ref["habits"][habit], var["habits"][habit]
        count_move = abs(var["counts"].get(habit, 0) - ref["counts"].get(habit, 0))
        if abs(after - before) > rule["rate"] and count_move >= rule["least"]:
            moved.append({"habit": habit, "before": before, "after": after,
                          "unit": rule["unit"]})
        else:
            held.append(habit)

    return {
        "status": "pass" if not moved else "review",
        "finding": _describe(moved, held),
        "moved": moved,
        "held": held,
        "note": "Habits, not authorship. A dropped habit may be exactly what the "
                "rewrite was asked to do; this says what changed, not whether it "
                "was right.",
    }


def _describe(moved: list[dict], held: list[str]) -> str:
    if not moved:
        return f"All {len(held)} measured habits stayed within their usual range."
    named = "; ".join(f"{m['habit']} {m['before']}→{m['after']} {m['unit']}"
                      for m in moved[:3])
    more = f", and {len(moved) - 3} more" if len(moved) > 3 else ""
    return f"{len(moved)} habit(s) moved: {named}{more}."
