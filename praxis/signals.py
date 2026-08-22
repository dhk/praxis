"""Deterministic text detectors shared by evaluation and shading.

Every detector answers one question about a draft with evidence: not "is
this warm" but "does a span acknowledging the reader appear, and where".
Nothing here judges quality. A detector returns the matched spans so a
caller can show the reader what it saw, which is the difference between
an inspectable finding and an opaque score.

These are recall-oriented and deliberately conservative: a miss reads as
"unknown", never as "absent". Callers must not treat an empty result as
proof that a property is missing from prose a regex simply cannot see.
"""

import re

FLAGS = re.IGNORECASE | re.MULTILINE

#: A direct request for the reader to do something.
ASK = re.compile(
    r"\b(?:please\s+\w+|can you\b|could you\b|would you\b|approve\b|approves?\b"
    r"|sign off\b|confirm\b|reply\b|respond\b|let me (?:know|have)\b"
    r"|need (?:your|a decision)\b|requesting\b|action required\b"
    r"|decision needed\b|asking (?:you|for)\b)", FLAGS)

#: A time by which something must happen.
DEADLINE = re.compile(
    r"\b(?:by|before|no later than|due|deadline)\s+"
    r"(?:\d{1,2}(?::\d{2})?\s*(?:a\.?m\.?|p\.?m\.?)|\d{4}-\d{2}-\d{2}"
    r"|today|tomorrow|tonight|EOD|COB|end of (?:day|week)|next week"
    r"|mon|tue|wed|thu|fri|sat|sun)\w*"
    r"|\b(?:today|EOD|COB|immediately|right away)\b", FLAGS)

#: Language that keeps a claim honest about what is not yet known.
#:
#: The modals carry a negative lookahead because "could you approve" and
#: "may I suggest" are polite requests, not hedges. Counting them inflated
#: the uncertainty score of every courteous draft and, worse, masked real
#: losses: a variant that deleted every genuine caveat still scored one
#: marker for saying "could you". Bare `if` is likewise absent — it marks
#: a conditional claim rather than the writer's confidence in it, and it
#: is common enough that including it swamped the signal.
UNCERTAINTY = re.compile(
    r"\b(?:preliminary|estimated?|estimates?|approximately|roughly|about\s+\d"
    r"|(?:may|might|could)\b(?!\s+(?:you|I)\b)|likely|unlikely|unconfirmed|unclear"
    r"|pending|subject to change|still (?:investigating|unknown)"
    r"|not yet (?:known|confirmed)|we (?:do not|don't) yet know|TBD|to be confirmed"
    r"|assum\w+)", FLAGS)

#: Language that weakens a request without adding truth. Distinct from
#: UNCERTAINTY: removing a hedge costs nothing, removing an uncertainty
#: marker changes what the message claims.
HEDGE = re.compile(
    r"\b(?:just\s+wanted|just\s+checking|if\s+possible|when you get a chance"
    r"|at your convenience|no rush|sort of|kind of|a bit\b|maybe\b|perhaps\b"
    r"|I (?:think|feel|guess) (?:maybe|perhaps)?|somewhat|fairly\b|quite\b"
    r"|I was wondering|I'd like to discuss|wanted to (?:reach out|flag))", FLAGS)

#: Recognition of the reader's effort, workload, or situation.
ACKNOWLEDGEMENT = re.compile(
    r"\b(?:thank(?:s| you)|appreciate|I (?:know|realise|realize|understand|recognise|recognize)\b"
    r"|I'm sorry|I am sorry|apolog\w+|aware that you|given (?:your|how)"
    r"|know (?:this|how much|you)\b)", FLAGS)

#: Visible support for a claim: measurement, source, or reference.
EVIDENCE = re.compile(
    r"https?://\S+|\b\d+(?:\.\d+)?%|\b\$\d[\d,.]*|\b\d{4}-\d{2}-\d{2}\b"
    r"|\b(?:according to|per the|based on|logs? show|data shows?|measured"
    r"|we (?:tested|measured|observed)|source:|see\s+\[)", FLAGS)

#: A named party who will carry an action.
OWNER = re.compile(
    r"\b(?:I will|I'll|we will|we'll|I am|I'm going to|owner:|assigned to"
    r"|[A-Z][a-z]+ will\b)|@[A-Za-z][\w.-]*", re.MULTILINE)

