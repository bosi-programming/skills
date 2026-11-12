---
name: plan-work
description: Plan a feature into tracker tickets, or review tickets already planned. Plan mode turns a feature, its details and specs into a project, milestones, issues and sub-issues (or one ticket), checks them against a planning standard and a lint, and writes them after approval. Review mode reports what breaks the standard and changes nothing. Works with any tracker. Use when someone wants a feature planned, broken into tickets, a ticket written or reformatted, or tickets checked.
argument-hint: "[plan|review] <feature, spec, link, or ticket/project>"
---

# Plan Work

Goal: tickets a builder, human or agent, can pick up and finish with no
follow-up questions. The rules for a good ticket sit in a separate standard
(`./references/standard.md`, or the team's own); this file only says what to do
in which order.

If this file ever contradicts the standard, follow the standard and tell the
user this file needs fixing.

The letters below (A to H) name sections of the bundled standard. With a team
standard, cite its own section names in their place.

## Settings

Look up each key as `../setup/references/config.md` describes: the current
folder's settings file, then the one in `$HOME`, then the default.

- `plan-work.standard`: where the team keeps its standard, as a path, a URL or
  `owner/repo@ref:path`. Default `''` means `./references/standard.md`.
- `plan-work.lint`: the command that lints a plan. Default `''` means the
  bundled lint for the bundled standard, and no lint for a team standard.
- `plan-work.team`: the tracker team or project for new tickets. Default `''`
  means ask.
- `plan-work.labels`: tracker label names by kind or area. Default `{}` means
  no labels.
- `plan-work.repos`: the repos this work can touch. Default `[]` means read
  them off the sources.
- `plan-work.featureFlags`: `true` ships each new Feature behind a flag.
  Default `false`.
- `plan-work.flagEngine`: the flag tool to name. Default `''` means write
  "feature flag" and ask.
- `plan-work.role`: `engineer` or `other`. Default `''` means ask at the end.

Rules a team adds on top of the standard go in the settings file under
`## plan-work`. Apply them as if they were part of the standard.

## Pick a mode

`plan` or `review` as the first word decides. With neither, read the request:

- **plan**: build, split, write, rewrite or reorganize tickets. A single ticket
  is just a small plan.
- **review**: audit, check, "is this OK". Reads only.

If the request could go either way ("look at ABC-12"), ask which. After a
review, switch to plan only if the user asks for fixes.

People often name the wrong size: they say "a ticket" when it needs a project,
or "a project" when one ticket will do. Standard G settles it; when it
disagrees with the request, tell the user before you continue.

## Get the standard first

Load the full standard before you plan or judge anything:

- no `plan-work.standard`: read `./references/standard.md`;
- a file path: read it;
- a URL: fetch it;
- `owner/repo@ref:path`: `gh api repos/<owner>/<repo>/contents/<path>?ref=<ref> --jq .content | base64 -d`.

Keep a note of the source and its ref for the draft and the report. If loading
fails, report the error and stop. A plan made from a remembered version of the
rules only looks compliant.

## What gets checked

The same list applies to a fresh draft and to tickets already in the tracker.
Cite the standard's letter with every result.

1. **Size and split:** project or ticket (G), milestones (G), split or not
   (D), one repo per piece (D).
2. **Kind:** each piece is Feature, Bug, Enablement or Design, with its block
   (C).
3. **Body:** each heading the template asks for, filled from a source (B),
   with nothing left from H's list.
4. **Criteria:** line format, numbering, tags, tag level, a reason on every
   `[manual]` (A).
5. **Extra work:** every line of E the change triggers.
6. **Flags:** F, read with the two flag settings.
7. **Links:** each wait is a `blocked by`, with no loops, and nothing linking
   sub-issues of different tickets (D).
8. **Team rules:** the `## plan-work` section, if there is one.

**Lint.** For the bundled standard, put the whole plan in one JSON file and
run the bundled lint. `$SKILL_DIR` is this `SKILL.md`'s folder:

```bash
python3 "$SKILL_DIR/scripts/check_plan.py" [--feature-flags] plan.json
```

The lint always checks each flag a ticket declares under `### Feature flags`:
a flag-off criterion and a removal ticket. Add `--feature-flags` only when
`plan-work.featureFlags` is `true`; it also makes every Feature declare a
flag. The JSON is `{"issues": [...]}`: per top-level ticket an
`identifier`, `title`, `description`, `blockedBy` (other top-level tickets)
and `children`. Each child has `identifier`, `title`, `description` and
`blockedBy` (siblings only). Bodies go in as full Markdown. Before the
tracker has ids, make some up (`NEW-1`, `NEW-2`). Output is
`{ready, gaps: [{issue, rule, message}]}`. The exit code is `0` when ready,
`1` when there are gaps, and `2` when the input is broken. For a team
standard, run `plan-work.lint` when set, and otherwise write
`Lint: not run (team standard, no lint set)`.

A clean lint is not a clean plan. The script can't judge most of the list
above.

## Plan

### 1. Understand

Take in every source before you think about shape:

- the request and everything said earlier in this session, including choices
  the user already made;
- linked specs, PRDs, mock-ups, chat threads and pages;
- the ticket or project being reworked, with its comments;
- the repo's docs and code on the default branch.

Read sources end to end. Anything you can't open goes in the questions,
marked unread.

For anything with a screen, open the files that will change. Specs name pages,
not what's on them. List each state the code can show (empty, loading, error,
dialog, banner, tooltip); standard A turns each into a criterion.

