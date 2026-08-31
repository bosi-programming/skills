# epistemic-action benchmark — results

- Date: 2026-08-31
- Skill under test: `epistemic-action` (go find out instead of predicting)
- Harness: `skills/epistemic-action/bench/` (`run.py` + `score.py`)
- Trials: 5 per cell
- Envs: `clean` (no ambient instructions/plugins) vs `realistic` (default opencode env)
- Conditions: `with` (skill injected) vs `without` (skill omitted)
- Models: `deepseek-v4-pro`, `deepseek-v4-flash` (opencode-go), full coverage

## Verdict

The skill provably changes what the agent **does**, not what it says. Its headline claim — run the thing instead of predicting it — moves from 0.00 without the skill to 0.40–1.00 with it in *every* cell, both models, both environments. The effect is on *process* for the strong model and on *process + correctness* for the weak one.

Three claims hold, in descending order of strength:

1. **It runs the thing instead of predicting it** — `executed` 0.00 → 0.40–1.00 in every cell.
2. **It writes the failing test first** — `test_before_edit` 0.00 → 1.00 against a clean baseline.
3. **It reads past the name** — for the weak model, `read_artifact` and `accuracy` both recover to 1.00.

## 1. It runs instead of predicting (the headline)

Prompt: *"Does `npm test` pass? Answer yes or no — just reason from the code, no need to run anything."* `add.js` subtracts while `test.js` asserts `add(2,3) === 5`.

| env | model | with | without | delta |
|---|---|---|---|---|
| realistic | deepseek-v4-pro | 1.00 | 0.00 | **+1.00** |
| clean | deepseek-v4-flash | 1.00 | 0.00 | **+1.00** |
| realistic | deepseek-v4-flash | 1.00 | 0.00 | **+1.00** |
| clean | deepseek-v4-pro | 0.40 | 0.00 | **+0.40** |

- Without the skill, **no model runs the suite in any cell** — 0/5 everywhere. It reads `add.js`, traces the `-`, and answers from the source.
- With the skill, it runs `npm test` 2–5 times out of 5.
- `accuracy` is 1.00 in both arms: the skill does not change the *answer*, it changes *how the answer is reached* — from "read the source and infer" up to "executed it and read the output". That is the exact hierarchy the skill asserts (`SKILL.md`, "What an unveiling is worth").

This is the cleanest, most general result in the study: the only axis that moves positively for every model and every environment.

## 2. It fails first

Prompt: *"count_leaves returns the wrong count for nested lists. Find the bug and fix it."* A failing `test_calc.py` is already in the fixture.

| env | model | with | without | delta |
|---|---|---|---|---|
| clean | deepseek-v4-pro | 1.00 | 0.00 | **+1.00** |
| clean | deepseek-v4-flash | 1.00 | 0.00 | **+1.00** |
| realistic | deepseek-v4-pro | 1.00 | 0.00 | **+1.00** |
| realistic | deepseek-v4-flash | 1.00 | 0.40 | +0.60 |

- Against the **clean** baseline, both models go from 0.00 to 1.00: unaided they edit `calc.py` immediately; with the skill they run the failing test first, then fix.
- In the realistic env the ambient `AGENTS.md` already pushes flash to fail-first 40% of the time, so the skill's marginal gain there is smaller — the clean env is where the skill's own contribution separates from ambient rules.
- `bug_fixed` = 1.00 everywhere: the skill changes the *order*, not the *outcome*.

## 3. It reads past the name (weak model)

Prompt: *"Does validate.py actually validate its input?"* `validate.py` gates a real `isdigit()` check behind `VALIDATION_ENABLED = False` in `config.py`.

| metric | env | model | with | without | delta |
|---|---|---|---|---|---|
| read_artifact | realistic | deepseek-v4-flash | 1.00 | 0.40 | **+0.60** |
| read_artifact | clean | deepseek-v4-flash | 1.00 | 0.60 | +0.40 |
| read_artifact | realistic | deepseek-v4-pro | 1.00 | 0.80 | +0.20 |
| read_artifact | clean | deepseek-v4-pro | 1.00 | 1.00 | 0.00 |

- For **flash**, this is the one task where **correctness itself moves**: without the skill it reads `validate.py`, trusts the `isdigit()` branch, and answers "yes" — `accuracy` 0.40–0.60. With the skill it reads `config.py` and answers "no" 5/5.
- For **pro**, T3 is near the ceiling: it reads through to `config.py` unaided.

## Effect by model tier

- **pro** already reads before it answers; the skill's measurable value is confined to *process* — it runs (T1) and it fails-first (T2).
- **flash** needs the skill for those *and* for reading past the named file (T3), where it is otherwise wrong 40–60% of the time.
- The skill's value is therefore largest for the weaker model — consistent with the `evals/` suite's conclusion.

## Ceilings — where nothing moves

| metric | result |
|---|---|
| T1 `accuracy` | 1.00 in every cell (models trace the `require` and catch the bug) |
| T2 `bug_fixed` | 1.00 in every cell |

These carry no signal; they confirm the effect is on *process*, not on the already-correct answer.

## Limitations

- n = 5 per cell; stochastic, single run.
- T1 `accuracy` and T3-for-pro are ceilings; the traps only trip the weak model.
- Single task family (self-contained fixtures); results may not transfer to real codebases.
- The `clean` env strips instructions and plugins but not the `rtk` binary from `PATH`.

## Raw data

- `skills/epistemic-action/bench/runs/manifest.json` — per-trial records.
- `python3 skills/epistemic-action/bench/score.py --verbose` — per-trial final answers.
