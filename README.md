# Bosi Programming Skills

Thirty-six Claude Code skills, packaged as an installable plugin. Two of them carry the rest:

- **`recipe-relay`** takes one ticket from the tracker to a reviewed pull request, ready for review, with nobody answering questions on the way. Every phase runs in its own sub-agent, every checkpoint takes its own recommendation and logs it, and the run stops only at a question with no reasonable default.
- **`open-restaurant`** is an LLM factory. Hand it a parent issue and it runs the parent's line and each sub-issue's line through `assembly-line`, in parallel across repos, then integrates the branches, QAs them as one system, writes proof and stops only at the human gates the lines name.

The other thirty-four feed those two or stand alone. `assembly-line` runs the stages a ticket's line names, and `plan-assembly-line` suggests each ticket's line and saves it as a comment on the ticket. `plan-work` turns a feature into tickets the two can build. `feature-recipe` is the six-phase workflow the relay runs, and `evaluate-ticket`, `plan-code`, `test`, `code`, `prepare-pr` and `code-docs` are its six stages as skills of their own, and `review-fix` runs the relay's closing review and fix as a skill of its own, and `ui-review` runs its UI review as a skill of its own, and `a11y-check` runs its accessibility check as a skill of its own, and `security-review` runs its security review as a skill of its own, and `judge` runs `open-restaurant`'s readiness gate as a skill of its own, and `contract` runs its contract step as a skill of its own, and `reproduce` runs its bug reproduction step as a skill of its own, and `integrate` runs its integration step as a skill of its own, and `qa` runs its QA and fix step as a skill of its own, and `proof` runs its proof step as a skill of its own, and `review-request` runs its review request as a skill of its own, and `merge` runs its merge gate as a skill of its own. `better-code-review` reviews a diff along three axes, and `code-standards` is the catalog it reads from. `ship-pr` commits, pushes and opens a PR from the repo's template. `uml` draws UML diagrams of a codebase or a description, and `non-functional-requirements` writes and reviews NFRs. `summarize-llm-response` and `epistemic-action` check the model's own writing and reasoning before it reaches you. `work-summary` writes up a work session as a dated note, `pause-work` parks half-done work as a task for tomorrow, `weekly-planning` fits the week's tickets around your meetings, `week-summary` turns a week of those notes and your tracker, GitHub and chat activity into a review, and `setup` writes the settings file the others read their defaults from.

The same thirty-six install into Codex, DeepSeek Harness, Pi and opencode, from the same `skills/` directory. One plugin source, five harnesses, nothing copied — so a skill cannot drift between harnesses. The one exception is opencode, which fetches a skill list over HTTP: `skills/index.json` is generated from that same tree and kept honest by `opencode/build-index.py --check`.

## Install

### Claude Code

```
/plugin marketplace add bosi-programming/skills
/plugin install bosi-programming-skills@bosi-programming
```

Then run `/reload-plugins` if the install summary asks for it.

Plugin skills are namespaced, so the commands are `/bosi-programming-skills:epistemic-action`, `/bosi-programming-skills:better-code-review`, and so on. Claude also loads them on its own when a description matches.

### Codex

```
codex plugin marketplace add bosi-programming/skills
codex plugin add bosi-programming-skills@bosi-programming
```

`.codex-plugin/plugin.json` is the manifest and `.agents/plugins/marketplace.json` is the catalog entry. Both keep the plugin root at the repository root, so `skills/` is what Codex reads. `codex plugin list` shows what landed.

### DeepSeek Harness

```
dsh plugin --profile <name> add github:bosi-programming/skills
```

`package.json` declares `dsh.bundle`, so the install contributes exactly one layer: a row mounting `dsh/index.js`, a Cordis plugin that registers a skill provider over `skills/`. Nothing else in the profile changes, and `dsh --profile <name> --dump-config` shows the layer. For a plain checkout, `DSH_BUNDLED_SKILL_DIR=<repo>/skills dsh` puts the same directory at the harness's bundled-skill root without installing anything.

### Pi

```
pi install git:github.com/bosi-programming/skills
```

`package.json` carries the Pi package manifest — a `pi` key whose `skills` entry points at `skills/` — alongside the `pi-package` keyword the gallery lists on. Pi resolves those paths against the package root, so the tree survives a git install intact. `pi list` shows the install and `pi config` toggles individual skills.

### opencode

```json
{
  "skills": {
    "urls": ["https://raw.githubusercontent.com/bosi-programming/skills/main/skills/"]
  }
}
```

opencode fetches `<url>/index.json`, then downloads each skill's files relative to `<url>/<name>/` into `~/.cache/opencode/skills/`. No checkout, no clone. The index carries a digest per skill, and opencode only refreshes a cached skill when that digest changes — so the digest moves with the files, or an edit upstream would never reach anyone who had already installed. `opencode/build-index.py` writes it; the check in "Validate a change" fails when it goes stale. Restart opencode after editing your config, and keep the global skill directories free of same-named copies.

Skills live outside your project, so an agent that denies `external_directory`
denies them too — `read` fails with `DeniedError` even though the skill is
installed. opencode evaluates the *last* matching `external_directory` rule, so
the broad deny has to come first and the skill directories after it:

```json
"external_directory": {
  "*": "deny",
  "~/.config/opencode/skills/**": "allow",
  "~/.cache/opencode/skills/**": "allow"
}
```

For a plain checkout, point opencode at the tree instead and skip the index entirely:

```json
{
  "skills": {
    "paths": ["/absolute/path/to/the/checkout/skills"]
  }
}
```

## The skills

### assembly-line

Runs one ticket's line: the ordered stages its line names. It reads the local line file `assembly-line.lineFile` names (`{cardsDir}/{ticket}.line.json`) and the ticket's comments through the tracker; the file wins when both exist, else it takes the line comment created last, the one with `"format": "assembly-line/1"`. A line comment may start from a saved line with `from`, edited by `add` and `drop`, and the run uses the expanded line. It changes no stage's files, and `recipe-relay` stays until BOS-112.

How the line runs:

1. **Validate.** The line goes through `validate-line.py` before any stage runs. An invalid line, no line file and no line comment or a `{"group": "sub-issues"}` line stops the run and writes nothing; it points to `plan-assembly-line`, or to `open-restaurant`.
2. **Stages.** Each stage runs in its own sub-agent, and every checkpoint takes its own recommendation, logged to the recipe card as `line:`. `judge`, `ui-review`, `security-review` and `review-fix` run in the session, because their own steps spawn sub-agents.
3. **Cooking.** `test` and `code` in parallel run as a test writer and a code writer that never see each other's files; the `code` after them is the fix and taste agent.
4. **Go-backs.** A failing verdict follows the stage's `return` entry in `catalog.json`, back to the stage it names, up to its `limit`. Past it, the run stops at `needs-input` or at a human gate.
5. **Gates.** A stage with `gate: human`, today `merge`, stops at `runStatus: gate` with a question in chat and on the card, and runs only on the person's approval.
6. **Signals.** After each stage the run reads `## Signals` on the card and applies the rows in `signals.json` to the steps not yet run, through `apply-signals.py`. No approval: a row is the approval. Each change posts a line comment naming the signal, the stage that raised it and the stage added or removed; a change `validate-line.py` rejects leaves the line and is logged.
7. **Run log.** After every stage run, go-back reruns and each parallel branch included, the run appends one JSON line to `runs.jsonl` (the file `assembly-line.runLog` names) through `run-log.py`: ticket, kind, line, stage, start and end times, verdict, loops, tokens and the signal that changed the line. A failed append is logged and never stops the run.
8. **Line board.** `board.py` prints every running card in `feature-recipe.cardsDir`: each ticket's stage, how many wait at each stage, and the bottleneck, the stage with the most waiting, ties going to the longest mean time in the run log. When more than one ticket is running, each step's report names the command.
9. **Close down.** At every stop it stops the sub-agents, background shells and dev servers the line started, and logs `line: closed down` on the card. A sub-agent or shell with no new output for 30 minutes gets stopped and its stage started again once; a second stall stops the run as `blocked`.

`assembly-line.codingModel`, `assembly-line.uiReviewerModel` and `assembly-line.routineModel` pick the models; `assembly-line.reviewState` (`In Review`) and `assembly-line.doneState` (`Done`) pick the tracker states; `assembly-line.runLog` (`~/.bosi-skills/runs.jsonl`) names the file the run log goes to. The line board reads cards from `feature-recipe.cardsDir` (`./recipes`). A `## assembly-line` section in a project's `.bosi-skills.md` adds rules every sub-agent follows there; the line reads `## recipe-relay` when it has none.

