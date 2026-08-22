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

# Derived from ASD-STE100 (Simplified Technical English), which governs
# *language* where the design layer's structures govern *order* — the
# distinction the pack exists to make usable. It implements the
# transferable half: sentence length, hidden actors, compound
# instructions, plain-word substitution. It deliberately does NOT
# implement the STE100 Dictionary (~900 approved words, one meaning and
# one part of speech each), which is the mechanism that makes STE100
# STE100. Approximating that list by hand would be our vocabulary
# wearing the standard's name, firing on most of any real document with
# no corpus to check it against. Hence the title: derived from, not
# conformant to. Rules cite what the standard asks for rather than a
# clause number, because the numbers cannot be verified from here.
CONTROLLED_LANGUAGE = Pack(
    id="controlled_language",
    version="0.1.0",
    title="Controlled Language (STE100-derived)",
    phrase_rules=(
        PhraseRule("CTL-001", "Remove filler before an instruction", r"\bPlease note that\s+", "", "Filler delays the instruction without qualifying it.", "safe"),
        PhraseRule("CTL-001", "Remove filler before an instruction", r"\bIt should be noted that\s+", "", "Filler delays the instruction without qualifying it.", "safe"),
        PhraseRule("CTL-001", "Remove filler before an instruction", r"\bIt is important to note that\s+", "", "Filler delays the instruction without qualifying it.", "safe"),
        PhraseRule("CTL-002", "Prefer the plainer word", r"\butilize\b", "use", "Controlled language keeps one plain word per meaning.", "low_risk"),
        PhraseRule("CTL-002", "Prefer the plainer word", r"\bprior to\b", "before", "Controlled language keeps one plain word per meaning.", "low_risk"),
        PhraseRule("CTL-002", "Prefer the plainer word", r"\bsubsequent to\b", "after", "Controlled language keeps one plain word per meaning.", "low_risk"),
        PhraseRule("CTL-002", "Prefer the plainer word", r"\bin the event that\b", "if", "Controlled language keeps one plain word per meaning.", "low_risk"),
        PhraseRule("CTL-002", "Prefer the plainer word", r"\bin order to\b", "to", "Controlled language keeps one plain word per meaning.", "low_risk"),
    ),
    flag_rules=(
        FlagRule("CTL-003", "Flag sentences above the controlled-language limit",
                 "Sentence contains {words} words; controlled language keeps sentences to 20 words or fewer.",
                 action="review_long_sentence", kind="long_sentence", threshold=20),
        FlagRule("CTL-004", "Flag a hidden actor",
                 "Passive construction leaves the actor unnamed; controlled language names who does the thing.",
                 action="review_hidden_actor",
                 pattern=r"\b(?:is|are|was|were|be|been|being)\s+(?:\w+ly\s+)?\w+(?:ed|en)\b(?!\s+by\b)"),
        FlagRule("CTL-005", "Flag a compound instruction",
                 "Two instructions share one sentence; controlled language gives each its own.",
                 action="review_compound_instruction",
                 pattern=r"\band then\b|\b,\s*and\s+(?:also\s+)?(?:you\s+)?(?:must|should|need to)\b"),
    ),
)

PACKS = {p.id: p for p in (CONCISE_SCIENTIFIC_WRITING, CLAUDE_SKILL_AUTHORING, RESUME_WRITING, CONTROLLED_LANGUAGE)}
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
