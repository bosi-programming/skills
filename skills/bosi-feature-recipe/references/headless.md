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

Keys in that order, space-separated. `question=<id>` is appended when
`status=needs-input` or `status=blocked`, and the id resolves in the card's
`## Open Questions`.

`next` is what to run *after* the status has been dealt with, so a driver with
no routing logic of its own just follows it:

| `status` | Means | Driver should |
|---|---|---|
| `done` | The phase finished and the card is updated. | Run `next` |
| `needs-input` | A checkpoint needs an answer, recorded as `question=<id>`. | Answer it on the card, then re-run `next`, which is this same phase |
| `blocked` | The run cannot continue without a person or a tool that is not here. The reason is `question=<id>`. | Fix what it names, then re-run `next` |
| `terminal` | The recipe is finished. | Stop |

`next=none` when the status is `terminal`.

## One turn per phase

Interactive Cooking falls straight through into Tasting without stopping, so a
human is only asked once. A headless run breaks that pair: every phase ends its
own turn, which is what lets the driver own the boundary and the driver's loop
stay a single shape — run the file in `next`, read the line, act on the status.

## What a headless phase does not do

- It does not load the next phase file. It names it in `next` and ends.
- It does not write a New session / Continue menu, or wait for one.
- It does not invent a tracker, chat or PR link. Where such a tool is missing,
  it records the outcome on the card and says the external update is pending.
