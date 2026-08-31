# epistemic-action benchmark

A/B harness for the `epistemic-action` skill: run each task with the skill injected vs without, in a clean vs realistic environment, and auto-score the observable behavior.

## What it measures

- **1-run-it** — process: does the agent *run* the thing (`executed`) instead of predicting the answer from the README/name?
- **2-failing-test-first** — process: does the agent run the failing test *before* editing the source (`test_before_edit`), and is the fix correct (`bug_fixed`)?
- **3-read-the-thing** — process: does the agent *read* the file that settles the answer (`read_artifact`, keyed to `config.py`) instead of stopping at the named file (`validate.py`) or the README?

`score.py` prints a **headline** table (process metric, with vs without) plus the full per-metric table. Accuracy metrics are still scored but are secondary — capable models are already accurate; the skill's effect is on the process.

## Cells

- `with` = `SKILL.md` concatenated into the prompt (epistemic-action has no `steps/`).
- `without` = same prompt, no skill text.
- `realistic` = default opencode env (loads your global `AGENTS.md` instructions).
- `clean` = `XDG_CONFIG_HOME`/`XDG_DATA_HOME`/`XDG_STATE_HOME` pointed at a minimal config (no instructions, no plugins), run under `/tmp` so no project `AGENTS.md` is auto-discovered.

## Run

```
python3 bench/run.py --trials 5                      # full: 3 tasks x 2 envs x 2 conditions x 5
python3 bench/run.py --smoke                         # 1 trial per cell
python3 bench/run.py --task 1-run-it --env clean --condition with without --trials 5
python3 bench/run.py --trials 5 --model opencode-go/deepseek-v4-flash
```

## Score

```
python3 bench/score.py                # rates per metric per cell
python3 bench/score.py --verbose      # + final answer text per trial
```

## Notes

- The skill is injected as a leading instruction block, not via opencode's skill auto-load (auto-load only triggers on description phrases, never on a bare benchmark prompt).
- `clean` removes the *instructions and plugins* but not the `rtk` binary from `PATH`; the epistemic signal (run vs predict, read vs name) is what's scored.
- Default model is `opencode-go/deepseek-v4-pro`; `--model opencode-go/deepseek-v4-flash` for a weaker model.
- `test_before_edit` is derived from transcript ordering: the first test-run bash command must precede the first `edit`/`write` of `calc.py`.
