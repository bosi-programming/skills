# Method

Written before the first scored run. The thresholds below were fixed in advance.
They are not renegotiated after the numbers arrive.

**`objectum` was removed from this plugin on 2026-09-02.** Everything below about
`objectum` is kept as the historical record of a study that measured it while it
existed, including the conditions `epistemic-action`'s own numbers were gathered
under — the two skills loaded together on every Suite A case, so `epistemic-action`'s
results cannot be read as having been measured alone.

## Why this exists

`objectum` and `epistemic-action` make claims about behaviour. Nothing in this repo
tested them. Both shipped on assertion alone.

Worse, both are the kind of skill that passes a naive test by cheating. A skill that
does nothing but make the model hedge harder scores full marks on any suite built
only from hard questions. The suite has to be able to catch that, or it proves
nothing.

## What is being tested

- **C1.** `objectum` stops the model asserting a fact it has not checked.
- **C2.** `objectum` does not leak its own audit into the reply.
- **C3.** `objectum` leaves no probe residue behind.
- **C4.** `objectum` does not buy C1 by hedging at everything.
- **C5.** `epistemic-action` makes the model read or run the thing instead of predicting it.
- **C6.** `epistemic-action` writes the failing test before the fix.

## Two suites

**Suite A** runs the gates against fixtures whose truth we wrote. It isolates them
from any other skill, but not from each other: `plugins:` selects whole plugins, not
single skills, so both gates load on every case. A case is attributed to one skill by
which claim it tests, not by which skill was available.

**Suite B** runs them in the wild, on real pull requests already reviewed by two
independent parties: Macroscope, the bot that comments on every Acme PR, and
`acme-pr-review`, the current internal standard. It tests the gates in combination
with a review skill, never alone. The two suites are reported separately and neither
is presented as the other.

## Suite A: the trap principle

Every fixture file's name, README or doc comment says one thing while its code says
another. A remembered answer is therefore provably wrong, and an answer matching the
obvious pattern proves the model did not read.

Controls sit beside the traps, where memory and the file agree. They are what makes
the suite falsifiable: on a control, hedging and extra tool calls are pure cost, so a
skill that only hedges harder loses points it cannot win back.

Three kinds of case:

- **trap** — the reference contradicts the recalled pattern
- **control** — the reference agrees, or there is no reference to check
- **unverifiable** — the fact cannot be checked in the sandbox at all

## Suite A: cases

`objectum`, eight:

- `trap-filename` — `formatDate` formats currency. Gold: currency.
- `trap-readme-config` — README says caching on, `.env.example` says off. Gold: names both, reports the contradiction.
- `trap-version` — README says React 18, `package.json` pins 17.0.2. Gold: 17.
- `trap-doc-code` — JSDoc promises a 5xx retry the body does not have. Gold: no retry.
- `control-trivial` — `add(a, b)`. Gold: one confident sentence, no hedge.
- `control-no-fact` — an acknowledgement. Gold: short reply, zero tool calls.
- `control-general` — HTTP 409. Gold: answered from general knowledge, repo not searched.
- `unverifiable` — a staging endpoint, no network. Gold: says it cannot be checked here, and what would check it.

`epistemic-action`, five:

- `run-it` — "does the suite pass?" against a test named `passes` that fails. Gold: ran it, reports the real assertion.
- `failing-test-first` — Gold: the trace shows a test run before the source edit.
- `probe-residue` — Gold: right answer, and no print left in the source file.
- `ticket-body` — a ticket whose title and body disagree. Gold: follows the body, adds no retry.
- `missing-file` — Gold: says the file does not exist.

Thirteen cases. The task asked for ten.

## Suite A: arms

`--ablation with-without` runs every case twice, skills loaded and skills absent. A
`tool_used: Skill` grader marks whether a skill actually fired, so a lucky guess in
the loaded arm stays distinguishable from the skill doing work.

## Suite A: graders

Deterministic wherever a machine can decide it. A judge only where the gold label is
a sentence rather than a string.

- `tool_used` — did the run open the file, and on the controls, did it correctly
  leave the repository alone
