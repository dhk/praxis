# Findings: Claude (in-session)

Written before reading any other source. Knowledge cutoff May 2026;
anything after that is a gap, and every entry below should be verified
against primary sources rather than taken from this file. Where a claim
is my inference rather than something I am recalling from a specific
work, it says so.

---

## Q1. Multi-model labelling in place of human labels

| Entry | What it is | RFC-0005 concept overlap | Verdict |
|---|---|---|---|
| LLM-as-a-judge (Zheng et al., MT-Bench / Chatbot Arena, NeurIPS 2023) | Uses a strong model to score outputs; reports agreement with human preference at roughly the level of human–human agreement, and documents position, verbosity and self-enhancement biases | Directly the "second model labels" half of open question 1 | adopt/reference |
| LLM annotators vs crowdworkers (Gilardi et al., PNAS 2023, and replications) | Finds model annotation matching or exceeding crowd labels on several classification tasks at far lower cost | Evidence that model labelling is not disqualified outright | adopt/reference |
| Query-by-committee (Seung, Opper & Sompolinsky, 1992) | Ensemble members vote; disagreement marks the informative examples | The escalation half of the proposal — disagreement as the signal, not the label | adopt/reference |
| Self-enhancement bias in judge models | A judge prefers text resembling its own output | Bears on whether the generating and judging model may share a family | differentiate |
| Model collapse under recursive synthetic data (Shumailov et al., 2024) | Training on model output degrades the distribution over generations | About training rather than evaluation, but the same correlated-blind-spot mechanism | differentiate |

**Notes:** The literature supports model annotation as a *cost* substitute for
crowd labour on tasks with clear guidelines. It does not, as far as I can find,
support it as a substitute for ground truth when the thing being evaluated was
authored by a model of the same kind — which is the specific situation here and
the thing I most want an outside source to check.

The strongest evidence *for* the proposal is local rather than published: in
this repository, an independent model review found seven detector faults that
the detectors' own author had tested and missed. That is a real result, but it
is n=1 and the reviewer was reading code, not labelling examples.

The distinction I would want confirmed or demolished: **agreement is not
correctness, but disagreement is reliably informative.** If that holds, the
sound design is to use two models to *triage* rather than to label — cheap
coverage, with human attention spent only where they diverge.

## Q2. Behavioural / capability test suites

| Entry | What it is | RFC-0005 concept overlap | Verdict |
|---|---|---|---|
| CheckList (Ribeiro et al., ACL 2020) | Behavioural testing by capability, with Minimum Functionality Tests, invariance and directional-expectation tests; templates generate many cases per capability | Almost exactly the proposed corpus, and the "category supplies the label" idea | adopt/reference |
| HANS (McCoy et al., ACL 2019) | A targeted set built so that shallow heuristics give the wrong answer | The model for adversarial-by-construction examples aimed at a known failure mode | adopt/reference |
| Dynabench (Kiela et al., NAACL 2021) | Humans write examples specifically to fool a live model, iteratively | A way to source hard cases without a fixed label budget | adopt/reference |
| Unit-test-style NLP suites generally | Small, named, per-behaviour assertions rather than aggregate accuracy | The existing `tests/test_measure.py` shape | adopt/reference |

**Notes:** CheckList is the closest published relative of what RFC-0005
proposes and should probably be cited in it directly. Its template mechanism is
the disciplined version of "write twenty sentences that mention updating and
name no time" — the label comes from the template slot, not from a judgment.

Its granularity answer is also useful for open question 2: CheckList works at
sentence level for most capabilities, which matches the corpus's current shape.

## Q3. Weak supervision and label denoising

| Entry | What it is | RFC-0005 concept overlap | Verdict |
|---|---|---|---|
| Snorkel (Ratner et al., VLDB 2017) | Users write noisy labelling functions; a generative model estimates each one's accuracy and correlations without ground truth, producing probabilistic labels | Directly open question 1: combining several noisy labellers | adopt/reference |
| Data programming (Ratner et al., NeurIPS 2016) | The theory underneath Snorkel | Same | adopt/reference |
| Dawid–Skene (1979) | Classic EM estimation of annotator reliability from unlabelled agreement patterns | The oldest form of the same idea; simpler and stdlib-implementable | adopt/reference |
| Snorkel's correlation assumption | Accuracy estimation degrades when labelling sources make *correlated* errors, which the model must be told about | The central risk for model annotators, who are correlated by construction | differentiate |

**Notes:** This is the strongest technical answer to "how do I combine noisy
labellers" and it comes with the exact caveat that matters here. Snorkel-style
denoising assumes sources fail somewhat independently; two language models do
not. Whether the correlation can be *estimated* rather than assumed away is the
question I would put to another source.

Worth noting for praxis specifically: the detectors themselves are labelling
functions in the Snorkel sense. There may be a design here where the regex and
two models are three sources over unlabelled text, rather than the regex being
the thing under test — but that inverts the RFC's framing and I flag it as an
idea, not a recommendation.

## Q4. Agreement statistics for model annotators

