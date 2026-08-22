"""Where things are in the draft.

Evaluation can say a message has no deadline. Transforming it needs to
say *where the deadline goes*, and which characters must not be touched
on the way. That is the whole difference between a critique and a
surgical change, and it is entirely a question of offsets.

Everything here is positional and deterministic: a span is a half-open
character range into the draft, and every span carries the text it
covers so a caller can show the writer what it means without re-slicing.
"""

from dataclasses import dataclass, asdict
import re

from . import signals
from .rules import split_sentences


@dataclass(frozen=True)
class Span:
    """A half-open character range `[start, end)` and the text in it."""
    start: int
    end: int
    text: str

    def overlaps(self, other: "Span") -> bool:
        return self.start < other.end and other.start < self.end

    def to_dict(self) -> dict:
        return asdict(self)


def locate(name: str, text: str) -> list[Span]:
    """Every span `name` matches, with its position.

    `signals.find` returns the matched strings; this returns where they
    were. The two must agree, so both go through the same compiled
    pattern rather than one re-deriving the other.
    """
    if name not in signals.DETECTORS:
        raise KeyError(f"Unknown detector '{name}'. "
                       f"Available: {', '.join(sorted(signals.DETECTORS))}")
    return [Span(m.start(), m.end(), m.group(0))
            for m in signals.DETECTORS[name].finditer(text)]


def phrase_pattern(phrase: str) -> re.Pattern:
    """Match `phrase` across whatever whitespace the draft happens to use.

    A writer types "perhaps we could discuss"; a hard-wrapped draft
    contains "perhaps we could\ndiscuss". Exact matching misses it and —
    worse — misses it *silently*, reporting the phrase as absent while
    the writer believes they have protected it. Every run of whitespace
    in the phrase matches any run of whitespace in the text.
    """
    words = phrase.split()
    if not words:
        return re.compile(r"(?!)")          # matches nothing
    return re.compile(r"\s+".join(re.escape(w) for w in words))


def contains_phrase(text: str, phrase: str) -> bool:
    """Is `phrase` present, allowing for different line wrapping?"""
    return bool(phrase.split()) and phrase_pattern(phrase).search(text) is not None


def protected_spans(text: str, phrases: list[str]) -> list[Span]:
    """Every occurrence of every declared phrase, in document order.

    A phrase the writer declared protected but that does not appear is
    not represented here — it cannot be a region of a document it is not
    in. `unlocatable` reports those separately rather than silently
    dropping them.
    """
    found: list[Span] = []
    for phrase in phrases:
        if not phrase:
            continue
        for match in phrase_pattern(phrase).finditer(text):
            found.append(Span(match.start(), match.end(), match.group(0)))
    return sorted(found, key=lambda s: (s.start, s.end))


def unlocatable(text: str, phrases: list[str]) -> list[str]:
    """Declared protected phrases that are not in the draft at all."""
    return [p for p in phrases if p and not contains_phrase(text, p)]


def sentences(text: str) -> list[Span]:
    """Sentence spans whose offsets match the text they carry.

    `rules.split_sentences` strips the body but not the offsets, so every
    sentence after the first claimed a range one character wider than its
    text — a revise or move edit built from one pointed at the wrong
    characters. The offsets are trimmed to match.
    """
    out: list[Span] = []
    for start, end, body in split_sentences(text):
        raw = text[start:end]
        lead = len(raw) - len(raw.lstrip())
        trail = len(raw) - len(raw.rstrip())
        out.append(Span(start + lead, end - trail, body))
    return out


def paragraphs(text: str) -> list[Span]:
    """Blocks separated by a blank line. Falls back to the whole text."""
    found = [Span(m.start(), m.end(), m.group(0))
             for m in re.finditer(r"[^\n]+(?:\n(?!\s*\n)[^\n]+)*", text)]
    return found or ([Span(0, len(text), text)] if text else [])


def opening(text: str) -> Span:
    """The span a reader's first glance covers.

    The first paragraph, not the first sentence: structures that lead
    with the conclusion mean the opening *block*, and a one-sentence
    insertion point would put a deadline in the middle of a thought.
    """
    blocks = paragraphs(text)
    return blocks[0] if blocks else Span(0, 0, "")


#: A greeting line, which is a line but not the start of the message.
#:
#: Neither alternative may contain terminal punctuation. Without that,
#: "Hello there body." read as a second greeting and the whole message
#: was skipped past.
SALUTATION = re.compile(
    r"^\s*(?:hi|hello|hey|dear|good (?:morning|afternoon|evening))\b[^.!?\n]{0,40}$"
    r"|^[^.!?\n]{0,30},\s*$", re.IGNORECASE)


def body_start(text: str) -> int:
    """Where the message actually begins.

    An insertion point for a bottom line has to clear the greeting.
    Putting the decision above "Hi Priya," is not leading with the
    conclusion, it is writing an envelope.

    Matched line by line rather than paragraph by paragraph: a greeting
    followed by a single newline is part of the same *paragraph* as the
    body, so a paragraph-level test saw "Hi Priya,\nPlease approve…",
    failed to recognise it, and put the insertion above the greeting.
    """
    offset = 0
    first_body = None
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped:
            if first_body is None:
                first_body = offset + (len(line) - len(line.lstrip()))
                if SALUTATION.match(stripped):
                    first_body = None          # keep looking, past the greeting
                else:
                    return first_body
        offset += len(line) + 1
    return 0


def carrying(text: str, name: str) -> list[Span]:
    """Sentences containing at least one `name` span.

    The unit a writer moves is a sentence, not a regex match — "move the
    risk to the front" means the sentence stating it, not the word
    "risk".
    """
    hits = locate(name, text)
    return [s for s in sentences(text) if any(s.overlaps(h) for h in hits)]


def longest_sentences(text: str, count: int = 3) -> list[Span]:
    """The sentences to look at first when a draft has to lose words."""
    return sorted(sentences(text), key=lambda s: -len(s.text))[:count]


def clear_of(span: Span, protected: list[Span]) -> bool:
    """Can this region be edited without disturbing protected content?"""
    return not any(span.overlaps(p) for p in protected)


def to_dicts(spans: list[Span]) -> list[dict]:
    return [s.to_dict() for s in spans]