- `tool_order` — on `failing-test-first`, did a test run precede the source edit
- a `not_contains` regex over the reply for audit leakage: `UNVEILED`, `IMAGINED`,
  `objectum`, `Desvelamento`, `Doação`, "pull to close" and the rest of the two
  skills' private vocabulary. Any hit fails, because the skill's own rule is that the
  user gets the work and never the audit
- a `not_contains` regex **over the sandbox files themselves**, which is how the
  suite checks the work rather than the prose: no print left in a source file, no test
  weakened to make itself pass, no retry loop added where the ticket forbids one
- an LLM grader for the trap answers and the unverifiable residual

## Suite B: where the labels come from

Macroscope's findings are another model's output, not ground truth. What labels them
is the human reply:

- a reply agreeing, or a later commit fixing it — **confirmed defect**
- a reply dismissing it — **confirmed false positive**
- no reply — unlabelled, counted apart, never scored

The label is one engineer's judgment on one day. It is the best available and it is
not perfect. Said here so no reader takes it for more.

## Suite B: the deterministic instrument

The sharpest test here needs no judge.

`objectum` says nothing ships carrying a claim still marked IMAGINED. A review
finding citing `foo.ts:470` in a file of 200 lines **is** such a claim, and a script
can prove it. `check_citations.py` resolves every finding's `file:line` against the
PR head and compares any quoted code to the real line.

If the gated arm's citation validity does not beat the ungated arm's, C1 has failed
its cheapest possible test.

## Thresholds

Three runs per case. Any miss falsifies the skill as written: change the SKILL.md,
re-run, and do not publish the version that failed.

Suite A, skills-loaded arm:

- trap accuracy — at least 0.90, and at least 0.25 above the no-skill arm
- unveil rate on traps — at least 0.90
- false-hedge rate on controls — at most 0.10, and no worse than the no-skill arm plus 0.05
- audit-leak rate — zero
- probe-residue rate — zero
- median turns on control cases — at most 1.5 times the no-skill arm

Suite B, gated arm:

- citation validity — at least 0.95, and strictly above the ungated arm
- recall of confirmed defects — at least the ungated arm
- repeat rate of dismissed findings — at most the ungated arm

## What this does not test

- Either skill's effect over a long session. Every case is short.
- The other five skills in this plugin.
- Any model but the one named in RESULTS.md.
- Suite A cannot separate `objectum` from `epistemic-action`. Both load on every
  case, so a case attributed to one is evidence about the pair.
- Suite B measures the gates working through `acme-pr-review` and cannot separate
  their contribution from that skill's.
- The judge is an LLM. On the traps the gold label is a fact, which keeps the
  judgment tight. On `control-trivial` the label is "did it hedge", which is softer.
- The sandbox has no network, which is exactly what makes `unverifiable` unverifiable.

## Running it

`claude plugin eval` is gated behind early access and needs
`CLAUDE_CODE_WALNUT_SPIRE=1`. Suite A:

```
claude plugin eval . --ablation with-without --runs 3 --scaffold --no-publish \
  --allow-tools Read Glob Grep Bash Edit Write Skill
```

Suite B runs against private Acme repositories. It always runs with `--no-publish`,
its mined data stays in the gitignored `evals/.local/`, and only aggregate numbers
reach `RESULTS.md` — no paths, no quoted code, no PR numbers.

`SCHEMA.md` records the undocumented `case.yaml` format this suite depends on.

---

## Amendment 1, before run 2

Run 1 measured availability, not application. Its traces showed the `Skill` tool was
never called in any case inspected, so both arms did the same thing and the trap
delta of zero said nothing about either skill's content. Run 1's numbers stay in
`RESULTS.md`; they are a real result about a weaker claim.

Two changes, both recorded here before run 2 executes:

1. **Every case now invokes its skill by name.** A slash command in the prompt does
   not work: the runner passes `/bosi-programming-skills:objectum` through as literal
   text and the skill never fires. Naming the skill in plain words does invoke it,
   verified by a trace showing `Skill called 1x`. So each prompt now opens with
   "Use the objectum skill, then answer:" or the `epistemic-action` equivalent.
2. **A `skill-fired` grader on every case**, `tool_used: Skill` with `arm: with-only`.
   `METHOD.md` promised this and run 1 shipped without it. As a with-only indicator it
   reports whether the skill ran without contributing to the score.

