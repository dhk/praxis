from .models import Transformation

def render_report(before_metrics: dict, after_metrics: dict, validation: dict, transformations: list[Transformation], final_text: str) -> str:
    rows = []
    for t in transformations:
        applied = "yes" if t.applied else "no"
        rows.append(f"| {t.id} | {t.rule_id} | {t.safety} | {applied} | `{t.before}` | `{t.after}` | {t.reason} | {t.validation_status} |")
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
