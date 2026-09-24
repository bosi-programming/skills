# Bosi Programming Skills

Nine Claude Code skills, packaged as an installable plugin. Three do work on a diff. Two check the model's own writing or reasoning before it reaches you. One takes a task all the way to a merged pull request. One runs that one hands-off, phase by phase, through sub-agents, and one runs it through agent terminals on the Maestri canvas. One is the standards catalog the code review reads from.

The same nine install into Codex, DeepSeek Harness, Pi and opencode, from the same `skills/` directory. One plugin source, five harnesses, nothing copied — so a skill cannot drift between harnesses. The one exception is opencode, which fetches a skill list over HTTP: `skills/index.json` is generated from that same tree and kept honest by `opencode/build-index.py --check`.

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

### better-code-review

Reviews the diff between `HEAD` and a fixed point you name, along three axes at once. Standards asks whether the code follows the repo's documented coding standards. Spec asks whether the code does what the originating issue or PRD asked for. Tests asks whether the tests in the diff are sound, and whether every behaviour the diff changes has a test that would catch it breaking. The three axes run as parallel sub-agents so none pollutes another's context. Before anything reaches you, the review checks each finding the way `epistemic-action` asks: it runs the project's scoped tests, lint and type-check, and proves each missing or tautological test with a probe, breaking the line in a throwaway worktree and watching whether any test turns red. Each finding says whether it was run, read or not verified. Then the findings render as a three-tab dark-theme HTML page that opens in your browser. With `--headless` it asks nothing, takes the merge base with the default branch when no fixed point is given, skips the Spec axis when no spec turns up and the Tests axis when there is nothing to test, and returns each finding as a plain-text block with its axis, kind, `file:line`, fix and whether it was verified, so another skill or agent can act on it. `recipe-relay` and the recipe's headless Tasting call it this way.

Based on Matt Pocock's code-review skill.

### code-standards

The standards the Standards and Tests axes check against, as five files: `Common/Clean Code.md` for naming, size, structure and immutability in any language; `Typescript/Imports.md` and `Typescript/Exports.md` for how TypeScript reaches other modules and what it publishes; `Frontend/Accessibility.md` for anything that renders in a browser; `Testing/Tests.md` for how tests are written, tautological tests included. Each file is a list of rules and the failures they prevent, closing with the red flags to catch in review.

`better-code-review` reads the catalog as its baseline and only applies the files the diff can violate. The catalog defers to the project: a standard the repo documents itself always wins, and a breach is a hard violation only where the repo documents the same rule — otherwise it is a judgement call, like any smell. It is a reference rather than a workflow, so there is nothing here to run.

### feature-recipe

Takes a task from a rough idea to a merged PR, cooked in six named phases — Reading the Recipe, Mise en Place, Cooking, Tasting, Plating, Documentation — most defaulting to a fresh context and handing the next one its work through a **recipe card**, a markdown file at `./recipes/{task-slug}.md` in the project being worked on (Reading the Recipe and Cooking/Tasting continue straight through instead, without a session break). Reading the Recipe and Mise en Place are where you and the skill agree on what is being built and why; Reading the Recipe runs `grill-me` only when the work is complex or leaves something undefined, and skips it for simple, fully stated work; Cooking writes each test before the code that satisfies it and commits as it goes; Tasting is a hard gate that runs `better-code-review` plus the project's own scoped tests and lint before anything opens; Plating opens at most one PR per run and never stacks them; Documentation closes the task out.

It carries no opinion about which tracker, chat or docs tool a project uses — it speaks in outcomes and leans on whatever the session already has.

Phases 1 to 6 can also run **headless** — a night run. Start one with `--headless` at whatever step the card is on, even a bare task with no card yet, and it carries the work through Reading the Recipe, Mise en Place, Cooking, Tasting, Plating and Documentation in one turn, taking the recommendation at each checkpoint and recording it as `unattended:` so the morning can see what was decided while nobody was watching. It stops only at the end of the recipe or when something needs a person — never merely because a phase ended — and it never opens a non-draft PR, merges, or deletes work. The run's result goes on the card as `runStatus`, `runNext` and `runQuestion` in the frontmatter, so a driver reads a file at a known path instead of parsing prose — prose gets fenced, glued to a heading, or turned into a question. The contract is `skills/feature-recipe/references/headless.md`.

### recipe-relay

Runs `feature-recipe` from a live session, without touching any of its files. Each phase (or phase-pair, for Cooking/Tasting) runs in its own sub-agent that auto-takes every checkpoint's own stated recommendation — the same content decisions a headless run would take, logged `relay:` instead of `unattended:` since a person is actually running it. The session moves from one unit to the next without pausing, posting one line per unit, and only stops at the end of the recipe or at its own one-way doors — the same contract as headless, just supervised instead of unattended. Once the recipe finishes, a sub-agent runs `better-code-review` headless against the branch, and the session fixes what it finds, test first, and reports which findings it fixed and which it rejected.

