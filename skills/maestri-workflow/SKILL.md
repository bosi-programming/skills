---
name: maestri-workflow
description: Orchestrate a ticket from the Maestri canvas by running recipe-relay with each unit handed to a fresh agent terminal instead of a sub-agent, one model for planning and another for code, on any harness the canvas has a preset for. The run never stops to ask; the orchestrator takes each stated recommendation, logs it to a shared note, and ends with a draft PR after a bosi-code-review pass it fixes. Use when the user is in Maestri and asks to work a ticket, issue or task through the recipe with a team of agents, or names this workflow.
---

# Maestri Workflow

You run inside the Maestri canvas as the orchestrator. The task is whatever
ticket the user named: a tracker key, a link, or a plain description. You work
it through `../recipe-relay/SKILL.md`, with one change: every unit recipe-relay
would hand to a sub-agent goes to a new agent terminal on the canvas instead.
You never do a unit's work yourself.

The run does not pause for the user between the request and the end. Where a
choice comes up, you take the recommendation this file or the recipe states,
log it to the shared note under `## Taken without asking`, and carry on. The
only stop is the end of the flow: a draft PR and the report in section 5.

Drive the canvas with the `maestri` CLI. Run `maestri help` and
`maestri <command> --help` before using a flag you have not seen this session,
and never guess one.

## 1. Settle the inputs

You need four things before anything starts:

- **The ticket.** Take it from what the user said. If they gave a key or link,
  read the ticket through whatever tracker access the session has, so later
  prompts can quote it. If the tracker is out of reach, pass the key or link
  through as-is; Phase 0 of the recipe knows how to take a task in any form.
- **The planning lane.** A harness and model for Reading the Recipe, Mise en
  Place, Documentation and the final review. These phases decide what gets
  built, so they want the strongest reasoning model on offer.
- **The coding lane.** A harness and model for Cooking/Tasting and Plating.
  These phases write and test code, so a faster coding model does.
- **Fresh or resume.** Whether earlier work on this ticket counts, or is
  legacy to leave behind.

Run `maestri preset list` to see which harnesses the canvas can launch. If the
user named a lane, use it. If they did not, take the recommended lanes:
planning on the most capable reasoning model the presets offer, coding on a
faster coding model, both on the harness you run on. The note does not exist
yet, so hold the choice and log it under `## Taken without asking` as the
first line once section 2 creates the note.

Default to resume. Start fresh only when the user says the earlier work is
legacy.

## 2. Prepare the ground

1. Pick the work root, so every unit starts from current code. Run
   `git fetch` and `git status`.
   - **Clean tree:** check out the latest default branch. The work root is the
     repository root.
   - **Uncommitted changes:** leave them untouched; they are not yours to
     stash or drop. Look in `git worktree list` for a worktree named for this
     ticket. On resume, reuse it. On a fresh start, or when there is none,
     create one off the latest default branch:
     `git worktree add --detach "../{repo name}-{task-slug}" "origin/{default branch}"`.
     Detached, so the recipe still names its own branch in Cooking. The work
     root is that worktree. Log which one you used.

   From here on, `{work root}` is where every recruit starts, every card lives
   and every command runs.
2. On a fresh start, look for an existing recipe card for this ticket under
   `{work root}/recipes/`. Rename it to `{task-slug}.legacy.md` so Phase 0
   opens a new one, and log the move to the note. Delete nothing: legacy
   branches, cards and PRs stay where they are.
3. Create the shared note with two headings:
   `maestri note create "$(printf '# {ticket}\n\n## Questions and problems\n\n## Taken without asking')" --name "{ticket} questions"`.
   Write the section 1 lanes under `## Taken without asking` first. Every
   recruit gets connected to the note. Under `## Questions and problems` they
   log what they could not settle; under `## Taken without asking` you log
   every default, fallback, recommendation taken and one-way door left, one
   line each.
4. Run `maestri list` and note your own name under `You:`. Recruits report
   back to that name.

## 3. Run recipe-relay through the canvas

Follow `../recipe-relay/SKILL.md` section by section. Phase 0 runs in this
session, as it says. Its units hold as written, and section 2's "spawn a
sub-agent" changes as the steps below say.

