# Testing

- Add or update tests for any behavior change, bug fix, or new feature once a
  test framework is established for this project.
- Prefer testing observable behavior (inputs/outputs, public APIs) over
  internal implementation details.
- Run the relevant test suite for any files you touch before considering a
  task complete, and fix failures introduced by your change.
- Don't weaken, skip, or delete existing tests to make a change pass unless
  the underlying behavior genuinely changed and the test is now incorrect.
- For UI changes, manually exercise the feature (e.g. via a dev server) in
  addition to any automated tests, and check the golden path plus obvious
  edge cases.
