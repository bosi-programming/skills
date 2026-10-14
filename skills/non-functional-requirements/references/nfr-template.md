# NFR Template

```markdown
---
title: <Project name> — Non-functional Requirements
type: nfr
project: <project>
owner: <github-handle-or-@team>
status: draft
last-reviewed: YYYY-MM-DD
tags:
  - nfr
  - <project>
---

# <Project name> — Non-functional Requirements

- Project issue: <link>
- Sources: <docs pages, issues, specs, code paths, monitoring queries used>
- Dashboard: <link, or "proposed">

## Summary

| ID | Type | ISO characteristic › subcharacteristic | Priority | Target |
|---|---|---|---|---|
| NFR-PERF-01 | Performance | 25010 Performance efficiency › Time behaviour | Must | p95 < 2 s per request, monthly |

## NFR-<TYPE>-<NN> — <short title>

- **Status:** Active | Retired — <reason>
- **Type:** <one of the 8 NFR types>
- **ISO:** <standard> <characteristic> › <subcharacteristic>
- **Priority:** Must | Should | Could | Won't — <one line on why>
- **Statement:** The <system part> must <behaviour> <target> <condition>.
- **Measure:** <what is measured and how: formula, percentile, window>
- **Target:** <number and unit>
- **Linked to:** <user story, business rule or issue>
- **Architectural impact:** <what the target forces in the design, or "None">
- **Source:** <where each fact above came from>

### Acceptance criteria

- [ ] <testable check with the number in it>

### Observability

- **Logs:** <event, level, fields, logger tag>
- **Metrics:** <name, type, unit, tags, source>
- **Dashboard widget:** <type, query, target marker>
- **Monitor:** <query, threshold, window, who gets the alert>
```

## Field rules

- **Frontmatter** — when the docs repo has its own frontmatter rules,
  add what they ask for on top of these fields. `type` is `nfr`.
  `project` matches the folder name. `status` starts as `draft` and
  moves to `active` once the team reviews it.
- **ID** — `NFR-<TYPE>-<NN>`, with TYPE one of `PERF`, `REL`, `AVAIL`,
  `SEC`, `USAB`, `PORT`, `SCAL`, `REG`. IDs never change and are never
  reused.
- **Statement** — one sentence, one requirement. Split it when you find
  an "and".
- **Measure and Target** — a number, a unit, and a window or percentile.
  "Fast", "secure" or "always up" fail the check.
- **Priority** — MoSCoW, ranked against the other NFRs of the same
  project:
  - **Must** — the release does not ship without it.
  - **Should** — expected at release; shipping without it needs a
    tracked follow-up.
  - **Could** — worth doing when it costs little.
  - **Won't** — agreed out of scope for this release; kept to record the
    decision.

  Two NFRs that conflict (for example, encryption cost against latency)
  must say which one wins.
- **Linked to** — at least one user story, business rule or issue. An
  NFR linked to nothing is a sign it does not belong to this project.
- **Architectural impact** — name the design choice the target forces:
  cache, queue, retry policy, index, new service, vendor limit. Write
  "None" only after checking.
- **Unknown values** — write `TBD — needs input from <role>`. Never fill
  in a plausible number.
