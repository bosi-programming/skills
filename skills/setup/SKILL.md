---
name: setup
description: Write or change the settings file the skills in this plugin read — where work-summary saves its notes, which values it tags a session against, where week-summary writes its reviews and who it counts as you, where feature-recipe keeps recipe cards, and whether feature-recipe and better-code-review run regular or headless by default. Use when the user wants to set up, configure or change the defaults of these skills, says "setup", or asks where a skill saves its files and wants that changed.
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
   i. Any guidance for the body's `## week-summary` section.
6. Folder for recipe cards.
7. `feature-recipe`:
   a. Default mode: `regular` or `headless`.
   b. Run `work-summary` when a recipe ends: yes or no.
   c. Where feature docs go, or ask each time.
8. `maestri-workflow` models for the planning and coding lanes, or let the
   skill pick.
9. `better-code-review` default mode: `conversation`, `page` or `headless`.

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