### plan-assembly-line

Suggests each ticket's line and saves it as a comment on the ticket or in a local line file, in the shape `assembly-line` reads. It never runs the line.

A ticket whose body holds the line Planned with `plan-work`. has already passed `plan-work`'s readiness check, so its line drops `judge` and carries `"planned": "plan-work"`; a parent keeps `judge`.

How it plans:

1. **Read.** It reads each ticket's body and comments through the tracker. A line comment already there, the one created last, is the starting suggestion.
2. **Suggest.** It starts from the saved line that matches the ticket's kind (`feature`, `bug`, `small-fix` or `parent`) and drops or adds stages by rule, saving it with `from`: no `test`/`code` group without a `[unit]`, `[int]`, `[e2e]` or `[story]` criterion; `ui-review` and `a11y-check` for a `## Design` link or a `[ui]` or `[story]` criterion; `code-docs` only for a `feat` title or a `[docs]` criterion. A parent gets `{"group": "sub-issues"}`, and its sub-issues join the list. Each line comes with a short why.
3. **Run log.** `stats.py` reads the run log for tickets of the same kind and suggests to add, look at or cut a stage, each with the count behind it, from 5 runs up. The suggestions are shown, not applied.
4. **Validate.** Every line goes through `validate-line.py` before it is shown. An error names the stage and rule, and the stage to add.
5. **Approve.** One table shows every ticket. The engineer confirms or edits, and an edit is validated again. Nothing is written to the tracker before approval, and a rejected line is not saved.
6. **Save.** `assembly-line.lineDestination` (`ticket`) picks where: one comment per ticket, in the `line-format.md` shape, or with `file` the JSON line alone at `assembly-line.lineFile`. It never edits or deletes an old line comment.
7. **Read back.** It reads each comment back and reports any difference from the approved line, with a link per ticket.

`plan-work` calls it on its new tickets when `plan-work.role` is `engineer`. It reads the run log at `assembly-line.runLog`, and `assembly-line.lineFile` and `assembly-line.lineDestination` for where lines live.

### recipe-relay

Takes one ticket to a pull request that is open, reviewed and ready for review, without asking you anything on the way. You name the task; the session runs `feature-recipe`'s six phases, each in its own sub-agent, without changing any of the recipe's files. Each sub-agent takes the recommendation every checkpoint states — the grilling, the plan, the test list, the PR description — and logs it to the recipe card as `relay:`, so you can read afterwards what it chose and why. What reaches the chat is one line per unit, and the session starts the next unit without waiting for a reply.

How the ticket moves:

1. **`evaluate-ticket` and `plan-code`** run as one sub-agent. It turns the ticket into a plan on the recipe card and names the interfaces.
2. **Cooking** splits. For each repo, a test writer, running `test`, and a code writer work at the same time on the same branch, neither opening the other's files, so the tests cannot bend to the code. The code writer runs `code` up to its code, and a last sub-agent runs `code` again to make the tests pass and run its checks: the project's scoped tests and lint.
3. **UI review** (`ui-review`). When the change reaches a screen, a UI reviewer runs after that last sub-agent. It compares the screenshots `code` captured with the design attached to the ticket, and sends critical and major differences back for up to two more rounds.
4. **`prepare-pr`** (Plating) opens the PR ready for review, never as a draft, waits on CI and fixes it, and moves the ticket to `recipe-relay.reviewState` (`In Review` by default).
5. **Review and fix** (`review-fix`). The moment the PR opens, a sub-agent runs `better-code-review --headless` against the branch; this is the run's one review. Another sub-agent checks each finding by how it was verified — `ran`, `read` or `no` — fixes the ones that hold, test first, pushes to the open PR, and logs each one it rejects with the reason.
6. **`code-docs`** (Documentation) closes the task out and moves the ticket to `recipe-relay.doneState` (`Done` by default).

It stops only at the end, or when a sub-agent reports `blocked` or `needs-input`: a one-way door or a question with no reasonable default. Then it asks you in chat, and running it again picks the card back up where it stopped. It never merges; the PR waits for a person. At every stop it first stops the sub-agents, background shells and dev servers it started, so no shell stays open after the run. A sub-agent or shell with no new output for 30 minutes gets stopped and its unit started again once; a second stall stops the run as `blocked`.

`recipe-relay.codingModel`, `recipe-relay.uiReviewerModel` and `recipe-relay.routineModel` pick the models for the writers, the UI reviewer, and the Plating (`prepare-pr`), Documentation (`code-docs`) and review sub-agents. A `## recipe-relay` section in a project's `.bosi-skills.md` adds rules every sub-agent follows in that project; delete the section when the project ends.

### open-restaurant

An LLM factory. Hand it a parent issue — an epic or a story with sub-issues — and it delivers every sub-issue to its own PR, then puts the parts together and proves they work as one. The parent is the order and each sub-issue a dish: this session runs the kitchen and never cooks a dish itself. It runs the parent's line and each sub-issue's line through `assembly-line`, so a ticket gets only the stages its line names. A person comes in at the gates the lines name, and nothing merges without one.

The run, in order:

1. **Lines first.** It reads the line comment of the parent and of every sub-issue, and validates each with `validate-line.py` before any card exists. A missing line, an invalid line, or a parent line with no `{"group": "sub-issues"}` stops the run and points to `plan-assembly-line`. An issue with no sub-issues runs alone through `assembly-line`.
2. **The parent's line.** It runs the stages the parent's line names through `assembly-line`, on a service card. A parent line can hold `judge` (readiness gate), `contract`, `integrate`, `qa`, `proof`, `review-request` and `merge`, in the order the line gives. At the `{"group": "sub-issues"}` step it seats and cooks the sub-issues.
3. **Cooking.** Each sub-issue runs its own line on its own recipe card, without its `merge`. A bug sub-issue's line names `reproduce`; one that does not reproduce gets a `## Blocked` comment, and nothing that depends on it starts. Sub-issues in different repos cook at the same time. Those in one repo cook one at a time in its checkout, and one blocked by another in the same repo stacks its PR on the blocker's branch. A sub-issue blocked by one in another repo starts as soon as the blocker's `plan-code` stage writes it an unblock note with the shapes it needs, not when the blocker's PR opens.
4. **Review per PR.** Each PR opens ready for review, linked to its own sub-issue, which moves to `open-restaurant.implementedState`. `review-fix` runs for each PR the moment it opens, and the findings get fixed on its branch.
5. **Integrate and QA.** Once every card ends, `integrate` lists the criteria QA proves and merges the branches into a local integration branch it never pushes. `qa` then brings up one QA env for the parent and proves each criterion with saved evidence. Failures get fixed on the owning sub-issue's branch, fast-forward only, for at most two QA rounds.
6. **Proof** (`proof`). A `## Proof` on each PR, and one on the parent with each criterion and its evidence.
7. **Review request and merge** (`review-request`, `merge`). `review-request` waits on checks and posts the PRs to `open-restaurant.reviewChannel`. `merge` stops for a person every time, then merges in blocks order and moves the sub-issues, and the parent when no criterion is left open, to `open-restaurant.doneState`.

Every stop writes its state to a service card next to the recipe cards; running it again on the same parent goes on from there. Before it reports a stop, it stops the sub-agents, background shells and QA env it started. A sub-agent or shell with no new output for 30 minutes gets stopped and its stage started again once.

Needs a tracker tool in the session and one repo checkout per repo in the folder it runs from. Team-specific steps (the readiness lint, QA skill, env, review groups) go in the settings file's `## open-restaurant` section; see `setup`.

### better-code-review

Reviews the diff between `HEAD` and a fixed point you name, along three axes at once. Standards asks whether the code follows the repo's documented coding standards. Spec asks whether the code does what the originating issue or PRD asked for. Tests asks whether the tests in the diff are sound, and whether every behaviour the diff changes has a test that would catch it breaking. The three axes run as parallel sub-agents so none pollutes another's context. Before anything reaches you, the review checks each finding the way `epistemic-action` asks: it runs the project's scoped tests, lint and type-check, and proves each missing or tautological test with a probe, breaking the line in a throwaway worktree and watching whether any test turns red. Each finding says whether it was run, read or not verified. Then the findings render as a three-tab dark-theme HTML page that opens in your browser. With `--headless` it asks nothing, takes the merge base with the default branch when no fixed point is given, skips the Spec axis when no spec turns up and the Tests axis when there is nothing to test, and returns each finding as a plain-text block with its axis, kind, `file:line`, fix and whether it was verified, so another skill or agent can act on it. `recipe-relay` and the recipe's headless `code` stage call it this way. With `--slack <link>` it reads the PR links in one Slack message, reviews each PR headless in a fresh clone it deletes afterwards, posts missing or partial requirements, scope creep, defects and hard violations as one GitHub review with inline comments, approves a PR with none of those, and posts a short English comment in the message's thread saying whether it approved or only commented. `better-code-review.reviewMode` decides whether it installs each clone's dependencies first: `fast`, the default, skips that and lists the checks it could not run as not verified; `slow` installs them.

