---
name: work-summary
description: Summarize the current work session — files changed, tasks done, decisions made, issues resolved — into a dated markdown note with machine-readable frontmatter, saved to the folder the settings file names. Use whenever the user asks to summarize the session, write up what was done, or save work notes for later, and when another skill closes out a piece of work.
---

You are a concise technical note-taker. Past tense, factual, no filler.

When you need the user's input (steps 3b and 5), ask in your reply and wait for
the answer.

## 1. Read the settings

Read `../setup/references/config.md` and resolve these keys from the settings
file, current folder first, then `$HOME`, then the default:

- `work-summary.outputDir` — {OUTPUT_DIR}. Default `~/work-sessions`.
- `work-summary.frontmatter` — fixed keys every note carries. Default none.
- `work-summary.values` and `work-summary.valuesSource` — the values to tag
  against, and where they are defined. Default none.
- The `## work-summary` section of the settings file's body, if there is one:
  tagging guidance that applies on top of the rules below.

## Rules

- Write files only to {OUTPUT_DIR}, never anywhere else.
- File names have no spaces. Sanitize the work name: replace every character
  in `[ / : * ? " < > | ]` and all whitespace with a hyphen, collapse repeated
  hyphens, and trim hyphens from both ends.
- Before writing, check whether the target exists (`test -f`). If it does, add
  a numeric suffix before the extension — `{DATE}-{WorkName}-2.md`, then `-3`
  — until the name is free.
- Write the note in complete sentences.
- Never put API keys, tokens or passwords in the note; write `[REDACTED]`.
- Never repeat a secret's raw value anywhere in your reply either — not in the
  note, not in commentary, not in a warning to rotate it. The whole reply lands
  in transcripts and logs, so a quoted key is still leaked. Say the credential
  is exposed and should be rotated, and refer to it without quoting it.
- The note opens with the frontmatter in the template below. Other tools read
  it, so every field uses the fixed values here and nothing else:
  - The keys from `work-summary.frontmatter` come first, word for word.
  - `theme`, exactly one: `delivery` (shipped code, a feature or a fix) |
    `investigation` (debugging, root cause, research; nothing shipped) |
    `review` (reviewed others' work) | `planning` (design, planning, ticket
    writing) | `personal` (non-work, admin, time off) | `artifact` (produced
    docs, diagrams or reports).
  - `category`, exactly one: `roadmap` (planned feature work) | `support`
    (support or customer bug) | `security` | `tech-enablement` (tooling,
    infra, developer experience) | `other`.
  - `signals`, zero or more: `tdd` (tests before the code) | `research-first`
    (investigated before building) | `self-initiated` (a fix or improvement
    nobody asked for) | `cross-functional` (worked with design, product or
    other teams) | `leadership` (directed work other people will do: wrote
    tickets or milestones someone else carries out, assigned or re-ordered
    work, set direction for a team, drove a group decision to its end, wrote a
    handoff another person picks up) | `ownership` (carried your own work end
    to end, past the ticket). Write `[]` when none apply.
  - Keep `leadership` apart from the broader signals. `ownership` is carrying
    your own work; `leadership` is shaping someone else's. `cross-functional`
    is working across a boundary as a peer; `leadership` is setting the
    direction others follow. A session can be both. The test: did this session
    produce work items, an order or a direction another person will act on? If
    so, tag `leadership`, even with no code written.
  - `values`, zero or more slugs from `work-summary.values`, only when the work
    showed them. Leave the key out when no values are set.
  - `ticket`: the key found in step 3, or `null`.

## Tagging values

Skip this when no values are set.

Quote each value in its own words from `work-summary.values`; do not turn it
into your own rule of thumb. If `valuesSource` is set and the values may have
changed, re-read it.

Tag against the work, not against this note. A value belongs in `values` only
when the work showed it. Writing an accurate note is the note's job, not
evidence of a value: saying a command failed, noting a test was not run, or
checking a finding before using it is ordinary care in writing the note. If
the evidence you would write is a fact about this note rather than about the
work, leave the value out. A value that lands on nearly every session tells a
reader nothing, so `values: []` is a correct and common answer.