### maestri-workflow

Runs `recipe-relay` from the Maestri canvas for any ticket — a tracker key, a link or a plain description. Where recipe-relay spawns a sub-agent, this recruits a fresh agent terminal named for its work, on whichever harness the canvas has a preset for: one model for the planning phases, another for the code phases. Every recruit shares one note where it logs the questions and problems it could not settle. The run never stops to ask: where recipe-relay would pause, the orchestrator takes the stated recommendation and logs it to the note, and it never merges, promotes the draft or deletes work. It ends with a draft PR, after recipe-relay's closing review runs in a last recruit and the orchestrator fixes what it finds, and a report of every call it made alone and every one-way door it left in the PR body.

Needs Maestri and its `maestri` CLI.

### code-visualizer

Turns a diff or pull request into an interactive web page that maps what changed and how the changed pieces relate. The page answers the questions a reviewer asks before reading a line: where to start, what to ask the author, which changed file ships with no test, what breaks for callers, how busy each file is and whose it is, and which design patterns the change uses or breaks. Every claim carries a `file:line` you can click through to the hunk itself, and a red mark on a box means nothing asserts what it now does. It writes a `model.json` first, so you can correct the model cheaply, then renders. Accepts a PR URL or number, a git ref range, a `.diff`/`.patch` file, or the working tree.

Needs `python3`. The renderer uses the standard library only.

### docs-visualizer

The same idea, aimed at prose. Turns a documentation diff into an interactive page that maps which docs and sections changed, how they link to each other, which writing patterns and anti-patterns the rewrite uses, and what the text actually claims. The side panel holds the writing patterns; the strip under the graph holds the rhetorical moves, so a claim with no evidence under it is visible at a glance. It counts words rather than lines, because a reflowed paragraph makes line counts lie.

Handles `.md` and `.mdx` fully, and `.txt`, `.rst` and `.adoc` with sectioning derived from blank-line blocks.

Needs `python3`. The renderer uses the standard library only.

### summarize-llm-response

The shape of anything a human is going to read: findings as bullets with the evidence inline, action items as a checklist, a TL;DR only when there are enough findings to need one, and the attribution tag each destination expects. It carries a skip list — yes/no answers, commit messages, code-only replies — because it is meant to be wired to a blanket "run this before any communication" rule, and a blanket rule hands it work it has nothing to say about.

It does not self-trigger. Measured on Sonnet, a description alone fires it on 0-21% of the prompts it is written for; the same skill behind a CLAUDE.md line naming it fires on 93%. Wire it to a rule or call it by name. See `skills/summarize-llm-response/evals/`.

### epistemic-action

Go find out instead of predicting: read the file, run the command, probe the thing. Use it whenever you catch yourself writing "should", "probably", or "typically" about a codebase you have not opened.

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
  maestri-workflow/   SKILL.md + scripts/
  recipe-relay/       SKILL.md
  code-standards/     SKILL.md + Common/ + Frontend/ + Typescript/
  code-visualizer/    SKILL.md + scripts/render_graph.py + references/
  docs-visualizer/    SKILL.md + scripts/render_docs_graph.py + references/
  epistemic-action/   SKILL.md
  summarize-llm-response/  SKILL.md + evals/ (trigger + behaviour harnesses)
```

Skills reference their own bundled files by path relative to their `SKILL.md` — `./references/patterns.md`, `../code-standards/SKILL.md` — so the paths resolve whether the skill is installed personally, in a project, or as part of this plugin, and under any agent runtime. See `AGENTS.md`.

## Validate a change

```
claude plugin validate --strict .
node --test 'dsh/**/*.test.mjs'
python3 skills/feature-recipe/scripts/check-headless-contract.py
python3 opencode/build-index.py --check
python3 skills/maestri-workflow/scripts/check-no-wait.py
python3 skills/better-code-review/scripts/check-headless.py
python3 skills/better-code-review/scripts/check-tests-axis.py
python3 skills/better-code-review/scripts/check-evidence.py
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

`check-no-wait.py` is `maestri-workflow`'s own check: it fails if the skill
tells the orchestrator to stop, ask or wait for the user before the end, if a
replacement for an old stop leaves the section it belongs in, if
`recipe-relay` pauses between units, loses its stop conditions or its closing
`better-code-review` pass, if `maestri-workflow` briefs a review of its own, or if
a relative path in the skill does not resolve. Offline, stdlib only — run it
after editing `maestri-workflow`.

`check-headless.py` is `better-code-review`'s own check: it fails if the
`## Headless` section loses its entry, a default for a step that would ask,
the text format of a finding or its closing lines, if steps 1, 2 or 6 stop
pointing to it, or if a relative path in the skill does not resolve. Offline,
stdlib only — run it after editing `better-code-review`.

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