Based on Matt Pocock's code-review skill.

### code-standards

The standards the Standards and Tests axes check against, as five files: `Common/Clean Code.md` for naming, size, structure and immutability in any language; `Typescript/Imports.md` and `Typescript/Exports.md` for how TypeScript reaches other modules and what it publishes; `Frontend/Accessibility.md` for anything that renders in a browser; `Testing/Tests.md` for how tests are written, tautological tests included. Each file is a list of rules and the failures they prevent, closing with the red flags to catch in review.

`better-code-review` reads the catalog as its baseline and only applies the files the diff can violate. The catalog defers to the project: a standard the repo documents itself always wins, and a breach is a hard violation only where the repo documents the same rule — otherwise it is a judgement call, like any smell. It is a reference rather than a workflow, so there is nothing here to run.

### feature-recipe

Takes a task from a rough idea to a merged PR, cooked in six named stages — `evaluate-ticket`, `plan-code`, `test`, `code`, `prepare-pr`, `code-docs` — most defaulting to a fresh context and handing the next one its work through a **recipe card**, a markdown file at `./recipes/{task-slug}.md` in the project being worked on (`evaluate-ticket` and `test` continue straight through instead, without a session break). `evaluate-ticket` and `plan-code` are where you and the skill agree on what is being built and why; `evaluate-ticket` runs `grill-me` only when the work is complex or leaves something undefined, and skips it for simple, fully stated work; `test` writes every mapped test and sees it fail before any code, and `code` makes them pass, commits as it goes, then holds a hard gate that runs `better-code-review` plus the project's own scoped tests and lint before anything opens; `prepare-pr` opens at most one PR per run and never stacks them unless a driver names a base branch; `code-docs` closes the task out.

It carries no opinion about which tracker, chat or docs tool a project uses — it speaks in outcomes and leans on whatever the session already has.

Phases 1 to 6 can also run **headless** — a night run. Start one with `--headless` at whatever step the card is on, even a bare task with no card yet, and it carries the work through `evaluate-ticket`, `plan-code`, `test`, `code`, `prepare-pr` and `code-docs` in one turn, taking the recommendation at each checkpoint and recording it as `unattended:` so the morning can see what was decided while nobody was watching. It stops only at the end of the recipe or when something needs a person — never merely because a phase ended — and it never opens a non-draft PR, merges, or deletes work. The run's result goes on the card as `runStatus`, `runNext` and `runQuestion` in the frontmatter, so a driver reads a file at a known path instead of parsing prose — prose gets fenced, glued to a heading, or turned into a question. The contract is `skills/feature-recipe/references/headless.md`.

### evaluate-ticket

The first build stage, once `feature-recipe`'s Reading the Recipe. It loads the task, decides whether the work is complex or leaves something undefined, runs `grill-me` only then, and writes the work card's `## Problem` and `## Goal & measure`. It takes the path to a work card; with no card it runs `feature-recipe`'s Phase 0 to find or make one. It writes `evaluate-ticket` to the card's `phase` and `phasesCompleted`, so `feature-recipe`, `recipe-relay` or a person can run it alone, for instance to redo this stage on a card. Cards from before the split, with `reading-the-recipe` in `phase` or `phase-1-reading-the-recipe.md` in `runNext`, still route here.

It is the first stage to declare a `stage.json`: what it takes from the card, what it delivers, where the line goes back to when it fails, and its gate. `skills/assembly-line/references/stage-spec.md` defines the keys.

### plan-code

The second build stage, once `feature-recipe`'s Mise en Place. It reads the work card's `## Problem`, drafts `## Solution`, `## Implementation Plan`, `## Acceptance Criteria` and `## Testing Strategy`, lists the test cases in `## TDD Test Mapping`, and names the public interfaces both a test writer and a code writer code to in `## Interfaces`. It takes the path to a work card; with no card it runs `feature-recipe`'s Phase 0 to find or make one. It writes `plan-code` to the card's `phase` and `phasesCompleted`, so `feature-recipe`, `recipe-relay` or a person can run it alone, for instance to redo this stage on a card. Cards from before the split, with `mise-en-place` in `phase` or `phase-2-mise-en-place.md` in `runNext`, still route here.

Its `stage.json` has the same shape as `evaluate-ticket`'s.

### test

The build stage after `plan-code`, once the test half of `feature-recipe`'s Cooking. It reads the work card's `## Acceptance Criteria`, `## Testing Strategy`, `## TDD Test Mapping` and `## Interfaces`, writes every mapped test before any code, runs them and confirms they fail, and marks each case written. It never opens a code file the plan names, so the tests cannot bend to the code. It takes the path to a work card; with no card it runs `feature-recipe`'s Phase 0 to find or make one. It writes `test` to the card's `phase` and `phasesCompleted`, so `feature-recipe`, `recipe-relay` or a person can run it alone, for instance to redo this stage on a card. In `recipe-relay` it is the test writer of Cooking in parallel. Cards from before the split, with `mise-en-place` or `plan-code` as the last phase, or `phase-3-cooking.md` in `runNext` and no `test` in `phasesCompleted`, route here.

Its `stage.json` has the same shape as `evaluate-ticket`'s.

### code

The build stage after `test`, once the rest of `feature-recipe`'s Cooking and all of its Tasting. It reads the work card's `## Solution`, `## Implementation Plan` and `## Interfaces`, writes the code to the tests `test` wrote, runs them and fixes the code until they pass, then holds a hard gate: `better-code-review` plus the project's own scoped tests, lint and type-check, fixed until each passes or is honestly deferred to CI, all written to `## Quality Gate Results`. It takes the path to a work card; with no card it runs `feature-recipe`'s Phase 0 to find or make one. It writes `code` to the card's `phase` and `phasesCompleted`, so `feature-recipe`, `recipe-relay` or a person can run it alone, for instance to redo this stage on a card. In `recipe-relay` it is both the code writer of Cooking in parallel, which stops once the code is written and never opens a test file, and the fix and taste step after it. Cards from before the split, with `test` or `cooking` as the last phase, or `phase-4-tasting.md` in `runNext`, route here.

Its `stage.json` has the same shape as `evaluate-ticket`'s, and raises `no-screen-change` when the change touches no surface a person sees.

### prepare-pr

The build stage after `code`. It reads the work card and the commits on the branch, decides the PR delivery strategy in `## PR Delivery Strategy`, opens the PR, attaches screenshots, waits on CI, and records `## PR`, `status` and `prUrl`. It takes the path to a work card; with no card it runs `feature-recipe`'s Phase 0 to find or make one. It writes `prepare-pr` to the card's `phase` and `phasesCompleted`, so `feature-recipe`, `recipe-relay` or a person can run it alone, for instance to redo the stage on a card. Cards from before the split, with `plating` in `phase` or `phase-5-plating.md` in `runNext`, still route here.

Its `stage.json` has the same shape as `evaluate-ticket`'s.

### code-docs

The last stage, after `prepare-pr`. It asks whether the change is worth documenting, writes the docs where the team keeps them or where `feature-recipe.docsDestination` says, marks the work card `delivered`, records the task done in the tracker, and runs `work-summary` unless `feature-recipe.runWorkSummary` is `false`. It reads the card's `## Problem`, `## Solution` and `## PR`. It takes the path to a work card; with no card it runs `feature-recipe`'s Phase 0 to find or make one. It writes `code-docs` to the card's `phase` and `phasesCompleted`, so `feature-recipe`, `recipe-relay` or a person can run it alone, for instance to redo the stage on a card. It ends the line: no New session / Continue menu, and a headless run ends with `runStatus: terminal`. Cards from before the split, with `documentation` in `phase` or `phase-6-documentation.md` in `runNext`, still route here.

Its `stage.json` has the same shape as `evaluate-ticket`'s.

### review-fix

