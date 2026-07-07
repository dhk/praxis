import re
from dataclasses import dataclass
from .models import Observation, Recommendation, Transformation

@dataclass(frozen=True)
class PhraseRule:
    id: str
    title: str
    pattern: str
    replacement: str
    reason: str
    safety: str = "safe"

PHRASE_RULES = [
    PhraseRule("CSW-001", "Remove unnecessary introductory phrases", r"\bIt should be noted that\s+", "", "Introductory phrase adds no information before the main claim.", "safe"),
    PhraseRule("CSW-001", "Remove unnecessary introductory phrases", r"\bIt is important to note that\s+", "", "Introductory phrase adds no information before the main claim.", "safe"),
    PhraseRule("CSW-002", "Replace verbose phrases with concise equivalents", r"\bdue to the fact that\b", "because", "Concise equivalent preserves causal meaning.", "low_risk"),
    PhraseRule("CSW-002", "Replace verbose phrases with concise equivalents", r"\bin order to\b", "to", "Shorter form preserves purpose.", "low_risk"),
    PhraseRule("CSW-002", "Replace verbose phrases with concise equivalents", r"\bhas the ability to\b", "can", "Shorter modal verb preserves ability claim.", "low_risk"),
    PhraseRule("CSW-003", "Convert nominalizations to stronger verbs", r"\bperform an analysis of\b", "analyze", "Verb form is shorter and more direct.", "low_risk"),
    PhraseRule("CSW-003", "Convert nominalizations to stronger verbs", r"\bconduct an evaluation of\b", "evaluate", "Verb form is shorter and more direct.", "low_risk"),
]

def split_sentences(text: str) -> list[tuple[int, int, str]]:
    matches = list(re.finditer(r"[^.!?]+[.!?]", text, flags=re.MULTILINE))
    return [(m.start(), m.end(), m.group(0).strip()) for m in matches]

def observe(text: str) -> list[Observation]:
    observations: list[Observation] = []
    seq = 1
    for rule in PHRASE_RULES:
        for m in re.finditer(rule.pattern, text, flags=re.IGNORECASE):
            observations.append(Observation(
                id=f"O-{seq:03d}", rule_id=rule.id, rule_title=rule.title,
                location=f"char:{m.start()}-{m.end()}", evidence=m.group(0),
                reason=rule.reason, safety=rule.safety))
            seq += 1
    for _, _, sentence in split_sentences(text):
        word_count = len(re.findall(r"\b\w+\b", sentence))
        if word_count > 35:
            observations.append(Observation(
                id=f"O-{seq:03d}", rule_id="CSW-004", rule_title="Flag long sentences for review",
                location="sentence", evidence=sentence,
                reason=f"Sentence contains {word_count} words; long sentences increase reader effort.",
                safety="review"))
            seq += 1
    return observations

def recommend(observations: list[Observation]) -> list[Recommendation]:
    recs: list[Recommendation] = []
    for i, obs in enumerate(observations, start=1):
        if obs.rule_id == "CSW-004":
            after = obs.evidence
            action = "review_long_sentence"
        else:
            rule = next(r for r in PHRASE_RULES if r.id == obs.rule_id and re.fullmatch(r.pattern, obs.evidence, re.IGNORECASE))
            after = re.sub(rule.pattern, rule.replacement, obs.evidence, flags=re.IGNORECASE)
            action = "apply_phrase_transformation"
        recs.append(Recommendation(id=f"R-{i:03d}", observation_id=obs.id, action=action,
                                   before=obs.evidence, after=after, reason=obs.reason, safety=obs.safety))
    return recs

def transform(text: str, observations: list[Observation], recommendations: list[Recommendation]) -> tuple[str, list[Transformation]]:
    transformed = text
    records: list[Transformation] = []
    idx = 1
    for rule in PHRASE_RULES:
        matches = list(re.finditer(rule.pattern, transformed, flags=re.IGNORECASE))
        for m in matches:
            before = m.group(0)
            after = re.sub(rule.pattern, rule.replacement, before, flags=re.IGNORECASE)
            records.append(Transformation(id=f"T-{idx:03d}", recommendation_id="derived", rule_id=rule.id,
                                          location=f"char:{m.start()}-{m.end()}", before=before, after=after,
                                          reason=rule.reason, safety=rule.safety, applied=True))
            idx += 1
        transformed = re.sub(rule.pattern, rule.replacement, transformed, flags=re.IGNORECASE)
    for rec in recommendations:
        if rec.safety == "review":
            records.append(Transformation(id=f"T-{idx:03d}", recommendation_id=rec.id, rule_id="CSW-004",
                                          location="sentence", before=rec.before, after=rec.after,
                                          reason=rec.reason, safety=rec.safety, applied=False,
                                          validation_status="not_applied_review_required"))
            idx += 1
    return transformed, records
