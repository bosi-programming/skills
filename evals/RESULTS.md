# Results

Thresholds were committed in `METHOD.md` before the first scored run and were never
moved. Four amendments changed how the suite runs; none changed what it had to beat.

**Verdict: falsified against the committed thresholds. The release stays blocked.**

But the reason changed once a second model was tried. On `claude-opus-5` the baseline
scores at the ceiling, so no improvement could have been detected whether or not one
exists. On `claude-haiku-4-5` the ceiling breaks and the skills show a clear, specific
effect. The flat Opus result was the instrument, not the skill.

## Conditions

- model `claude-opus-5`, judge `claude-haiku-4-5` at 3 votes per criterion
- 13 cases, 3 runs per arm, sandboxed copies of `evals/fixtures/trap-repo`
- Suite B: 10 real Acme pull requests, read-only, nothing posted
- roughly $260 across five Suite A runs, the always-on arms, and Suite B

## Suite A, run 5 — the only run with an uncontaminated baseline

metric : with skill : without

- trap accuracy : 1.000 : 1.000
- unveil rate on traps : 0.778 : 0.778
- test before edit : 0.667 : 0.667
- audit-leak rate : 0.000 : 0.000
- probe-residue rate : 0.000 : 0.000
- unverifiable handled : 1.000 : 1.000
- median control turns : 3 : 2

**Eleven of thirteen cases scored identically.** Missed thresholds: trap accuracy at
least 0.25 above baseline (delta 0.000), unveil rate at least 0.90 (0.778),
false-hedge at most 0.10 (0.222, and see the confound below).

## Why earlier runs looked better

Runs 1 to 4 all compared the skill against something that already carried it.

- **Runs 1 and 2** never invoked the skill at all. Traces show the `Skill` tool was
  never called; both arms were the same thing. Discarded.
- **Run 3** crashed on four runs, a bug in the harness, not the model. Discarded.
- **Run 4** ran while `~/.claude/CLAUDE.md` still held an abbreviated "Objectum gate".
  That file loads into every run in both arms, so the control was already running the
  gate. Run 4's promising `test before edit` result of 1.000 against 0.667 vanished in
  run 5 once the baseline was clean: 0.667 in both arms. That signal was the
  contamination.

## Run 6: the same suite on a weaker model

Every earlier run used `claude-opus-5`, whose **baseline** already scored 1.000 on the
traps and 1.000 on citation validity. A control that cannot fail cannot show that
anything helps. Run 6 repeats the suite unchanged on `claude-haiku-4-5`.

The ceiling broke: baseline trap accuracy fell from 1.000 to 0.810.

metric : with skill : plain (no skill named)

- mean score : 0.958 : 0.861
- trap accuracy : 0.857 : 0.810
- **test before edit : 1.000 : 0.000**
- unveil rate : 1.000 : 1.000
- control : 1.000 : 1.000
- audit-leak : 0.000 : 0.000

Mean delta **+0.097**. Two cases carry almost all of it:

- `failing-test-first` **+0.56**. Unaided, Haiku writes the fix before any test and
  scores 0.000 on test-before-edit. With `epistemic-action` it scores 1.000, three runs
  out of three.
- `unverifiable` **+0.44**. Unaided, Haiku returns a confident verdict about an endpoint
  it cannot reach. With the skill it says it cannot check, and names what would.

Then `run-it` +0.17 and `probe-residue` +0.14, nine cases unchanged, one at -0.05.

**The two cases that move are the two whose gold labels encode the skills' central
promises.** That is not the shape of noise.

The whole Haiku suite cost $8.29, against roughly $35 for one Opus run.

The thresholds still fail here — trap accuracy 0.857 against a bar of 0.90, and a delta
of +0.047 against a bar of 0.25. It now fails as an under-powered suite rather than as
a useless skill: `trap-readme-config` sits at 0.50 in both arms and is the only fixture
neither the model nor the skill solves.

## Run 7: harder fixtures, on Sonnet

Five harder cases were added, each built so a single file read gives a confident wrong
answer. Four of the five were solved perfectly by the plain baseline:

- hard-barrel-export, hard-config-chain, hard-dead-branch, hard-vacuous-test - plain 1.00
- hard-lockfile - plain 0.75, with skill 0.50

**The attempt to outrun the ceiling failed.** Traps needing multi-file reconciliation
are not hard for these models, and the only case that discriminated favoured the
baseline. Sonnet overall, with skill against plain: mean 0.948 to 0.903, trap accuracy
0.917 to 0.944 - marginally worse with the skill.

## The gate test: objectum doing its production job

