import re
from .models import Transformation

def protected_tokens(text: str) -> set[str]:
    # The percent sign has its own alternative (tried first) because a trailing
    # `\b` can never match right after `%` when it's followed by whitespace or
    # punctuation (both non-word chars) — requiring it there silently drops the
    # `%` from every "50% " in ordinary prose.
    patterns = [
        r"https?://\S+",
        r"\b\d+(?:\.\d+)?%|\b\d+(?:\.\d+)?\b",
        r"\[[^\]]+\]",
        r"\([^)]*\d{4}[^)]*\)",
        r"```[\s\S]*?```",   # fenced code blocks
        r"`[^`\n]+`",        # inline code spans
    ]
    tokens: set[str] = set()
    for pattern in patterns:
        tokens.update(re.findall(pattern, text))
    return tokens

def validate(original: str, final: str) -> dict:
    """Check that protected tokens survived the transformation. Pure — takes
    only the two documents, returns a result dict, no side effects. See
    apply_validation_status for stamping that result onto Transformations.
    """
    missing = sorted(protected_tokens(original) - protected_tokens(final))
    status = "pass" if not missing else "fail"
    return {
        "status": status,
        "checks": {"protected_tokens_preserved": status, "missing_protected_tokens": missing},
        "note": "Validation is conservative and evidence-based; it does not prove semantic equivalence.",
    }

def apply_validation_status(transformations: list[Transformation], status: str) -> None:
    """Stamp each pending Transformation with the run's overall validation
    outcome from validate(). Mutates in place — called once, right after
    validate(), so the JSON/report artifacts reflect what it computed.
    """
    outcome = "pass" if status == "pass" else "needs_review"
    for t in transformations:
        if t.validation_status == "pending":
            t.validation_status = outcome
