# Planning standard

What a ticket must look like before `plan-work` writes it, unless
`plan-work.standard` points to the team's own rules. `../scripts/check_plan.py`
enforces what a script can parse; the rest is up to the reader. `plan-work`
cites these sections by letter, such as "standard B".

## A. Proving each criterion

Start a plan from what has to be proven, then build the tickets around it.

Every criterion is one checkbox line: `- [ ] #<n> [<tag>] <criterion>`. The
numbers run 1, 2, 3 down the list; after an insert, delete or move, number the
list again from the top.

The tag says what evidence closes the box:

- `[unit]`: a unit test that the PR adds or changes.
- `[int]`: a test in the PR that hits a real database or a stubbed network.
- `[api]`: a call to the running API, with request and response saved.
- `[e2e]`: an end-to-end test in the PR that calls the endpoint and checks
  what comes back.
- `[ui]`: someone using the screen. Write it as `As <who> on <screen>, when I
  <action>, then <what they see>`, with one person and one starting state per
  line.
- `[story]`: a component story in the PR, one per state the component shows.
- `[run]`: a script, job or query run on a real case, output attached.
- `[docs]`: the docs build passes and the page renders.
- `[design]`: the frames exist at the design link. Design tickets only.
- `[manual]`: a named person checks it. The line says why a machine can't, as
  `... because <reason>`.

Three limits:

- `[unit]`, `[int]` and `[story]` prove one piece of code. They belong on a
  sub-issue, or on a ticket that has no sub-issues. A ticket with sub-issues
  speaks only for the whole feature: `[ui]`, `[api]`, `[e2e]`, `[run]`,
  `[docs]`, `[manual]`.
- CI already runs types, lint and formatting. Don't list them.
- A changed component shows states: empty, loading, error, a dialog, a banner,
  a tooltip. Give each one its own line.
- Notes under a criterion go on indented lines; only top-level lines count as
  criteria.

## B. Ticket bodies

Use these headings word for word; the lint looks for them. Every body opens
with the line Planned with `plan-work`. above `## What`; it tells `plan-assembly-line` that
`plan-work` already checked the ticket.

**Ticket**

```markdown
Planned with `plan-work`.

## What
<one paragraph: the result, not the steps>

## Who notices and how
<one paragraph: what changes for the people who use it; if nobody outside the team notices, say that and name the gain behind it>

## Goal & measure
- **What changes for whom:** <result and the people it reaches>
- **Where we see it:** <a dashboard, query, metric or report a source names>
- **After release:** <the signal to watch and which way counts as success>

## Context
<why this, why now; links to related tickets and docs>

## Decisions
<only calls a product owner or tech lead already made>

## Technical design
- Approach: <how it gets built>

### Contracts
<when there are two or more sub-issues: each payload, event or config one makes and another reads>

### Feature flags
<when it adds a flag: one `flag-key` per line>

## Out of scope
- <what this ticket leaves out>

## Acceptance criteria
- [ ] #1 [<tag>] <criterion>
```

No product signal? Replace the three Goal bullets with one:
`- **No product metric:** <the gain, and how to tell it held>`. Use it only
when the work changes nothing users do, such as a refactor or tooling. When a
Feature should move a signal but no source names one, write
`[[gap Qn: …]]` and ask.

Put code, markup and literal words like `TODO` in backticks or a fenced
block; the lint skips them when it looks for leftovers.

A ticket with no sub-issues also carries `## Repos and key paths` (below), and
may use any tag.

**Sub-issue**

```markdown
Planned with `plan-work`.

## What
<the piece this sub-issue adds>

## Technical design
- Approach: <how>
- Data: <tables, fields, payloads>

## Repos and key paths
- Repo: `<repo>`
- `<key path>`

## Acceptance criteria
- [ ] #1 [<tag>] <criterion>
```

Each piece also gets its kind's block (C).

**Screen work.** Any piece with a `[ui]` or `[story]` criterion carries a
`## Design` section. On a split ticket it goes on each screen sub-issue, or
once on the ticket.

```markdown
## Design
- Link: <the design file or frame>
- <screen>: ![now](<screenshot of today>) → ![after](<screenshot of the design>)
```

One line per changed screen or state, so a reviewer can compare before and
after without opening the design tool. When nothing looks different, write
`- No visual change: <why>`. When the design does not exist yet, write
`- No design yet: <design ticket id>`, and plan that design ticket (C).

**Titles.** A ticket with sub-issues gets a sentence a customer could read. A
sub-issue, or a ticket built in one PR, gets the repo's PR title format.

## C. Kinds

Each piece of work is one of four kinds, and the kind
adds a block:

- **Feature**, new or changed behaviour: `## Before → after`, what someone sees
  now and what they will see.
- **Bug**, behaviour that is not what was meant: the ticket gets
  `## Bug report` (where it showed up, steps, what was expected and what
  happened). Each piece gets `## Root cause` and a criterion that fails on the
  default branch today.
- **Enablement**, work that changes no behaviour but unblocks other work (a
  refactor, a spike, a decision, tooling, monitoring): `## Why this shape` and
  `## Behaviour held constant`. A spike lists `## Questions` and the doc it
  produces under `## Output`.