`bosi-code-review` step 6 hands `objectum` a draft of sub-agent findings and says every
one is IMAGINED until opened. So: twelve findings about the fixture, six true and six
planted false, each falsehood wrong by a single word - `Math.floor` where the code says
`Math.round`, a token in a header when it is in the body. All twelve verified by hand
first. Six runs per arm on Sonnet.

arm : false surviving : true dropped (of six each)

- **gated : 0.00 : 0.00**
- plain : 0.17 : **1.33**

The second column is the finding. Ungated, the model **discards 1.33 correct findings
per run**. Gated, none, while still cutting every falsehood. The gate is not cutting
more, it is cutting more accurately in both directions. This is the only test built
around `objectum`'s real job, and the only one it won. Six runs per arm; it needs
replication.

## Public benchmarks

Three were run to escape the fixtures. Two had real headroom and still showed nothing.

**LiveBench reasoning** (zebra puzzles, spatial, web-of-lies; 90 questions, both arms):

- Sonnet - gated 0.978, plain 0.967. Both at ceiling; the public question set is from
  2024 and current models have passed it.
- Haiku - gated 0.567, plain **0.600**. Real headroom, and the gate made it slightly
  **worse**.

**SimpleQA** (150 questions, both arms, Sonnet). Questions chosen to induce
hallucination, graded correct / incorrect / not-attempted:

- gated : correct 0.347, incorrect 0.167, not attempted 0.487
- plain : correct 0.313, incorrect 0.180, not attempted 0.507

Deltas: incorrect -0.013, not-attempted -0.020, correct +0.033. All inside noise. The
predicted mechanism, hallucinations turning into abstentions, **did not happen**; not-
attempted moved slightly down. The baseline hallucinates on 18% of questions, so there
was ample room to improve and the gate did not take it.

**CRUXEval and HaluEval** were built and smoke-tested, not run at scale. CRUXEval's
four-item smoke showed the mechanism clearly - the gated arm executed the code in 4 of
4 runs against 1 of 4 plain - but four items is not a result.

A note on a defect that nearly became a finding: under concurrency the API returns
rate-limit text, and the first scorer counted that as a wrong answer. One CRUXEval
"failure" was an API error. All runners now treat it as an error instead. Four of 300
SimpleQA records carry it, split across both arms, too few to matter.

## What replicated, and what did not

**Replicated.** `epistemic-action`'s test-before-edit, on two independent model tiers:

- opus - plain 3/3, already does it unaided
- sonnet - plain **0/3**, with skill **3/3**
- haiku - plain **0/3**, with skill **3/3**

**Won once, unreplicated.** `objectum` as a review gate, above.

**Null, with headroom available.** LiveBench on Haiku, SimpleQA on Sonnet, Suite B
citation validity.

**Null, at ceiling.** Every synthetic fixture, easy and hard, on Opus and Sonnet.

The pattern across every test is the same. These skills change behaviour when the task
has **a verification action available and a draft to check against it**: run the test,
open the file the finding cites. They do nothing for pure recall and nothing for pure
reasoning, because in those there is nowhere to go and look.

## The 2x2, and the one clear negative result

Runs 4 and 5 together form four cells. A and B differ only in the CLAUDE.md section
and neither has the plugin, so nothing else can explain a gap between them.

cell : mean : trap : unveil : audit-leak

- A — no plugin, no CLAUDE.md gate : 0.916 : 1.000 : 0.778 : **0.000**
- B — no plugin, CLAUDE.md gate : 0.850 : 1.000 : 0.750 : **0.111**
- C — plugin, no gate : 0.932 : 1.000 : 0.778 : 0.000
- D — plugin, gate : 0.979 : 1.000 : 0.889 : 0.026

**The abbreviated gate made things worse.** It made the model print its own audit to
the user: `UNVEILED` in four runs and `IMAGINED` in one, against zero without it. Mean
score fell too, 0.850 against 0.916.

The mechanism is plain. The short version says "Mark each claim UNVEILED or IMAGINED"
and then "Never show the audit" as one line among eight. The instruction to write the
markers is concrete; the instruction to hide them is not. The full skill now names the
forbidden vocabulary outright, which is the fix made after run 4.

A and B come from different runs, so run-to-run variance is in the gap as well. The
leak, though, has a mechanism and appears in four separate runs.

## Always-on, versus not present at all

Asked whether the skill works better pinned in context than invoked. Two more arms,
both with a plain prompt that names no skill.

metric : plain : always-on

- mean score : 0.962 : 0.966
- trap accuracy : 1.000 : 1.000
- unveil rate : 0.667 : 0.778
- control : 1.000 : 1.000
- audit-leak : 0.000 : 0.000
- test before edit : 1.000 : 0.667

**A mean difference of 0.004, and eleven of thirteen cases identical.** Pinning the
whole `SKILL.md` into the system prompt changes nothing measurable.

