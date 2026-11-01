# The bundled planning standard

The rules `plan-work` plans and reviews against when `plan-work.standard`
names no team standard. `../scripts/check_plan.py` checks the parts a script
can check; the rest is checked by reading. Section numbers below are what the
skill cites in its reasons and findings, such as "standard §3".

## 1. Levels

| Level | Is | Done when |
|---|---|---|
| Project | A goal that needs more than one standalone issue | The goal is met and checked, and clean-up is done |
| Milestone | A chunk of a project that can be released on its own | Its issues are done and its exit criteria proven |
| Issue | A standalone piece of functionality | Its acceptance criteria are proven |
| Sub-issue | One repo, one PR of an issue | Its PR merges |

## 2. Issue or project

The test: if the goal is reached once one issue is done, it is an issue. If
reaching it takes several issues that someone must order and track, it is a
project. One of these is usually why:

- the goal is released in steps;
- it needs more than one piece of functionality, each with its own user story;
- it spans teams;
- it rolls out to customers over time, or needs a migration and a retirement.

It is **not** a project when it fits in one issue, however many PRs that
takes; when it has no end (bugs, tech debt and routine work belong to labels
and views); or when it is one issue plus its rollout or flag removal.

A project holds: a one-sentence goal written as an outcome, and a description
with **Goal**, **Why now**, **How we would know it worked** (something that can
be checked once done), **Links**, **Scope**, **Out of scope** and
**Clean-up**. It does not list its issues: the tracker shows them.

## 3. Milestones

A project needs milestones only when it releases more than once. Each
milestone is one of three kinds:

| Kind | Releases |
|---|---|
| Internal checkpoint | Something the team builds on, with no change the user sees |
| Customer release | Part of the feature users can use, for the users or customers it names |
| Clean-up | What the project left behind: flags, legacy paths, docs to fold into references |

- **A milestone is a vertical slice, never a layer.** One milestone per repo
  or per layer releases nothing until the last lands.
- **Name:** `<n>. <what is released>`, numbered from 1 in release order.
- **Description:** kind, what is released and to whom, exit criteria (each
  with a proof tag, §7), out of scope.
- **Every project with milestones ends with a clean-up milestone**, even when
  it holds one issue.
- No milestone holds an open question: a question becomes a discovery issue
  that `blocks` the milestone's issues.

## 4. Issues and sub-issues

An issue is split into sub-issues only when it needs more than one PR or more
than one repo.

| The issue needs | Built as |
|---|---|
| One repo, one PR | The issue itself, with no sub-issues |
| More than one PR or repo | The issue plus one sub-issue per repo or area, each one PR |

- The issue holds the user story, the decisions, a high-level technical design
  (approach, the contracts between sub-issues, the feature flags) and the out
  of scope. Its criteria are about the functionality, from the user's side.
- Each sub-issue holds one part: what it adds, its detailed design, its one
  repo, and criteria that prove the part works on its own.
- **Never one sub-issue.** Work that fits one PR is built directly.
- **At most one sub-issue per area in a repo.** A part too big for one PR
  means the issue is too big: it becomes several issues in a project.
- **Sub-issues block each other only where one needs another**, with the
  tracker's `blocked by` relation. Sub-issues of different issues never relate
  to each other: relate their parent issues.
- **The issues are the spec.** Each issue and sub-issue carries every detail
  needed to build it. A design doc may be linked for context, never in place
  of the detail.

## 5. Kind

Whatever is built as one PR has one Kind, which adds its block:

| Kind | Is | Block |
|---|---|---|
| Feature | New or changed behaviour | `## Before → after`: what the user sees today, and after |
| Bug | Behaviour differs from what was intended | On the issue: `## Bug report` (where seen, steps, expected vs actual). On each part: `## Root cause`, and one criterion that fails on the default branch |
| Enablement | Work that enables other work with no behaviour change: refactor, discovery, decision, tooling, observability | `## Why this shape` and `## Behaviour held constant`. A discovery has `## Questions` and `## Output` (a doc) instead |

Work that removes a flag, a path or a config is Enablement and carries
`## Removes`, listing what goes. A feature flag does not change the Kind: judge
it with the flag on.

## 6. Templates

Headings are exact: the lint reads them.

**Issue**

