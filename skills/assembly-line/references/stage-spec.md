# Stage spec

A stage is one skill on a line built for one ticket. Each stage declares what
it reads from the work card, what it writes, where the line goes back to when
it fails, which signals it can raise, and whether a person must approve its
work. The catalog and the line validator read these declarations, so every
stage writes them the same way.

## Where it lives

In `stage.json`, beside the stage's `SKILL.md`. Not in the frontmatter: the dsh
reader takes only top-level scalars from frontmatter, and five harnesses read
the same `SKILL.md`, so nested data there would break some of them.

## Keys

Every key but `spec` is required. Lists may be empty.

| Key | Type | What it holds |
| --- | --- | --- |
| `spec` | string | Path from `stage.json` to this file. Optional; it tells a reader where the rules are. |
| `takes` | list of strings | What the stage reads from the work card. `## Problem` names a section; a bare name such as `task` names a frontmatter field. |
| `delivers` | object | What the stage writes. `sections` and `fields` follow the same rule as `takes`; `verdicts` lists every verdict the stage can end with. |
| `return` | object | One entry per failing verdict. See below. |
| `signals` | list of strings | Names of the signals the stage can raise. It writes them to `## Signals` on the card. What a signal adds to or removes from the line lives in the catalog. |
| `gate` | `auto` or `human` | `human` when a person must approve the stage's work before the line moves on. |

### `return`

Each key is a verdict from `delivers.verdicts`. Its value is an object:

| Field | Type | What it holds |
| --- | --- | --- |
| `to` | string | A role: the name of a stage skill under `skills/`. The line goes back to the latest stage with that name. |
| `limit` | integer, 0 or more | How many times the line may go back before it stops. |
| `past` | `needs-input` or `human` | What happens once the limit is used up: stop the run with `runStatus: needs-input`, or hand the card to a person. |

`to` names a role, never a position. Lines differ per ticket, so "two stages
back" means something different on each one; "the latest `code`" does not.

## Signal rows

A stage writes each signal it raises to `## Signals` on the card, one per line:
`<signal> — <stage> — <evidence>`. Rows in `../assembly-line/references/signals.json`
(or `./signals.json` from this folder; one of the two must resolve) say what a
signal does to the line. Each row holds:

| Key | Holds |
| --- | --- |
| `signal` | The signal's name. The `raisedBy` stage lists it in its `signals`. |
| `raisedBy` | The stage that raises it. A row matches only a signal from this stage. |
| `add` or `remove` | Exactly one: the stage to add to the line or to remove from it. |
| `where` | `after <stage>` or `before <stage>`. Required with `add`, not allowed with `remove`. |

A row never removes `judge`, `merge` or a stage with `gate: human`;
`build-catalog.py` fails the build on one. A row applies without approval and
changes only the steps not yet run.

## Example

`skills/evaluate-ticket/stage.json`:

```json
{
  "spec": "../assembly-line/references/stage-spec.md",
  "takes": ["task"],
  "delivers": {
    "sections": ["## Problem", "## Goal & measure", "## Decisions", "## Open Questions"],
    "fields": ["phase", "phasesCompleted", "lastTouched"],
    "verdicts": ["done", "blocked"]
  },
  "return": {
    "blocked": { "to": "evaluate-ticket", "limit": 0, "past": "needs-input" }
  },
  "signals": [],
  "gate": "auto"
}
```

`evaluate-ticket` is the first stage, so a `blocked` verdict returns to itself
with no retries and stops the run for a person to answer.

## Check

Run from the repository root:

```bash
python3 skills/assembly-line/scripts/check-stage-spec.py skills/evaluate-ticket
```

It fails, naming the key, when `stage.json` is missing, does not parse, lacks a
key, holds a value of the wrong type, lists a `return` verdict that is not in
`delivers.verdicts`, or returns to a stage that is not a skill under `skills/`.
