# Code Style

- Match the formatting, naming, and structure of surrounding code rather than
  introducing new conventions.
- Prefer small, focused changes over large refactors. Don't restructure code
  that isn't related to the task at hand.
- Avoid premature abstractions: don't add helpers, config flags, or layers of
  indirection for hypothetical future use cases.
- Keep functions and modules focused on a single responsibility.
- Default to no comments. Only add a comment when it explains non-obvious
  *why* (a workaround, a subtle invariant, a hidden constraint) — never
  restate *what* the code does.
- Remove dead code instead of commenting it out or leaving unused exports
  "just in case".
- Run the project's formatter/linter (once configured) before considering a
  change complete, and fix any issues it reports in the touched files.
