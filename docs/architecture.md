# Architecture

praxis is a pass-based document transformation harness.

The current implementation is intentionally small:

1. Parse source Markdown into a lightweight document representation.
2. Apply a transformation pack to produce observations.
3. Convert observations into recommendations.
4. Apply safe transformations.
5. Validate that protected content was preserved.
6. Render an audit report.

The system favors explicit artifacts over hidden behavior. The artifact trail is the product.

## Vocabulary

| Term | Meaning |
| --- | --- |
| Document | Source content being analyzed or transformed. |
| Pass | Named operation with explicit inputs and outputs. |
| Observation | Evidence detected in the document. |
| Recommendation | Proposed action derived from an observation. |
| Transformation | Actual edit applied to content. |
| Validation | Check that the transformation did not violate invariants. |
| Artifact | Persisted intermediate output. |
| Transformation Pack | Versioned domain knowledge used by the harness. |

## Non-goal

This harness does not claim to prove semantic equivalence. Validation is evidence-based and conservative.