The stage after `prepare-pr`. It reads the work card's `task` and `prUrl`, runs `better-code-review --headless` against the branch, fixes each finding by how it was verified (`ran`, `read` or `no`), test first, pushes to the open PR, and logs what it rejects and what stays not verified to `## Decisions` and `## Quality Gate Results`. It leaves `phase` and `phasesCompleted` alone, and stops `blocked` when the card has no open PR. It reads `recipe-relay.routineModel` and `recipe-relay.codingModel`. `recipe-relay` runs its section 5 through this skill, and it also runs alone on a card.

Its `stage.json` has the same shape as `evaluate-ticket`'s.

### ui-review

The stage after `code` when a change reaches a screen. It reads the work card's `task` (the design attached to the ticket), `## Solution` and the screenshots in `{scratch}/ui-review/`, never starts the app or takes screenshots, rates each difference critical, major or minor and writes `## UI Review`. It ends `fail` on a critical or major finding, which sends the line back to `code` at most twice, `pass` otherwise, and `inconclusive` with no screenshots or no design. It logs minor findings to `## Quality Gate Results` and leaves `phase` and `phasesCompleted` alone. It reads `recipe-relay.uiReviewerModel`. `recipe-relay` runs its UI review through this skill, and it also runs alone on a card.

Its `stage.json` has the same shape as `evaluate-ticket`'s.

### a11y-check

The stage after `ui-review` when a change reaches a screen. It reads the work card's `## Solution` for the routes the change touches, starts the app with `a11y-check.devCommand`, reaches each route under `a11y-check.baseUrl`, scans it with axe-core through Playwright and walks it by keyboard against `Accessibility.md`: `keyboard-reach`, `keyboard-trap`, `aria-hidden-focusable`, `focus-indicator`, `modal-focus` and `route-focus`. It writes `## Accessibility` and ends `fail` on a `critical` or `serious` finding, which sends the line back to `code` at most twice, `pass` otherwise, and `inconclusive` when a key is empty, the app never answers, the card names no route or Playwright cannot load. It logs `moderate` and `minor` findings to `## Quality Gate Results` and leaves `phase` and `phasesCompleted` alone. It reads `a11y-check.devCommand` and `a11y-check.baseUrl`. `no-screen-change` from `code` removes it from the line.

Its `stage.json` has the same shape as `evaluate-ticket`'s.

### security-review

The stage after `code` when a change touches security. `code` raises `touches-security` when the diff touches auth, sessions, permissions, secrets, crypto, parsing of outside input, or adds or bumps a dependency, and the line adds this stage after it. It reads the work card's `task` and `## Solution` and the diff from the fixed point to `HEAD`, runs one reviewer sub-agent against `references/checks.md` (OWASP Top 10 2021 and ASVS 4.0.3 level 1, limited to what a diff shows), never edits code, and writes `## Security Review` with findings that name file, line, check id and severity. It ends `fail` on a `critical` or `high` finding, which sends the line back to `code` at most twice, then `needs-input`, and `pass` otherwise, including an empty diff. It logs medium and low findings to `## Quality Gate Results` and leaves `phase` and `phasesCompleted` alone. `assembly-line` runs it in its own session, and it also runs alone on a card.

### judge

The readiness gate, run before anything is designed. It reads a work card's `task` or an `open-restaurant` service card's `parent`, runs a lint and then a judge sub-agent. One ticket gets only `open-decision` and `manual-reason`; a parent gets all four rules. A gap comments `## Not ready`, opens an issue that blocks the ticket, writes the gaps to `## Open Questions` and stops `blocked`; otherwise it comments `## Ready`. It leaves `phase` and `phasesCompleted` alone, and reads `open-restaurant.judgeModel` and the settings file's `## open-restaurant` section. `open-restaurant` runs it as a stage on a parent's line, and it also runs alone on a card.

Its `stage.json` has the same shape as `evaluate-ticket`'s.

### contract

The contract step for a parent and its sub-issues. It reads a work card's `task` or an `open-restaurant` service card's `parent`. A sub-agent copies, word for word from the issues, each shape one sub-issue produces and another consumes into `contract.json`; the skill posts it as `## Contract <id>` on the parent, copies it and the comment's link into the card's `## Contract`, and ends `done`. A shape no issue states goes to `gaps`, written to `## Open Questions`, and the skill ends `gaps` with `runStatus: needs-input`. An issue with no sub-issues needs no contract. It leaves `phase` and `phasesCompleted` alone and reads `open-restaurant.judgeModel`. `open-restaurant` runs it as a stage on a parent's line, and it also runs alone on a card.

Its `stage.json` has the same shape as `evaluate-ticket`'s.

### reproduce

The bug reproduction step, run before a bug's design. It reads a work card's `task`. One sub-agent tries the bug on `origin/<default branch>`, editing no tracked file and committing nothing. If it reproduces, the skill writes what it tried to `## Reproduction` and ends `reproduced`. If not, it comments `## Blocked <id>` on the ticket with what it tried, writes the comment's link to `## Reproduction` and `r1` to `## Open Questions`, and ends `not-reproduced` with `runStatus: blocked`. It leaves `phase` and `phasesCompleted` alone and reads no setting. `open-restaurant` runs it as a stage on a sub-issue's line, and it also runs alone on a card.

Its `stage.json` has the same shape as `evaluate-ticket`'s.

### integrate

The integration step for a parent and its sub-issues, run before QA. It reads a work card's `task`, or a service card's `parent` and `## Sub-issues`. It lists the criteria the parent QA proves under `## Integration`, and ends `no-scope` when there are none. In each repo checkout it builds `integration/<parent>` from `origin/<default branch>`, merging each sub-issue branch in blocks order, and never pushes it. It ends `integrated`, or on a merge conflict writes `i1` naming the two branches and ends `conflict` with `runStatus: needs-input`. It leaves `phase` and `phasesCompleted` alone and reads no setting key. `open-restaurant` runs it as a stage on a parent's line, and it also runs alone on a card.

Its `stage.json` has the same shape as `evaluate-ticket`'s.

### qa

The QA and fix step for a parent and its sub-issues, run after `integrate`. It reads a work card's `task` or a service card's `parent` and `## Sub-issues`, and the `## Integration` section `integrate` writes. It brings up one env, proves each criterion in QA scope with a `verdict.json` each, and posts each round as `## QA <parent>`. On `fail` it sends the fix to the owning branch, fast-forward only, rebuilds through `integrate` and runs again, at most twice. Past that, or on `inconclusive` or `blocked`, it stops at a human gate with `runStatus: gate`. Under a line it ends at the verdict, and the line sends `fail` back to `code`. It leaves `phase` and `phasesCompleted` alone and reads `open-restaurant.envName`, `open-restaurant.qaModel` and `open-restaurant.fixModel`. `open-restaurant` runs it as a stage on a parent's line, and it also runs alone on a card. Its `stage.json` has the same shape as `evaluate-ticket`'s.

### proof

The proof step for a parent and its sub-issues, run after `qa`. It reads a work card's `task` and `prUrl`, or a service card's `parent` and `## Sub-issues`, and the `## QA` section `qa` writes. It posts `## Proof` on each PR with the criteria it owns, each with its verdict and evidence, and one `## Proof <parent>` on the parent with each parent criterion, its evidence uploaded to the tracker, and a `### Sub-issues` list with each PR and how many of its criteria are met. A criterion QA did not prove takes its verdict from the sub-issue's card. It ends `done`, or `blocked` when a post does not land or there is no PR. It leaves `phase` and `phasesCompleted` alone and reads no setting key. `open-restaurant` runs it as a stage on a parent's line, and it also runs alone on a card. Its `stage.json` has the same shape as `evaluate-ticket`'s.

### review-request

The review request step for a parent and its sub-issues, or one ticket, once the PRs are ready. It reads a work card's `task` and `prUrl`, or a service card's `parent` and `## Sub-issues`. It waits on each PR's checks, then posts one message naming every PR to `open-restaurant.reviewChannel`, tagging the review groups the settings map from the team, and attaches the message link to the parent or ticket. It ends `requested`, or `skipped` with the reason on a red check, a timeout, no channel or a chat failure. It leaves `phase`, `phasesCompleted` and `gate` alone. `open-restaurant` runs it as a stage on a parent's line, and it also runs alone on a card. Its `stage.json` has the same shape as `evaluate-ticket`'s.

### merge

