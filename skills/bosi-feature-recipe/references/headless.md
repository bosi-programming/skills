# Headless runs

A headless run is the recipe with no human in the loop: an external agent drives
it, answers what comes up along the way, and carries the work from wherever it
starts to the end of the recipe in one go. It is built for a night run — the
thinking phases are done and the decisions are taken, and the rest should be
finished by morning.

Phases 3 to 6 support it — Cooking, Tasting, Plating, Documentation. Phases 0 to
2 do not: the grill round and the design approval are where intent enters the
recipe, so a run that answered them for itself would be inventing requirements
rather than collecting them.

## Starting one

Pass `--headless`, or say "headless" in the invocation. The flag is the entry
point; the phase that accepts it records it on the card as `runMode: headless`,
because the recipe's premise is that every phase starts in a fresh context and a
flag does not survive one. Phase 0 does this and then routes as usual.

A run starts at the current step and does not stop at the next phase boundary.
It may enter at phase 3 at the earliest: if the card has not completed
`mise-en-place`, Phase 0 stops with `status=blocked` and says why, rather than
drifting into the phases that need a person.

**A human in the room outranks the recorded mode.** `runMode: headless` means
only "nobody is watching". An interactive invocation against a headless card
switches it back and logs the switch; the reverse is logged too. There is no
state in which the recipe turns a person away.

## The shape of a run

1. Start where the card says: Phase 0 routes to the current phase, or the driver
   names the phase file itself.
2. Do that phase's work. When it completes, load, read completely and execute
   the next phase file — the way interactive Cooking already falls through into
   Tasting — and keep going.
3. Stop when the recipe is finished, or when something needs a person. Only the
   phase that ends the run writes the routing line; a phase that hands the baton
   on writes nothing.

So a run from Cooking goes 3 → 4 → 5 → 6 in one turn, and ends with the recipe
delivered rather than with a baton in the air.

## Checkpoints

The checkpoints are the ones each phase already has — Cooking's deviations log,
Tasting's scope-creep findings, Plating's chunk split, PR description and
reviewer routing, Documentation's "is this worth documenting". Nobody is awake
to answer them, so the run takes the phase's own recommendation and keeps
moving:

1. Take the recommendation the phase already states for that checkpoint.
2. Log it to `## Decisions` prefixed `unattended:`, quoting the recommendation,
   so the morning reader can see exactly which calls were made while nobody was
   looking.
3. Where a driving agent is reachable in-process, its answer replaces the
   recommendation — log that one `driver:` instead.

The rule exists so a decision never looks confirmed when nobody confirmed it. A
night run that quietly guesses its way past a checkpoint and writes nothing down
is the failure it guards against — not the act of deciding.

## One-way doors

The run does not open these. It stops and asks, because silence is not consent
and neither is a recommendation.

- Opening a pull request as anything but a draft. A draft is the reversible form
  of a PR: a night run opens drafts, and leaves them drafts.
- Merging, and promoting a draft to ready-for-review.
- Deleting work that was deliberately written.
- Irreversible migrations, force-pushes, history rewrites, credential and
  production changes.

## The routing line

A run ends with exactly one line, the last line of the turn, so the driver never
has to parse prose:

```
RECIPE phase=<phase-token> status=<status> next=<phase-file|none> card=<path>
```

All four keys, space-separated, on one line — the driver parses them by name, so
their order does not matter. `question=<id>` joins them when `status=needs-input`
or `status=blocked`, and the id resolves in the card's `## Open Questions`.

Emit it **bare**: a plain line of output, nothing after it — no closing code
fence, no summary, no sign-off. The fenced blocks in this file are markdown for
whoever is reading it, not part of the line. A driver that reads only the last
line of the turn must get the routing line and nothing else.

| `status` | Means | Driver should |
|---|---|---|
| `terminal` | The run finished the recipe: every phase through Documentation is done. | Read the card, review the PR |
| `needs-input` | The run stopped at a one-way door, recorded as `question=<id>`. | Answer it on the card, then re-run `next` |
| `blocked` | The run cannot continue until something external changes. The reason is `question=<id>`. | Fix what it names, then re-run `next` |

`next=none` when the status is `terminal`; otherwise `next` is the phase to
re-run once the answer or the fix is in.

## What the card says while a run is waiting

A run that stops has not completed the phase it stopped in, so it leaves the
card's position alone: `phase` stays the last completed phase and
`phasesCompleted` is not touched. What changes is `status` — to `needs-input` or
`blocked` — and an entry in `## Open Questions` naming the phase that stopped.

That entry is what a resume routes from. When `status` is `needs-input` or
`blocked`, Phase 0 goes back to the phase named in the question, not forward to
the phase after `phase`: a mid-phase stop would otherwise read as "that phase was
finished" and resume one phase too late.

## What a headless run does not do

- It does not stop at a phase boundary. Finishing Cooking means loading Tasting.
- It does not write a New session / Continue menu, or wait for one.
- It does not finish with a question in prose. The question goes to
  `## Open Questions` and the line carries its id — a driver that reads only the
  last line of the turn must still find something to route on.
- It does not promote a draft, merge or delete. Those wait for the morning.
- It does not invent a tracker, chat or PR link. Where such a tool is missing, it
  records the outcome on the card and says the external update is pending.
