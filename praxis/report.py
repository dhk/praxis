import re
from .models import Transformation

def _cell(text: str) -> str:
    """Escape text for a single-line Markdown table cell (backslash-escape `\\`
    and `|` per CommonMark table conventions, collapse embedded newlines/runs
    of whitespace) so evidence text containing either never corrupts the
    table's column structure.
    """
    # Backtick can't be backslash-escaped inside a single-backtick code span
    # per CommonMark, so swap it for a lookalike rather than leave the span
    # unterminated.
    text = text.replace("\\", "\\\\").replace("|", "\\|").replace("`", "ˋ")
    return re.sub(r"\s+", " ", text).strip()

def render_report(before_metrics: dict, after_metrics: dict, validation: dict, transformations: list[Transformation], final_text: str) -> str:
    rows = []
    for t in transformations:
        applied = "yes" if t.applied else "no"
        rows.append(f"| {t.id} | {t.rule_id} | {t.safety} | {applied} | `{_cell(t.before)}` | `{_cell(t.after)}` | {_cell(t.reason)} | {t.validation_status} |")
    table = "\n".join(rows) if rows else "| — | — | — | — | — | — | — | — |"
    return f"""# praxis Report

## Metrics

| Metric | Before | After |
| --- | ---: | ---: |
| Characters | {before_metrics['characters']} | {after_metrics['characters']} |
| Words | {before_metrics['words']} | {after_metrics['words']} |
| Sentences | {before_metrics['sentences']} | {after_metrics['sentences']} |
| Avg sentence words | {before_metrics['average_sentence_words']} | {after_metrics['average_sentence_words']} |

## Validation

| Check | Result |
| --- | --- |
| Overall status | {validation['status']} |
| Protected tokens preserved | {validation['checks']['protected_tokens_preserved']} |

{validation['note']}

## Transformation Diff Log

| ID | Rule | Safety | Applied | Before | After | Reason | Validation |
| --- | --- | --- | --- | --- | --- | --- | --- |
{table}

## Final Document

{final_text}
"""