The last human gate on a line. It reads a work card's `task`, `prUrl` and `## PR`, or a service card's `parent` and `## Sub-issues`. Unresolved review threads end `threads-open` and send the line back to `review-fix`, at most twice. Otherwise it stops at `runStatus: gate` every time and, on a person's approval, merges in blocks order, retargets stacked PRs and moves the tickets to `open-restaurant.doneState`. A failed merge goes back to the gate. It leaves `phase`, `phasesCompleted` and `status` alone.

Its `stage.json` has the same shape as `evaluate-ticket`'s, with `gate: human`.

### uml

Draws UML diagrams of a repo, a folder or a system you describe, with PlantUML, and serves them on a local dark-theme page. It covers class, sequence, state, profile, composite structure, component, deployment, object, package and activity diagrams, plus entity-relationship diagrams drawn from migrations, SQL or ORM entities; `--diagrams=class,state` picks some. For the sequence, state and activity diagrams it picks the central flow or entity and says which and why, and a type the source gives no basis for gets a note instead of an invented drawing. The LLM writes only the `.puml` sources and a `uml.json` manifest; a Node script with no dependencies themes them, renders them and serves the page, where each diagram has an editor that saves back to its source and redraws. The server listens on `127.0.0.1` only and stops after 30 idle minutes.

`/uml` draws the current repo, `/uml src/orders` draws one path, and `/uml an order service where carts become orders` draws from the text. The sources land in `docs/uml` by default and stay there: a second run with the same types and target only renders them, a run that asks for other types or another target writes them anew and says why, and so does `--regenerate`. Stop the server early with the `kill <pid>` line it prints.

Needs Node, and either Java with the PlantUML jar (the skill offers to download it) or a PlantUML server URL. Graphviz is optional. The output folder, jar path, server and idle time are settings; see `setup`.

### non-functional-requirements

Writes or reviews the non-functional requirements of a project. Each NFR names an ISO/IEC 25010:2023 or 25019:2023 characteristic and subcharacteristic, states a target with a number, a unit and a window or percentile, has acceptance criteria that pass or fail, links to a user story, business rule or issue, and notes its architectural impact and MoSCoW priority. An NFR measured at runtime carries an observability plan in the project's monitoring tool, such as Datadog or Sentry: logs, metrics, a dashboard widget and a monitor. Write mode drafts or updates `<docsDir>/<project>/nfr.md` from docs pages, issues, the codebase and the monitoring tool; a value no source supports becomes `TBD — needs input from <role>`, and the skill asks for all of them in one round. Review mode audits a doc or a draft in four layers (standards, template, observability, coverage) and returns findings by severity, changing nothing unless you name the fixes.

The docs folder is a setting; see `setup`.

### summarize-llm-response

The shape of anything a human is going to read: findings as bullets with the evidence inline, action items as a checklist, a TL;DR only when there are enough findings to need one, and the attribution tag each destination expects. It carries a skip list — yes/no answers, commit messages, code-only replies — because it is meant to be wired to a blanket "run this before any communication" rule, and a blanket rule hands it work it has nothing to say about.

It does not self-trigger. Measured on Sonnet, a description alone fires it on 0-21% of the prompts it is written for; the same skill behind a CLAUDE.md line naming it fires on 93%. Wire it to a rule or call it by name. See `skills/summarize-llm-response/evals/`.

### epistemic-action

Go find out instead of predicting: read the file, run the command, probe the thing. Use it whenever you catch yourself writing "should", "probably", or "typically" about a codebase you have not opened.

### work-summary

Writes up the current session as a dated markdown note: what was done, the decisions, the problems and how they were solved, and what is left. The note opens with frontmatter another tool can read — a theme, a category and the signals the work showed, such as `tdd` or `leadership` — and, if you give it values to tag against, the values the work showed. It redacts secrets and never overwrites an older note. `feature-recipe` runs it as its last step when it is installed.

### pause-work

Parks half-done work for tomorrow. It reads the folder, branch and git state, finds the ticket key on the branch or in the conversation (or writes `none`, never a made-up key), and writes one task: the ticket, the absolute folder, where the work stopped, what is left as a checklist starting with the very next action, and the open questions as a numbered list. It saves the task due tomorrow in the to-do tool the settings name, such as Todoist, or as a comment on the ticket in a ticket tool such as Linear or GitHub, then reads it back to check it landed. With no tool set or found, it prints the task.

The tool, project, due date and labels are settings; see `setup`.

### plan-work

Plans a feature into tickets, or reviews tickets already planned, in any tracker. In plan mode it reads the feature, its details and specs, checks the tracker for work that already exists, then decides the shape: one ticket or a project, milestones as vertical slices with clean-up last, and sub-issues only when the work needs more than one PR or repo. It writes each body from a template, puts a `[[gap Qn: …]]` marker and a numbered question where a fact is missing instead of guessing, runs a bundled lint (`scripts/check_plan.py`) on the draft, and shows it. Nothing reaches the tracker before approval; after writing, it reads the tickets back and lints them again. Review mode fills a fixed report, each finding with the exact change it proposes, and writes nothing.

Screen work carries a `## Design` section with the design link and before/after screenshots; a design ticket always names the frontend ticket that builds it, existing or new. The rules live in a standard, bundled at `references/standard.md` or the team's own. The standard, lint, tracker team, labels, repos, whether every new Feature goes behind a feature flag and which flag tool, whether to hand the tickets to `plan-assembly-line`, and whether their lines go on the ticket or in a local file (`assembly-line.lineDestination`) are settings; see `setup`.

Every ticket and sub-issue it saves opens with the line Planned with `plan-work`., which `plan-assembly-line` reads to skip `judge`.

### weekly-planning

Plans the work week around your calendar. It counts the work days, leaving out holidays and days off, reads the meetings you have not declined, takes your open tickets from the tracker plus anything you add when you call it, and fits them into the free time with a bundled script: never more than two tickets in progress at once, nothing on top of a meeting, blocks of at most two hours. Tickets without an estimate get one question. What does not fit goes in its own list. It saves the plan to a folder, one file per week, or to a tool such as Todoist (one task per day) or Notion, then reads it back; with no destination, it prints it.

Where the plan goes, where tickets come from, the work hours, hours per estimate point and the ticket limit are settings; see `setup`.

### week-summary

Writes a review of one week, one file per week: tickets closed, PRs merged and confirmed by their real merge date, reviews of other people's PRs counted by when you submitted them, one line per work-session note, and chat activity by theme. A Signal section reads across all four for patterns, gaps included, and a Summary block rolls up the counts, with sessions per day divided by working days, not calendar days. Your reflection headers and the last Weekly Update question stay yours to fill. It reads the notes `work-summary` writes, and skips any source the session has no tool for.

Needs the `gh` CLI for GitHub.

### ship-pr

Turns working-tree changes into pull requests. It finds every repo in the folder with changes, plans one Conventional Commit per stage with a body that gives context and trade-offs, fills the repo's own PR template from the diff and the ticket, and ticks a checklist box only when the diff proves it. A revert keeps the branch's own ticket key in the header and names the reverted ticket in the body. It commits from a message file, opens one PR per repo, never stacks PRs, and by default pauses for your approval before any push.

Needs the `gh` CLI. The commit header shape, the approval pause, draft PRs, the commands to run before each commit and the MCP server that reads tickets are settings; see `setup`.

### setup

Writes `.bosi-skills.md`, the settings file the other skills read: where `work-summary` saves notes and which values it tags against, where `week-summary` writes reviews and who it counts as you, where `feature-recipe` keeps recipe cards, which mode `feature-recipe` and `better-code-review` run in when the request names none, which tracker states and models `recipe-relay` uses, how `ship-pr` titles, gates and validates a PR, where `uml` keeps its sources and how it renders them, where `non-functional-requirements` writes its NFR docs, how `open-restaurant` maps sub-issues to repos, names its QA env, moves tracker states and picks its models, where `pause-work` saves the task for tomorrow, where `weekly-planning` saves the week plan, where its tickets come from, the work hours and how many tickets run at once, and which standard, lint, team, labels, repos and flag rules `plan-work` plans with. A skill looks in the current folder first, then in `$HOME`, and each setting falls back on its own, so a project file only holds what it changes. With no file, every skill keeps its old behaviour. The contract is `skills/setup/references/config.md`.

## Layout

