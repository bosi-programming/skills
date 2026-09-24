# Tests

Eleven rules, and the failures they exist to catch. A test is code that exists to fail when the behaviour it guards breaks; every rule here serves that. The list at the end is what to call out in review rather than fix quietly.

## 1. Test behaviour, not implementation

Assert on what a caller can see: the return value, the rendered output, the message sent, the row written. A test that checks which private helper ran, or in what order, breaks on every refactor and passes through real bugs.

## 2. Names that state the scenario and the outcome

`returns 404 when the account is closed` tells a reader what broke from the test runner's output alone. `test account 3` sends them into the file to find out.

## 3. One reason to fail

Each test checks one behaviour. When a test asserts five unrelated things, the first failure hides the other four, and the name can no longer say what it covers.

## 4. Arrange, act, assert, and no logic

Set up, do the one thing, check the result, in that order. No `if`, no loops, no `try`/`catch` inside a test: logic in a test is code that needs its own test, and a branch means some runs check less than the name promises.

## 5. Deterministic

The same code gives the same result on every run. No real clock, no unseeded randomness, no network, no `sleep` waiting for something to settle. Inject time and randomness, and wait on a condition rather than a delay.

## 6. Isolated

No test depends on another having run first, or on state one left behind. Each test builds what it needs and cleans up what it made, so the suite passes in any order and any subset.

## 7. Mock at the edges, not the unit

Stub what the code under test does not own: the network, the clock, a third-party API. Never mock the unit under test, and prefer a real collaborator over a mock of it when the real one is fast and deterministic.

## 8. Specific assertions

Assert the value you expect: `toEqual({ status: 'closed' })`, not `toBeTruthy()`. A snapshot on its own is not an assertion about behaviour; it records whatever the code did, right or wrong.

## 9. Error paths and edge cases

The happy path is the one least likely to be broken. Empty input, the boundary value, the failed call and the missing permission each get a test.

## 10. A bug fix comes with a test that failed first

Write the test that reproduces the bug, watch it fail, then fix. A regression test written after the fix, and never seen red, may not test the bug at all.

## 11. No tautological tests

A test that cannot fail proves nothing. Write expected values out by hand; never compute them with the code under test. Don't assert that a mock returns what it was told to return, or that a constant equals itself. If breaking the code would not turn the test red, the test is decoration.

## Red flags

Call these out in review:

- a test with no assertion, or one whose only assertion is that no error was thrown
- `.skip`, `.only`, `xit`, `fdescribe` or any focus or skip marker left in
- commented-out assertions or commented-out tests
- an expected value produced by the function under test
- an assertion on a value the test's own mock supplied
- `sleep`, fixed timeouts, or `Date.now()` and `Math.random()` used without being controlled
- tests that pass only when run in a certain order
- a mock of the module the test claims to test
- test data far larger than the case needs, hiding which field matters
- a snapshot as the only check on behaviour
- changed behaviour with no test added or changed