- **Design**, mock-ups or flows with no code: a ticket of its own, never a
  sub-issue, with no `## Technical design` or `## Repos and key paths`. In
  their place it has:

  ```markdown
  ## Design deliverable
  - Screens: <screens and states it covers>
  - Where it lands: <the design file or folder>
  - Frontend ticket: <id of the ticket that builds it>
  ```

  Its criteria use `[design]`: the frames exist at the link, one line per
  screen or state. A design ticket always leads to a frontend ticket. Name an
  existing one, or plan a new one in the same plan, `blocked by` the design
  ticket. Either way, once the design is done, the frontend ticket's
  `## Design` gets the link and the screenshots, replacing its
  `No design yet` line.

In a split ticket, `## Before → after` and `## Bug report` go on the ticket;
`## Root cause`, `## Why this shape` and `## Behaviour held constant` go on
each piece.

Taking something out (a flag, a code path, a config key) is Enablement, with
`## Removes` listing each thing that goes. Judge the kind of flagged work as if
the flag were on.

## D. When to split a ticket

Ask first: does it fit in one PR, in one repo? Then it is one ticket and
nothing more.

Otherwise:

- The ticket keeps the feature-level view: who it is for, decisions, the
  approach, the contracts between pieces, flags, and what is out of scope. Its
  criteria read from the user's side.
- Each sub-issue is one PR in one repo. It says what it adds, how, and where,
  and its criteria prove that piece in isolation.
- Two sub-issues or more. One alone means the ticket should be built directly.
- If one piece won't fit in a PR, the ticket is doing too much. Make it a
  project with several tickets (G) instead of adding sub-issues.
- Link pieces with `blocked by` only where one truly waits on another. When a
  sub-issue waits on a sub-issue under a different ticket, link the two
  tickets instead.
- Write every detail a builder needs into the tickets themselves. Link a
  design doc for background if you like, but never as the only place a detail
  lives.

## E. Work a change brings with it

Some changes always bring extra work. Check every line:

- New feature flag: a flag-off criterion and a removal ticket (F).
- New or changed endpoint: an `[e2e]` or `[api]` line per scenario, checking
  the contract.
- New or changed user flow: an end-to-end test piece, placed last, blocked by
  the pieces it exercises.
- Screen change inside a flow that stays the same: a `[ui]` line that the
  flow's existing tests still pass.
- New or changed component: a `[story]` line per state.
- Any screen change: `## Design` with the link and before/after screenshots,
  or a design ticket that the frontend work waits on (B, C).
- Behaviour a doc describes: a docs piece, or a line on the piece that edits
  the doc.
- A claim about a product result: Goal & measure, each bullet backed by a
  source.
- Code, config or schema taken out: `## Removes`, unchanged tests for what
  stays, and data showing nobody still hits it.

## F. Feature flags

Driven by `plan-work.featureFlags` and `plan-work.flagEngine`.

- With `featureFlags: true`, each new Feature ships behind a flag. Name it
  under `### Feature flags`. Add a criterion that names the flag and says
  nothing changes while it is `off`. Add a `[manual]` line saying who turns it
  on, where, and why that is not automated. Add a clean-up ticket with
  `## Removes` for it, blocked by the release.
- With `featureFlags: false`, add a flag only when a source asks for one, and
  then apply the same four rules.
- `flagEngine` names the tool (a flag service, an environment variable). Put
  it in the design, the turn-on line and the removal ticket. Left empty, write
  "feature flag" and ask in the questions which tool to use.

## G. Projects and milestones

A project is for a goal no single ticket reaches. If the goal is met when one
ticket closes, there is no project. Signs that you need one: the goal ships in
stages; it holds several user stories; more than one team works on it; or it
reaches customers bit by bit, through a migration and a cut-over. It is not a
project when it fits in one ticket however many PRs that takes, when it never
ends (bugs, debt and routine work go in labels and views), or when it is a
ticket plus its rollout or flag removal.

A project's description covers **Goal** (one sentence, as a result), **Why
now**, **How we would know it worked** (something you can check at the end),
**Links**, **Scope**, **Out of scope** and **Clean-up**. The tracker already
lists its tickets; don't repeat them.

Milestones only matter when a project ships more than once. Each milestone
ships something on its own, cutting across every repo it needs; a milestone
that is "the backend" or "the UI" ships nothing until the rest lands. Three
kinds:

- **Groundwork**: something the team builds on, invisible to users.
- **Release**: a part users can use, for the users or customers it names.
- **Clean-up**: removing what the project left behind (flags, old paths) and
  folding notes into reference docs. Every project with milestones ends with
  one, even if it holds a single ticket.

Name each one `<n>. <what ships>`, counting from 1 in shipping order. Its
description gives the kind, what ships and to whom, exit criteria tagged as in
A, and what it leaves out. A milestone never holds an open question: turn the
question into a spike ticket that blocks the milestone's tickets.

## H. Before anything is written

- No `[[gap …]]`, `<placeholder>`, TBD or TODO left.
- Every "waits on" is a `blocked by` link, not a sentence.
- Nothing the tracker shows on its own (status, owner, estimate, child list)
  is copied into a body.
- No fact without a source. A missing fact becomes a question.
