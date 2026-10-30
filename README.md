# Bosi Programming Skills

Fourteen Claude Code skills, packaged as an installable plugin. Two of them carry the rest:

- **`recipe-relay`** takes one ticket from the tracker to a reviewed pull request, ready for review, with nobody answering questions on the way. Every phase runs in its own sub-agent, every checkpoint takes its own recommendation and logs it, and the run stops only at a question with no reasonable default.
- **`open-restaurant`** is an LLM factory. Hand it a parent issue and it runs `recipe-relay` once per sub-issue, in parallel across repos, then integrates the branches, QAs them as one system, writes proof and stops only at the human gates for review and merge.

The other twelve feed those two or stand alone. `feature-recipe` is the six-phase workflow the relay runs. `better-code-review` reviews a diff along three axes, and `code-standards` is the catalog it reads from. `ship-pr` commits, pushes and opens a PR from the repo's template. `uml` draws UML diagrams of a codebase or a description, and `non-functional-requirements` writes and reviews NFRs. `summarize-llm-response` and `epistemic-action` check the model's own writing and reasoning before it reaches you. `work-summary` writes up a work session as a dated note, `pause-work` parks half-done work as a task for tomorrow, `week-summary` turns a week of those notes and your tracker, GitHub and chat activity into a review, and `setup` writes the settings file the others read their defaults from.

The same fourteen install into Codex, DeepSeek Harness, Pi and opencode, from the same `skills/` directory. One plugin source, five harnesses, nothing copied — so a skill cannot drift between harnesses. The one exception is opencode, which fetches a skill list over HTTP: `skills/index.json` is generated from that same tree and kept honest by `opencode/build-index.py --check`.

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

### recipe-relay

Takes one ticket to a pull request that is open, reviewed and ready for review, without asking you anything on the way. You name the task; the session runs `feature-recipe`'s six phases, each in its own sub-agent, without changing any of the recipe's files. Each sub-agent takes the recommendation every checkpoint states — the grilling, the plan, the test list, the PR description — and logs it to the recipe card as `relay:`, so you can read afterwards what it chose and why. What reaches the chat is one line per unit, and the session starts the next unit without waiting for a reply.

How the ticket moves:

1. **Reading the Recipe and Mise en Place** turn the ticket into a plan on the recipe card.
2. **Cooking** splits. One sub-agent names the interfaces; then, for each repo, a test writer and a code writer work at the same time on the same branch, neither opening the other's files, so the tests cannot bend to the code. A last sub-agent makes the tests pass and runs Tasting: the project's scoped tests, lint and `better-code-review`.
3. **UI review.** When the change reaches a screen, a UI reviewer runs beside that last sub-agent. It waits for the screenshots Tasting captures, compares them with the design attached to the ticket, and sends critical and major differences back for up to two more rounds.
4. **Plating** opens the PR ready for review, never as a draft, waits on CI and fixes it, and moves the ticket to `recipe-relay.reviewState` (`In Review` by default).
5. **Review and fix.** The moment the PR opens, a sub-agent runs `better-code-review --headless` against the branch. The session checks each finding by how it was verified — `ran`, `read` or `no` — fixes the ones that hold, test first, pushes to the open PR, and logs each one it rejects with the reason.
6. **Documentation** closes the task out and moves the ticket to `recipe-relay.doneState` (`Done` by default).

It stops only at the end, or when a sub-agent reports `blocked` or `needs-input`: a one-way door or a question with no reasonable default. Then it asks you in chat, and running it again picks the card back up where it stopped. It never merges; the PR waits for a person.

`recipe-relay.codingModel` and `recipe-relay.uiReviewerModel` pick the models for the writers and the UI reviewer. A `## recipe-relay` section in a project's `.bosi-skills.md` adds rules every sub-agent follows in that project; delete the section when the project ends.

### open-restaurant

An LLM factory. Hand it a parent issue — an epic or a story with sub-issues — and it delivers every sub-issue, each through `recipe-relay` on its own recipe card, to its own PR, then puts the parts together and proves they work as one. The parent is the order and each sub-issue a dish: this session runs the kitchen and never cooks a dish itself. A person comes in at two gates: before review is requested and before anything merges.

