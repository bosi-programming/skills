# Reproducing the epistemic-action benchmark (and benchmarking other skills)

This is a runbook for an LLM agent. It explains how the `epistemic-action` benchmark works, how to reproduce the study, and how to adapt it to a different skill or build new task families.

## 1. What the harness is

A/B harness that runs the same prompt with the skill injected vs not, across two environments, and auto-scores the observable behavior (tool calls + final text + files). No LLM judge.

Components (under `skills/epistemic-action/bench/`):

- `run.py` — orchestrator. Builds trial dirs, invokes `opencode run` headless, records `runs/manifest.json`.
- `score.py` — auto-scorer. Reads the manifest, computes per-metric rates, prints a headline (process metric, with vs without) + full tables.
- `tasks/` — one directory per task, each with `fixture/`, `prompt.txt`, `truth.json`.
- `runs/` — generated trial dirs + `manifest.json` (git-ignored).

## 2. Prerequisites

- `opencode` CLI on PATH, with valid auth (`~/.local/share/opencode/auth.json`).
- A model that can be invoked via `-m <provider>/<model>` (see `opencode models`).
- Python 3 (stdlib only; no deps).

## 3. Task format

Each `tasks/<name>/` contains:

```
fixture/          # files copied verbatim into the trial dir
prompt.txt        # the task prompt (one line)
truth.json        # task metadata
```

`truth.json` fields by `kind`:

| kind | fields |
|---|---|
| `run-it` | `task`, `kind`, `expected` (`"yes"`/`"no"`) |
| `failing-test-first` | `task`, `kind`, `check_cmd` (shell command, exit 0 = fixed) |
| `read-the-thing` | `task`, `kind`, `expected`, `artifact` (filename to read) |

## 4. How `run.py` works

Four dimensions per trial: `condition` × `env` × `model` × `trial`.