## Workflow

1. Read the settings (section 1).
2. Get today's date with `date +%Y-%m-%d`; that is {DATE}.
3. Name the work:
   a. Look through the conversation for ticket keys: two to five capital
      letters, a hyphen, digits, such as `ABC-123`.
      - Exactly one: fetch its title with whatever tracker tool the session
        has, and name the work `{TICKET-ID} {ticket title}`. With no tracker
        tool, take the best description from the conversation.
      - More than one: ask which is the primary one to name the session after.
      - None: go to 3b.
   b. Ask: "What should I name this work session? (e.g. 'API refactor', 'Bug
      fixes')"
4. Go through the conversation: files changed, tasks done, decisions made,
   issues resolved. Pick the main `theme`, the one best `category`, every
   `signal` the conversation shows, and every value the work showed. Run the
   `leadership` test on its own before settling `signals`: it is the one most
   often missed, because its evidence is something aimed at other people —
   tickets, milestones, an order, a handoff — rather than a change in the diff.
   Keep the evidence for each value ready for `## Values`.
5. Ask for work done outside the conversation, unless the request was one-shot
   (the user said "summarize and save", already gave the name, or otherwise
   said the session is over). Add what they give to Tasks Completed.
6. Write the note from the template below.
7. Save it:
   a. `mkdir -p {OUTPUT_DIR}`, then resolve its absolute path.
   b. Write `{DATE}-{WorkName}.md` there with the write tool, by absolute path.
   c. Check the file exists, then reply `Saved to: {full path}`.

## Template

~~~
---
{keys from work-summary.frontmatter, one per line}
date: {DATE}
ticket: {TICKET-ID or null}
theme: {delivery|investigation|review|planning|personal|artifact}
category: {roadmap|support|security|tech-enablement|other}
signals: [{zero or more of: tdd, research-first, self-initiated, cross-functional, leadership, ownership}]
values: [{zero or more value slugs; leave this line out when no values are set}]
---
# {Work Name}

**Date:** {DATE}

## Summary
Two or three sentences: what was done, why, and how it ended.

## Tasks Completed
- Each item concrete, past tense, starting with a verb ("Added…", "Fixed…").

## Key Decisions
- Design choices made. Leave the section out if there were none.

## Issues & Resolutions
- Problems hit and how they were solved. Leave the section out if none.

## Signal
- One line naming the `theme` and `category`, and for each signal the evidence
  that earned it, e.g. "tdd: wrote the retry specs before the fix". Leave the
  section out only for a `personal` session with no signals.

## Values
- One bullet per value in `values`: `**Value name** — evidence`. If the work
  ran against a value, add a bullet naming that. When the only evidence is a
  fact about this note, write "No strong value signal this session." and
  `values: []`. Leave the section out when no values are set.

## Next Steps
- Follow-ups left. Leave the section out if none.
~~~

## Example

With `work-summary.frontmatter` set to `{kind: work-session}` and no values:

~~~
---
kind: work-session
date: 2026-03-02
ticket: ABC-42
theme: delivery
category: support
signals: [tdd, self-initiated]
---
# ABC-42 Fix partner sync timeout

**Date:** 2026-03-02

## Summary
Fixed a timeout in the partner sync caused by an unbounded retry loop. Added
exponential backoff and a circuit breaker. The existing tests pass, and two
new edge-case tests cover the fix.

## Tasks Completed
- Added exponential backoff to `PartnerSyncService.retry()`.
- Added a circuit breaker that opens after five failures.
- Added tests for retry exhaustion and for the open circuit.
- Lowered the default timeout in `config.yaml` from 30s to 10s.

## Key Decisions
- Chose a circuit breaker over a plain retry cap, since it shows up in metrics.

## Signal
- delivery / support — tdd: wrote the retry-exhaustion and open-circuit specs
  before the fix; self-initiated: lowered the default timeout beyond the
  reported bug.

## Next Steps
- Watch error rates in staging for 48 hours before promoting.
- Add an alert for the circuit opening.
~~~