The line, in order:

1. **Readiness gate.** A lint, then a judge sub-agent, look for open decisions, "same as X" shorthand, shapes passed between sub-issues that neither one states, and manual checks with no reason. A gap stops the run with a `## Not ready` comment and an issue that blocks the parent. It never fills a gap on the parent's behalf.
2. **Contract.** A sub-agent copies, word for word from the issues, each shape one sub-issue produces and another consumes, and posts it on the parent. A person may edit it there; the latest comment wins.
3. **Cooking.** Sub-issues in different repos cook at the same time. Those in one repo cook one at a time in its checkout, and one blocked by another in the same repo stacks its PR on the blocker's branch. A sub-issue blocked by one in another repo starts as soon as the blocker's Interfaces unit writes it an unblock note with the shapes it needs, not when the blocker's PR opens.
4. **Review per PR.** Each PR opens ready for review, linked to its own sub-issue, which moves to `open-restaurant.implementedState`. Its own headless `better-code-review` sub-agent starts the moment it opens, and the findings get fixed on its branch.
5. **Integrate and QA.** Once every card ends, it merges the branches into a local integration branch it never pushes, brings up one QA env for the parent, and proves each criterion with saved evidence. Failures get fixed on the owning sub-issue's branch, fast-forward only, for at most two QA rounds.
6. **Proof.** A `## Proof` on each PR, and one on the parent with each criterion and its evidence.
7. **Human gates.** It stops before asking for review, then waits on checks and posts the PRs to `open-restaurant.reviewChannel`. It stops again before merging, then merges in blocks order and moves the sub-issues, and the parent when no criterion is left open, to `open-restaurant.doneState`.

Every stop writes its state to a service card next to the recipe cards; running it again on the same parent goes on from there.

Needs a tracker tool in the session and one repo checkout per repo in the folder it runs from. Team-specific steps (the readiness lint, QA skill, env, review groups) go in the settings file's `## open-restaurant` section; see `setup`.

### better-code-review

Reviews the diff between `HEAD` and a fixed point you name, along three axes at once. Standards asks whether the code follows the repo's documented coding standards. Spec asks whether the code does what the originating issue or PRD asked for. Tests asks whether the tests in the diff are sound, and whether every behaviour the diff changes has a test that would catch it breaking. The three axes run as parallel sub-agents so none pollutes another's context. Before anything reaches you, the review checks each finding the way `epistemic-action` asks: it runs the project's scoped tests, lint and type-check, and proves each missing or tautological test with a probe, breaking the line in a throwaway worktree and watching whether any test turns red. Each finding says whether it was run, read or not verified. Then the findings render as a three-tab dark-theme HTML page that opens in your browser. With `--headless` it asks nothing, takes the merge base with the default branch when no fixed point is given, skips the Spec axis when no spec turns up and the Tests axis when there is nothing to test, and returns each finding as a plain-text block with its axis, kind, `file:line`, fix and whether it was verified, so another skill or agent can act on it. `recipe-relay` and the recipe's headless Tasting call it this way. With `--slack <link>` it reads the PR links in one Slack message, reviews each PR headless in a fresh clone it deletes afterwards, posts missing or partial requirements, scope creep, defects and hard violations as one GitHub review with inline comments, approves a PR with none of those, and posts a short English comment in the message's thread saying whether it approved or only commented. `better-code-review.reviewMode` decides whether it installs each clone's dependencies first: `fast`, the default, skips that and lists the checks it could not run as not verified; `slow` installs them.

Based on Matt Pocock's code-review skill.

### code-standards

The standards the Standards and Tests axes check against, as five files: `Common/Clean Code.md` for naming, size, structure and immutability in any language; `Typescript/Imports.md` and `Typescript/Exports.md` for how TypeScript reaches other modules and what it publishes; `Frontend/Accessibility.md` for anything that renders in a browser; `Testing/Tests.md` for how tests are written, tautological tests included. Each file is a list of rules and the failures they prevent, closing with the red flags to catch in review.