```markdown
## What
<one paragraph: what the issue delivers, as an outcome>

## How this impacts the final user
<one paragraph: what the user sees or does differently; when the work does not reach users, say so and name the indirect benefit>

## Goal & measure
- **What changes for whom:** <outcome and who it reaches>
- **Where we see it:** <dashboard, query, metric or report the sources name>
- **After release:** <signal to watch and the direction that counts as success>

## Context
<why now: the problem, the trigger, related tickets and docs>

## Decisions
<only when a product or tech-lead call was made>

## Technical design
- Approach: <how it is built>

### Contracts
<only with two or more sub-issues: each shape one part produces and another consumes>

### Feature flags
<only when it adds a flag: one `flag-key` per line>

## Out of scope
- <what the issue does not cover>

## Acceptance criteria
- [ ] #1 [<tag>] <criterion>
```

An issue built directly adds `## Repos and key paths` (below) and may use
part tags. When the work has no product signal, `## Goal & measure` holds one
line, `- **No product metric:** <indirect benefit and how to check it>`.

**Sub-issue**

```markdown
## What
<the part this sub-issue builds>

## Technical design
- Approach: <how>
- Data: <tables, fields, payloads>

## Repos and key paths
- Repo: `<repo>`
- `<key path>`

## Acceptance criteria
- [ ] #1 [<tag>] <criterion>
```

Add the Kind block (§5) to each part, and to the issue for a Bug report.

Titles: an issue with sub-issues gets a plain-language title; an issue built
directly and each sub-issue get the PR's title format.

## 7. Acceptance criteria

A criterion reads `- [ ] #<n> [<tag>] <criterion>`, numbered from `#1` in
order. Renumber the whole list after adding, removing or moving one.

| Tag | Proven by |
|---|---|
| `[unit]` | A unit test in the diff |
| `[int]` | An integration test in the diff (database, mocked network) |
| `[api]` | A real HTTP call against the running API, request and response kept |
| `[e2e]` | An end-to-end test in the diff that calls the endpoint and asserts its contract |
| `[ui]` | Driving the screen as a user: `As <who> on <screen>, when I <action>, then <what they see>` |
| `[story]` | A component story in the diff, one per state |
| `[run]` | A tool, job or query run on a real case, with its output |
| `[docs]` | The docs build passing and the rendered page |
| `[manual]` | A named person, with the reason it cannot be automated: `... because <reason>` |

- **An issue with sub-issues uses behaviour tags only**: `[ui]`, `[api]`,
  `[e2e]`, `[run]`, `[docs]`, `[manual]`. `[unit]`, `[int]` and `[story]` prove
  a part, so they go on sub-issues or on an issue built directly.
- Types, lint and formatting are not criteria: CI runs them on every PR.
- Each `[ui]` criterion names one user and one starting state. Each visible
  state a changed component can show (empty, loading, error, modal, callout)
  gets its own criterion.

## 8. Feature flags

Read from the settings, `plan-work.featureFlags` and `plan-work.flagEngine`.

- **`featureFlags: true`** puts every new Feature behind a flag. The issue
  names the flag under `### Feature flags`; a criterion proves nothing changes
  with the flag off (it names the flag and says `off`); a `[manual]` criterion
  names who turns it on, where, and why that cannot be automated; and a clean-up
  issue with `## Removes` takes the flag out, `blocked by` the release.
- **`featureFlags: false`** plans a flag only when a source asks for one, and
  then follows the same rules.
- **`flagEngine`** names the tool (a flag service, an env var). The design,
  the turn-on criterion and the removal issue name it. When empty, write
  "feature flag" and ask which tool under Open questions.

## 9. Required by the change

| When the change | It must carry |
|---|---|
| Adds a feature flag | A flag-off criterion and a removal issue (§8) |
| Adds or changes an endpoint's request or response | One `[e2e]` or `[api]` criterion per scenario, asserting the contract |
| Introduces or changes a UX flow | An end-to-end or journey test part, last, blocked by the parts it drives |
| Changes a screen inside an existing flow | A `[ui]` criterion that the tests covering the flow still pass |
| Adds or changes a component | A `[story]` criterion, one per state |
| Changes behaviour a doc describes | A docs issue or part, or a criterion on the part that changes the doc |
| Claims a product outcome | `## Goal & measure` with each bullet traced to a source |
| Removes a path, config or schema | `## Removes`, tests of kept behaviour unchanged, and data showing nobody reaches the path |

## 10. Always

- No `<placeholder>`, `<missing: …>`, TBD or TODO left in anything written to
  the tracker.
- Every dependency is a `blocked by` relation, never prose.
- Nothing the tracker already shows (status, assignee, estimate, child list)
  is repeated in a description.
- Nothing is invented: a fact no source gives becomes a question.
