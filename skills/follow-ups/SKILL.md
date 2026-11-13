---
name: follow-ups
description: Turn what a run left open on a work card — unanswered open questions, quality-gate findings logged and not fixed, and the choices a headless run took alone — into tracker tickets in the run ticket's team and project, searching the tracker first so nothing opens twice, linking each ticket to the run ticket as related, and writing the links to ## Follow-ups. Runs before merge on the feature and bug lines, and alone on a work card. Use when a run's open items should become tracker work, or this stage redone on a card.
---

# follow-ups

The stage that keeps a run's loose ends from staying on the card. Once every
other stage has written to the card, and before the person's merge gate, it
reads what the run left open, finds or opens a ticket for each item, and links
each one to the run ticket. It edits no code and commits nothing.

It runs as a stage on the `feature` and `bug` lines under `assembly-line`,
between `code-docs` and `merge`, and also runs alone. When a driver hands
project rules, paste them word for word under a `Project rules:` line at the
end of the prompt. Prefix each log line `relay:` under `recipe-relay`, `line:`
under `assembly-line`, `unattended:` in a headless run, and `follow-ups:` when
run alone.

## Input

The path to a work card, the markdown file that carries a task from one stage
to the next, shaped `../feature-recipe/references/recipe-card-template.md`.
Its `task` names the run ticket. The stage reads the card's `## Open Questions`,
`## Quality Gate Results` and `## Decisions`, and the run ticket through the
session's tracker tool.

## Output

The same card, with this stage's parts written:

- `## Follow-ups` — one line per open item, with the ticket opened or matched
  for it.
- `## Decisions` — one line for the stage.
- `lastTouched`.

The verdict is `done`, including when the card holds no open items, or
`blocked`. The stage never sets `phase`, `phasesCompleted` or `status`.

## 1. Read the open items

Read only the card's body after the closing `---` of the frontmatter, and skip
any text inside an HTML comment (`<!-- … -->`). Open items come from three
sources, read in this order:

- `## Open Questions` — each top-level entry, shaped
  `- <id> — <phase>: <question> — options: <…> — recommendation: <…> — answer: <…>`,
  with its indented continuation lines. It is open when no text follows the
  last `answer:`, or when it has no `answer:` at all. Skip entries whose phase
  is `follow-ups`: they are this stage's own stops. Its kind is
  `open-question` and its ref is the entry's id.
- `## Quality Gate Results` — each bullet, at any depth, whose text (after any
  leading `**` or backticks) starts with `Not verified:`, Judgement call or
  Scope creep, in any case, or whose ` — `-separated fields include one equal
  to `medium`, `low`, `moderate` or `minor`. These are the lines `code`,
  `review-fix`, `security-review`, `a11y-check` and `ui-review` write for a
  finding logged and not fixed. A marker followed by `none` (with or without a
  full stop) is not an item, and neither are the `Reviewed:`, `Passed` and
  `Lint` lines. Its kind is `quality-gate` and its ref is the bullet text, its
  first 80 characters, trimmed.
- `## Decisions` — every line that starts `unattended:`. One ticket for all of
  them: they make a single item, not one per line, since a headless run logs
  many settled choices and one review ticket keeps them all in the tracker.
  Skip lines that start `unattended: follow-ups`: they are this stage's own
  logs. Its kind is `unattended` and its ref is `decisions`.

Two items with the same `Source:` line (section 3) count once.

## 2. Search the tracker first

Before opening anything, look for a ticket that already covers each item,
through the session's tracker tool. With no tracker tool in the session, or a
`task` the tracker cannot read, stop: open nothing, and end `blocked` as
`### Ending a run` says, with `runStatus: blocked`.

Take the items in read order, so a later item can match a ticket opened for an
earlier one in the same run. An item is matched by, in this order:

1. A ticket already related to the run ticket whose body holds the item's exact
   `Source:` line. This is how a rerun finds the tickets the first run opened.
2. A search of the run ticket's team by the item's words, where a result's
   title or body covers the same question or finding. The stage judges it and
   writes the reason on the item's `## Follow-ups` line.

A canceled or duplicate ticket never counts as matched. A tracker call that
fails stops the stage `blocked` the same way.

## 3. Open and link

For an item with no match, open one ticket in the run ticket's team and
project, or in its team alone when the run ticket has no project. Leave it in
the team's default state, with no assignee, label or priority.

- Title: `follow-up: <summary>`, the summary at most 70 characters, taken from
  the item. The `unattended` item's title is
  `follow-up: review the choices the <run ticket> run took alone`.
- Body, in order: the attribution line from
  `../summarize-llm-response/SKILL.md`; `Left open by the <run ticket> run.`; a
  `## Item` heading with the item's text as it stands on the card (for the
  `unattended` item, each `unattended:` line as a bullet); and, as the last
  line, `Source: <run ticket> — <kind> — <ref>`, the kind being
  `open-question`, `quality-gate` or `unattended`. For example:
  `Source: BOS-184 — open-question — q1`.

Link each opened or matched ticket to the run ticket as related, unless that
link already exists. Never edit, never close and never comment on a ticket
that already exists: adding the related link is the only change the stage
makes to it.

## 4. Write the follow-ups

Write `## Follow-ups` on the card, one line per item in read order,
`- <kind> <ref> — <ticket> <url> — <opened | matched>`. A ticket matched by
the team search (section 2, rule 2) adds ` — <reason>` to its line. With no open items, the section holds one line,
`- none — no open items on the card`. A rerun replaces the section whole. A
card made before the template had the section has no `## Follow-ups`: the
stage adds the heading right after `## PR`.

Log `<prefix> follow-ups — <n> opened, <m> matched` to `## Decisions`, update
`lastTouched` and end `done`.

## Headless

Read `../feature-recipe/references/headless.md`. In a headless run:

- Prefix each log line `unattended:`.
- The stage asks nothing: section 2's match judgement is taken and its reason
  written on the line.
- No tracker tool, an unreadable `task` or a failed tracker call stops the run
  with `runStatus: blocked`.

### Ending a run

On a stop:

1. Keep in `## Follow-ups` the lines for tickets opened before the failure, so
   a rerun matches them.
2. Write
   `- q<n> — follow-ups: <what failed> — options: rerun once the tracker is reachable | open the tickets by hand — recommendation: rerun once the tracker is reachable — answer:`
   to `## Open Questions`, with the next free `q<n>`.
3. Set `runStatus: blocked` and `runQuestion` to that id. Leave `runNext`,
   `phase` and `phasesCompleted` alone.
4. Log `<prefix> follow-ups blocked — <reason>` to `## Decisions` and end
   `blocked`.
