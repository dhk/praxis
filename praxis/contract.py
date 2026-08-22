"""The communication contract: a compact, editable model of the situation.

The contract is the durable artifact of this layer. Prose is disposable —
regenerate it whenever. The contract is what the writer actually owns:
who reads this, what they must be able to do afterwards, what is at risk,
what may not change. It is small enough to read in one screen and
explicit enough to argue with.

Two properties matter more than the field list:

* **Every value carries provenance.** `stated` came from the writer.
  `inferred` is the assistant's guess, and an inference is never allowed
  to masquerade as a fact — the brief's rule that reader beliefs,
  authority, and trust must not be silently assumed is enforced here as
  data, not as a habit.
* **The domains are closed.** Strategy selection is a lookup over these
  values (see `strategy.py`), and `strategy.material_questions` decides
  what to ask by perturbing a field across its domain and watching
  whether the recommendation moves. A field with an open domain cannot
  be reasoned about that way, so free-text fields are explicitly the
  ones that describe the situation rather than select the strategy.
"""

from dataclasses import dataclass, field, replace
from typing import Any

STATED, INFERRED, UNSET = "stated", "inferred", "unset"


@dataclass(frozen=True)
class Field:
    """One contract field: where it lives, what it may hold, what it asks.

    `domain` is a tuple of permitted values, or None for free text.
    `question` is what the assistant asks a human when the answer would
    change the strategy — phrased for a person, not for a form.
    """
    name: str
    section: str
    question: str
    domain: tuple[str, ...] | None = None
    note: str = ""
    kind: str = "text"
    """`text`, `number`, or `list`.

    The CLI passes every `--set` value as a string, so without this a
    numeric field arrived as `"250"`, failed the `isinstance(int)` check
    in the evaluator, and was silently ignored — accepted at one
    interface and enforced at another."""


FIELDS: tuple[Field, ...] = (
    # --- artifact ------------------------------------------------------
    Field("genre", "artifact", "What kind of thing is this?", None,
          "Cover letter, decision memo, incident update, postmortem, handoff."),
    Field("medium", "artifact", "How will they read it?",
          ("slack", "email", "memo", "report", "proposal", "handoff", "doc")),
    Field("length_limit", "artifact", "Is there a length you must stay under?", None,
          "In words.", kind="number"),
    # --- situation -----------------------------------------------------
    Field("trigger", "situation", "What happened, and why write now?", None),
    Field("urgency", "situation", "How soon must this land?",
          ("none", "this_week", "today", "immediate")),
    Field("stakes", "situation", "What is the cost of being misunderstood?",
          ("low", "moderate", "high", "safety_critical", "crisis"),
          "Drives evidence, uncertainty, and verification requirements."),
    Field("consequence_of_failure", "situation",
          "What happens if they misunderstand, delay, or do nothing?", None),
    # --- reader --------------------------------------------------------
    Field("primary_reader", "reader", "Who reads this first?", None),
    Field("authority", "reader", "What can they actually decide or do?",
          ("decides", "approves", "advises", "acts", "informed")),
    Field("prior_knowledge", "reader", "What do they already know about this?",
          ("none", "partial", "expert")),
    Field("time_available", "reader", "How much attention will they have?",
          ("low", "medium", "high")),
    Field("likely_objection", "reader", "What will they push back on?", None),
    # --- outcome -------------------------------------------------------
    Field("intent", "outcome", "What must they do, decide, or understand afterwards?",
          ("inform", "explain", "teach", "request", "recommend", "persuade",
           "warn", "reassure", "correct", "repair", "demonstrate", "escalate"),
          "The single-minded proposition: one primary reader response."),
    Field("desired_action", "outcome", "What is the one action you are asking for?", None),
    Field("decision_deadline", "outcome", "By when?", None),
    # --- relationship --------------------------------------------------
    Field("sensitivity", "relationship", "How much care does this relationship need right now?",
          ("low", "moderate", "high")),
    Field("power_distance", "relationship", "Are you writing up, across, or down?",
          ("upward", "peer", "downward")),
    # --- evidence ------------------------------------------------------
    Field("evidence_available", "evidence", "What can you point to?", None),
    Field("uncertainty", "evidence", "What is still estimated, pending, or unknown?", None),
    # --- constraints ---------------------------------------------------
    Field("protected", "constraints",
          "Which exact words, figures, or commitments may not change?", None,
          "A list of literal strings. Checked byte-identically in every variant.",
          kind="list"),
    Field("voice", "constraints", "How much may the writing stop sounding like you?",
          ("preserve", "adapt", "match_exemplar")),
)

