# Headless runs

A headless run is the recipe with no human in the loop: an external agent drives
it, answers what comes up along the way, and carries the work from wherever it
starts to the end of the recipe in one go. It is built for a night run — the
thinking phases are done and the decisions are taken, and the rest should be
finished by morning.

Phases 1 to 6 support it — Reading the Recipe, Mise en Place, Cooking, Tasting,
Plating, Documentation. Only Phase 0 is exempt, and only because it is pure
routing with nothing in it worth a recommendation.

## Starting one

Pass `--headless`, or say "headless" in the invocation. The flag is the entry
point; the phase that accepts it records it on the card as `runMode: headless`,
because the recipe's premise is that every phase starts in a fresh context and a
flag does not survive one. Phase 0 does this and then routes as usual.

A run starts at the current step and does not stop at the next phase boundary.
It may enter at phase 1 for a bare task with no card yet — the same routing an
interactive invocation gets from Phase 0. There is no phase left that needs a
person just to enter it.

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
   phase that ends the run writes the run record; a phase that hands the baton
   on leaves it alone.

So a run from Cooking goes 3 → 4 → 5 → 6 in one turn, and ends with the recipe
delivered rather than with a baton in the air.

## Checkpoints

The checkpoints are the ones each phase already has — Reading the Recipe's
grill-or-skip call and `grill-me` frontier, Mise en Place's section drafts,
cross-check and test-case list, Cooking's deviations log, Tasting's
scope-creep findings, Plating's chunk split, PR description and reviewer
routing, Documentation's "is this worth documenting". Nobody is awake to answer them, so the run takes the
phase's own recommendation and keeps moving:

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

## The run record

A run's result lives on the card, in the frontmatter — never in what the run
prints. A driver that reads only the last line of a turn will miss prose that got
fenced, glued to a heading, or turned into a question; it cannot miss a file at a
known path with a fixed shape.

| Field | Values | Written |
|---|---|---|
| `runStatus` | `running`, `terminal`, `needs-input`, `blocked` | `running` when a run starts; overwritten when it ends |
| `runNext` | a phase file, or `none` | the phase in flight, so a dead run can be resumed; `none` only when the recipe is finished |
| `runQuestion` | an id from `## Open Questions`, or empty | when the run stops on one |

- `terminal` — the recipe is finished, every phase through Documentation done.
- `needs-input` — the run stopped at a one-way door. `runQuestion` names it.
- `blocked` — the run cannot continue until something external changes.
  `runQuestion` names what.
- `running` — a run is in flight. A card left `running` is a run that died: pick
  it up from `runNext`.

Each phase sets `runNext` to its own file as it starts, so the field always names
the phase in flight and a mid-phase stop needs no extra write to be resumable.
The phase that ends the run sets `runStatus`, and `runQuestion` if it stopped
short. `runNext` goes to `none` only when `runStatus` is `terminal`.

The driver's whole loop: read the frontmatter; if `runStatus` is `needs-input` or
`blocked`, deal with `runQuestion`; then run `runNext`, unless it is `none` or
the status is `terminal`, in which case stop.

Nothing about the end of the turn matters for routing. A run may summarise what
it did, or ask a morning reader to look at the card, in whatever words it likes —
the handoff already happened when the frontmatter was written.

## What the card says while a run is waiting

A run that stops has not completed the phase it stopped in, so `phase` stays the
last completed phase and `phasesCompleted` is not touched. Before setting
`runStatus` and `runQuestion`, write the entry itself to `## Open Questions`
first: a short id, the question or reason, any options considered, and the
recommendation. `runQuestion` is only a pointer to that entry — it names
nothing if the entry was never written.

Resume from `runNext`, not from the phase after `phase`: a mid-phase stop would
otherwise read as "that phase was finished" and resume one phase too late. Phase
0 does the same when it is asked to pick a run up.

## What a headless run does not do

- It does not stop at a phase boundary. Finishing Cooking means loading Tasting.
- It does not route through what it prints. The handoff is the frontmatter.
- It does not write a New session / Continue menu, or wait for one.
- It does not promote a draft, merge or delete. Those wait for the morning.
- It does not invent a tracker, chat or PR link. Where such a tool is missing, it
  records the outcome on the card and says the external update is pending.
