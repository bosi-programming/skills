# Headless runs

A headless run is the recipe with no human in the loop: an external agent
drives the flow, answers the checkpoints, and carries each phase's output into
the next. Phases 3 to 6 support it — Cooking, Tasting, Plating, Documentation.
Phases 0 to 2 do not: the grill round and the design approval are where intent
enters the recipe, so a phase that answered them for itself would be inventing
requirements rather than collecting them.

Nothing else about a phase changes. A headless run does the same work, in the
same order, writing the same card — it only ends its turn differently.

## Starting one

Pass `--headless`, or say "headless" in the invocation. The flag is the entry
point; the phase that accepts it records it on the card as `runMode: headless`,
because the recipe's premise is that every phase starts in a fresh context and
a flag does not survive one. Phase 0 does this and then routes as usual.

A headless run may enter at phase 3 at the earliest. If the card has not
completed `mise-en-place`, Phase 0 stops with `status=blocked` and says why,
rather than drifting into the phases that need a person.

**A human in the room outranks the recorded mode.** `runMode: headless` means
only "nobody showed up". An interactive invocation against a headless card
switches it back and logs the switch; the reverse is logged too. There is no
state in which the recipe turns a person away.

## Checkpoints

The checkpoints are the ones each phase already has — Cooking's deviations log,
Tasting's scope-creep findings, Plating's chunk split, PR description and
reviewer routing, Documentation's "is this worth documenting". A headless run
neither skips them nor answers them itself.

1. Put the checkpoint to the agent driving the run: the question, the options,
   and the phase's own recommendation, with the evidence needed to decide.
2. Use the answer, and log it to `## Decisions` prefixed `driver:`.
3. If nothing in-process can answer — a one-shot invocation with nobody on the
   other end — stop instead of guessing. Write the question, its options and
   the recommendation to `## Open Questions` on the card under a short id, then
   end the turn with `status=needs-input` and `question=<id>`. The next
   invocation answers it by id and the phase resumes from there.

Answering the checkpoint yourself to get past it is the failure this whole mode
guards against. A recommendation is not an answer: if no driver gave one, the
checkpoint is still open, and a run that decides it quietly produces the exact
outcome a person would have refused. Record it and ask.

## One-way doors

A headless run does not open these. It stops and waits for an explicit answer
instead — silence is not consent.

- Opening a pull request as anything but a draft. A draft is the reversible
  form of a PR, and headless Plating opens drafts.
- Merging, and promoting a draft to ready-for-review before CI is green.
- Deleting work that was deliberately written.
- Irreversible migrations, force-pushes, history rewrites, credential and
  production changes.

## The routing line

Every headless phase ends its turn with exactly one routing line, as the last
line of the response, so the driver never has to parse prose:

```
RECIPE phase=<phase-token> status=<status> next=<phase-file|none> card=<path>
```

All four of those keys, space-separated, on one line — the driver parses them
by name, so their order does not matter. `question=<id>` joins them when
`status=needs-input` or `status=blocked`, and the id resolves in the card's
`## Open Questions`.

Emit it **bare**: a plain line of output, nothing after it — no closing code
fence, no summary, no sign-off. The fenced blocks in this file are markdown for
whoever is reading it, not part of the line. A driver that reads only the last
line of the turn must get the routing line and nothing else.

`next` is what to run *after* the status has been dealt with, so a driver with
no routing logic of its own just follows it:

| `status` | Means | Driver should |
|---|---|---|
| `done` | The phase finished and the card is updated. | Run `next` |
| `needs-input` | A checkpoint needs an answer, recorded as `question=<id>`. | Answer it on the card, then re-run `next`, which is this same phase |
| `blocked` | The run cannot continue without a person or a tool that is not here. The reason is `question=<id>`. | Fix what it names, then re-run `next` |
| `terminal` | The recipe is finished. | Stop |

`next=none` when the status is `terminal`.

## The driver's loop

A headless run is not one long turn. Phase 0 starts it; from there the driver
runs one phase per invocation and follows `next`:

1. Run the file named in `next` — or, for the first one, let Phase 0 pick it
   from the card.
2. Read the last line of the turn.
3. `done`: run `next`. `needs-input` or `blocked`: deal with `question=<id>`,
   then run `next`, which is the same phase. `terminal`: stop. Nothing else
   ends the run.

A phase that closes cleanly and hands back is a finished step, not a
half-finished recipe — everything it did is on the card, and the recipe is done
when a line says `terminal`. A driver that wants the whole thing in one go
loops on that until it reads one.

## What the card says while a run is waiting

A phase that stops to ask has not completed, so it leaves the card's position
alone: `phase` stays the last completed phase and `phasesCompleted` is not
touched. What changes is `status` — to `needs-input` or `blocked` — and an
entry in `## Open Questions` naming the phase that asked.

That entry is what a resume routes from. When `status` is `needs-input` or
`blocked`, Phase 0 goes back to the phase named in the question, not forward to
the phase after `phase`; a mid-phase stop would otherwise read as "that phase
was finished" and resume one phase too late.

## One turn per phase

Interactive Cooking falls straight through into Tasting without stopping, so a
human is only asked once. A headless run breaks that pair: every phase ends its
own turn, which is what lets the driver own the boundary and the driver's loop
stay a single shape — run the file in `next`, read the line, act on the status.

## What a headless phase does not do

- It does not load the next phase file. It names it in `next` and ends.
- It does not write a New session / Continue menu, or wait for one.
- It does not finish with a question in prose. The question goes to
  `## Open Questions` and the line carries its id — a driver that reads only
  the last line of the turn must still find something to route on. Asking
  conversationally and stopping leaves the run with no way forward.
- It does not invent a tracker, chat or PR link. Where such a tool is missing,
  it records the outcome on the card and says the external update is pending.
