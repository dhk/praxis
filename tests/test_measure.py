"""The corpus, and the scoring that makes it mean something.

Wave 4's premise: every finding praxis reports rests on `signals.py`, and
until now nothing checked those patterns beyond the strings whoever last
edited them happened to think of. Seven corrections this session came
from a reviewer noticing a detector firing on something it should not.

The corpus caught a different class of failure on its first run — three
detectors that *missed* things, including `consequential` at zero recall,
which is what decides whether a high-stakes claim needs evidence. Review
found false positives; the corpus found false negatives. They are
complementary, which is the argument for having both.
"""

import json

import pytest

from praxis import signals
from praxis.measure import CORPUS, load, report, score


def test_the_corpus_parses_and_labels_only_real_detectors():
    examples = load()
    assert len(examples) >= 30
    for example in examples:
        assert example["text"].strip()
        for name in example.get("present", []) + example.get("absent", []):
            assert name in signals.DETECTORS


def test_a_label_cannot_contradict_itself():
    for example in load():
        assert not set(example.get("present", [])) & set(example.get("absent", []))


def test_no_example_is_unlabelled():
    """An example that asserts nothing costs review attention and buys
    no evidence."""
    for example in load():
        assert example.get("present") or example.get("absent"), example["text"]


def test_every_example_declares_where_it_came_from():
    """A generated example is weaker evidence than one a reviewer found
    praxis failing on, and the scores have to be able to say so."""
    for example in load():
        assert example.get("source") in ("hand", "review", "corpus", "generated")


def test_no_duplicate_examples():
    texts = [e["text"] for e in load()]
    assert len(texts) == len(set(texts))


ALL_SOURCES = ("hand", "review", "corpus", "generated")


def test_every_labelled_detector_is_perfect_on_the_corpus():
    """The bar is 1.0 both ways, because the corpus is small enough that
    anything less is a known bug nobody wrote down. It rises by adding
    examples, never by lowering this."""
    result = score(sources=ALL_SOURCES)
    for name, bucket in result["detectors"].items():
        assert bucket["precision"] in (None, 1.0), (name, bucket["fired_wrongly"])
        assert bucket["recall"] in (None, 1.0), (name, bucket["missed"])


def test_the_recall_failures_the_corpus_found_stay_fixed():
    """`consequential` scored zero recall: "the migration will fail" was
    not a consequence, so a high-stakes draft asserting it needed no
    evidence."""
    assert signals.find("consequential", "The migration will fail.")
    assert signals.find("consequential", "The release will slip.")
    assert signals.find("ask", "May I suggest Thursday?")
    assert signals.find("deadline", "Please respond by 9.")


@pytest.mark.parametrize("text,detector", [
    ("The release slipped by 5 days.", "deadline"),
    ("Costs rose by 12 percent.", "deadline"),
    ("The queue grew by 3 items.", "deadline"),
    ("The plan will work.", "consequential"),
    ("I may look at it later.", "ask"),
])
def test_the_recall_fix_did_not_buy_precision(text, detector):
    """A duration is not a deadline and not every "will" is a consequence.
    These negatives were added to the corpus *before* the patterns were
    touched, so the fix could not quietly trade one error for the other."""
    assert signals.find(detector, text) == []


def test_an_unmeasured_detector_is_not_reported_as_zero():
    """A detector with no labelled example has not scored 0%; it has not
    been measured, and printing them the same would be a lie about
    coverage."""
    result = score(sources=ALL_SOURCES)
    assert set(result["unmeasured"]) == {"evidence", "scan"}
    text = report(result)
    assert "no labelled example yet: evidence, scan" in text
    # and a detector that *is* unmeasured prints as such rather than 0.000
    from praxis.measure import _show
    assert _show(None) == "unmeasured"
    assert _show(0.0) == "0.000"


def test_generated_examples_are_excluded_from_the_headline():
    """The detectors were written by a language model. A corpus written by
    one shares its blind spots, so those examples are scored separately."""
    from praxis.measure import TRUSTED
    assert "generated" not in TRUSTED


def test_the_corpus_file_is_one_json_object_per_line():
    for line in CORPUS.read_text(encoding="utf-8").splitlines():
        if line.strip():
            assert isinstance(json.loads(line), dict)
