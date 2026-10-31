---
name: setup
description: Write or change the settings file (.bosi-skills.md) the skills in this plugin read for their defaults, such as where notes, recipe cards, reviews, UML sources and NFR docs go, run modes, ship-pr titles and gates, and open-restaurant repo maps, states and models. Use when the user wants to set up or change these defaults, says "setup", or asks where a skill saves its files.
---

Writes `.bosi-skills.md`, the one file the other skills here read their
defaults from. `./references/config.md` is the contract: where the file lives,
how a skill looks it up, and every key with its default. Read it first.

## 1. Pick the file

Ask where the settings go:

- `~/.bosi-skills.md`, for every project. Recommended for a first setup.
- `./.bosi-skills.md` in the current folder, for this project only. Each
  setting falls back on its own, so this file only needs the keys that differ.

Read both files if they exist, and note which one sets each key today.

## 2. Ask for every setting at once

Ask all the questions in one numbered list. For each, show the value in force
today and where it comes from (this file, the other file, or the default), give
the options, and say which one you recommend and why in one line. The keys are
the ones in `./references/config.md`:

1. Folder for `work-summary` notes.
2. Fixed frontmatter keys `work-summary` adds to every note, or none.
3. Values `work-summary` tags a session against, or none. Take them as the
   user gives them: pasted, or a link to read them from. Quote each value's own
   wording in `text`, do not paraphrase it, and put the link in
   `valuesSource`.
4. Any tagging guidance for `work-summary`, which goes in the body's
   `## work-summary` section.
5. `week-summary`:
   a. Folder for weekly reviews.
   b. Folder of session notes to read, if not `work-summary`'s.
   c. GitHub login and email, if not the ones `gh` and `git` report.
   d. How a review cites a session note.
   e. Day the week starts on.
   f. Skill the Weekly Update prose goes through, or none.
   g. Logical symbols in the terse sections: yes or no.
   h. Heading of the values section.
   i. Brag file to draft the Weekly Update's last answer from, or none.
   j. Any guidance for the body's `## week-summary` section.
6. Folder for recipe cards.
7. `feature-recipe`:
   a. Default mode: `regular` or `headless`.
   b. Run `work-summary` when a recipe ends: yes or no.
   c. Where feature docs go, or ask each time.
   d. Model for the `recipe-relay` sub-agents that write tests and code, or
      the one the relay runs on.
   e. Model for the `recipe-relay` UI reviewer, or the one the relay runs on.
   f. Model for the `recipe-relay` Plating and Documentation units and the
      sub-agent that runs its closing review, or the one the relay runs on.
   g. State the relay moves a task to once its PR opens, or `In Review`, and
      the state it moves it to when Documentation closes it, or `Done`.
   h. Any rules for the body's `## recipe-relay` section, which belongs in
      the project's own file while the project lasts.
8. `better-code-review`:
   a. Default mode: `conversation`, `page` or `headless`.
   b. Model for the three review sub-agents, or the one the review runs on.
   c. For PRs taken from Slack, `fast`, which skips installing dependencies,
      or `slow`, which installs them so the project's checks run.
   d. Any rules for the body's `## better-code-review` section.
9. `ship-pr`:
    a. Title format: `type(scope): subject [KEY]` or `[KEY] type(scope): subject`.
    b. Pause for approval before push and PR: yes or no.
    c. Open PRs as drafts: yes or no.
    d. Commands to run before each commit, or none.
    e. MCP server that reads tickets, or none.
    f. Any guidance for the body's `## ship-pr` section.
10. `uml`:
    a. Folder for the UML sources and `uml.json`.
    b. Path to the PlantUML jar, or the cache folder.
    c. Render with the local jar, or the URL of a PlantUML server.
    d. Minutes with no request before the page server stops.
11. Folder that holds one folder per project, where
    `non-functional-requirements` writes each project's `nfr.md`.
12. `open-restaurant`:
    a. Map from sub-issue label to repo folder, or take the repo from the
       sub-issue's text.
    b. State a sub-issue moves to once its PR opens, or `In Review`; none skips the move.
    c. State for merged sub-issues and a fully proved parent.
    d. Name of the QA env, with `{parent}` for the parent identifier.
    e. Chat channel for the review request, or none.
    f. Models for the readiness judge, the QA agent and the QA fix agent, or
       the one the session runs on.
    g. Any team steps for the body's `## open-restaurant` section.
13. `pause-work`:
    a. Tool the paused-work task goes to, such as `Todoist`, `Linear` or
       `gh`, or ask each time.
    b. Project, list or team in that tool, or its inbox.
    c. Due date.
    d. Labels, or none.

An answer of "keep" or no answer leaves that key as it is.

## 3. Write it

Start from `./assets/bosi-skills.md` when the file is new, or from the file as
it stands when it exists. Change only the keys the user answered; keep every
other key and all the prose in the body.

In a project file, leave out keys that match what `$HOME` or the default
already gives, so the project file shows only what it changes.

For a project file, check whether the project's `.gitignore` covers it and
tell the user either way. Ask before adding it there.

## 4. Confirm

Read the file back and show the settings now in force for this folder: each
key, its value, and the file it comes from.
