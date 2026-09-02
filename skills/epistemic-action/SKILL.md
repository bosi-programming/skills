---
name: epistemic-action
description: Go find out instead of predicting. Use whenever you are about to state something you have not run or read - how a function behaves, whether a test passes, what a config holds, why something broke, what a ticket actually says. Also use when you catch yourself writing "should", "probably" or "typically" about this codebase, and before any debugging conclusion. Covers reading, running and probing digital objects.
---

You cannot act on the physical world. You can act on **digital objects**: files, tests, queries, endpoints, repos, tickets. That is enough. Every question you were about to answer from memory has an action that would answer it from evidence.

## The distinction

- **Pragmatic action** moves the deliverable closer to done. Writing the code. Editing the file. Opening the PR.
- **Epistemic action** changes a digital object *only* so it will speak. Running the test to watch it fail. Printing a variable. `git log` on the file.

The failure to watch for is collapsing the two: **writing the code does not tell you the code works.** A pragmatic action produces an artifact, never a finding. If the only thing you did was build it, you know nothing about it yet.

## The Tetris rule

Tetris players rotate falling pieces in ways that place nothing. Under a pragmatic reading the moves are waste. They are not: the rotation unveils the piece and the topography faster than imagining it would.

So: **never judge an action by whether it advances the deliverable.** A log line you will delete, a throwaway probe script, a test run whose result you are sure of already, a `git blame` on code you think you understand. These advance nothing and are not waste.

## Why acting beats predicting

Three reasons, and all three are about cost:

1. **Fewer steps.** Predicting means simulate the code, simulate the input, simulate the output, then act. Acting means run it and read.
2. **Less held in context.** The prediction has to be carried in your window until you use it. The finding is on the screen.
3. **Fewer errors.** Prediction is less reliable than execution, and its errors are silent.

**Acting is cheaper than imagining, not more expensive.** When you feel the pull to skip the check and close the turn, that pull is wrong about the price.

## The repertoire

Three families. Reach for the cheapest one that actually settles the question.

### Exploration, nothing changes

Read the actual file. `grep`. `git log` and `git blame`. Read the ticket body itself, not its title. Read the schema. List the directory. Check the lockfile for the real version.

### Manipulation, run it, no residue

Run the test. Execute the read-only query. Run the linter or typechecker. `curl` the endpoint. Check out the branch and see. Run the script with `--help`.

### Transformation, alter the object so it speaks

The family you underuse. It is not a last resort: one member of it is where the work *starts*.

- **Write the failing test first, then read what it actually says when it fails.** This is the opening move on any change or bug fix, never a fallback. The failure message is your first finding, and you have not unveiled a bug until you have watched a test fail on it.

The other four are for when exploration and manipulation both come back mute:

- Insert a temporary print or log at the line you are unsure about
- Write a throwaway probe script that imports the real module and calls it
- Comment out a block to isolate which half is responsible
- `git bisect` when the question is "when did this start"

## The probe loop

A probe goes in the **real file**, because that is the only place it can observe the real thing. Deletion is a step in the loop, not an afterthought:

1. Insert the probe
2. Run it
3. Read the output
4. **Delete the probe**

Do not batch step 4. Delete before you move to the next question. A transformation that leaves residue has quietly become a pragmatic action.

## What an unveiling is worth

Truth happens in the **use** of a thing, not in a proposition about it. So evidence ranks by the action that produced it, strongest first:

1. Executed it and read the output
2. Read the specific source file
3. Read a doc or README about it
4. Recalled a general pattern
5. Inferred it from a name

Only 1 and 2 count as evidence. Levels 3 to 5 are hypotheses wearing the clothes of findings.

## Record the conditions

Truth is multiple and still objective. A finding is tied to the conditions that produced it, and those conditions travel with it.

- Not "the test passes", but "the test passes at this commit, on this branch, with this fixture"
- Not "the endpoint returns 200", but "it returned 200 for this payload against staging"

State the conditions and a reader can tell what your finding does not cover. Drop them and one run silently becomes a general law.

## When to stop

Relevance is relative to the question you are answering. A fact that decides everything in one model is noise in another.

**Stop when the unveiling settles the decision at hand.** This is not a licence to read the whole repo. If you cannot say which decision the next action would settle, you are done acting and it is time to write.

## Whose path did you walk

Reaching for the cached general answer shortens your steps and costs you your reading of *this* object. It is the same trade as looking up a place instead of going there: faster, and someone else's unveiling.

Before you rely on a remembered pattern, ask whether the question was about software in general or about **this** repo, this config, this ticket. If it was the second, go and read it.
