---
name: plan-work
description: Plan a feature into tracker tickets, or review tickets already planned. Plan mode turns a feature, its details and specs into a project, milestones, issues and sub-issues (or one ticket), checks them against a planning standard and a lint, and writes them after approval. Review mode reports what breaks the standard and changes nothing. Works with any tracker. Use when someone wants a feature planned, broken into tickets, a ticket written or reformatted, or tickets checked.
argument-hint: "[plan|review] <feature, spec, link, or ticket/project>"
---

# Plan Work

Turn a feature into tickets someone, person or agent, can build without
asking, or check tickets that already exist. The rules a plan meets live in a
**standard**, not in this file: the one bundled at `./references/standard.md`,
or the team's own. This file holds the workflow: which check runs when, and how
the result is shown and written.

When this file and the standard disagree, the standard wins. Say so, so the
skill gets fixed.

## Settings

Read the settings file as `../setup/references/config.md` says, current
folder first, then `$HOME`, then the default:

- `plan-work.standard` — the team's standard: a path, a URL or
  `owner/repo@ref:path`. Default `''`: `./references/standard.md`.
- `plan-work.lint` — command that lints a plan. Default `''`: the bundled
  lint with the bundled standard; no lint with a team standard.
- `plan-work.team` — tracker team or project new tickets go in. Default
  `''`: ask.
- `plan-work.labels` — map from Kind or area to the tracker's label name.
  Default `{}`: no labels.
- `plan-work.repos` — repos the work may touch. Default `[]`: take them from
  the sources.
- `plan-work.featureFlags` — `true` puts every new Feature behind a flag.
  Default `false`.
- `plan-work.flagEngine` — the flag tool tickets name. Default `''`: write
  "feature flag" and ask which tool.
- `plan-work.role` — `engineer` or `other`. Default `''`: ask once, at the
  end.

The settings file's `## plan-work` section, when present, holds team rules
the plan meets on top of the standard, such as a label every ticket needs.

## Modes

Take the mode from the first argument when it is `plan` or `review`, else from
the request:

