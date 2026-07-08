import re
from .models import Observation, Recommendation, Transformation
from .packs import Pack

FLAG_REGEX_FLAGS = re.IGNORECASE | re.MULTILINE

def split_sentences(text: str) -> list[tuple[int, int, str]]:
    matches = list(re.finditer(r"[^.!?]+[.!?]", text, flags=re.MULTILINE))
    return [(m.start(), m.end(), m.group(0).strip()) for m in matches]

def observe(pack: Pack, text: str) -> list[Observation]:
    observations: list[Observation] = []
    seq = 1
    for rule in pack.phrase_rules:
        for m in re.finditer(rule.pattern, text, flags=re.IGNORECASE):
            observations.append(Observation(
                id=f"O-{seq:03d}", rule_id=rule.id, rule_title=rule.title,
                location=f"char:{m.start()}-{m.end()}", evidence=m.group(0),
                reason=rule.reason, safety=rule.safety))
            seq += 1
    for rule in pack.flag_rules:
        if rule.kind == "long_sentence":
            for _, _, sentence in split_sentences(text):
                word_count = len(re.findall(r"\b\w+\b", sentence))
                if word_count > rule.threshold:
                    observations.append(Observation(
                        id=f"O-{seq:03d}", rule_id=rule.id, rule_title=rule.title,
                        location="sentence", evidence=sentence,
                        reason=rule.reason.format(words=word_count),
                        safety="review"))
                    seq += 1
        else:
            for m in re.finditer(rule.pattern, text, flags=FLAG_REGEX_FLAGS):
                observations.append(Observation(
                    id=f"O-{seq:03d}", rule_id=rule.id, rule_title=rule.title,
                    location=f"char:{m.start()}-{m.end()}", evidence=m.group(0),
                    reason=rule.reason, safety="review"))
                seq += 1
    return observations

def recommend(pack: Pack, observations: list[Observation]) -> list[Recommendation]:
    flag_actions = {r.id: r.action for r in pack.flag_rules}
    recs: list[Recommendation] = []
    for i, obs in enumerate(observations, start=1):
        if obs.rule_id in flag_actions:
            after = obs.evidence
            action = flag_actions[obs.rule_id]
        else:
            rule = next(r for r in pack.phrase_rules if r.id == obs.rule_id and re.fullmatch(r.pattern, obs.evidence, re.IGNORECASE))
            after = re.sub(rule.pattern, rule.replacement, obs.evidence, flags=re.IGNORECASE)
            action = "apply_phrase_transformation"
        recs.append(Recommendation(id=f"R-{i:03d}", observation_id=obs.id, action=action,
                                   before=obs.evidence, after=after, reason=obs.reason, safety=obs.safety))
    return recs

def transform(pack: Pack, text: str, observations: list[Observation], recommendations: list[Recommendation]) -> tuple[str, list[Transformation]]:
    obs_by_id = {obs.id: obs for obs in observations}
    transformed = text
    records: list[Transformation] = []
    idx = 1
    for rule in pack.phrase_rules:
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
            obs = obs_by_id[rec.observation_id]
            records.append(Transformation(id=f"T-{idx:03d}", recommendation_id=rec.id, rule_id=obs.rule_id,
                                          location=obs.location, before=rec.before, after=rec.after,
                                          reason=rec.reason, safety=rec.safety, applied=False,
                                          validation_status="not_applied_review_required"))
            idx += 1
    return transformed, records
