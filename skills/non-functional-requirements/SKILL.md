---
name: non-functional-requirements
description: Write, update or review a project's non-functional requirements (NFRs) against ISO/IEC 25010:2023 and 25019:2023, with a plan of logs, metrics, dashboards and monitors for each in the project's monitoring tool. Use when planning a project, writing or updating NFRs, setting performance, availability, security, usability or compliance targets, or reviewing an NFR doc.
---

# Write or Review NFRs

## Two modes
This skill has two modes. Pick the right one before doing anything else:

- **Mode 1 — Write.** Produce a new NFR doc, or update an existing one
  with new content sourced from docs pages, the issue tracker, the
  codebase or the monitoring tool. Triggered by verbs like "write", "draft",
  "create", "generate", "update", "migrate this page".
- **Mode 2 — Review.** Audit an existing NFR doc (or a draft the
  engineer hands you) against the standards, the template and the
  observability rules. Produce a findings report. Triggered by verbs
  like "review", "validate", "audit", "check compliance", "does this
  follow the rules".

When the verb is ambiguous ("look at this doc and tell me what's
missing"), ask the engineer which mode they want before reading
anything. Mode 1 ends in a written file; Mode 2 ends in a findings
report. Confusing them wastes work.

The two modes share the operating principle below and re-read the same
standards, but their workflows diverge. Mode 1 is below; Mode 2 follows
after.

## Where the doc lives

The NFR doc of a project is `<docsDir>/<project>/nfr.md`, relative to the
root of the repo that holds the project's docs. `<docsDir>` is the
`non-functional-requirements.docsDir` setting, default `docs/projects`; see
`../setup/references/config.md`. `<project>` is the kebab-case project
name, the same one the project folder already uses when it exists.

## Operating principle: don't fabricate

An NFR that contains plausible-sounding-but-invented details is
worse than no doc at all: the next engineer reads it as ground truth, the
mistake spreads, and the doc becomes a confident source of bugs.

So the bar is hard:

- **Every fact in the output must be traceable to a source the engineer
  provided** (a docs page, an issue, a code path, a config file, a
  monitoring query, a screenshot they pointed you at).
- **When a template field asks for something the sources don't cover,
  stop and ask the engineer.** Do not guess. Do not generalize from
  related features. Do not "complete the picture" from what looks
  reasonable.
- Multiple unknowns can be batched into a single clarification round.

This rule applies to targets, priorities, ISO choices, metric names,
monitor thresholds, laws and regulations alike. If you don't have the
answer, the doc says "TBD — needs input from <role>" and you call it out
in your summary; you do not invent a placeholder that reads as fact.


## Mode 1: Writing NFRs

### Step 1 — Read the standards and what the project has

Read `./references/standards.md`. Then read what the project already has:

- `<docsDir>/<project>/` — an existing `nfr.md`, and any reference,
  discovery or runbook docs beside it.
- The project's specs and design docs, wherever the engineer points.
  They hold the user stories, business rules and architecture the NFRs
  link to.

If `<docsDir>/<project>/nfr.md` already exists, follow "Updating an
existing NFR doc" below.

### Step 2 — Resolve the NFR types

We have 8 types of NFR: performance; reliability; availability;
security; usability; portability; scalability; and regulations/laws.
`./references/iso-quality-models.md` maps each one to its ISO
characteristics.

For each type, decide from the specs and design docs whether the project
needs it:

- **Needed** — a source asks for it, or the project's design depends on
  it (a new external call needs a latency and a failure target; a new
  screen needs a usability target; new PII needs a security target).
- **Not needed** — note one line on why, for the summary.
- **Unclear** — add it to the question round.

For regulations/laws, only name a law, a rule or a client requirement
that a source names: a spec, a contract, or an answer from Compliance
or Security. Never list laws from general knowledge.

### Step 3 — Gather sources

The engineer will name what to draw from. Use the right tool for each
source and pull in parallel when you can:

- **Docs pages** — use the tool the session has for the docs space to
  find and read the pages. Pull the full page, not the search snippet.
  If a page links to others, ask the engineer whether to follow the
  links before fetching more.
- **Issue tracker** — read the issue and its comments (the comments
  often hold the real targets). Capture: title, description, acceptance
  criteria, parent project.
- **Codebase** — use Read / Grep / Glob. Look for what the NFRs
  constrain: external calls and their timeouts and retries, queues,
  caches, PII fields, logger calls and tracing spans. Ask the engineer
  which repos and folders the project touches when it isn't clear.
  Config files often hold per-client limits and SLAs.
- **Monitoring tool** — such as Datadog or Sentry. Use the MCP server or
  CLI the session has for it to read the current numbers for the
  endpoints, spans and screens the project touches: p95 latency,
  error rate, uptime, throughput. They show how far a target is from
  today. They are evidence, not the target: the target still comes from
  a source or from the engineer.

For each source, take notes you can cite back: "timeout from
`src/.../payments.client.ts`", "issue ABC-123 description, paragraph 2",
"Datadog trace, `POST /orders`, p95 over the last 30 days". This is what
makes the "don't fabricate" rule enforceable later.

### Step 4 — Draft the NFRs

Read these before drafting:

- `./references/nfr-template.md` — the doc shape, the frontmatter and
  the field rules.
- `./references/iso-quality-models.md` — the ISO characteristics and how
  the 8 NFR types map to them.
- `./references/observability.md` — the observability plan each NFR carries.

Then, for each NFR type the project needs:

1. **Pick the ISO subcharacteristic.** Use the mapping table. Every NFR
   names its standard, characteristic and subcharacteristic exactly as
   written there.
2. **Write the statement.** One sentence, one requirement, with a number,
   a unit, and a window or percentile. Take the number from the sources.
   If the sources hold no number, write `TBD — needs input from <role>`.
3. **Write the acceptance criteria.** Each criterion is a check a test,
   a monitor or a reviewer can pass or fail, with the number in it.
4. **Link it.** Name the user story, business rule or issue the NFR
   serves.
5. **Note the architectural impact.** Name the design choice the target
   forces, or "None" after checking.
6. **Plan the observability.** For every NFR measured at runtime, write
   the logs, metrics, dashboard widget and monitor in the
   monitoring tool. Reuse what
   already exists before proposing anything new. For NFRs measured
   outside production, write `N/A` and say how they are verified.
7. **Rank it.** Set the MoSCoW priority against the other NFRs of the
   project, and say which one wins when two conflict.

Batch all `TBD` items into one question round before writing the file.

Write the file to `<docsDir>/<project>/nfr.md` with the Write tool.
Confirm the project name with the engineer when no project folder exists
yet.

### Updating an existing NFR doc

When `nfr.md` already exists, the steps above apply with these rules:

- Keep every existing ID. Dashboards and monitors are named after them.
- Never renumber. A new NFR takes the next free number of its type.
- A dropped NFR stays in the doc with `Status: Retired — <reason>` so
  its ID is never reused, and its monitor is listed for removal in the
  summary.
- Bump `last-reviewed` to today.

### Step 5 — Self-check before reporting done

Before telling the engineer the doc is ready, verify:

- [ ] The doc lives at `<docsDir>/<project>/nfr.md`, and `<project>`
      matches the existing project folder when there is one.
- [ ] The frontmatter has every field from `./references/nfr-template.md`,
      with `type: nfr`, `project:` equal to `<project>`, and no
      placeholder left.
- [ ] The doc follows `./references/nfr-template.md`: the summary table
      lists every NFR, and every NFR has all the template fields.
- [ ] Every ID follows `NFR-<TYPE>-<NN>` and is unique in the doc. On an
      update, no existing ID changed.
- [ ] Every NFR names a standard, characteristic and subcharacteristic
      exactly as written in `./references/iso-quality-models.md`. Any
      mismatch with the 8-type mapping was flagged to the engineer.
- [ ] Every statement holds one requirement and contains a number, a
      unit, and a window or percentile. No "fast", "secure", "always
      up", "user-friendly" or similar word stands in for a target.
- [ ] Every acceptance criterion carries the number from the target and
      can be passed or failed by a test, a monitor or a reviewer.
- [ ] Every NFR links to at least one user story, business rule or
      issue, and the link resolves.
- [ ] Every NFR has an architectural impact, or "None" after checking.
- [ ] Every NFR has a MoSCoW priority, and every pair of NFRs that
      conflict says which one wins.
- [ ] Every NFR measured at runtime has logs, metrics, a dashboard
      widget and a monitor. Every monitor threshold equals the NFR
      target. Every `N/A` says how the NFR is verified instead.
- [ ] Every log, metric, span, dashboard and monitor named as existing
      was found in the codebase or in the monitoring tool during this
      run.
      Everything else is marked `proposed`.
- [ ] No log field or metric tag carries PII.
- [ ] Every law, rule or client requirement named has a source.
- [ ] Every fact is traceable to a source. Anything not traceable is
      either gone, marked `TBD`, or was confirmed by the engineer in
      this conversation (note which in your summary).
- [ ] Every NFR type skipped has a one-line reason ready for the
      summary.

Finally, report back to the engineer with:

- The path of the file you wrote.
- The NFRs written, as the summary table.
- The NFR types skipped, each with its reason.
- The list of `TBD` items, each with what's needed and from whom.
- The monitoring items marked `proposed`, so the engineer can build them.
- Anything in the sources that didn't fit the template or the ISO
  mapping — a hint that either the requirement is functional, not
  non-functional, or the standards could evolve.


## Mode 2: Reviewing NFRs

Read `./references/review-workflow.md` and follow it. In short:

1. Locate the doc: an `nfr.md` file (check its path and frontmatter) or
   a draft in the issue tracker, a docs page or the chat (skip both
   checks).
2. Reread the four reference files and the project's sources.
3. Walk four layers: standards (critical), template (warnings),
   observability (warnings; PII is critical), coverage (suggestions).
4. Produce the findings report in the shape the workflow gives.
5. Apply fixes only when the engineer names them. Never fill in a
   target, priority or ISO choice on your own.
