# Mode 2 — Reviewing an NFR doc

Read this file when the engineer asks to **review, validate, audit or
lint** an existing NFR doc, or a draft they hand you. `../SKILL.md`
points here once Mode 2 is the chosen mode.

The goal is a **findings report**: what breaks the standards, what
breaks the template, what breaks the observability plan, and what is a
soft suggestion. Do not change the file unless the engineer says "apply
these fixes" at the end.

The operating principle from `../SKILL.md` applies: don't fabricate
findings. Every finding cites a rule (`./standards.md`,
`./nfr-template.md`, `./iso-quality-models.md` or `./observability.md`)
and a location in the doc. If you can't cite both, don't raise it.

## Step 1 — Locate the doc

The engineer points at the NFRs to review. Read them with the right tool:

- **A file in the repo** — Read it, then check its path against
  `<docsDir>/<project>/nfr.md` (see "Where the doc lives" in
  `../SKILL.md`). A wrong path or a filename other than `nfr.md` is a
  finding. Then check the frontmatter against `./nfr-template.md`: a
  missing field, a `type` other than `nfr`, or a `project` that doesn't
  match the folder is a **warning** that cites the Frontmatter field
  rule.
- **A draft elsewhere** — an issue, a docs page, or text pasted in the
  chat. Skip the path and frontmatter checks, and ask the engineer for
  the project name so you can read its sources in Step 2.

If the engineer hands you several docs, review each one on its own and
add a short total at the top.

## Step 2 — Reread the rules and the sources

Read fresh, every time:

- `./standards.md`
- `./nfr-template.md`
- `./iso-quality-models.md`
- `./observability.md`

Then read the project's sources, as in Mode 1 Step 1: the other docs in
`<docsDir>/<project>/` and the project's specs and design docs. You need
them to check the links and to spot NFRs the doc is missing.

## Step 3 — Walk the four layers

Collect findings for each layer. Fix nothing yet.

**Layer A — standards.** From `./standards.md`. Failures here are
**critical**: the NFR cannot be built or verified as written.

- The statement is specific and measurable: a number, a unit, and a
  window or percentile. "Fast", "secure", "always up" or similar fail.
- The NFR names an ISO characteristic and subcharacteristic, written
  exactly as in `./iso-quality-models.md`.
- The NFR has a MoSCoW priority (Must, Should, Could, Won't).
- The NFR has an architectural impact, or "None".
- The acceptance criteria can pass or fail and carry the number from
  the target.
- The NFR links to a user story, business rule or issue, and the link
  resolves.

**Layer B — template.** From `./nfr-template.md`. Failures here are
**warnings**.

- The doc has the header block and the summary table, and the table
  lists every NFR in the doc and nothing else.
- Every NFR has every template field, in the template's order.
- Every ID follows `NFR-<TYPE>-<NN>`, is unique, and its TYPE matches
  the **Type** field.
- Every statement holds one requirement. An "and" joining two targets
  is a finding.
- Every pair of NFRs that conflict says which one wins.
- `TBD` items name the role that must answer them.
- Every retired NFR keeps its ID and has `Status: Retired — <reason>`.
  When reviewing a change to an existing doc, compare with the previous
  version in git: a renumbered or reused ID is a finding.

**Layer C — observability.** From `./observability.md`. Failures here
are **warnings**, except PII in a log field or metric tag, which is
**critical**.

- Every NFR measured at runtime has logs, metrics, a dashboard widget
  and a monitor.
- Every monitor threshold equals the NFR target.
- Every `N/A` says how the NFR is verified instead.
- Every log, metric, span, dashboard or monitor the doc calls existing
  still exists. Grep the codebase and check the monitoring tool with the
  MCP server or CLI the session has for it. A missing one is a warning; suggest marking it `proposed`.
- The dashboard link in the header resolves, or says `proposed`.

**Layer D — coverage.** Failures here are **suggestions**.

- Each of the 8 NFR types is either covered or not needed. When the
  specs or design docs point at a need the doc doesn't cover (a latency
  target, a client SLA, a regulation), suggest the missing NFR and cite
  the source.
- An NFR that reads as a functional requirement (what the system does,
  not how well) is a finding; suggest moving it to the spec.
- Every law, rule or client requirement named has a source. One with
  no source is a warning.
- Every fact traces to a source. A number with no source is a warning,
  not a suggestion.

## Step 4 — Produce the findings report

Use this shape:

```markdown
# Review: <doc path>

**Reviewed against:** `standards.md`, `nfr-template.md`, `iso-quality-models.md`, `observability.md`
**Findings:** <N critical, M warnings, K suggestions>

## Critical

The NFR cannot be built or verified as written. Fix before merging.

1. **<short title>** — <NFR ID and field, e.g. NFR-PERF-01 › Statement>
   - **Issue:** <what's wrong, quoting the doc>
   - **Rule:** <file and section>
   - **Suggested fix:** <concrete change>

## Warnings

(same shape)

## Suggestions

(same shape)

## Summary

<one or two sentences: is the doc ready to merge? If not, the top one or
two fixes.>
```

## Step 5 — Apply fixes only when asked

End the report by asking whether the engineer wants any fixes applied.
Apply only the items they name.

For a draft outside the repo, don't write back to the issue tracker or
the docs page. Offer to write the fixed version to
`<docsDir>/<project>/nfr.md` instead, following Mode 1.

When you apply a fix to `nfr.md`, bump `last-reviewed` to today in the
same edit.

- **Safe to apply:** missing frontmatter field with a known value,
  missing summary-table row, field order, an existing monitoring item
  that no longer exists marked `proposed`, PII removed from a log field or
  tag.
- **Needs the engineer:** any target number, priority, ISO choice,
  conflict winner, architectural impact, or a missing NFR. Write
  `TBD — needs input from <role>` rather than a guessed value.
