# Git Workflow

- Develop on feature branches; do not commit directly to `main`.
- Write commit messages that explain *why* a change was made, not just what
  changed. Keep the summary line concise.
- Create focused commits: one logical change per commit rather than bundling
  unrelated work.
- Never use destructive git operations (`reset --hard`, `push --force`,
  `clean -f`, branch deletion, etc.) without explicit user confirmation.
- Never amend or rewrite commits that have already been pushed, unless
  explicitly asked to.
- Don't skip git hooks (`--no-verify`) or bypass commit signing
  (`--no-gpg-sign`) unless explicitly requested.
- Open pull requests as drafts by default, and include a short summary and a
  test plan in the description.
