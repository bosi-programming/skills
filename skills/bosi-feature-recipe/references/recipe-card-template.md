# Recipe card template

One file per task, at `./recipes/{task-slug}.md`. `{task-slug}` is a kebab-case
short form of the task name or issue reference — `TICK-000` becomes
`TICK-000`, "add CSV export" becomes `add-csv-export`.

Copy this whole skeleton when creating a fresh card. Each phase writes only
its own section, below, and never rewrites a section a previous phase wrote.

```markdown
---
task: '<short name or issue reference, whatever the user gave>'
phase: ''                    # last completed phase, e.g. 'mise-en-place'
phasesCompleted: []
status: 'in-progress'        # in-progress | pr-created | delivered
prUrl: ''
lastTouched: '<date>'
---

## Decisions

<!-- one or two lines per phase, appended as phases complete, never rewritten -->

## Problem

<!-- written by Phase 1: Reading the Recipe -->

## Solution

<!-- written by Phase 2: Mise en Place -->

## Implementation Plan

<!-- written by Phase 2: Mise en Place -->

## Acceptance Criteria

<!-- written by Phase 2: Mise en Place -->

## Testing Strategy

<!-- written by Phase 2: Mise en Place -->

## TDD Test Mapping

<!-- written by Phase 2: Mise en Place -->

## PR Delivery Strategy

<!-- written by Phase 3: Cooking, only if the plan is large enough to warrant chunking -->

## Quality Gate Results

<!-- written by Phase 4: Tasting -->

## PR

<!-- written by Phase 5: Plating -->
```

The `phase` and `phasesCompleted` fields are the only things Phase 0 reads to
route a resumed task to the right phase file — keep them accurate on every
write. Valid phase tokens, in order: `reading-the-recipe`, `mise-en-place`,
`cooking`, `tasting`, `plating`, `documentation`.
