import re
from .models import Transformation

def protected_tokens(text: str) -> set[str]:
    # The percent sign has its own alternative (tried first) because a trailing
    # `\b` can never match right after `%` when it's followed by whitespace or
    # punctuation (both non-word chars) — requiring it there silently drops the
    # `%` from every "50% " in ordinary prose.
    patterns = [r"https?://\S+", r"\b\d+(?:\.\d+)?%|\b\d+(?:\.\d+)?\b", r"\[[^\]]+\]", r"\([^)]*\d{4}[^)]*\)"]
    tokens: set[str] = set()
    for pattern in patterns:
        tokens.update(re.findall(pattern, text))
    return tokens

def validate(original: str, final: str, transformations: list[Transformation]) -> dict:
    missing = sorted(protected_tokens(original) - protected_tokens(final))
    status = "pass" if not missing else "fail"
    for t in transformations:
        if t.validation_status == "pending":
            t.validation_status = "pass" if status == "pass" else "needs_review"
    return {
        "status": status,
        "checks": {"protected_tokens_preserved": status, "missing_protected_tokens": missing},
        "note": "Validation is conservative and evidence-based; it does not prove semantic equivalence.",
    }