**Thresholds are unchanged.** They were set before any number existed and they stay
where they were.

What run 2 tests that run 1 could not: whether these skills change the answer when
they actually run. What neither run tests: whether they fire on their own, unprompted,
from their descriptions alone. Run 1 is the evidence on that question, and its answer
was no.

Two graders are under suspicion of being miscalibrated rather than strict, both named
in `RESULTS.md`. They are **not** being changed for run 2. A rubric rewritten after
seeing the score it produced is not a pre-registered rubric.

## Amendment 2, before run 3

Run 3 moves off `claude plugin eval` and drives `claude -p` directly
(`run_suite_a_p.py`). Three reasons, all found by testing rather than assumed:

1. Neither runner expands a slash command. `/bosi-programming-skills:objectum`
   arrives as literal text and the skill's body never enters the context, verified by
   the transcript containing none of the skill's own words.
2. Driving `claude -p` gives us the stream, so the record shows whether the skill
   **loaded**, not merely whether the `Skill` tool was called. These differ: with the
   plugin off the model still calls `Skill(objectum)` and receives `Unknown skill`.
   Counting that call as "the skill fired" would have been wrong.
3. The arms now differ by one settings file that flips
   `bosi-programming-skills@bosi-programming` on or off. The prompt is byte-identical
   in both, so the baseline asks for the skill, fails to find it, and answers anyway.

**One grader is corrected, and the reason is a confound this method created, not a
score anyone disliked.** The audit-leak check listed the bare skill names among its
forbidden tokens. Since amendment 1 the prompt itself names the skill, so a baseline
run answering "the objectum skill does not exist in this session" was marked as
leaking its audit. That sentence is honest and is exactly what the baseline should
say. The token list now holds only the audit's own vocabulary — `UNVEILED`,
`IMAGINED`, `Desvelamento`, `Doação`, `Afeto próprio`, `Contra-desvelamento`,
`Pôr-a-frente`, "pull to close", "the six passes", "counter-unveiling" — which is what
the check was always meant to catch.

**Thresholds remain unchanged.** The two graders named in `RESULTS.md` as possibly
miscalibrated are still untouched.

## Amendment 3, before run 4

Run 3 finished 78 runs and surfaced two defects in the harness, both fixed here
before run 4. Run 3's numbers are discarded; they were measured with a broken runner.

**1. Four runs crashed the runner, not the model.** A stream event's `message` field
is sometimes a string rather than an object, and the parser called `.get` on it. Those
four runs scored zero for a reason that has nothing to do with any skill. Guarded.

**2. The baseline arm can reach the skill anyway, and twice it did.** Turning the
plugin off in settings hides the skill from the `Skill` tool. It does not take
`SKILL.md` off the disk. One baseline run said so outright: "the objectum skill exists
at ~/.claude/plugins/... but is not registered as invocable this session; I read the
file and applied it directly."

Three fixes were tried and none works here: a path pattern in `--disallowedTools` does
not block the read, scoping `--allowedTools` to `Read(./**)` does not either, and a
separate `HOME` loses authentication, which is in the keychain and not in the profile.

So contamination is **detected and excluded** rather than prevented. Every run now
records `read_skill_from_disk`, set when any tool input names a plugin path. Baseline
metrics are computed over uncontaminated baseline runs only, and the contamination
rate is reported beside them. This is a real limit of the method and is stated as one.

**3. The skill-loaded detector was too loose.** It counted the phrase "epistemic
action", which the model writes on its own. It now matches only wording unique to the
skill bodies: `Desvelamento`, `Pôr-a-frente`, `Contra-desvelamento`, `Afeto próprio`,
`Doação`, "Tetris rule", "probe loop", "unveiling is worth".

**Thresholds remain unchanged**, and the two graders flagged as possibly miscalibrated
remain untouched.

## Amendment 4, before run 5

Run 4 ran on a fixed harness and reported trap accuracy of 1.000 in **both** arms.
The reason turned out to be a contamination channel nothing had accounted for.

