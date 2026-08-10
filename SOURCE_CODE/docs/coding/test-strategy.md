# Test Strategy

## General Testing Rules
- Every function that contains logic should have at least one test.
- Tests should be independent — no test should depend on another test running first.
- Test the happy path, the edge cases, and the error cases.
- Use descriptive test names that explain what is being tested and what is expected.

## HTML / UI Testing
- Verify all buttons render and are clickable.
- Verify all input fields accept expected values and reject invalid ones.
- Verify the UI state changes correctly after user interactions.
- Verify timer/countdown logic starts, stops, and resets correctly.

## Python Testing
- Use pytest as the test framework.
- Place tests in a tests/ folder mirroring the source structure.
- Mock all external dependencies (API calls, file system, database).
- Aim for above 90% code coverage on core logic functions.

## SQL Testing
- Verify INSERT, UPDATE, DELETE operations with SELECT to confirm state.
- Test foreign key constraints are enforced.
- Test that indexes improve query performance on large datasets.

## Deployment Readiness
- All tests must pass before code is considered ready.
- No hardcoded credentials, no debug print statements, no commented-out code blocks.
- The code must run without modification on a clean machine with dependencies installed.
