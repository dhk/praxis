from dataclasses import dataclass, field

@dataclass(frozen=True)
class PhraseRule:
    id: str
    title: str
    pattern: str
    replacement: str
    reason: str
    safety: str = "safe"

@dataclass(frozen=True)
class FlagRule:
    """Observation-only rule: flags evidence for human review, never edits.

    kind "regex" matches `pattern` (IGNORECASE | MULTILINE); kind
    "long_sentence" flags sentences above `threshold` words and formats
    `reason` with the actual count.
    """
    id: str
    title: str
    reason: str
    action: str
    kind: str = "regex"
    pattern: str = ""
    threshold: int = 0

@dataclass(frozen=True)
class Pack:
    id: str
    version: str
    title: str
    phrase_rules: tuple = field(default_factory=tuple)
    flag_rules: tuple = field(default_factory=tuple)

    def rule_count(self) -> int:
        return len({r.id for r in self.phrase_rules + self.flag_rules})

CONCISE_SCIENTIFIC_WRITING = Pack(
    id="concise_scientific_writing",
    version="0.1.0",
    title="Concise Scientific Writing",
    phrase_rules=(
        PhraseRule("CSW-001", "Remove unnecessary introductory phrases", r"\bIt should be noted that\s+", "", "Introductory phrase adds no information before the main claim.", "safe"),
        PhraseRule("CSW-001", "Remove unnecessary introductory phrases", r"\bIt is important to note that\s+", "", "Introductory phrase adds no information before the main claim.", "safe"),
        PhraseRule("CSW-002", "Replace verbose phrases with concise equivalents", r"\bdue to the fact that\b", "because", "Concise equivalent preserves causal meaning.", "low_risk"),
        PhraseRule("CSW-002", "Replace verbose phrases with concise equivalents", r"\bin order to\b", "to", "Shorter form preserves purpose.", "low_risk"),
        PhraseRule("CSW-002", "Replace verbose phrases with concise equivalents", r"\bhas the ability to\b", "can", "Shorter modal verb preserves ability claim.", "low_risk"),
        PhraseRule("CSW-003", "Convert nominalizations to stronger verbs", r"\bperform an analysis of\b", "analyze", "Verb form is shorter and more direct.", "low_risk"),
        PhraseRule("CSW-003", "Convert nominalizations to stronger verbs", r"\bconduct an evaluation of\b", "evaluate", "Verb form is shorter and more direct.", "low_risk"),
    ),
    flag_rules=(
        FlagRule("CSW-004", "Flag long sentences for review",
                 "Sentence contains {words} words; long sentences increase reader effort.",
                 action="review_long_sentence", kind="long_sentence", threshold=35),
    ),
)

# Grounded in the skill-map study of ~5,000 crawled skills
# (github.com/dhk/skill-map, docs/best-practices.md): corpus-measured defects
# and the canonical anthropics/skills + openai/skills conventions.
CLAUDE_SKILL_AUTHORING = Pack(
    id="claude_skill_authoring",
    version="0.1.0",
    title="Claude Skill Authoring",
    phrase_rules=(
        PhraseRule("SKL-001", "Remove instruction filler", r"\bPlease note that\s+", "", "Filler adds tokens without changing the instruction.", "safe"),
        PhraseRule("SKL-001", "Remove instruction filler", r"\bsimply\s+", "", "Filler adds tokens without changing the instruction.", "safe"),
        PhraseRule("SKL-002", "Prefer plain verbs in instructions", r"\butilize\b", "use", "Plain verbs keep instructions short and unambiguous.", "low_risk"),
        PhraseRule("SKL-002", "Prefer plain verbs in instructions", r"\bleverage\b", "use", "Plain verbs keep instructions short and unambiguous.", "low_risk"),
        PhraseRule("SKL-002", "Prefer plain verbs in instructions", r"\bin the event that\b", "if", "Plain verbs keep instructions short and unambiguous.", "low_risk"),
    ),
    flag_rules=(
        FlagRule("SKL-003", "Open the description with an action verb",
                 "Gold-standard descriptions open with an action verb (Creates…, Converts…, Reviews…); 'This skill…' wastes the trigger surface the model reads.",
                 action="review_description_opener",
                 pattern=r"^description:[^\S\n]*[\"']?This skill (?:allows|helps|lets|enables|can be used)\b[^\n]*$"),
        FlagRule("SKL-004", "State when to use the skill",
                 "The description is the only text the model sees when deciding whether to invoke the skill; 31% of crawled skills omit a 'use when…' trigger.",
                 action="review_missing_when_trigger",
                 pattern=r"^description:(?![^\n]*\buse (?:this |it )?when\b)(?![^\n]*\bwhen (?:the user|you)\b)[^\n]*$"),
        FlagRule("SKL-005", "State when NOT to use the skill",
                 "Only 2.5% of crawled skills state an anti-trigger ('Do NOT use when…'); omitting one causes false-positive invocation on adjacent tasks.",
                 action="review_missing_anti_trigger",
                 pattern=r"^description:(?![^\n]*\b(?:do not use|don't use|not for)\b)[^\n]*$"),
        FlagRule("SKL-006", "Scope Bash tool grants",
                 "More than half of Bash grants in the crawled corpus are unscoped; scope to specific commands, e.g. Bash(git:*).",
                 action="review_unscoped_bash",
                 pattern=r"^allowed-tools:[^\n]*\bBash\b(?!\()[^\n]*$"),
    ),
)

