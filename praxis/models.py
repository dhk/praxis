from dataclasses import dataclass, asdict
from typing import Any

@dataclass
class Observation:
    id: str
    rule_id: str
    rule_title: str
    location: str
    evidence: str
    reason: str
    safety: str

@dataclass
class Recommendation:
    id: str
    observation_id: str
    action: str
    before: str
    after: str
    reason: str
    safety: str

@dataclass
class Transformation:
    id: str
    recommendation_id: str
    rule_id: str
    location: str
    before: str
    after: str
    reason: str
    safety: str
    applied: bool
    validation_status: str = "pending"

def to_dicts(items: list[Any]) -> list[dict[str, Any]]:
    return [asdict(item) for item in items]