- **condition `with`**: the prompt is prefixed with `"Apply the following instructions to yourself, then complete the task."` + the skill's `SKILL.md`, then `TASK:` + the task prompt. `epistemic-action` has no `steps/`, so the injected block is just `SKILL.md`.
- **condition `without`**: just the task prompt.
- **env `clean`**: `XDG_CONFIG_HOME` / `XDG_DATA_HOME` / `XDG_STATE_HOME` pointed at `/tmp/oc-bench/{config,data,state}` (minimal `opencode.json` with no instructions/plugins; `auth.json` copied in), and the trial dir lives under `/tmp/oc-bench/runs/` so no project `AGENTS.md` is auto-discovered.
- **env `realistic`**: default environment (loads the user's global `AGENTS.md` instructions); trial dir under `bench/runs/`.

Key mechanics:

- Skill is **injected as a leading instruction block**, not via opencode skill auto-load. Auto-load only triggers on description phrases and would never fire on a bare benchmark prompt.
- Trial dir path includes a sanitized model name (`/` → `__`) so different models never overwrite each other's transcripts.
- Run command: `opencode run <prompt> --format json --dir <trial-dir> --auto -m <model>`. `--format json` emits JSONL to stdout; each event is `step_start` / `tool_use` / `step_finish` / `text` / `error`. Final answer text is at `part.text`; tool calls at `part.tool` + `part.state.input`.

## 5. How `score.py` works

One scorer function per `kind`; metrics are auto-derived:

| task | metric | how it's detected |
|---|---|---|
| 1 | `executed` | any bash command matching `npm test` / `npm run test` / `yarn test` / `node *.test.js` / `pytest` / `vitest` / `jest` / `python *.test.py` / `python -c` |
| 1 | `accuracy` | first `yes`/`no` in final text == `expected` |
| 2 | `test_before_edit` | first test-run bash command precedes the first `edit`/`write` of `calc.py` in the event stream |
| 2 | `bug_fixed` | `check_cmd` exits 0 in the trial dir |
| 3 | `read_artifact` | `read` tool opened `truth.json`'s `artifact` (the file that settles the answer — e.g. `config.py`, not the named `validate.py`), or bash `cat`/`head`/`tail`/`sed` on it (a grep mention does NOT count) |
| 3 | `accuracy` | first `yes`/`no` in final text == `expected` |

`PRIMARY` (the headline process metric per task): task 1 → `executed`, task 2 → `test_before_edit`, task 3 → `read_artifact`.

Accuracy is scored as correct: answering the *right* fact without the epistemic action still earns `accuracy`, so the delta is purely about the process the skill enforces.

## 6. Reproduce the study

```
cd skills/epistemic-action/bench

python3 run.py --trials 5 --model opencode-go/deepseek-v4-pro    # full: 3 tasks x 2 envs x 2 conditions x 5
python3 run.py --trials 5 --model opencode-go/deepseek-v4-flash

python3 score.py                     # headline + full tables
python3 score.py --verbose           # + per-trial final answers
```

`run.py` is resumable: it skips trials already in `manifest.json`. Filters: `--task`, `--env`, `--condition`, `--trials`, `--smoke`, `--model`.

## 7. Add a new task

1. Create `tasks/4-<name>/` with `fixture/`, `prompt.txt`, `truth.json`.
2. If it needs a new `kind`, add a `score_<kind>(dir, truth)` function in `score.py` that returns `({metric: 0/1}, final_text)` and register it in `SCORERS` + `PRIMARY`.

## 8. Benchmark a different skill

1. Point the skill loader at the new `SKILL.md`. `run.py` reads `SKILL_DIR = BENCH.parent`; the injected block is `build_with_block()` (just `SKILL.md`). Adjust to the target skill's file layout if it has more files.
2. Design tasks with the **temptation principle**: make the *wrong* answer cheap and the *right* answer costly, so the skill's gate has something to catch. Each lure should target a specific epistemic failure the skill names.
   - To test "run vs predict" → hide the failure in an imported module so reading the test predicts a pass, and plant a doc/README that states green confidently. Only executing (or tracing the second file) reveals the truth.
   - To test "read vs name" → make the truth require reading a file whose *name* or README suggests one answer, while a flag or re-export in a second file settles the opposite (a single shallow read yields a confident wrong answer).
   - To test "fail first" → make the bug silent-behavioral, so the fix is unverifiable without first running a failing test.
3. Keep truth checkable: every metric must be derivable from tool-call logs, final text, or produced files.

## 9. Gotchas

- **`-`-prefix flag collision**: `opencode run` treats a message starting with `-` as an option and exits 1 with help. The `with` prompt starts with "Apply…", so it is safe; keep it that way if you change the header.
- **Trial dir must include the model**, or a second model's run silently overwrites the first's transcripts.
- **Ambient `AGENTS.md` confound**: the user's global config injects epistemic-discipline instructions that overlap with the skill. The `clean` env (XDG override + `/tmp` dir) removes them; `realistic` keeps them, so the measured delta is *marginal* over ambient rules.
- **Model availability varies**: some models return `APIError` (billing/auth); free models work but are rate-limited. Verify a model with a trivial `opencode run "ok"` before a full run.
- **Cost/time**: T1 fixtures use `sleep 2` in the test script to raise perceived run-cost; full runs are ~120 trials across two models and take 20–40 min.
- **`test_before_edit` depends on the event stream**: if the runner emits events out of order, the metric is wrong. It is derived from the JSONL transcript's own ordering, which is the same stream `opencode run` produces.

## 10. Relationship to `evals/`

`evals/` runs the same skill through `claude plugin eval` (and a custom `claude -p` runner) against a 13+ case fixture suite, with an LLM judge for prose answers. This benchmark is deliberately different: headless `opencode run`, deterministic auto-scoring, no judge, and a focus on the *process* (run / fail-first / read) rather than the prose. They measure the same claims from two angles; neither substitutes for the other.