# Same design as the skills pack: mechanical fixes are applied, judgment
# calls are flagged. Dates, employers, and metrics are protected tokens, so
# validation proves the rewrite never touched a fact.
RESUME_WRITING = Pack(
    id="resume_writing",
    version="0.1.0",
    title="Resume Writing",
    phrase_rules=(
        PhraseRule("RES-001", "Lead with action verbs", r"\bResponsible for managing\b", "Managed", "Action verbs claim the achievement directly; 'responsible for' only claims the assignment.", "low_risk"),
        PhraseRule("RES-001", "Lead with action verbs", r"\bResponsible for leading\b", "Led", "Action verbs claim the achievement directly; 'responsible for' only claims the assignment.", "low_risk"),
        PhraseRule("RES-001", "Lead with action verbs", r"\bResponsible for developing\b", "Developed", "Action verbs claim the achievement directly; 'responsible for' only claims the assignment.", "low_risk"),
        PhraseRule("RES-002", "Remove empty intensifiers", r"\bsuccessfully\s+", "", "If the result is stated, 'successfully' adds nothing; if it isn't, the intensifier can't replace it.", "safe"),
        PhraseRule("RES-002", "Remove empty intensifiers", r"\beffectively\s+", "", "If the result is stated, 'effectively' adds nothing; if it isn't, the intensifier can't replace it.", "safe"),
        PhraseRule("RES-003", "Prefer plain verbs", r"\butilized\b", "used", "Plain verbs read faster in a six-second scan.", "low_risk"),
        PhraseRule("RES-003", "Prefer plain verbs", r"\bleveraged\b", "used", "Plain verbs read faster in a six-second scan.", "low_risk"),
    ),
    flag_rules=(
        FlagRule("RES-004", "Avoid first-person pronouns",
                 "Resume convention omits 'I/my/me'; recruiters read the implied subject and pronouns spend space without adding facts.",
                 action="review_first_person",
                 pattern=r"\b(?:I|my|me)\b"),
        FlagRule("RES-005", "Quantify the achievement",
                 "A bullet with no number, percentage, or amount claims activity, not impact. Add scale, delta, or frequency — or justify why none exists.",
                 action="review_unquantified_bullet",
                 pattern=r"^[ \t]*[-*][ \t](?![^\n]*[\d%$])[^\n]+$"),
        FlagRule("RES-006", "Show, don't self-describe",
                 "Trait claims ('team player', 'detail-oriented') are unverifiable; replace with an achievement that demonstrates the trait.",
                 action="review_trait_claim",
                 pattern=r"\b(?:team player|hard[- ]working|detail[- ]oriented|results[- ]driven|self[- ]starter|go[- ]getter)\b"),
    ),
)

