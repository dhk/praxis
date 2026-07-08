---
name: release-helper
description: This skill helps you with releases and versioning and various related tasks.
allowed-tools: Read, Grep, Bash
---

# Release helper

Please note that this skill automates the release process end to end.

## Workflow

1. simply run the version bump script to update the changelog and tags.
2. utilize `git log` to collect the commits since the last release (v2.3.1).
3. leverage the changelog template in `reference/template.md` to draft notes.
4. In the event that CI is red, stop and report before tagging.
5. Push the tag and open the release PR (see https://example.org/release-docs and [RFC-12]).

## Notes

The 3 most recent releases took 45 minutes each; target 30 minutes.