BY_NAME = {f.name: f for f in FIELDS}
SECTIONS = ("artifact", "situation", "reader", "outcome", "relationship",
            "evidence", "constraints")

#: Fields with a closed domain, and so the ones `material_questions` can
#: perturb. Not the same as "fields that select the strategy" — see
#: `strategy.STRATEGY_INPUTS`, which is derived from the rule tables and
#: is what `schema()` and the confidence calculation use. `voice` has a
#: closed domain and no rule reads it; perturbation correctly finds it
#: immaterial, but counting it as a known strategy input made a contract
#: look more decided than the rules supported.
SELECTORS = tuple(f.name for f in FIELDS if f.domain)


class ContractError(ValueError):
    """A contract value outside its declared domain."""


@dataclass(frozen=True)
class Contract:
    """A situation, as the system currently understands it.

    Immutable: `with_value` returns a new contract. Perturbation-based
    question selection depends on that — it builds dozens of speculative
    contracts and must never disturb the real one.
    """
    values: dict[str, Any] = field(default_factory=dict)
    provenance: dict[str, str] = field(default_factory=dict)

    def get(self, name: str, default: Any = None) -> Any:
        return self.values.get(name, default)

    def origin(self, name: str) -> str:
        return self.provenance.get(name, UNSET)

    def is_set(self, name: str) -> bool:
        return self.values.get(name) not in (None, "", [])

    def with_value(self, name: str, value: Any, origin: str = STATED) -> "Contract":
        return replace(self,
                       values={**self.values, name: value},
                       provenance={**self.provenance, name: origin})

    def assumptions(self) -> list[str]:
        """Fields the assistant guessed at. These are what a human confirms."""
        return sorted(n for n, o in self.provenance.items()
                      if o == INFERRED and self.is_set(n))

    def unresolved(self) -> list[str]:
        """Selector fields with no value at all, in declaration order."""
        return [n for n in SELECTORS if not self.is_set(n)]

    def protected_strings(self) -> list[str]:
        raw = self.get("protected") or []
        if isinstance(raw, str):
            raw = [raw]
        return [s for s in (str(x).strip() for x in raw) if s]

    def to_dict(self) -> dict:
        """Nested by section, the shape the brief writes contracts in."""
        out: dict[str, dict] = {s: {} for s in SECTIONS}
        for f in FIELDS:
            if self.is_set(f.name):
                out[f.section][f.name] = self.values[f.name]
        return {"sections": {s: v for s, v in out.items() if v},
                "provenance": dict(sorted(self.provenance.items())),
                "assumptions": self.assumptions(),
                "unresolved": self.unresolved()}


def build(values: dict[str, Any] | None = None,
          inferred: dict[str, Any] | None = None) -> Contract:
    """Make a contract from stated and inferred values, validating domains.

    Stated wins on conflict: a human's answer is never overwritten by a
    guess about the same field.
    """
    contract = Contract()
    for source, origin in ((inferred or {}, INFERRED), (values or {}, STATED)):
        for name, value in source.items():
            contract = contract.with_value(name, _check(name, value), origin)
    return contract


def _check(name: str, value: Any) -> Any:
    f = BY_NAME.get(name)
    if f is None:
        raise ContractError(
            f"Unknown contract field {name!r}. Known fields: {', '.join(BY_NAME)}")
    if value in (None, ""):
        return value
    if f.domain and value not in f.domain:
        raise ContractError(
            f"{name}={value!r} is outside its domain. Allowed: {', '.join(f.domain)}")
    if f.kind == "number":
        try:
            return int(str(value).strip())
        except (TypeError, ValueError):
            raise ContractError(f"{name}={value!r} must be a whole number") from None
    if f.kind == "list" and isinstance(value, str):
        return [value]
    return value


def schema() -> list[dict]:
    """The field registry as data, for clients that render a contract form."""
    from .strategy import STRATEGY_INPUTS  # local: strategy reads contracts

    return [{"name": f.name, "section": f.section, "question": f.question,
             "domain": list(f.domain) if f.domain else None, "note": f.note,
             "kind": f.kind, "selects_strategy": f.name in STRATEGY_INPUTS}
            for f in FIELDS]