When a design exists for screen work, get its link and a screenshot of each
changed screen as it is today and as designed. Both go in `## Design`
(standard B). Screenshots you can't get become questions; never point at a
frame you haven't opened.

Then search the tracker and the docs for the same work. If some already
exists, don't draft yet. Show the matches with links and say how much of the
request they already cover. Then let the user choose: plan fresh anyway,
rework the existing tickets, or review them first. Skip the stop only when the
user already chose, and still list what you found.

Write nothing a source doesn't back: no user stories, criteria, payloads,
mock-up links, metric names, flag names or customer names of your own. Each
hole becomes a question.

### 2. Shape

Settle these in order; each depends on the last:

1. Ticket or project (G).
2. Milestones if it is a project that ships more than once, clean-up last (G).
3. Split each ticket or not (D), using `plan-work.repos` or the repos the
   sources name. If you can't tell whether two pieces share state, ask.
4. Kind of each piece (C). A Design ticket always lands in a frontend ticket.
   Search the tracker for the one that will build it. If it exists, name it in
   `Frontend ticket:` and plan an edit that adds the `## Design` section (or a
   `No design yet` line until the design is done). If none exists, plan a new
   frontend ticket, `blocked by` the design ticket.
5. Flags (F): with `featureFlags` on, each new Feature gets one; with it off,
   only the flags a source asks for. Each flag gets a removal ticket (in the
   clean-up milestone when there is one), naming `plan-work.flagEngine`.
6. Extra work (E). Go down the whole list; most plans miss items here.
7. `blocked by` links.

Give each choice a one-line reason with its letter. When the plan is a project
or holds more than five items, show just the tree and reasons and wait for a
yes. Bodies are the expensive part, and a dropped milestone would throw them
away.

### 3. Draft

Fill each item from the templates in standard B. Open every ticket and
sub-issue body with the line Planned with `plan-work`., above `## What`.

Where a fact is missing, put `[[gap Qn: what is missing]]` in the body and add
`Qn` to the questions. Use that form for every hole, so a search finds them
all and nothing half-written reaches the tracker by accident.

Run the checks above, then the lint, and fix everything they flag. Anything
you can't fix without a source becomes a question naming the item and the
rule.

### 4. Show

Present it in four parts, then wait:

1. **Tree:** project, milestones, tickets, sub-issues, each with title, kind,
   labels (`plan-work.labels`) and `blocked by`, plus a short reason per choice.
2. **Bodies:** each one exactly as it will be saved. When reworking, tag each
   item new, changed or unchanged, and show the diff.
3. **Questions:** numbered, one fact each, each tied to its item. Only the
   `[[gap Qn: …]]` marker goes in a body, never the question itself.