- **Plan:** the user wants work planned, broken down, created, a ticket
  written or reformatted, or existing tickets reorganized. One ticket is the
  small case of a plan, not a separate mode. See [Plan mode](#plan-mode).
- **Review:** "review", "audit", "check", "does this follow the standard". It
  reads the tracker and changes nothing. See [Review mode](#review-mode).

When a request fits both, such as "look at ABC-12", ask once. A review leads
into plan mode only when the user asks.

The level is not always the one the user names: "a ticket" can need a
project, and "a project" can be one ticket. The standard's §2 decides. When
its answer differs from the request, say so and why before going further.

## Step 1: Load the standard

Read the whole standard before planning or reviewing anything:

- **Bundled:** `./references/standard.md`.
- **Path:** read the file.
- **URL:** fetch it.
- **`owner/repo@ref:path`:** `gh api repos/<owner>/<repo>/contents/<path>?ref=<ref>`
  with `--jq .content | base64 -d`, so the result does not depend on a local
  checkout.

Note where it came from and at which ref or commit: the draft and the review
report both name it. When the standard cannot be read, stop and say what
failed. Never plan or review from memory: the result would look like the
standard without being checked against it.

## The checks

Plan mode runs them on its draft before showing it; review mode runs them on
what the tracker holds. Each check cites the standard's section:

- **Shape:** issue or project, milestones and their kinds, built directly or
  with sub-issues, one sub-issue per repo or area.
- **Kind:** Feature, Bug or Enablement for each item built as one PR, and its
  block.
- **Contents:** every section the template names, filled from a source.
- **Criteria:** format, numbering, proof tags, issue-level tags, a reason on
  every manual check.
- **Required work:** every row of the "required by the change" table the
  change triggers.
- **Flags:** the rules for `plan-work.featureFlags` and `plan-work.flagEngine`.
- **Order:** every dependency is a `blocked by` relation, the graph has no
  cycle, and sub-issues of different issues never relate.
- **Team rules:** the `## plan-work` section, when present.

**The lint runs too.** With the bundled standard, run the bundled lint on one
JSON file holding the whole plan; `$SKILL_DIR` is the folder this `SKILL.md`
sits in:

```bash
python3 "$SKILL_DIR/scripts/check_plan.py" [--feature-flags] plan.json
```

Pass `--feature-flags` when `plan-work.featureFlags` is `true`, or when the
plan adds any flag. The file holds `{"issues": [...]}`, one entry per
top-level issue: `identifier`, `title`, `description`, `blockedBy` (other
top-level issues), and `children`, each with `identifier`, `title`,
`description` and `blockedBy` (sibling sub-issues). Use the full Markdown
bodies, and placeholder ids such as `NEW-1` before anything is in the tracker.
It prints `{ready, gaps: [{issue, rule, message}]}` and exits `0` ready, `1`
not ready, `2` bad input. With a team standard, run `plan-work.lint` when
set; otherwise record `Lint: not run (team standard, no lint set)`.

A lint pass does not replace the checks: the lint covers only what a script
can read.

## Plan mode

### P1: Gather sources

Collect everything before deciding the shape. Sources can be any mix of:

- what the user wrote, and the session's conversation so far: decisions
  already made count, with the user as author;
- specs, PRDs, design files, chat threads or pages the user points to;
- an existing ticket or project to restructure, with its comments;
- the repo's own docs and code, read from the default branch.

Read each source in full. One that cannot be read in this session goes under
Open questions; never plan around it as if it said something.

**For screen work, the changed files are a source too.** A spec lists
screens; it does not list what a person can see. Open each file the work
names and note every visible state it renders (empty, loading, error, modal,
callout, tooltip). Each becomes a criterion, per the standard.

**Never invent** user stories, criteria, contracts, payloads, design links,
metric names, flag names or customers. A gap becomes a targeted question,
never a guess in a body.

### P2: Check whether it already exists

Search the tracker by the feature's key terms, and the repo's docs. When the
work, or part of it, already exists, stop before drafting and show:

- what exists, with links;
- how much of the request it covers;
- three ways on: plan it as new work anyway, restructure what exists, or
  review it first.

Wait for the answer. When the user already chose, go on and mention what you
found in the draft.

### P3: Decide the shape

In this order, since each decision depends on the one before:

1. Issue or project (standard §2).
2. Milestones, for a project that releases more than once, with clean-up
   last (§3).
3. Each issue built directly or with sub-issues (§4), using
   `plan-work.repos` or the repos the sources name. When the sources do not
   say whether two parts share state, ask.
4. The Kind of each item built as one PR (§5).
5. Flags (§8): with `plan-work.featureFlags` `true`, each new Feature gets a
   flag, and the clean-up gets a removal issue for it. Name the tool from
   `plan-work.flagEngine`.
6. Required work (§9): check every row; these are the items most often
   forgotten.
7. `blocked by` order.

Write down the reason for each decision, citing the section. **For a project,
or a plan of more than five items, show the tree and reasons and get the shape
approved before writing bodies:** a milestone the user drops wastes every body
written for it. A smaller plan goes straight to P4.

### P4: Write the bodies

Write each item from the standard's templates. Titles follow its title rule.

When a body needs a fact nobody gave, write `<missing: what is missing, see
Qn>` in its place and add question `Qn`. One marker for every gap, so the gaps
can be found and the draft can tell which items are not ready.

Then go through every item against [the checks](#the-checks), lint the draft,
and fix every gap. A draft the lint fails is one an agent cannot build. What
stays unmet because a source is missing goes under Open questions, naming the
item and the rule.

### P5: Show the draft

Show, in this order, and stop:

1. **The shape:** the tree (project, milestones, issues, sub-issues), each
   with title, Kind, labels from `plan-work.labels`, and `blocked by`, plus a
   one-line reason per decision citing the standard.
2. **The bodies:** each description exactly as it would be written. When
   restructuring, mark items new, changed or unchanged, and show the change.
3. **Open questions:** one numbered list, one question per missing fact, each
   naming its item. These never go into a body.
4. **Where the rules came from:** the standard and its ref, and the lint
   verdict or `Lint: not run (<reason>)`.

Write nothing to the tracker until the user approves. Apply edits and show the
draft again. An item that still holds a `<missing: …>` marker is not ready:
do not write it, even when told to, and name what is missing. Items without one
can be written.

### P6: Write to the tracker

Use the tracker tool the session has. Settle the team or project from
`plan-work.team`, else ask; never pick one silently. Write in dependency
order, since each step needs the ids the one before returns:

1. **Labels:** resolve each name from `plan-work.labels` to the tracker's id
   before writing. Label names with emoji or odd spacing often fail to match by
   name. A label that does not resolve: tell the user rather than write the item
   without it.
2. **The project**, then **the milestones** in release order.
3. **The issues**, then **the sub-issues** under them, in the same project and
   milestone.
4. **The relations**, once every id exists. A sub-issue that depends on a
   sub-issue of another issue gets no relation: relate the two parent issues.

**When restructuring,** write only the approved changes. Keep titles, labels,
relations, assignees and states the plan does not change. Add and remove
labels one by one where the tool replaces the whole set. Never delete or
cancel: propose it, and let the user do it.

### P7: Verify

Before calling anything ready:

1. Re-read every created or changed item from the tracker, with its
   sub-issues, labels and relations. Use the bodies as the tracker returns
   them, never the drafts: this catches what writing changed.
2. Build the lint's JSON from what came back and run it.
3. Report each gap with its item and rule before any statement that the work
   is ready. Never say "ready" about a plan that was not linted from the
   tracker.

Report a link for each item in the tree's shape, then anything not written and
why.

### P8: Hand off the line

Each ticket's line, the skills that build it, goes in a comment on the ticket,
written by `plan-assembly-line`, not by this skill.

- `plan-work.role` is `engineer`: run `plan-assembly-line` on the tickets
  just written.
- `other`: stop, and say the line is left for an engineer to plan.
- Empty: ask once whether to plan the line now.

When `plan-assembly-line` is not installed, say so and stop: the tickets are
written, and the line can be planned later.

## Review mode

Review mode reads and reports. It never writes to the tracker, not even a
comment, unless the user asks after seeing the review.

### R1: Read everything

- **An issue:** the issue, its sub-issues, labels, relations both ways, and
  comments; the project and milestone, when there is one.
- **A project:** its summary and description, milestones, every issue and
  sub-issue, their labels and relations.

Read in bulk: one list call by parent or project, asking for descriptions,
labels, states and parents, instead of one call per item. Read every item
before judging any: some findings only show across items, such as a
milestone that is a layer, a dependency with no relation, or the same mistake
on every sub-issue.

### R2: Check each item

Classify each item's role first (issue with sub-issues, issue built directly,
sub-issue), since the same text is judged differently in each. Then run
[the checks](#the-checks) and the lint. Judge what the tracker holds, not what
the work probably was: when a check needs a fact the tracker lacks, neither pass
nor fail it, and ask.

### R3: Report

Read `./references/review-report.md` and fill it exactly, every time: its
sections, order, severity scale and operations, and nothing beyond them. Every
finding carries a **Proposed change** with the exact content to write, built
from the item, the sources and the templates. A missing fact points to its
question; never fill it with a guess.

When the user then wants the items fixed, switch to plan mode with the review
as the source: the proposed changes become the plan, and nothing is written
before P5's approval.

## Output

Run the draft and the report through `summarize-llm-response` when the
session has it; it adds the attribution line the tracker needs. Write ticket
bodies in plain words: short sentences, active voice, no filler.
