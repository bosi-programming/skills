---
name: research
description: Answer the questions of a spike ticket from its sources, the repo and the web, write the answers to ## Findings on the work card, post the doc the ticket's ## Output names as one new ticket comment, then stop at a human gate for a person to approve or ask for changes. The one stage of a spike line. Runs alone on a work card. Use when a ticket holds ## Questions and ## Output and needs its questions answered, or this step redone on a card.
---

# research

The stage that runs a spike. A spike ticket asks questions and names the doc
that answers them; this stage answers each question, cites its sources, posts
the doc on the ticket and stops for a person to approve it. It opens no
tickets: `plan-work` turns the decision into tickets afterwards.

It runs as a stage on the `spike` line under `assembly-line`, and also runs
alone. When a driver hands project rules, paste them word for word under a
`Project rules:` line at the end of the prompt. Prefix each log line `relay:`
under `recipe-relay`, `line:` under `assembly-line`, `unattended:` in a
headless run, and `research:` when run alone.

## Input

The path to a work card, the markdown file that carries a task from one stage
to the next, shaped `../feature-recipe/references/recipe-card-template.md`.
Its `task` names the spike ticket. Read the ticket and its comments through the
session's tracker tool.

With no card, no `task`, or a ticket the tracker cannot read, stop, write
nothing else, set `runStatus: blocked` and log it. There is no verdict.

## Output

The same card, with this stage's parts written:

- `## Findings` — one block per question, then the link of the posted comment.
  A second round appends `### Round <n>` instead of replacing the section.
- `## Decisions` — one line for the verdict.
- `## Open Questions` — one entry per question left `open`.
- `runStatus` — `gate` while the stage waits for a person.
- `lastTouched`.

The verdict is `approved` or `changes`. The stage leaves `phase` and
`phasesCompleted` alone, opens no ticket and commits no code.

## 1. Read the questions

Read the ticket's `## Questions` and `## Output`. Each item under `## Questions`
is one question, numbered in order. `## Output` names the doc to write: its
title and what it holds. Note every source the ticket names: links, files,
tickets, people's notes.

With no `## Questions` or no `## Output`, stop with `runStatus: blocked` and
log which is missing.

## 2. Answer each question

Take the questions one at a time. Use the sources the ticket names first, then
the repo, then the web. Every claim in an answer carries a source: a link, a
`path:line`, or a command and its output. A claim with no source is left out.

A question the sources cannot answer stays `open`: write what was tried, give
no made-up answer, and write an entry to `## Open Questions` with the question
and what was tried.

To answer a question by running something, write throwaway code under
`{scratch}/research/`. It never goes in the checkout and is never committed: the stage ends with no tracked file changed.

## 3. Write the findings

Write `## Findings` on the card, one block per question:

```
### Q<n>: <question as the ticket states it>
Answer: <answer | open>
- <claim> — <source: link, path:line, or command and its output>
Tried: <what was tried>
```

`Tried:` appears only when the answer is `open`. The last line of the section is
`Output comment: <link | not posted — no tracker tool>`, written after
section 4.

## 4. Post the output

Post the doc `## Output` names as one new comment on the ticket, through the
session's tracker tool. It opens with the `## Output` heading and the
attribution line, then the doc's title, then one `### <question>` per question
with its answer and sources. An `open` question says so and lists what was
tried.

The comment is posted before the gate, so a person can read it while the line
waits. A rerun posts a new comment and never edits an old one. Open no ticket.

With no tracker tool in the session, post nothing: the doc stays in
`## Findings`, `Output comment:` reads `not posted — no tracker tool`, and the
gate question says it was not posted.

## 5. Gate

Set `runStatus: gate`. Write the question to `## Open Questions` ("approve the
findings of <ticket>, or say what to change"), post it in chat and stop. The
stage is `gate: human`: `assembly-line` resumes it with the person's answer.

- Approval: log verdict `approved` to `## Decisions`, update `lastTouched` and
  end `approved`. The line ends here.
- A request for changes: log verdict `changes` with what to change, update
  `lastTouched` and end `changes`. The line goes back to `research` at most
  twice, then to a person. The rerun starts at section 2 on the questions the
  person named, appends a `### Round <n>` block to `## Findings` and posts a
  new comment.

## Headless

Read `../feature-recipe/references/headless.md`. In a headless run:

- Prefix each log line `unattended:`.
- A question the sources cannot answer stays `open`; it is never guessed at.
- Section 5 is the stop: the run waits for a person, since approving findings
  is not a decision the run takes for them.

### Ending a run

At the gate, and on a bad input:

1. Write the entry to `## Open Questions`.
2. Set `runStatus: gate` at the gate, or `blocked` on a bad input, and
   `runQuestion` to the entry's id where the card has the field. Leave
   `runNext`, `phase` and `phasesCompleted` alone.
3. Log the stop to `## Decisions`.
