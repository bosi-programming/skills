# Phase 0 — Start / Resume

This phase is the entry gate, not a work phase. It doesn't produce anything
worth a session break, so unlike every phase after it, it does **not** end
with the New session / Continue menu — it routes straight into whichever phase
file comes next and that phase's own ending is where the user gets asked.

## 0. Headless invocations

If the invocation says `--headless` or "headless", no human is in the loop and
nothing may be asked of one. Read `../references/headless.md` — it is the
contract — then:

- Take the task from the invocation text instead of asking what it is, and take
  the default card root instead of asking where cards go. Log both to
  `## Decisions` prefixed `driver:`.
- Write `runMode: headless` to the card's frontmatter. A phase resumed in a
  fresh context reads the mode from there, since the flag does not survive the
  reset.
- A headless run enters at phase 3 at the earliest. If the card has not
  completed `mise-en-place`, stop here: write the reason to `## Open Questions`
  under a short id, then set `runStatus: blocked`, `runQuestion: <id>` and
  `runNext: phase-0-start.md` in the frontmatter. Phases 1 and 2 need a person —
  say that in the reason rather than attempting them.
- Otherwise route normally, and write the run record as you go: `runStatus:
  running` and `runNext` set to the phase you hand off to. In a headless run
  Phase 0 asks nothing.
- When a card is resumed with `runStatus: needs-input` or `blocked`, route to
  `runNext` rather than to the phase after `phase` — the phase that stopped has
  not completed.

## 1. Find an existing recipe card

Look for `./recipes/*.md` at the project root. If the task the user named
matches one of these cards (by its `task` frontmatter field or an obvious
name match), that's the card to resume.

If `./recipes/` doesn't exist or has nothing matching, do one broader pass
before concluding there's no prior work: search the project for markdown
files carrying a `phasesCompleted:` frontmatter key (a card may have been
placed somewhere other than the default). If one turns up for a different
task, note where it lives — that's the answer to "where do recipe cards go
in this project" for step 3, without asking again.

## 2. Resume, if found

Read the matched card's frontmatter (`phase`, `phasesCompleted`, `status`,
`prUrl`) and its `## Decisions` section, then read the rest of the card for
full context.

If `status` is `delivered`, the task is already done — tell the user and ask
if they want to start a new task instead (go to step 3) rather than silently
re-running anything.

Otherwise, map the last completed phase to the next phase file:

| Last completed phase | Next phase file |
|---|---|
| *(none — fresh card)* | `phase-1-reading-the-recipe.md` |
| `reading-the-recipe` | `phase-2-mise-en-place.md` |
| `mise-en-place` | `phase-3-cooking.md` |
| `cooking` | `phase-4-tasting.md` |
| `tasting` | `phase-5-plating.md` |
| `plating` | `phase-5-plating.md` if `## PR Delivery Strategy` lists a chunked delivery with any chunk still not `opened`; otherwise `phase-6-documentation.md` |
| `documentation` | *(terminal — already delivered)* |

A chunked delivery revisits `plating` more than once — Plating itself checks
whether the most recently opened chunk's PR has merged before starting the
next one (see that phase's own section 1a), so routing here only needs to
know whether any chunk is still waiting to be opened at all.

Tell the user what's already done (the `## Decisions` log, read aloud in
brief) and what phase is next, then load, read completely, and execute that
phase file.

## 3. Fresh task, if not found

Ask what the task is — a ticket link, a plain description, an existing doc,
whatever the user has. Take whatever tracker or source they point at as
given; if a matching tool is available in this session, use it to pull
details, otherwise take their description at face value.

**Where should the recipe card live?** Only ask this the first time a card
is created in this project (i.e. no `./recipes/` directory exists yet and
step 1's broader search found nothing). Default to `./recipes/`, and if the
user wants somewhere else, use that for every future card in this project
too — later fresh-task runs find the answer by reading an existing card's
location rather than re-asking.

Check whether the chosen directory is covered by the project's own
`.gitignore`. If it isn't, add an entry for it (asking first if the project
has no `.gitignore` at all, since creating one is a bigger decision than
appending to an existing one) — the card is local scratch state, not
something to commit.

Create the card from `./references/recipe-card-template.md`
at `{cardRoot}/{task-slug}.md`, with `task` set to whatever the user gave and
every other field at its default.

Load, read completely, and execute `phase-1-reading-the-recipe.md`.
