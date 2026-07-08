from .rules import observe, recommend, transform
from .validation import validate
from .metrics import metrics
from .report import render_report
from .models import to_dicts
from .packs import DEFAULT_PACK_ID, get_pack

def run_pipeline(text: str, pack_id: str = DEFAULT_PACK_ID) -> dict:
    """Run the full pipeline on `text` and return the artifact trail.

    The returned dict mirrors the files a CLI run writes: each value is
    JSON-serializable, and dumping it produces the same content as the
    corresponding artifact file. Callers (the CLI, a browser shim) decide
    how to persist or display it.
    """
    pack = get_pack(pack_id)
    observations = observe(pack, text)
    recommendations = recommend(pack, observations)
    final, transformations = transform(pack, text, observations, recommendations)
    validation = validate(text, final, transformations)

    before_metrics = metrics(text)
    after_metrics = metrics(final)
    report = render_report(before_metrics, after_metrics, validation, transformations, final)

    return {
        "observations": to_dicts(observations),
        "recommendations": to_dicts(recommendations),
        "transformations": to_dicts(transformations),
        "validation": validation,
        "final": final,
        "report": report,
        "metrics": {"before": before_metrics, "after": after_metrics},
        "pack": {"id": pack.id, "version": pack.version, "title": pack.title,
                 "transformations": pack.rule_count()},
    }
