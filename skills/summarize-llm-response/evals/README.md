# summarize-llm-response evals

Two harnesses, because a formatting skill can fail in two independent ways.

| Harness | Question | Failure it catches |
| --- | --- | --- |
| `trigger.py` | Does the description make the skill fire? | Skill never loads, so its rules never apply |
| `run.py` + `score.py` | Given the skill is applied, is the output right? | Rules are wrong, vague, or contradict each other |

Both run headless `claude -p` against an isolated context, so results are not
polluted by the operator's own `CLAUDE.md`, installed skills or MCP servers.

## Behaviour

```bash
python3 run.py --trials 2 --model claude-sonnet-5
python3 score.py --model claude-sonnet-5
```

`run.py` runs every case in `evals.json` twice: `with` injects the SKILL.md body
via `--append-system-prompt`, `without` is the bare prompt. Both arms use
`--safe-mode`, which drops CLAUDE.md, skills, plugins and hooks — so the skill
is the only difference between them.

`score.py` checks each output against the rules SKILL.md actually states and
prints a with/without table. A rule that scores the same in both columns is a
rule the skill is not buying you.

Outputs land in `runs/<model>/<case>/<condition>/trial<N>/output.md`. Reruns
skip cases that already have output; delete `runs/` to start fresh.

Cases marked `"target": "in-conversation"` get the prompt verbatim. External
targets get a note that no integrations are available, because headless safe
mode has no Linear/Slack/Todoist tools. Do not add that note to
in-conversation cases — telling the model to "write out what you would post"
is enough to push a plain summary into issue format.

## Trigger

```bash
python3 trigger.py --trials 3 --model claude-sonnet-5
python3 trigger.py --trials 3 --description-file candidate.txt
```

Installs the skill into a throwaway project, runs each prompt in
`trigger_cases.json`, and reports whether Claude invoked the skill.
`should_fire: true` prompts measure recall; `false` prompts measure
over-triggering. `--description-file` swaps in a candidate description without
touching SKILL.md, so descriptions can be A/B'd.

`--strict-mcp-config` is not optional here. Without it the operator's MCP
servers load and the model reaches for Linear directly instead of the skill —
which wrecks the measurement and risks a real write to a real workspace.

## Cost

Roughly 24 behaviour runs and 39 trigger runs per full pass on Sonnet. Use
`--model claude-haiku-4-5-20251001` for a cheap smoke test; format-following
is weaker there, so do not read absolute numbers off it.
