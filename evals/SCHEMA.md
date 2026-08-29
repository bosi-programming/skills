# case.yaml schema

`claude plugin eval` is in early access and its case format is not documented.
Everything below was read out of the runner's own validator or observed in a run.
Nothing here is guessed.

## The case

```yaml
schema_version: "1.0"        # required
name: my-case                # required, non-empty
description: ...             # optional
tags: [a, b]                 # default []
plugins: [name, ...]         # optional, selects plugins by name
context:
  scaffold_script: scaffold.sh   # see below
  history_file: ...              # optional
  add_dirs: []                   # default []
execution:
  prompt: |                  # optional
  max_turns: 10              # default 10, max 200
  timeout_seconds: 300       # default 300, max 3600
  model: ...                 # optional
  allowed_tools: []          # default []
  append_system_prompt: ...  # optional
  env: {}                    # default {}
runs: 3                      # default 3, max 50
graders: [...]               # at least one, names must be unique
expected_outcome: ...        # optional
```

Unknown keys on the case object are dropped in silence, so a misplaced field fails
by doing nothing rather than by erroring. Grader objects are strict and do error.

## scaffold_script

Three things the error messages taught us, each the hard way:

- It is a **path to a script**, not a command line. `bash foo.sh .` is read as a
  filename and reported missing.
- `${CLAUDE_PLUGIN_ROOT}` is **not expanded** in it.
- The path **must sit inside the case directory**. A `..` segment or an absolute
  path is rejected outright.

So every case dir carries a `scaffold.sh` shim that resolves its own location and
calls the shared `evals/scripts/scaffold.sh`. `gen_cases.py` writes both.

The script runs with the sandbox as its working directory and receives no
arguments. Nothing happens unless `--scaffold` is passed on the command line.

## Graders

Every grader takes `name` (required, unique) and `weight` (positive, default 1),
plus an optional `arm` of `with-only` or `both`.

- `regex` — `pattern`; `target` (default `last_message`); `flags` (JS RegExp
  flags); `match` of `contains` | `not_contains` | `count:N`, default `contains`
- `tool_used` — `tool`; optional `input_match`, `min`, `max`
- `tool_order` — `before`, `after`, each a tool name or `{tool, input_match}`
- `file_exists` — `path`; `exists` boolean, default true
- `llm` — `criteria`; `focus` (same shape as `target`, default `last_message`)
- `baseline` — `baseline_file`, `criteria`

There is no shell-command grader.

### target and focus

Either one of `trace`, `last_message`, `files`, `mock_calls`, or a file:

```yaml
target:
  source: file
  path: src/utils/parseAmount.js
```

Pointing a `regex` at a file in the sandbox is how this suite checks the work
rather than the prose: that no print was left in a source file, that a test was
not weakened to pass, that no retry loop was added.

### Asserting absence

Use `match: not_contains`. A negative lookahead also works but reads badly and is
easy to get wrong.

### tool_used ranges

`min` and `max` default to `1..∞`. `max: 0` on its own renders as `1..0`, which can
never pass, so asserting a tool was never called needs both `min: 0` and `max: 0`.
Verified by making the same grader pass for an unused tool and fail for a used one
in one run.

## Running

The command is gated behind early access and needs `CLAUDE_CODE_WALNUT_SPIRE=1`.