The no-pause rule: wherever the recipe, Phase 0 or recipe-relay would pause for
the user, post a checkpoint and wait, or stop on `needs-input` or `blocked`,
you take the recommendation that text states, log it under
`## Taken without asking`, and continue. This holds only under
maestri-workflow. `../recipe-relay/SKILL.md` run on its own keeps its stop
conditions.

1. **Pick the lane.** Reading the Recipe, Mise en Place and Documentation take
   the planning lane. Cooking/Tasting and Plating take the coding lane. The
   code review in recipe-relay's section 5 takes the planning lane, is named
   `{ticket} code review`, and is briefed with that section's step 1 instead
   of the section 2 prompt.
2. **Recruit a fresh agent for the unit**, so it starts with a clean context,
   the way a sub-agent would. Name it for the ticket and the work it does,
   such as `{ticket} mise en place` or `{ticket} cooking`, and start it in
   the work root:
   `maestri recruit "{name}" --preset "{lane preset}" --dir "{work root}"`.
3. **Pin the lane's model.** Use the first method that works:
   - a preset that already pins the model;
   - `--command` with the harness's own model flag, read from that harness's
     `--help` first;
   - the harness's in-session model switch, sent once the agent boots.

   Check the agent's screen with `maestri check "{name}"` to confirm the model
   it shows. If none of these works, run the unit on the harness default, log
   the model it shows under `## Taken without asking`, and continue. Never let
   a unit run on a model that is not in the note.
4. **Connect the note:** `maestri connect "{ticket} questions" "{name}"`.
5. **Brief it.** Send recipe-relay's section 2 prompt with the phase files and
   card path filled in, as paths the recruit can open from the work root. Add
   three lines:
   - "Before you start, run `maestri list` and read `{ticket} questions`."
   - "Append each question you could not settle, and each problem you hit, to
     `{ticket} questions` with `maestri note edit`, one line each, prefixed
     with your name."
   - "When the unit is done, report back with
     `maestri ask \"{your name}\" \"<summary and Phase-done recommendation>\"`."

   The Plating recruit gets a fourth line: "Deliver one draft PR, no chunks.
   Leave it a draft. Log both to `## Decisions` as `relay:`." That answers
   Plating's chunk-split checkpoint, so the flow never waits for a merge.
6. **Wait for the report.** Size the `ask` timeout to the phase, and if it
   expires, read progress with `maestri check` instead of sending the prompt
   again. Never interrupt a working agent.
7. **Read the note** once the report lands. Settle whatever you can from the
   ticket, the card or the code, and write the answer under the entry. For
   what is left, take its recommended option, or the one the card and code
   support best, write it under the entry, and log it under
   `## Taken without asking`.
8. **Act on the unit's result.**
   - **New session** recommended: log it and start the next unit at once.
   - **Continue**, or no menu: start the next unit at once.
   - **`needs-input` or `blocked`:** read the entry the card's `runQuestion`
     names in `## Open Questions`. Take the recommendation it states, write it
     into its `answer:`, log it, and re-run the unit once with a fresh recruit.
     If the entry is a one-way door, the answer is "not taken; left for the
     user", and the door goes on the list for the PR body in section 4. If the
     same unit stops again, the flow ends with whatever draft PR exists, and
     section 5 reports the block first. No second retry.

Leave finished recruits on the canvas, so the user can read their history.
Only dismiss one when the user asks.

## 4. Close the run

When recipe-relay reaches `terminal`, its section 5 reviews the branch and you
fix what the review finds; its findings come back through `maestri ask` like
any unit's report. If a unit stayed stopped after its retry, or Plating could
not open a PR (no remote, no `gh` auth), the flow ends: log it, skip the
review, add any one-way doors to the PR body if a PR exists, and section 5
reports the stop first. The PR stays a draft through the fixes.

A one-way door is a merge, promoting the draft to ready, a production write, a
delete of deliberate work, or a force-push. You never take one, and neither
does any recruit. Append each door the run met to the PR body under a
`## Left for you` heading with `gh pr edit`, one line per door, and log it
under `## Taken without asking`.

## 5. Report

This is the one place the run stops. Tell the user, in short bullets:

- first, if either happened: no PR could open, or a unit stayed stopped after
  its retry, with the reason;
- the draft PR link and its CI state;
- every line under `## Taken without asking`: defaults taken, each fallback,
  each recommendation taken;
- every one-way door left for the user, as listed in the PR body;
- which review findings you fixed and which you rejected, with the reason;
- every open entry left under `## Questions and problems`.