`better-code-review` reads the catalog as its baseline and only applies the files the diff can violate. The catalog defers to the project: a standard the repo documents itself always wins, and a breach is a hard violation only where the repo documents the same rule — otherwise it is a judgement call, like any smell. It is a reference rather than a workflow, so there is nothing here to run.

### feature-recipe

Takes a task from a rough idea to a merged PR, cooked in six named phases — Reading the Recipe, Mise en Place, Cooking, Tasting, Plating, Documentation — most defaulting to a fresh context and handing the next one its work through a **recipe card**, a markdown file at `./recipes/{task-slug}.md` in the project being worked on (Reading the Recipe and Cooking/Tasting continue straight through instead, without a session break). Reading the Recipe and Mise en Place are where you and the skill agree on what is being built and why; Reading the Recipe runs `grill-me` only when the work is complex or leaves something undefined, and skips it for simple, fully stated work; Cooking writes each test before the code that satisfies it and commits as it goes; Tasting is a hard gate that runs `better-code-review` plus the project's own scoped tests and lint before anything opens; Plating opens at most one PR per run and never stacks them unless a driver names a base branch; Documentation closes the task out.

It carries no opinion about which tracker, chat or docs tool a project uses — it speaks in outcomes and leans on whatever the session already has.

Phases 1 to 6 can also run **headless** — a night run. Start one with `--headless` at whatever step the card is on, even a bare task with no card yet, and it carries the work through Reading the Recipe, Mise en Place, Cooking, Tasting, Plating and Documentation in one turn, taking the recommendation at each checkpoint and recording it as `unattended:` so the morning can see what was decided while nobody was watching. It stops only at the end of the recipe or when something needs a person — never merely because a phase ended — and it never opens a non-draft PR, merges, or deletes work. The run's result goes on the card as `runStatus`, `runNext` and `runQuestion` in the frontmatter, so a driver reads a file at a known path instead of parsing prose — prose gets fenced, glued to a heading, or turned into a question. The contract is `skills/feature-recipe/references/headless.md`.

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

### week-summary

Writes a review of one week, one file per week: tickets closed, PRs merged and confirmed by their real merge date, reviews of other people's PRs counted by when you submitted them, one line per work-session note, and chat activity by theme. A Signal section reads across all four for patterns, gaps included, and a Summary block rolls up the counts, with sessions per day divided by working days, not calendar days. Your reflection headers and the last Weekly Update question stay yours to fill. It reads the notes `work-summary` writes, and skips any source the session has no tool for.

Needs the `gh` CLI for GitHub.

### ship-pr

Turns working-tree changes into pull requests. It finds every repo in the folder with changes, plans one Conventional Commit per stage with a body that gives context and trade-offs, fills the repo's own PR template from the diff and the ticket, and ticks a checklist box only when the diff proves it. A revert keeps the branch's own ticket key in the header and names the reverted ticket in the body. It commits from a message file, opens one PR per repo, never stacks PRs, and by default pauses for your approval before any push.

Needs the `gh` CLI. The commit header shape, the approval pause, draft PRs, the commands to run before each commit and the MCP server that reads tickets are settings; see `setup`.

### setup

