# Contributing to AutoBus

This project's own quality review flagged version-control hygiene as an area
to improve: the history at the time was two large, non-descriptive commits,
which makes it hard to review a change in isolation, bisect a regression, or
understand *why* a particular line exists. This document is the fix going
forward — a short, concrete convention rather than a general "write good
commits" reminder.

## Commit conventions

- **One logical change per commit.** A commit should do one thing:
  "add centralized configuration," "add audit tamper-detection tests,"
  "document the improvements in README" — not all three bundled together.
  If you find yourself writing "and" in a commit summary, it's probably two
  commits.
- **Commit as you go, not at the end.** Don't stage a day's worth of
  unrelated edits and split them retroactively — that's error-prone and
  tends to regress into the "two large commits" pattern this document
  exists to avoid. Commit each change when it's complete and passing.
- **Write descriptive summaries.** The summary line should say what changed
  and, where it's not obvious, why:
  - Good: `Add pydantic-settings config module, wire into LyzrGovernance`
  - Not useful: `Debugging`, `fix`, `updates`
  A useful rule of thumb: `git log --oneline` should read like a changelog
  a reviewer could skim without opening a diff.
- **Prefer the imperative mood** ("Add X", "Fix Y") to match the style
  `git log` and `git shortlog` are designed around.
- **Keep formatting/refactor commits separate from behavior changes.** A
  pure rename or reformat should never be in the same commit as a logic
  change — mixing them hides the logic change in a large diff.

## Before opening a pull request

- Run the test suite locally: `cd backend && pytest -q`. New logic needs a
  test that would fail without it; a bug fix needs a regression test that
  reproduces the bug.
- Run the linter: `ruff check backend agents --select E9,F63,F7,F82`.
- If you touched configuration (`backend/config.py`) or anything that reads
  an environment variable, check `.env.example` is still accurate.
- Keep the PR description scoped to what the PR actually does — link the
  issue/rubric item it addresses if there is one, rather than re-explaining
  the whole feature area.

## What CI checks

`.github/workflows/ci-cd.yml` runs on every push and pull request against
`main`: linting, a full source compile, the test suite (with a coverage
report uploaded as a build artifact), and a Docker build. A pull request
that fails any of these should be fixed before merge, not merged and
fixed later — the whole point of the pipeline is to catch that before it
reaches `main`.
