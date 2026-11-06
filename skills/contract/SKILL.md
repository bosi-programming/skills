---
name: contract
description: List each shape one sub-issue of a parent produces and another consumes, copied word for word from the issues and never invented, write contract.json, post it as ## Contract on the parent and copy it into the card; a shape no issue states stops the line. Runs alone on a work card or under open-restaurant. Use when someone wants the shared contract of a parent and its sub-issues written, or this step redone on a card.
---

# contract

The contract step for a parent and its sub-issues. `open-restaurant` runs its
section 3 through this skill, and it also runs alone. It never invents a shape.
Prefix each log line `restaurant:` under `open-restaurant`, `unattended:` in a
headless run, `contract:` when run alone.

## Input

The path to a card. A work card is the markdown file that carries a task from
one stage to the next; its shape is
`../feature-recipe/references/recipe-card-template.md`, and its `task` names the
parent. A service card is the one `../open-restaurant/SKILL.md` opens; its
`parent` names the parent. Read the parent, its comments and every sub-issue
through the session's tracker tool.

An issue with no sub-issues needs no contract: log it, write nothing else, and
end `done`.

With no card, neither `task` nor `parent`, or an issue the tracker cannot read,
stop, write nothing else, set `runStatus: blocked` and log it. There is no
verdict.

## Output

The same card, with this stage's parts written:

- `## Contract` — `Comment: <link>`, then the JSON; made on a work card when
  missing.
- `## Decisions` — the verdict line.
- `## Open Questions` — on `gaps`, one `c<n>` entry per gap.
- `runStatus` — `needs-input` on `gaps`, `blocked` on bad input; untouched on
  `done`.
- `runQuestion` — `c1` on `gaps`, only where the card has the field.
- `lastTouched`.

`contract.json` lands at the root of the folder the session runs from, and the
`## Contract <id>` comment on the parent. The verdict is `done` or `gaps`. The
stage leaves `phase` and `phasesCompleted` as they are.

## Settings

Resolve the key from the settings file as `../setup/references/config.md`
describes, without opening that file:
`grep -n -A8 '^open-restaurant:' .bosi-skills.md ~/.bosi-skills.md`, current
folder first, then `$HOME`, then the default:

- `open-restaurant.judgeModel` — the model of the contract sub-agent. Default
  `''`: the session's model.

## 1. Shapes

One sub-agent on `open-restaurant.judgeModel`, allowed to write files and
nothing else, lists each shape one sub-issue produces and another consumes:
`{ name, kind: api|event|config, producer, consumers, shape }`. It copies each
shape word for word from the issues and must never invent one; a part no issue
states goes to `gaps`. It writes `contract.json` at the folder root:
`{ "entries": [ { name, kind, producer, consumers, shape } ], "gaps": [ { name, issues, message } ] }`.
With no shared shape, `entries` is empty.

## 2. Post

Post `contract.json` as a `## Contract <id>` comment on the parent, `<id>` the
parent identifier, the body the heading and the JSON in a `json` block, gaps
included. Copy it into the card's `## Contract`: first line `Comment: <link>`
with the comment's link, then the JSON; make the section on a work card when
missing. A tracker write that fails is logged and the stage stops with
`runStatus: blocked`.

Every later step reads the latest `## Contract` comment on the parent, not the
file: the latest `## Contract` comment wins, since a person may have edited it.

## 3. Gaps

On any entry in `gaps`, write each gap to `## Open Questions` as `c1`, `c2`, …
(`- c1 — contract: <the shape of name between issues> — options: state it in the producer's issue | drop it — recommendation: state it in the producer's issue — answer:`),
set `runStatus: needs-input` (and `runQuestion` to `c1` where the card has the
field), log verdict `gaps` to `## Decisions`, update `lastTouched`, and end
`gaps`. A gap is never filled on the issue's behalf.

## 4. Done

With no gap, log verdict `done` to `## Decisions`, update `lastTouched`, and end
`done`. The line goes on.

## Headless

Read `../feature-recipe/references/headless.md`. In a headless run:

- Prefix each log line `unattended:`. Nothing in it waits on a person.
- Gaps are never answered on the issue's behalf, and no shape is invented.
- A gap is not a one-way door but a stop.

### Ending a run

On `gaps`:

1. Make section 3's writes.
2. Set `runStatus: needs-input` and `runQuestion` to the first gap's id, where
   the card has the field. Leave `runNext`, `phase` and `phasesCompleted` alone.
3. Log the stop to `## Decisions`.
