---
name: maestri-workflow
description: Orchestrate a ticket from the Maestri canvas by running recipe-relay with each unit handed to a fresh agent terminal instead of a sub-agent, one model for planning and another for code, on any harness the canvas has a preset for. Ends with a bosi-code-review pass the orchestrator fixes, and keeps a shared note where every agent logs questions and problems. Use when the user is in Maestri and asks to work a ticket, issue or task through the recipe with a team of agents, or names this workflow.
---

# Maestri Workflow

You run inside the Maestri canvas as the orchestrator. The task is whatever
ticket the user named: a tracker key, a link, or a plain description. You work
it through `../recipe-relay/SKILL.md`, with one change: every unit recipe-relay
would hand to a sub-agent goes to a new agent terminal on the canvas instead.
You never do a unit's work yourself.

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
user named a lane, use it. If they did not, ask for every missing input in one
numbered list, with the presets as options and a recommendation: planning on
the most capable reasoning model the user's harnesses offer, coding on a
faster coding model, both on the harness you run on unless the user says
otherwise.

Default to resume. Start fresh only when the user says the earlier work is
legacy.

## 2. Prepare the ground

1. Fetch and check out the latest default branch, so every unit starts from
   current code. If the working tree has uncommitted changes, stop and ask:
   they are not yours to stash or drop.
2. On a fresh start, look for an existing recipe card for this ticket under
   `./recipes/`. Rename it to `{task-slug}.legacy.md` so Phase 0 opens a new
   one, and tell the user which file you moved. Delete nothing: legacy
   branches, cards and PRs stay where they are.
3. Create the shared note:
   `maestri note create "# {ticket}: questions and problems" --name "{ticket} questions"`.
   Every recruit gets connected to it, and it is where they log what they
   could not settle.
4. Run `maestri list` and note your own name under `You:`. Recruits report
   back to that name.

## 3. Run recipe-relay through the canvas

Follow `../recipe-relay/SKILL.md` section by section. Phase 0 runs in this
session, as it says. Its units, checkpoints and stop conditions hold as
written. Only section 2's "spawn a sub-agent" changes:

1. **Pick the lane.** Reading the Recipe, Mise en Place and Documentation take
   the planning lane. Cooking/Tasting and Plating take the coding lane.
2. **Recruit a fresh agent for the unit**, so it starts with a clean context,
   the way a sub-agent would. Name it for the ticket and the work it does,
   such as `{ticket} mise en place` or `{ticket} cooking`, and start it in
   this repository:
   `maestri recruit "{name}" --preset "{lane preset}" --dir "{repo root}"`.
3. **Pin the lane's model.** Use the first method that works:
   - a preset that already pins the model;
   - `--command` with the harness's own model flag, read from that harness's
     `--help` first;
   - the harness's in-session model switch, sent once the agent boots.

   Check the agent's screen with `maestri check "{name}"` to confirm the model
   it shows. If none of these works, stop and ask the user. Never let a unit
   run on a model the user did not choose.
4. **Connect the note:** `maestri connect "{ticket} questions" "{name}"`.
5. **Brief it.** Send recipe-relay's section 2 prompt with the phase files and
   card path filled in, as paths the recruit can open from the repository
   root. Add three lines:
   - "Before you start, run `maestri list` and read `{ticket} questions`."
   - "Append each question you could not settle, and each problem you hit, to
     `{ticket} questions` with `maestri note edit`, one line each, prefixed
     with your name."
   - "When the unit is done, report back with
     `maestri ask \"{your name}\" \"<summary and Phase-done recommendation>\"`."
6. **Wait for the report.** Size the `ask` timeout to the phase, and if it
   expires, read progress with `maestri check` instead of sending the prompt
   again. Never interrupt a working agent.
7. **Read the note** once the report lands. Settle whatever you can from the
   ticket, the card or the code, and write the answer under the entry. Anything
   that needs a person goes to the user in chat, all in one numbered list.

Leave finished recruits on the canvas, so the user can read their history.
Only dismiss one when the user asks.

## 4. Review and fix

When recipe-relay stops because the card reached `terminal` or Plating is
waiting on a merge, the branch holds the code. Before you report the run as
done:

1. Recruit one last planning-lane agent, named `{ticket} code review`, and
   pin its model as in section 3.
2. Brief it to run `../bosi-code-review/SKILL.md` against the merge base of
   the branch and the default branch, with the ticket as the spec source. It
   asks no questions, skips the HTML report, and returns every finding as
   text with its `file:line` through `maestri ask "{your name}" "..."`.
3. Work through the findings yourself, on the same branch: write a failing
   test first where the finding is a behaviour, then fix, then run the
   project's scoped tests and lint. Push to the open PR. A finding you judge
   wrong goes in the note with the reason, not into the code.

If recipe-relay stops on `blocked` or `needs-input`, skip the review. Bring
the open question to the user as recipe-relay section 4 says.

## 5. Report

Tell the user, in short bullets:

- the PR link and its CI state;
- which review findings you fixed and which you rejected, with the reason;
- every open entry left in `{ticket} questions`.