Writes `.bosi-skills.md`, the settings file the other skills read: where `work-summary` saves notes and which values it tags against, where `week-summary` writes reviews and who it counts as you, where `feature-recipe` keeps recipe cards, which mode `feature-recipe` and `better-code-review` run in when the request names none, which tracker states and models `recipe-relay` uses, how `ship-pr` titles, gates and validates a PR, where `uml` keeps its sources and how it renders them, where `non-functional-requirements` writes its NFR docs, how `open-restaurant` maps sub-issues to repos, names its QA env, moves tracker states and picks its models, and where `pause-work` saves the task for tomorrow. A skill looks in the current folder first, then in `$HOME`, and each setting falls back on its own, so a project file only holds what it changes. With no file, every skill keeps its old behaviour. The contract is `skills/setup/references/config.md`.

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
  better-code-review/ SKILL.md + assets/report-template.html + scripts/
  feature-recipe/     SKILL.md + dependencies/ + phases/ + references/ + scripts/
  open-restaurant/    SKILL.md + scripts/
  recipe-relay/       SKILL.md + scripts/
  code-standards/     SKILL.md + Common/ + Frontend/ + Testing/ + Typescript/ + scripts/
  epistemic-action/   SKILL.md + bench/
  summarize-llm-response/  SKILL.md + evals/ (trigger + behaviour harnesses)
  work-summary/       SKILL.md + evals/ (scenarios)
  pause-work/         SKILL.md + evals/ (scenarios)
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
python3 skills/feature-recipe/scripts/check-pr-screenshots.py
python3 skills/recipe-relay/scripts/check-review-evidence.py
python3 skills/recipe-relay/scripts/check-split-cooking.py
python3 skills/recipe-relay/scripts/check-ui-review.py
python3 skills/open-restaurant/scripts/check-open-restaurant.py
python3 skills/code-standards/scripts/check-tooling-rule.py
python3 skills/setup/scripts/check-config.py
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
disappear, if the old `b972f03` phase-end footer creeps back, if Reading the
Recipe loses its grill-or-skip call, or if this README
stops describing the skills that exist. Offline, stdlib only — run it after
editing a phase file.

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
Tasting stops keeping the review's `Reviewed:` line and `Not verified:`
entries, runs the checks again on code the review already ran them on, or if
the rule against code comments loses its exception. Offline, stdlib only — run
it after editing Tasting or the skill's rules.

`check-goal-and-measure.py` is `feature-recipe`'s third check: it fails if the
recipe card loses `## Goal & measure` or moves it away from `## Problem`, if
Reading the Recipe stops grilling on how we will know it worked, stops writing
the three bullets, allows an invented metric, or drops the headless gap log, or
if Plating stops carrying the section into the PR. Offline, stdlib only — run
it after editing Reading the Recipe, Plating or the card template.

`check-pr-screenshots.py` is `feature-recipe`'s fourth check: it fails if
Plating stops attaching the run's screenshots with `gh pr edit --attach`,
drops their alt text or the way to place them in the description, retries
every upload after a partial failure, takes or invents screenshots of its own,
or asks about them in a night run. Offline, stdlib only — run it after editing
Plating.

`check-review-evidence.py` is `recipe-relay`'s own check: it fails if the
closing review pass stops sorting findings by `ran`, `read` or `no`, stops
or stops logging what the review left not verified. Offline, stdlib only — run it
after editing `recipe-relay`.

`check-no-pause.py` is `recipe-relay`'s no-pause check: it fails if the skill
pauses between units or posts a checkpoint to wait on, loses its stop
condition for open questions, or drops the closing headless
`better-code-review` pass. Offline, stdlib only — run it after editing
`recipe-relay`.

`check-split-cooking.py` is `recipe-relay`'s other check: it fails if Cooking
stops naming its interfaces first, starting a test writer and a code writer
per repo at the same time on the same branch and worktree, or keeping each
blind to the other's work; if it gives the writers worktrees of their own; or
if either skill drops its model setting. Offline, stdlib only — run it after
editing `recipe-relay` or step 4 of `better-code-review`.

`check-ui-review.py` is `recipe-relay`'s third check: it fails if the UI
review stops running beside the last Cooking unit, starts the app or takes its
own screenshots, loses the `screenshots.done` signal or its stale-signal rule,
guesses a design it was not given, or stops sending critical and major
findings back at most twice. Offline, stdlib only — run it after editing
`recipe-relay`.

`check-open-restaurant.py` is `open-restaurant`'s own check: it fails if a
section goes missing, if the readiness gate stops blocking on gaps, if the
contract may invent a shape, if same-repo sub-issues stop running one at a
time, if the early unblock loses its note file, follow-up or change rule, if
the integration branch may be pushed or a fix forced, if the QA limits or the
human review and merge gates go, if the skill names private content, if
Plating stops taking a named base branch, or if this README or the DeepSeek
Harness test stops listing the skill. Offline, stdlib only — run it after
editing `open-restaurant` or Plating.

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