| Entry | What it is | RFC-0005 concept overlap | Verdict |
|---|---|---|---|
| Cohen's κ, Fleiss' κ, Krippendorff's α | Chance-corrected agreement for two, many, and arbitrary-scale annotators | The reporting question in open question 6 | adopt/reference |
| Landis & Koch interpretation bands | The conventional "substantial / almost perfect" κ thresholds | Convention that may not transfer to model annotators | differentiate |
| "Are we modeling the task or the annotator?" (Geva et al., EMNLP 2019) | Annotator identity leaks into labels and inflates measured performance | The same hazard when one model both writes and labels | adopt/reference |
| Reporting both agreement and accuracy separately | Practice of publishing inter-annotator agreement alongside the headline metric | Answers open question 3 directly | adopt/reference |

**Notes:** My inference, not a recalled finding: chance-corrected agreement
assumes annotators err independently, so κ between two models will read higher
than the same κ between two people would warrant. If that is right, the
conventional interpretation bands should not be carried over, and any reported
κ needs the annotator type stated beside it. I would like this checked — it
determines whether RFC-0005 can report a single number at all.

## Q5. Synthetic-corpus distribution shift

| Entry | What it is | RFC-0005 concept overlap | Verdict |
|---|---|---|---|
| Machine-text detectability literature | Generated text is reliably distinguishable from human text by statistical means, implying a measurable distribution difference | If the two are separable, evaluating on one and deploying on the other is a shift | adopt/reference |
| Homogenisation of model prose (Chakrabarty et al., 2026; already cited in the wave-1 brief) | Generated writing is stylistically narrower than human writing | Generated examples under-represent real variation | adopt/reference |
| Template-based generation as a mitigation | Fixing surface form via templates rather than free generation | Bounds the shift by removing the model's stylistic choices | adopt/reference |
| Naturally-occurring-only evaluation sets | The practice of insisting evaluation data be found rather than made | The conservative position; expensive but unimpeachable | differentiate |

**Notes:** The concrete instance in praxis is small and telling: a protected
phrase spanning a hard line-wrap was silently reported absent. That bug was
found in a hand-written example that happened to be wrapped. Generated examples
are almost never hard-wrapped, carry no quoted thread, no signature block, no
inconsistent punctuation. I have no measured figure for how much the score
would move, and that is exactly the gap.

## Q6. Counterfactual and boundary examples

| Entry | What it is | RFC-0005 concept overlap | Verdict |
|---|---|---|---|
| Counterfactually-Augmented Data (Kaushik, Hovy & Lipton, ICLR 2020) | Humans minimally edit examples to flip the label; models trained or tested on these rely less on spurious cues | Exactly the minimal-pair idea, with human editing as the mechanism | adopt/reference |
| CheckList directional expectation tests | Assert which way a prediction should move under a controlled perturbation | The "by 9" versus "by 5 days" pair as a directional test | adopt/reference |
| Contrast sets (Gardner et al., Findings of EMNLP 2020) | Expert-authored local perturbations around existing examples, to probe decision boundaries | The generation method for boundary pairs | adopt/reference |

**Notes:** All three treat the minimal edit as *human* work, because the value
is in choosing which single property to vary. That is the strongest argument I
found against generating this particular class of example — and it is also the
class praxis needs most, since every one of the seven review findings was a
boundary case.

## Q7. Spending scarce human attention

| Entry | What it is | RFC-0005 concept overlap | Verdict |
|---|---|---|---|
| Uncertainty sampling / active learning (Lewis & Gale, 1994 onward) | Label where the model is least certain | The default answer to open question 5 | adopt/reference |
| Query-by-committee | Label where annotators disagree | Fits the two-model proposal exactly | adopt/reference |
| Risk-based test prioritisation (software testing) | Spend test effort in proportion to consequence of failure | `consequential` and `escalation` gate safety-critical requirements; they deserve more labels than `scan` | adopt/reference |
| Active learning's known fragility | Gains are inconsistent and sometimes worse than random sampling, especially at small budgets | A caution against over-engineering the sampling for a corpus this size | differentiate |

**Notes:** A regular expression has no calibrated uncertainty, so classic
uncertainty sampling does not apply directly. Committee disagreement does, and
so does consequence-weighting — which is a product judgment praxis can already
make from the stakes ladder.

## Open gaps

1. **Whether two models from different families are independent enough for
   Snorkel-style denoising to estimate their accuracies.** This is the load-
   bearing question for the whole proposal and I could not answer it.
2. **Whether chance-corrected agreement statistics retain their conventional
   interpretation with model annotators.** Stated above as inference only.
3. **Any measured figure for the precision/recall gap between synthetic and
   naturally-occurring evaluation text.** I found the direction, not the size.
4. **Post-May-2026 work on all of the above**, which I cannot see at all.
5. **Whether anyone has published on evaluating rule-based components that a
   model authored** — the exact circularity in RFC-0005. I suspect this is
   too new or too niche to have a literature, and a confirmation that it does
   not exist would itself be a useful finding.