4. **Sources of the rules:** the standard and ref, and the lint result or why
   it did not run.

Approval comes before any write. Rework and show again as many times as the
user asks. An item with a `[[gap …]]` is never saved, even on request; say what
it still lacks. The others can go.

### 5. Save

Use whatever tracker tool the session has. Team or project comes from
`plan-work.team`; if that is empty, ask.

Save every body with the line Planned with `plan-work`. under the attribution line,
above `## What`.

Not every tracker has sub-issues, milestones or `blocked by`. Map each to what
the tracker offers (an epic or parent link, a label or version, a task list or
a "depends on" link), show that map in step 4, and ask when nothing fits. Save in an order where every id exists
before something needs it:

1. Labels: turn each name in `plan-work.labels` into the tracker's id first.
   Names with emoji or extra spaces often won't match as text. If one doesn't
   resolve, stop and say so; never save the item bare.
2. Project, then milestones in shipping order.
3. Tickets, then their sub-issues, in the same project and milestone.
4. `blocked by` links last. A sub-issue waiting on another ticket's sub-issue
   gets no link itself; link the two tickets.

When reworking, apply only what was approved. Leave titles, labels, links,
owners and states alone unless the plan changes them. If the tool replaces all
labels at once, add and remove one at a time. Don't delete or cancel anything;
suggest it and leave it to the user.

### 6. Check what landed

1. Fetch every saved item back from the tracker with sub-issues, labels and
   links. Work from what the tracker returns, not from your draft: saving can
   change text.
2. Build the lint JSON from that and run the lint.
3. List every gap with item and rule. Only then say whether the plan is ready,
   and never call it ready without this pass.

Reply with a link per item, laid out like the tree, and what was not saved and
why.

### 7. Hand off

The skills that will build each ticket (its line) go in a comment on the
ticket, or in a local file. `plan-assembly-line` writes it; this skill
doesn't.

Where the line goes is `assembly-line.lineDestination` (`ticket`; read as
`../setup/references/config.md` says, under `assembly-line:`): `ticket` posts
a comment, `file` writes the local file `assembly-line.lineFile` names
(`{cardsDir}/{ticket}.line.json`). When handing off, offer both and recommend
the setting's value; pass the choice to `plan-assembly-line`.

- `role: engineer`: run `plan-assembly-line` on the new tickets.
- `role: other`: stop, and say an engineer still has to pick the line.
- no role: ask once whether to do it now.

If `plan-assembly-line` isn't installed, say so and stop there. The tickets are
saved, and the line can come later.

## Review

Reads only. It writes nothing to the tracker, not even a comment, unless the
user asks once the report is out.

### 1. Read

- **One ticket:** the ticket, its sub-issues, labels, links in both
  directions, comments, and its project and milestone if any.
- **A project:** its summary and description, milestones, every ticket and
  sub-issue, their labels and links.

Fetch in as few calls as the tool allows, for example one list query by
parent or project that returns bodies, labels, states and parents. Finish
reading before judging. Some problems only appear across items: a milestone
cut by layer, a wait with no link, one mistake on every sub-issue.

### 2. Judge

Decide what each item is before judging it: a ticket with sub-issues, a ticket
built directly, or a sub-issue. The same body passes in one role and fails in
another. Then run the checks and the lint. Judge the text as saved, not what
the author likely meant. If a check depends on something the tracker doesn't
record, mark it unknown and add a question.

### 3. Report

Open `./references/review-report.md` and follow it to the letter: same
sections, same order, same severities and operations, nothing added. Each
finding ends with a **Proposed change** holding the exact text to save, built
from the item, its sources and the templates. If a fact is missing, point to
the question that asks for it instead of making it up.

If the user wants the fixes made, go to plan mode with the report as the
source. Its proposed changes are the plan, and the approval in step 4 still
comes before any save.

## Output

Pass drafts and reports through `summarize-llm-response` when the session has
it; it adds the attribution line the tracker expects. Write bodies plainly:
short sentences, active voice, no filler.
