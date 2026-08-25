# Example Project README

Please note that this project provides a small command-line tool for auditable
document rewrites. It is important to note that the tool exists in order to
make use of a fixed rule pipeline rather than a black-box model, and the CLI
is able to run entirely offline.

## Installation

```bash
pip install example-project
example-project run docs/input.md --out artifacts/
```

## Status

TODO: document the config file format before the next release.

It was decided that the CLI defaults to dry-run mode; utilize the `--apply`
flag to write changes to disk.

This paragraph intentionally runs long because the repo-docs pack needs a
sentence whose word count crosses its review threshold, which is set higher
than the scientific-writing pack's threshold since technical documentation
often strings together compound clauses, conditional asides, and cross
references to other sections that would otherwise get flagged too eagerly by
a stricter limit tuned for prose instead of reference material.