#: A mechanism that confirms the message was received and acted on.
#:
#: Deliberately not "approve by": that is an ask plus a deadline, both of
#: which have their own detectors. Counting it here meant rewording
#: "Approve by 3 p.m." to "approve before 3 p.m." registered as losing a
#: confirmation the message never had.
VERIFICATION = re.compile(
    r"\b(?:reply (?:\"?approved\"?|to (?:this|confirm))|confirm receipt|acknowledge"
    r"|sign off|read ?back|let me know (?:if|once|when|by)"
    r"|please confirm|respond by)", FLAGS)

#: A claim whose consequences make it worth supporting.
CONSEQUENTIAL = re.compile(
    r"\b(?:will (?:cause|delay|break|miss|cost|result)|results? in|leads? to"
    r"|risks?\b|impacts?\b|delays?\b|costs?\b|outage|breach|failure|blocked"
    r"|missed?\s+(?:commitment|deadline|target)|revenue|churn|liabilit\w+)", FLAGS)

#: A route for the reader when the normal path fails.
#:
#: `if this is not …` was once an alternative on its own, which matched
#: "Let me know if this is not clear." — so a courtesy sentence satisfied
#: the escalation requirement of a safety-critical message. The
#: conditional forms now have to name the failure they are a route out of.
ESCALATION = re.compile(
    r"\b(?:escalat\w+|on[- ]?call|page (?:me|the|us)\b|otherwise contact"
    r"|fall ?back to|failing that|in the meantime,? contact"
    r"|if (?:it|this|that) (?:is )?(?:still )?(?:un|not )?resolved"
    r"|if (?:you|we) (?:cannot|can't|are unable to) reach)\b", FLAGS)

#: A commitment to say more, *and when*.
#:
#: The time is the requirement — `strategy.REQUIREMENTS` asks a crisis
#: message for "a named next update time", and an earlier version matched
#: "I will update the runbook.", which names neither an update to the
#: reader nor a time. Every alternative here carries a temporal anchor.
_WHEN = (r"(?:by|at|before|within|every|each)\b|tomorrow|today|tonight|hourly|daily"
         r"|EOD\b|COB\b|end of (?:day|week)|\d{1,2}(?::\d{2})?\s*(?:a\.?m\.?|p\.?m\.?)"
         r"|mon|tue|wed|thu|fri|sat|sun")
UPDATE_CADENCE = re.compile(
    r"\b(?:next update\b[^.\n]{0,40}?(?:" + _WHEN + r")"
    r"|(?:I|we)(?:'ll| will) (?:update|report back|follow up|write again)\b"
    r"[^.\n]{0,60}?(?:" + _WHEN + r")"
    r"|(?:another|further) update\b[^.\n]{0,40}?(?:" + _WHEN + r")"
    r"|updates? (?:every|hourly|daily)\b)", FLAGS)

#: Structural affordances that let a reader scan instead of read.
SCAN = re.compile(r"^\s{0,3}(?:[-*+]\s|\d+[.)]\s|#{1,6}\s)|\*\*[^*]+\*\*", re.MULTILINE)

DETECTORS = {
    "ask": ASK, "deadline": DEADLINE, "uncertainty": UNCERTAINTY, "hedge": HEDGE,
    "acknowledgement": ACKNOWLEDGEMENT, "evidence": EVIDENCE, "owner": OWNER,
    "verification": VERIFICATION, "consequential": CONSEQUENTIAL, "scan": SCAN,
    "escalation": ESCALATION, "update_cadence": UPDATE_CADENCE,
}


def find(name: str, text: str) -> list[str]:
    """Return every span `name` matches in `text`, in document order."""
    if name not in DETECTORS:
        raise KeyError(f"Unknown detector '{name}'. Available: {', '.join(sorted(DETECTORS))}")
    return [m.group(0).strip() for m in DETECTORS[name].finditer(text)]


def signal_counts(text: str) -> dict[str, int]:
    """How many spans each detector finds. The shape difference maps diff."""
    return {name: len(find(name, text)) for name in DETECTORS}


def first_words(text: str, count: int = 40) -> str:
    """The opening of a document, as the reader's first glance sees it."""
    words = text.split()
    return " ".join(words[:count])
