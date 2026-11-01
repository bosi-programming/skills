# Review report template

Fill this exactly, every time. Keep every section, in this order, even when
empty (write `None.`). Two reviews of the same work must read side by side.

## Severity

| Severity | Means |
|---|---|
| **Blocker** | The work cannot be built or proven as written: a missing part, a criterion nobody can run, a cycle, a placeholder |
| **Major** | It can be built, but breaks a rule that costs rework or review time: wrong split, wrong tag level, missing required work (standard §9) |
| **Minor** | Wording, order or format that a builder can work past |

## Operations

Each finding proposes one operation:

- `edit-description <item>`: the exact new text of the section it changes
- `add-item <parent or project>`: title, Kind, and the full body
- `move-item <item> → <parent or milestone>`
- `add-relation <item> blocked by <item>` / `remove-relation …`
- `set-labels <item>`: labels added and removed
- `ask <Qn>`: the fact is missing; no change until it is answered

Never `delete` or `cancel`: propose them in words, for a person to do.

## Template

```markdown
# Review: <identifier or project> · <title>

- **Standard:** <bundled standard | team standard path or URL @ ref>
- **Lint:** <check_plan.py verdict | team lint verdict | not run (<reason>)>
- **Items read:** <n issues, n sub-issues, n milestones>

## Scorecard

| Check | Result | Findings |
|---|---|---|
| Shape | ✅ / ❌ / ❓ | <n> |
| Kind | ✅ / ❌ / ❓ | <n> |
| Contents | ✅ / ❌ / ❓ | <n> |
| Criteria | ✅ / ❌ / ❓ | <n> |
| Required work | ✅ / ❌ / ❓ | <n> |
| Flags | ✅ / ❌ / ❓ / n/a | <n> |
| Order | ✅ / ❌ / ❓ | <n> |

❓ means a check needs a fact the tracker does not hold; its question is below.

## Findings

Blockers first, then Major, then Minor. Within a severity, in tree order.
A mistake repeated on several items is one finding listing every item.

### F1 · <Blocker | Major | Minor> · <check> · <item(s)>
- **Rule:** <standard § or team rule>
- **Found:** <what the item says or lacks, quoted>
- **Proposed change:** <operation> — <exact content>

## Questions

1. <item>: <the missing fact>

## Lint gaps

- <item> `<rule>`: <message>
```