# Docs *about* a repo — README, design docs, how-tos — not the code itself.
# Mechanical filler cuts apply automatically; unresolved placeholders and
# ownership-hiding passives are judgment calls, so they're flagged rather
# than edited. Long-sentence threshold is looser than the scientific-writing
# pack since technical docs carry more compound/conditional clauses.
REPO_DOCS = Pack(
    id="repo_docs",
    version="0.1.0",
    title="Repo Docs (README, Design, How-To)",
    phrase_rules=(
        PhraseRule("RPD-001", "Remove instruction filler", r"\bPlease note that\s+", "", "Filler adds tokens without changing the instruction.", "safe"),
        PhraseRule("RPD-001", "Remove instruction filler", r"\bIt is important to note that\s+", "", "Filler adds tokens without changing the instruction.", "safe"),
        PhraseRule("RPD-002", "Replace verbose phrases with concise equivalents", r"\bin order to\b", "to", "Shorter form preserves purpose.", "low_risk"),
        PhraseRule("RPD-002", "Replace verbose phrases with concise equivalents", r"\bmake use of\b", "use", "Shorter form preserves meaning.", "low_risk"),
        PhraseRule("RPD-002", "Replace verbose phrases with concise equivalents", r"\bis able to\b", "can", "Shorter modal verb preserves ability claim.", "low_risk"),
        PhraseRule("RPD-003", "Prefer plain verbs", r"\butilize\b", "use", "Plain verbs read faster in reference docs.", "low_risk"),
    ),
    flag_rules=(
        FlagRule("RPD-004", "Flag unresolved placeholders",
                 "Unresolved placeholder should be resolved before this doc ships.",
                 action="review_unresolved_placeholder",
                 pattern=r"\b(?:TODO|FIXME|TBD|coming soon)\b"),
        FlagRule("RPD-005", "Flag hidden ownership",
                 "Passive construction hides who decided or built this; name the owner.",
                 action="review_hidden_ownership",
                 pattern=r"\b(?:it was decided that|has been decided that|was implemented by)\b"),
        FlagRule("RPD-006", "Flag long sentences for review",
                 "Sentence contains {words} words; long sentences increase reader effort.",
                 action="review_long_sentence", kind="long_sentence", threshold=40),
    ),
)

# Product briefs and concept docs: buzzwords and unquantified impact claims
# read as confidence but carry no evidence, so they're flagged rather than
# auto-rewritten — there's rarely a mechanical substitute for "disruptive."
# Long-sentence threshold is tighter than the docs pack since briefs are
# written for a skimming executive audience.
PM_WRITING = Pack(
    id="pm_writing",
    version="0.1.0",
    title="Product Briefs & Concepts",
    phrase_rules=(
        PhraseRule("PMW-001", "Prefer plain verbs over buzzwords", r"\butilize\b", "use", "Plain verbs read faster than jargon.", "low_risk"),
        PhraseRule("PMW-001", "Prefer plain verbs over buzzwords", r"\bleverage\b", "use", "Plain verbs read faster than jargon.", "low_risk"),
        PhraseRule("PMW-002", "Replace verbose phrases with concise equivalents", r"\bin order to\b", "to", "Shorter form preserves purpose.", "low_risk"),
        PhraseRule("PMW-002", "Replace verbose phrases with concise equivalents", r"\bat this point in time\b", "now", "Shorter form preserves meaning.", "low_risk"),
    ),
    flag_rules=(
        FlagRule("PMW-003", "Flag buzzwords with no mechanical substitute",
                 "Buzzword asserts value without evidence; replace with a concrete capability or metric.",
                 action="review_buzzword",
                 pattern=r"\b(?:synerg(?:y|ies)|disrupt(?:ive|ion)?|best[- ]in[- ]class|cutting[- ]edge|game[- ]changing|revolutionary|world[- ]class|frictionless)\b"),
        FlagRule("PMW-004", "Flag unquantified impact claims",
                 "Superlative claims impact without a number; add a metric or replace with the specific effect.",
                 action="review_unquantified_superlative",
                 pattern=r"\b(?:significant(?:ly)?|substantial(?:ly)?|dramatically|robust)\b"),
        FlagRule("PMW-005", "Flag vague shipping commitments",
                 "Vague modal on a shipping verb reads as a promise without a commitment; state what's actually decided.",
                 action="review_vague_commitment",
                 pattern=r"\b(?:may|might|could)\s+(?:ship|launch|release)\b"),
        FlagRule("PMW-006", "Flag long sentences for review",
                 "Sentence contains {words} words; long sentences increase reader effort.",
                 action="review_long_sentence", kind="long_sentence", threshold=30),
    ),
)

PACKS = {p.id: p for p in (CONCISE_SCIENTIFIC_WRITING, CLAUDE_SKILL_AUTHORING, RESUME_WRITING, REPO_DOCS, PM_WRITING)}
DEFAULT_PACK_ID = CONCISE_SCIENTIFIC_WRITING.id

def get_pack(pack_id: str) -> Pack:
    if pack_id not in PACKS:
        raise KeyError(f"Unknown pack '{pack_id}'. Available: {', '.join(PACKS)}")
    return PACKS[pack_id]

def list_packs() -> list[dict]:
    return [
        {"id": p.id, "version": p.version, "title": p.title, "transformations": p.rule_count()}
        for p in PACKS.values()
    ]