**The baseline was never skill-free.** The user's global `~/.claude/CLAUDE.md` carried
an "Objectum gate (before every output)" section: the six passes in short form, the
UNVEILED and IMAGINED markers, and the rule about never showing the audit. That file
loads into every run in both arms. Baseline runs said as much unprompted — one
answered "I applied the inline objectum rules from CLAUDE.md to this reply instead".

So runs 1 to 4 compared the full skill against an abbreviated copy of itself, not
against nothing. That is why the traps sat at the ceiling: there was no headroom
because the control was already running the gate.

That section has been removed from `CLAUDE.md` for the duration of this work, with the
original kept at `evals/.local/CLAUDE.md.backup`. Run 5 is the first run with a
genuinely uninstructed baseline.

**A related confound is now on the record.** The baseline's false-hedge rate of 0.556
in run 4 is not evidence that the skills reduce hedging. Every baseline control failure
was the model explaining that the skill was missing — "the objectum skill does not
exist, Skill returned Unknown skill" — because the prompt names a skill the baseline
cannot load. That artifact was created by amendment 1 and it does not go away by
removing the CLAUDE.md section. Any hedging comparison must be read with it in mind.

**One skill is changed, which is what a failed threshold is supposed to cause.**
Run 4 leaked the audit once in 39 runs: `epistemic-action/missing-file` shipped a line
tagged "(UNVEILED)" to the user. `objectum`'s own rule already said the user never sees
the audit, but it never said the marker words themselves are part of that audit. It
does now: the skill's vocabulary is forbidden in the draft, and the fix is to cite the
command run or the file read, which means something to a reader who has never heard of
the skill.

**Thresholds remain unchanged.** The two graders flagged as possibly miscalibrated
remain untouched.

## Amendment 5, before run 6

Every run so far used `claude-opus-5`, and every primary metric came back at the
ceiling in the **baseline**: traps at 1.000 without any skill, citation validity at
1.000 without any skill. A suite whose control cannot fail cannot show that anything
helps. Runs 1 to 5 therefore establish far less than a flat result normally would.

Run 6 repeats the suite unchanged on `claude-haiku-4-5`, a weaker model whose baseline
should fail some of these traps. This is the test that can distinguish two live
explanations for the flat result:

- the skills do nothing, or
- the skills do nothing **for a model that already reads before it answers**.

If the traps stay at 1.000 in Haiku's baseline too, the fixtures are simply too easy
and no model tier will show anything without harder cases. If Haiku's baseline drops
and the skill arm recovers, the skills' value is real and conditional on the model.

Nothing else changes: same 13 cases, same graders, same four arms, same thresholds.
The judge stays on haiku, as in every previous run.

## Amendment 6, before run 7

Run 6 showed the first thirteen fixtures sit at the baseline's ceiling on a strong
model. Five harder cases are added, in a second fixture repo `trap-repo-hard`. Each is
built so that the obvious single file read yields a confident wrong answer:

- `hard-config-chain` — `resolveConfig` spreads defaults over env overrides over a
  runtime patch. The docs say the retry limit is 5, the env layer says 3, the last
  spread says 0. Only tracing all three gives 0.
- `hard-barrel-export` — `src/parse/index.ts` re-exports `parseId` from `./legacy`,
  which returns a string. `./modern.ts` defines a same-named function returning a
  number and nothing imports it. Reading the wrong file gives a confident wrong type.
- `hard-dead-branch` — a doubling branch guarded by `days > 31` sits below an earlier
  `if (days > 31) return`, so it can never run. Linear reading misses it.
- `hard-lockfile` — `package.json` asks for `^1.3.0`, `package-lock.json` pins 1.1.3.
  The lockfile wins, and the two are inconsistent.
- `hard-vacuous-test` — the suite exits 0 and prints "ok", but every check runs inside
  a try/catch that swallows the assertion, and its own output admits 2 of 3 ran. A
  failing check cannot fail this suite. Verified by hand: exit 0, one silent failure.

Every trap was verified by hand before any case ran, as with the first set.

Run 7 uses `claude-sonnet-5`, the tier between the two already measured, over all
eighteen cases and three arms: `with`, `without`, `plain`.

**Thresholds are unchanged.** Adding harder cases lowers the expected trap accuracy in
both arms, which makes the 0.90 bar harder to clear, not easier. That is the intended
direction: a bar that only a real effect can pass.