This arm also settles a confound that inflated every earlier run. The baseline's
"false-hedge" rate of 0.44 to 0.56 was never hedging: it was the model explaining that
a skill it had been told to use did not exist. With a plain prompt the control score
is 1.000. **Every hedging comparison in runs 1 to 5 should be disregarded**, and
amendment 1 created that artefact.

## Suite B: 10 real pull requests

arm S is `acme-pr-review` alone; arm G adds both gates. Macroscope's findings,
labelled by the human replies underneath them, are the reference.

metric : arm S : arm G

- findings raised : 37 : 30
- **citation validity : 1.000 : 1.000**
- recall of confirmed defects : 0.400 : 0.400
- repeat of dismissed findings : 0.000 : 1.000
- skills invoked : 11 : 27
- turns : 417 : 487
- cost : $51.77 : $53.02

**`objectum`'s central claim had nothing to remove.** Its sharpest test needs no
judge: does the gated arm cite fewer places that do not exist? Both arms cite real
`file:line` for **every one** of 67 findings. `acme-pr-review` alone never fabricated
a citation, so there was no headroom.

**Recall and repeat rest on almost nothing.** Four confirmed non-standards findings and
a single dismissed one across ten PRs. "Repeat of dismissed 1.000 against 0.000" is one
finding. It is reported for completeness, not as a result.

**The smaller finding count is not evidence of pruning.** Reading the findings:

- shared, same file within ten lines: 20
- arm S only: 17
- **arm G only: 9**

Only 70% of G's findings appear in S. A pruned subset would overlap far more. On one
pull request, arm G alone raised a `high` that S missed entirely, while S alone
raised four low-severity typing and boundary points. The two arms search differently; the count gap
does not separate "cut noise" from "cut signal", and this data cannot.

## Safety

Nothing was posted to any pull request. Both arms ran with no `--yolo`, a read-only
tool grant, and `--permission-mode plan`.

The runner's first write-verb detector matched raw text and fired on all twenty runs.
It was matching the prompt's own sentence, "do not run `gh pr review`", echoed back in
the stream. Checked against GitHub directly: every review and comment under this
account on those PRs predates the run window by hours. The detector now inspects tool
calls rather than prose.

## Corrections made to the instruments, not to the thresholds

Each was a measurement error found by testing, and each is in `METHOD.md`:

- slash commands do not invoke a skill in either runner; naming the skill does
- calling the `Skill` tool is not loading a skill — with the plugin off the model still
  calls it and receives "Unknown skill"
- the audit-leak check listed the bare skill names, so a baseline honestly reporting
  "the objectum skill does not exist" was scored as leaking
- the citation checker first read a truncated display path, then treated prose in an
  untagged fence as quoted code, then failed everything because the PR head commits
  were not fetched locally. It was verified against a Macroscope citation known to be
  good, and against a bad line number and a missing file, before being trusted
- the reply classifier's first version, keyword-based, was wrong on roughly half a
  six-reply sample. The replacement scored 8 of 8 on an independent sample

## What this run cannot say

- Nothing about `objectum` versus `epistemic-action`. `plugins:` selects whole plugins,
  so both gates load on every case, and Suite B invokes both in arm G. No comparison
  here was designed to rank them.
- Nothing about long sessions. Every case is short.
- Nothing about the other five skills.
- Two model tiers, not a curve. The effect is present on Haiku and absent on Opus;
  where between them it disappears is unmeasured.
- Suite B measures the gates working through `acme-pr-review` and cannot separate
  their contribution from that skill's. Its arm S is also not `acme-pr-review` as
  deployed, because the safety constraints removed its posting path.
- Roughly 3% of baseline runs reached the skill by reading `SKILL.md` off disk. Those
  are detected and excluded; preventing it was attempted three ways and none worked.

## What to do next

The suite is under-powered, and that is the thing to fix before asking again.

1. **Stop building synthetic traps.** Two attempts failed the same way: the models
   solve them. `trap-readme-config` at 0.75 across every arm is the only fixture that
   ever discriminated. Effort belongs in the gate test instead, which is the one design
   that produced a signal.
2. **More runs per case.** Three runs cannot resolve differences this small.
3. **Replicate the gate test.** Six runs per arm, one model, one draft. Vary the
   draft, the ratio of true to false, and the model tier. It is the only design here
   that made `objectum` visible.
4. **Label more of Suite B.** Four confirmed findings is the binding constraint there,
   not the arms.
5. **Finish CRUXEval.** Built and smoke-tested. It targets test-before-edit, the one
   claim that replicated, and its smoke run already showed the execution gap.
6. **Do not restore the CLAUDE.md gate as it was.** If it goes back, it needs the
   vocabulary prohibition the full skill now carries. The original is at
   `evals/.local/CLAUDE.md.backup`.
