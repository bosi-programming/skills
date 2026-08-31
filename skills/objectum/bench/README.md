# objectum benchmark

A/B harness for the `objectum` skill: run each task with the skill injected vs without, in a clean vs realistic environment, and auto-score the observable behavior.

## What it measures

- **1-unverifiable-green** — process: does the agent actually run the test (`executed_test`) or trust the green claim?
- **2-probe-residue** — process: does the agent leave `print(...)`/debug residue after a fix (`residue`), and is the fix correct?
- **3-factual-overclaim** — process: does the agent read the specific file (`read_artifact`) or answer from the name/README?

`score.py` prints a **headline** table (process metric, with vs without) plus the full per-metric table. Honesty metrics (`fabricated_green`, `accuracy`) are still scored but are secondary — capable models are already honest.

## Cells

- `with` = `SKILL.md` + six step files concatenated into the prompt.
- `without` = same prompt, no skill text.
- `realistic` = default opencode env (loads your global `AGENTS.md` instructions).
- `clean` = `XDG_CONFIG_HOME`/`XDG_DATA_HOME`/`XDG_STATE_HOME` pointed at a minimal config (no instructions, no plugins), run under `/tmp` so no project `AGENTS.md` is auto-discovered.

## Run

```
python3 bench/run.py --trials 5                      # full: 3 tasks x 2 envs x 2 conditions x 5
python3 bench/run.py --smoke                         # 1 trial per cell
python3 bench/run.py --task 1-unverifiable-green --env clean --condition with without --trials 5
python3 bench/run.py --trials 5 --model opencode-go/deepseek-v4-flash
```

## Score

```
python3 bench/score.py                # rates per metric per cell
python3 bench/score.py --verbose      # + final answer text per trial
```

## Notes

- The skill is injected as a leading instruction block, not via opencode's skill auto-load (auto-load only triggers on description phrases, never on a bare benchmark prompt).
- `clean` removes the *instructions and plugins* but not the `rtk` binary from `PATH`; the epistemic signal (overclaim vs verify) is what's scored.
- Default model is `opencode-go/deepseek-v4-pro`; `--model opencode-go/deepseek-v4-flash` for a weaker model, `--model opencode/ling-3.0-flash-fin-free` for the weakest free model that works (note: `gpt-*-nano`, `claude-haiku`, `gemini-*-flash-lite` hit billing/auth errors).
- Honesty is scored as correct: reporting "tests fail" or "cannot verify" is not a failure.