```
.agents/
  plugins/marketplace.json  Codex marketplace catalog, one entry pointing at the repo root
.claude-plugin/
  marketplace.json    Claude Code marketplace catalog, one entry pointing at the repo root
  plugin.json         Claude Code plugin manifest
.codex-plugin/
  plugin.json         Codex plugin manifest
dsh/
  cordis.patch.yml    DeepSeek Harness bundle layer: one row, mounting the provider
  index.js            the Cordis plugin — a skill provider over skills/
  index.test.mjs      holds that provider to the skills that actually exist
opencode/
  build-index.py      writes and checks skills/index.json, the list opencode fetches
package.json          Pi package manifest (`pi.skills`) and DeepSeek Harness bundle (`dsh.bundle`)
skills/
  index.json          the skill list at the root of the URL opencode downloads from
  better-code-review/ SKILL.md + references/ (page, slack) + assets/report-template.html + scripts/
  feature-recipe/     SKILL.md + phases/ + references/ + scripts/
  evaluate-ticket/    SKILL.md + dependencies/ (grill-me) + scripts/
  plan-code/          SKILL.md + stage.json + scripts/
  prepare-pr/         SKILL.md + stage.json + scripts/
  test/               SKILL.md + stage.json + scripts/
  code/               SKILL.md + stage.json + scripts/
  code-docs/          SKILL.md + stage.json + scripts/
  review-fix/         SKILL.md + stage.json + scripts/
  ui-review/          SKILL.md + stage.json + scripts/
  a11y-check/         SKILL.md + stage.json + scripts/
  security-review/    SKILL.md + stage.json + references/ + scripts/
  judge/              SKILL.md + stage.json + scripts/
  contract/           SKILL.md + stage.json + scripts/
  reproduce/          SKILL.md + stage.json + scripts/
  integrate/          SKILL.md + stage.json + scripts/
  qa/                 SKILL.md + stage.json + scripts/
  proof/              SKILL.md + stage.json + scripts/
  review-request/     SKILL.md + stage.json + scripts/
  merge/              SKILL.md + stage.json + scripts/
  open-restaurant/    SKILL.md + scripts/
  recipe-relay/       SKILL.md + scripts/
  code-standards/     SKILL.md + Common/ + Frontend/ + Testing/ + Typescript/ + scripts/
  epistemic-action/   SKILL.md + bench/
  summarize-llm-response/  SKILL.md + evals/ (trigger + behaviour harnesses)
  work-summary/       SKILL.md + evals/ (scenarios)
  pause-work/         SKILL.md + evals/ (scenarios)
  weekly-planning/    SKILL.md + scripts/plan_week.py (+ tests) + evals/ (scenarios)
  plan-work/          SKILL.md + references/ (standard, review report) + scripts/check_plan.py (+ tests) + evals/ (scenarios)
  week-summary/       SKILL.md + templates/week-review.md + evals/ (scenarios)
  ship-pr/            SKILL.md + references/conventions.md + scripts/detect_context.sh + evals/ (scenarios)
  uml/                SKILL.md + references/ (notation per diagram type) + scripts/uml.mjs + evals/
  non-functional-requirements/  SKILL.md + references/ (standards, ISO models, template, observability, review)
  setup/              SKILL.md + assets/bosi-skills.md + references/config.md + scripts/
```

Skills reference their own bundled files by path relative to their `SKILL.md` — `./references/patterns.md`, `../code-standards/SKILL.md` — so the paths resolve whether the skill is installed personally, in a project, or as part of this plugin, and under any agent runtime. See `AGENTS.md`.

## Validate a change

```
claude plugin validate --strict .
node --test 'dsh/**/*.test.mjs'
node --test 'skills/uml/scripts/*.test.mjs'
python3 skills/feature-recipe/scripts/check-headless-contract.py
python3 opencode/build-index.py --check
python3 skills/better-code-review/scripts/check-headless.py
python3 skills/better-code-review/scripts/check-tests-axis.py
python3 skills/better-code-review/scripts/check-evidence.py
python3 skills/better-code-review/scripts/check-slack.py
python3 skills/feature-recipe/scripts/check-tasting-evidence.py
python3 skills/recipe-relay/scripts/check-no-pause.py
python3 skills/feature-recipe/scripts/check-goal-and-measure.py
python3 skills/evaluate-ticket/scripts/check-evaluate-ticket.py
python3 skills/plan-code/scripts/check-plan-code.py
python3 skills/prepare-pr/scripts/check-prepare-pr.py
python3 skills/test/scripts/check-test.py
python3 skills/code/scripts/check-code.py
python3 skills/code-docs/scripts/check-code-docs.py
python3 skills/review-fix/scripts/check-review-fix.py
python3 skills/ui-review/scripts/check-ui-review.py
python3 skills/a11y-check/scripts/check-a11y-check.py
python3 skills/security-review/scripts/check-security-review.py
python3 skills/judge/scripts/check-judge.py
python3 skills/contract/scripts/check-contract.py
python3 skills/reproduce/scripts/check-reproduce.py
python3 skills/integrate/scripts/check-integrate.py
python3 skills/qa/scripts/check-qa.py
python3 skills/proof/scripts/check-proof.py
python3 skills/review-request/scripts/check-review-request.py
python3 skills/merge/scripts/check-merge.py
python3 skills/assembly-line/scripts/check-stage-spec.py skills/evaluate-ticket
python3 skills/assembly-line/scripts/check-stage-spec.py skills/plan-code
python3 skills/assembly-line/scripts/check-stage-spec.py skills/prepare-pr
python3 skills/assembly-line/scripts/check-stage-spec.py skills/test
python3 skills/assembly-line/scripts/check-stage-spec.py skills/code
python3 skills/assembly-line/scripts/check-stage-spec.py skills/code-docs
python3 skills/assembly-line/scripts/check-stage-spec.py skills/review-fix
python3 skills/assembly-line/scripts/check-stage-spec.py skills/ui-review
python3 skills/assembly-line/scripts/check-stage-spec.py skills/a11y-check
python3 skills/assembly-line/scripts/check-stage-spec.py skills/security-review
python3 skills/assembly-line/scripts/check-stage-spec.py skills/judge
python3 skills/assembly-line/scripts/check-stage-spec.py skills/contract
python3 skills/assembly-line/scripts/check-stage-spec.py skills/reproduce
python3 skills/assembly-line/scripts/check-stage-spec.py skills/integrate
python3 skills/assembly-line/scripts/check-stage-spec.py skills/qa
python3 skills/assembly-line/scripts/check-stage-spec.py skills/proof
python3 skills/assembly-line/scripts/check-stage-spec.py skills/review-request
python3 skills/assembly-line/scripts/check-stage-spec.py skills/merge
python3 skills/assembly-line/scripts/test_check_stage_spec.py
python3 skills/assembly-line/scripts/check-line-format.py
python3 skills/assembly-line/scripts/test_check_line_format.py
python3 skills/assembly-line/scripts/build-catalog.py --check
python3 skills/assembly-line/scripts/test_build_catalog.py
python3 skills/assembly-line/scripts/test_validate_line.py
python3 skills/assembly-line/scripts/test_apply_signals.py
python3 skills/assembly-line/scripts/test_run_log.py
python3 skills/assembly-line/scripts/test_board.py
python3 skills/assembly-line/scripts/check-assembly-line.py
python3 skills/assembly-line/scripts/check-no-pause.py
python3 skills/assembly-line/scripts/check-split-cooking.py
python3 skills/plan-assembly-line/scripts/check-plan-assembly-line.py
python3 skills/plan-assembly-line/scripts/test_stats.py
python3 skills/feature-recipe/scripts/check-pr-screenshots.py
python3 skills/recipe-relay/scripts/check-review-evidence.py
python3 skills/recipe-relay/scripts/check-split-cooking.py
python3 skills/recipe-relay/scripts/check-ui-review.py
python3 skills/open-restaurant/scripts/check-open-restaurant.py
python3 skills/code-standards/scripts/check-tooling-rule.py
python3 skills/setup/scripts/check-config.py
python3 -m unittest discover -s skills/plan-work/scripts -p 'test_*.py'
```

Codex has no validator subcommand, so the nearest equivalent is a throwaway home. This installs the plugin for real and leaves your own Codex config untouched:

```
home=$(mktemp -d)
CODEX_HOME="$home" codex plugin marketplace add .
CODEX_HOME="$home" codex plugin add bosi-programming-skills@bosi-programming
```

Pi has no validator subcommand either, but `PI_CODING_AGENT_DIR` relocates its config directory, so the same probe runs against a throwaway settings file:

```
agent=$(mktemp -d)
PI_CODING_AGENT_DIR="$agent" PI_OFFLINE=1 pi install .
PI_CODING_AGENT_DIR="$agent" PI_OFFLINE=1 pi list
```

