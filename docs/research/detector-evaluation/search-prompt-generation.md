# Search prompt: generating and labelling corpus content

A narrower companion to [`handoff-prompt.md`](handoff-prompt.md). That one
asks seven questions across evaluation methodology; this one asks only
about the part being decided first — **how much of the corpus can be
machine-generated, and who assigns the labels.**

Use this when the recipient is a search tool rather than a researcher.
Everything below the rule is the paste.

---

Prior-art search: **generating and labelling text examples to evaluate a
text classifier.**

Context in two lines: I have about a dozen regular-expression detectors
that flag communication signals in prose — does this message contain a
request, a deadline, a route to escalate, a named next update time. I need
a labelled corpus to measure their precision and recall, and I'm deciding
how much of it can be machine-generated rather than hand-written.

Find established methods, papers, datasets and tools for each of the
following. For each one: name it, say what it actually does, and say
whether the evidence supports using it **in place of** human labels or only
**alongside** them.

1. **Generation where the spec supplies the label** — producing examples
   from a template or capability description so the category is known by
   construction, rather than generating text and having an annotator judge
   it afterwards.
2. **LLMs as annotators on existing text** — how reliable is it, measured
   how, against what human baseline, and what systematic biases are
   documented.
3. **Minimal pairs and contrast sets** — generating examples that differ in
   exactly the property under test, and validating that they do.
4. **Combining several noisy labelling sources** into one label without
   ground truth, including how each source's reliability is estimated and
   what independence assumptions that requires.
5. **Quality control on synthetic corpora** — how people detect and correct
   for generated text being narrower, cleaner or more archetypal than
   naturally occurring text, and what that does to a measured precision or
   recall figure.

Prefer primary sources with links. Include negative results — "this was
tried and the labels were unusable" is exactly as useful to me as a
success. Flag anything recent that supersedes earlier practice.