`check-headless-contract.py` is `feature-recipe`'s own check: it fails if a
phase stops speaking the headless dialect, if the interactive endings
disappear, if the old `b972f03` phase-end footer creeps back, if
`evaluate-ticket` loses its grill-or-skip call, if Phase 0 stops routing old
and new cards to `evaluate-ticket` and `prepare-pr`, or if this README
stops describing the skills that exist. Offline, stdlib only — run it after
editing a phase file or `evaluate-ticket`.

`check-headless.py` is `better-code-review`'s own check: it fails if the
`## Headless` section loses its entry, a default for a step that would ask,
the text format of a finding or its closing lines, if steps 1, 2 or 6 stop
pointing to it, if _Default mode_ loses its grep for the key, if the run
stops stating its mode and where it came from before step 1, or if a relative
path in the skill does not resolve. Offline, stdlib only — run it after
editing `better-code-review`.

`check-tests-axis.py` is `better-code-review`'s other check: it fails if
`code-standards/Testing/Tests.md` loses a rule or a red flag, if the catalog
stops listing it, or if the Tests axis drops out of the review's process, its
headless format, the report template, this README or the plugin manifests.
Offline, stdlib only — run it after editing either skill.

`check-evidence.py` is `better-code-review`'s third check: it fails if the
review stops reading the tooling config, running the project's checks,
probing missing and tautological tests in a throwaway worktree, tagging
evidence as ran, read or no, or linking `epistemic-action`. Offline, stdlib
only — run it after editing `better-code-review`.

`check-tasting-evidence.py` is `feature-recipe`'s second check: it fails if
`code` stops keeping the review's `Reviewed:` line and `Not verified:`
entries, runs the checks again on code the review already ran them on, or if
the rule against code comments loses its exception. Offline, stdlib only — run
it after editing `code` or the skill's rules.

`check-goal-and-measure.py` is `feature-recipe`'s third check: it fails if the
recipe card loses `## Goal & measure` or moves it away from `## Problem`, if
`evaluate-ticket` stops grilling on how we will know it worked, stops writing
the three bullets, allows an invented metric, or drops the headless gap log, or
if `prepare-pr` stops carrying the section into the PR. Offline, stdlib only — run
it after editing `evaluate-ticket`, `prepare-pr` or the card template.

`check-evaluate-ticket.py` is `evaluate-ticket`'s own check: it fails if the
skill loses its frontmatter, stops naming the work card as its input and
Phase 0 as the way in without one, stops listing the card fields it writes or
writing `evaluate-ticket` to `phase`, drops its `## Headless` section or its
hand-off to `plan-code`, links a file that does not exist, or if this README
loses its section. Offline, stdlib only — run it after editing
`evaluate-ticket`.

`check-plan-code.py` is `plan-code`'s own check: it fails if the skill loses
its frontmatter, stops naming the work card as its input and Phase 0 as the
way in without one, stops listing the card fields it writes or writing
`plan-code` to `phase`, drops the `## Interfaces` step or its stop on a plan
too vague to name them, drops its `## Headless` section or its hand-off to
`test`, links a file that does not exist, if the old phase file comes back,
or if this README loses its section. Offline, stdlib only — run it after
editing `plan-code`.

`check-prepare-pr.py` is `prepare-pr`'s own check: fails if the skill loses
its frontmatter, stops naming the work card as its input and Phase 0 as the
way in without one, stops listing the card fields it writes or writing
`prepare-pr` to `phase`, drops the chunk pick-up section or its `## Headless`
section, loses its hand-off to `code-docs`, links a file that does not
exist, if the old phase file comes back, or if this README loses its section.
Offline, stdlib only — run it after editing `prepare-pr`.

`check-test.py` is `test`'s own check: it fails if the skill loses its
frontmatter, stops naming the work card as its input and Phase 0 as the way in
without one, stops listing the card fields it writes or writing `test` to
`phase`, drops the rule that it never opens a code file or that the tests must
fail first, drops its `## Headless` section or its hand-off to `code`, links a
file that does not exist, if `code` writes the mapped tests again, or if this
README loses its section. Offline, stdlib only — run it after editing `test`
or `code`.

`check-code.py` is `code`'s own check: it fails if the skill loses its
frontmatter, stops naming the work card as its input and Phase 0 as the way in
without one, stops listing the card fields it writes or writing `code` to
`phase`, drops the rule that the code writer beside `test` never opens a test
file, drops the review or the hard gate, drops its `## Headless` section or its
hand-off to `prepare-pr`, links a file that does not exist, if the old Cooking
or Tasting phase file comes back, or if this README loses its section.
Offline, stdlib only — run it after editing `code`.

`check-code-docs.py` is `code-docs`'s own check: it fails if the skill loses
its frontmatter, stops naming the work card as its input and Phase 0 as the
way in without one, stops listing the card fields it writes or writing
`code-docs` to `phase` and `delivered` to `status`, stops reading its two
settings or running `work-summary`, offers a New session / Continue menu,
drops its `## Headless` section or its terminal run record, stops logging a
skipped docs step or saying "no docs" in its summary, links a file that
does not exist, if the old Documentation phase file comes back, or if this
README loses its section. Offline, stdlib only — run it after editing
`code-docs`.

`check-review-fix.py` is `review-fix`'s own check: it fails if the skill loses
its frontmatter, stops naming the work card, `prUrl` and `task` as its input,
stops ending `blocked` without an open PR, stops listing the card fields it
writes or leaving `phase` and `phasesCompleted` alone, stops reading its two
settings, drops the headless review, the fix by `Verified:` tag or its
`## Headless` section, says "recipe card", links a file that does not exist,
if `recipe-relay` stops loading it, or if this README loses its section.
Offline, stdlib only — run it after editing `review-fix`.

`skills/ui-review/scripts/check-ui-review.py` is `ui-review`'s own check: it
fails if the skill loses its frontmatter, stops naming the work card, `task`,
`## Solution` and `{scratch}/ui-review/` as its input, stops ending
`inconclusive` with no screenshots, stops listing the card fields it writes or
leaving `phase` and `phasesCompleted` alone, stops reading its setting, drops
the design, compare or verdict step, lets the reviewer start the app or take
screenshots, loses its `## Headless` section, says "recipe card", links a file
that does not exist, names private content, if `stage.json` stops returning
`fail` to `code` twice, if `recipe-relay` stops loading it, or if this README
loses its section. Offline, stdlib only — run it after editing `ui-review`.

`check-judge.py` is `judge`'s own check: it fails if the skill loses its
frontmatter, stops naming the work card, `task`, the service card and `parent`
as its input, stops ending `not-ready` with `runStatus: blocked` when it cannot
read the issue, stops listing the card fields it writes or leaving `phase` and
`phasesCompleted` alone, stops reading its setting, drops the lint, the four
judge rules, the one-ticket rule, the not-ready or ready step or its
`## Headless` section, says "recipe card", links a file that does not exist,
names private content, if its intro points at an `open-restaurant` section again, or if this README
loses its section. Offline, stdlib only — run it after editing `judge`.

`check-contract.py` is `contract`'s own check: it fails if the skill loses its
frontmatter, stops naming the work card, `task`, the service card and `parent`
as its input, stops ending `blocked` on bad input or `done` on an issue with no
sub-issues, stops listing the card fields it writes or leaving `phase` and
`phasesCompleted` alone, stops reading its setting, drops the shapes, post, gaps
or done step, loses the rule that the latest `## Contract` comment wins, drops
its `## Headless` section, says "recipe card", links a file that does not
exist, names private content, if `stage.json` stops returning `gaps` to
`contract` with limit 0 and gate `auto`, if its intro points at an `open-restaurant` section again,
or if this README loses its section or its Validate lines. Offline, stdlib only
— run it after editing `contract`.

`check-reproduce.py` is `reproduce`'s own check: it fails if the skill loses its
frontmatter, stops naming the work card, `task` and the bug ticket as its input,
stops ending `blocked` on bad input, stops listing the card fields it writes or
leaving `phase` and `phasesCompleted` alone, grows a settings section, drops the
try, not-reproduced or reproduced step, stops trying on
`origin/<default branch>` with no tracked file edited and nothing committed,
stops commenting `## Blocked <id>` with what it tried, drops its `## Headless`
section, says "recipe card", links a file that does not exist, names private
content, if `stage.json` stops returning `not-reproduced` to `reproduce` with
limit 0, past `human` and gate `auto`, if its intro points at an `open-restaurant` section again, or
if this README loses its section or its Validate lines. Offline, stdlib only —
run it after editing `reproduce`.

`check-integrate.py` is `integrate`'s own check: it fails if the skill loses its
frontmatter, stops naming the work card, `task`, the service card, `parent` and
`## Sub-issues` as its input, stops ending `blocked` on bad input or uncommitted
changes, stops listing the card fields it writes or leaving `phase` and
`phasesCompleted` alone, drops a verdict, loses the QA scope guidance in
`## Settings`, drops the scope, integrate, conflict or integrated step, stops
building `integration/<parent>` from `origin/<default branch>` in blocks order,
may push it, loses its rebuild guard, stops aborting a conflicting merge and
naming the two branches, drops its `## Headless` section, says "recipe card",
links a file that does not exist, names private content, if `stage.json` stops
returning `conflict` to `integrate` with limit 0, past `needs-input` and gate
`auto`, if its intro points at an `open-restaurant` section again, or if this README loses its
section or its Validate lines. Offline, stdlib only — run it after editing
`integrate`.

`check-qa.py` is `qa`'s own check: it fails if the skill loses its
frontmatter, stops naming the work card, `task`, the service card, `parent`,
`## Integration` and `### QA scope` as its input, stops ending `blocked` on bad
input or a checkout off `integration/<parent>`, stops listing the card fields it
writes or leaving `phase` and `phasesCompleted` alone, drops a verdict, loses
its three keys or the QA guidance in `## Settings`, loses its `## Under a line`
section, drops the QA, on pass, on fail, fix, fix check or limits step, stops
running one env for the parent, may force a push or push `integration/<parent>`,
stops rebuilding through `integrate`, drops its `## Headless` section, says
"recipe card", links a file that does not exist, names private content, if
`stage.json` stops taking, delivering or returning as `qa` needs, with gate
`auto`, if its intro points at an `open-restaurant` section again, or if this README loses its
section or its Validate lines. Offline, stdlib only — run it after editing `qa`.

`check-proof.py` is `proof`'s own check: it fails if the skill loses its
frontmatter, stops naming the work card, `task`, the service card, `parent`,
`## Sub-issues`, `prUrl` and `## QA` as its input, stops ending `blocked` on bad
input or no PR, stops listing the card fields it writes or leaving `phase` and
`phasesCompleted` alone, drops a verdict, loses its no-key line in `## Settings`,
drops the criteria, PR, parent, check or done step, stops posting `## Proof` on
each PR and `## Proof <parent>` on the parent, drops its `## Headless` section,
says "recipe card", links a file that does not exist, names private content, if
`stage.json` stops taking, delivering or returning as `proof` needs, with gate
`auto`, if its intro points at an `open-restaurant` section again, or if this README loses its
section or its Validate lines. Offline, stdlib only — run it after editing
`proof`.

`check-review-request.py` is `review-request`'s own check: it fails if the skill
loses its frontmatter, stops naming the work card, `task`, the service card,
`parent`, `## Sub-issues` and `prUrl` as its input, stops ending `blocked` on bad
input or no PR, stops listing the card fields it writes or leaving `phase`,
`phasesCompleted` and `gate` alone, drops a verdict, loses
`open-restaurant.reviewChannel` or its default in `## Settings`, drops the open
PRs, checks, request, link or done step, stops waiting on checks, counting no
checks as green or skipping on red or a timeout, stops posting one message with
every PR, never guessing a group or retrying a post once, drops its `## Headless`
section, says "recipe card", links a file that does not exist, names private
content, if `stage.json` stops taking, delivering or returning as
`review-request` needs, with gate `auto`, if its intro points at an `open-restaurant` section again,
or if this README loses its section or its Validate lines. Offline, stdlib only
— run it after editing `review-request`.

`check-merge.py` is `merge`'s own check: it fails if the skill loses its
frontmatter, stops naming the work card, `task`, `prUrl`, `## PR`, the service
card and `parent` as its input, stops ending `blocked` on bad input, stops
listing the card fields it writes or leaving `phase`, `phasesCompleted` and
`status` alone, stops reading its setting, drops the threads, gate, merge or
done step, merges without approval, loses its `## Headless` section, says
"recipe card", links a file that does not exist, names private content, if
`stage.json` stops returning `threads-open` to `review-fix`, if its intro points at an `open-restaurant` section again, if the work card template's `runStatus` loses `gate`, or if
this README loses its section. Offline, stdlib only — run it after editing
`merge`.

`check-pr-screenshots.py` is `feature-recipe`'s fourth check: it fails if
`prepare-pr` stops attaching the run's screenshots with `gh pr edit --attach`,
drops their alt text or the way to place them in the description, retries
every upload after a partial failure, takes or invents screenshots of its own,
or asks about them in a night run. Offline, stdlib only — run it after editing
`prepare-pr`.

`check-review-evidence.py` is `recipe-relay`'s own check: it fails if the
closing review pass, read from `review-fix`, stops sorting findings by `ran`,
`read` or `no`, stops logging what the review left not verified, or if
relay section 5 stops loading `review-fix`. Offline, stdlib only — run it
after editing `recipe-relay` or `review-fix`.

`check-no-pause.py` is `recipe-relay`'s no-pause check: it fails if the skill
pauses between units or posts a checkpoint to wait on, loses its stop
condition for open questions, or drops the closing headless
`better-code-review` pass, which it reads from `review-fix`, or its load in
relay section 5. Offline, stdlib only — run it after editing
`recipe-relay`.

`check-split-cooking.py` is `recipe-relay`'s other check: it fails if Cooking
stops naming its interfaces first, starting a test writer and a code writer
per repo at the same time on the same branch and worktree, or keeping each
blind to the other's work; if it gives the writers worktrees of their own; or
if either skill drops its model setting. Offline, stdlib only — run it after
editing `recipe-relay` or step 4 of `better-code-review`.

`check-ui-review.py` is `recipe-relay`'s third check: it fails if the UI
review stops running after the last Cooking unit, goes back to waiting on a
signal, stops loading `ui-review`, or stops sending a `fail` back at most
twice. It reads the design and comparison steps from `ui-review`, and fails if
the relay stops loading it. Offline, stdlib only — run it after editing
`recipe-relay`.

`check-open-restaurant.py` is `open-restaurant`'s own check: it fails if a
section goes missing, if an old fixed-stage section (readiness gate, contract,
integrate and QA, proof, review gate, merge gate) comes back, if the skill
names `recipe-relay`, a `gate: review` or a stage `SKILL.md` link, if it stops
reading every line before any card exists, stops requiring a line comment, a
valid line and a `{"group": "sub-issues"}`, or stops running the parent's line
through `assembly-line` with the `restaurant:` prefix, the returns off the
line and the merge gate, if same-repo sub-issues stop running one at a time, if
the sub-issue PR may be a draft, batched in one review or linked to the parent,
if the early unblock loses its note file, follow-up or change rule, if the
skill names private content, if `prepare-pr` stops taking a named base branch,
or if this README or the DeepSeek Harness test stops listing the skill.
Offline, stdlib only — run it after editing `open-restaurant` or
`prepare-pr`.

`check-tooling-rule.py` is `code-standards`' own check: it fails if the catalog
goes back to guessing what tooling enforces instead of reading the lint,
format and type-check config, or if a catalog file it lists is missing.
Offline, stdlib only — run it after editing `code-standards`.

`check-config.py` is `setup`'s own check: it fails if the settings contract
loses the file name, the lookup order or a key's default, if the template
lacks a key, if a skill that reads a key stops pointing to the contract, or if
`work-summary`, `week-summary` or their scenarios name private content or
hard-code a folder or login, or if `AGENTS.md` loses the workflow for adding a
setting. Offline, stdlib only — run it after editing `setup`, `work-summary`,
`week-summary` or a skill that reads the settings.

## Falsify a change

`epistemic-action` claims things about how the model behaves, so it gets tested
rather than asserted. `evals/` holds a suite of cases built on a fixture repository
where every file's name, README or doc comment contradicts its own code. An answer
from memory is provably wrong there, and control cases sit beside the traps so that
a skill cannot score well by doing nothing but hedge.

```
CLAUDE_CODE_WALNUT_SPIRE=1 claude plugin eval . \
  --ablation with-without --runs 3 --scaffold --no-publish \
  --allow-tools Read Glob Grep Bash Edit Write Skill
```

The ablation runs every case twice, once with the plugin and once without, so the
number that matters is the gap between the two rather than the score on its own.

`claude plugin eval` is in early access. `evals/SCHEMA.md` records the
`case.yaml` format it expects, which is not documented anywhere else.

## License

MIT. See `LICENSE`.
