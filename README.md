# Bosi Programming Skills

Seven Claude Code skills, packaged as an installable plugin. Three do work on a diff. Two check the model's own writing or reasoning before it reaches you. One takes a task all the way to a merged pull request. One is the standards catalog the code review reads from.

## Install

```
/plugin marketplace add bosi-programming/skills
/plugin install bosi-programming-skills@bosi-programming
```

Then run `/reload-plugins` if the install summary asks for it.

Plugin skills are namespaced, so the commands are `/bosi-programming-skills:epistemic-action`, `/bosi-programming-skills:bosi-code-review`, and so on. Claude also loads them on its own when a description matches.

## The skills

### bosi-code-review

Reviews the diff between `HEAD` and a fixed point you name, along two axes at once. Standards asks whether the code follows the repo's documented coding standards. Spec asks whether the code does what the originating issue or PRD asked for. Both axes run as parallel sub-agents so neither pollutes the other's context, then the findings render side by side as a dark-theme HTML page that opens in your browser.

Based on Matt Pocock's code-review skill.

### code-standards

The standards the Standards axis checks against, as four files: `Common/Clean Code.md` for naming, size, structure and immutability in any language; `Typescript/Imports.md` and `Typescript/Exports.md` for how TypeScript reaches other modules and what it publishes; `Frontend/Accessibility.md` for anything that renders in a browser. Each file is a list of rules and the failures they prevent, closing with the red flags to catch in review.

`bosi-code-review` reads the catalog as its baseline and only applies the files the diff can violate. The catalog defers to the project: a standard the repo documents itself always wins, and a breach is a hard violation only where the repo documents the same rule — otherwise it is a judgement call, like any smell. It is a reference rather than a workflow, so there is nothing here to run.

### bosi-feature-recipe

Takes a task from a rough idea to a merged PR, cooked in six named phases — Reading the Recipe, Mise en Place, Cooking, Tasting, Plating, Documentation — each one meant to run in a fresh context and hand the next one its work through a **recipe card**, a markdown file at `./recipes/{task-slug}.md` in the project being worked on. Reading the Recipe and Mise en Place are where you and the skill agree on what is being built and why; Cooking writes each test before the code that satisfies it and commits as it goes; Tasting is a hard gate that runs `bosi-code-review` plus the project's own scoped tests and lint before anything opens; Plating opens at most one PR per run and never stacks them; Documentation closes the task out.

It carries no opinion about which tracker, chat or docs tool a project uses — it speaks in outcomes and leans on whatever the session already has.

Phases 3 to 6 can also run **headless** — a night run. Start one with `--headless` at whatever step the card is on, and it carries the work through Cooking, Tasting, Plating and Documentation in one turn, taking the recommendation at each checkpoint and recording it as `unattended:` so the morning can see what was decided while nobody was watching. It stops only at the end of the recipe or when something needs a person — never merely because a phase ended — and it never opens a non-draft PR, merges, or deletes work. The run's result goes on the card as `runStatus`, `runNext` and `runQuestion` in the frontmatter, so a driver reads a file at a known path instead of parsing prose — prose gets fenced, glued to a heading, or turned into a question. The contract is `skills/bosi-feature-recipe/references/headless.md`.

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
.claude-plugin/
  marketplace.json    marketplace catalog, one entry pointing at the repo root
  plugin.json         plugin manifest
skills/
  bosi-code-review/   SKILL.md + assets/report-template.html
  bosi-feature-recipe/  SKILL.md + phases/ + references/ + scripts/
  code-standards/     SKILL.md + Common/ + Frontend/ + Typescript/
  code-visualizer/    SKILL.md + scripts/render_graph.py + references/
  docs-visualizer/    SKILL.md + scripts/render_docs_graph.py + references/
  epistemic-action/   SKILL.md
  summarize-llm-response/  SKILL.md + evals/ (trigger + behaviour harnesses)
```

Skills reference their own bundled files through `${CLAUDE_SKILL_DIR}`, so the paths resolve whether the skill is installed personally, in a project, or as part of this plugin.

## Validate a change

```
claude plugin validate .
claude plugin validate skills
python3 skills/bosi-feature-recipe/scripts/check-headless-contract.py
```

The last one is `bosi-feature-recipe`'s own check: it fails if a phase stops
speaking the headless dialect, if the interactive endings disappear, if the old
`b972f03` phase-end footer creeps back, or if this README stops describing the
skills that exist. Offline, stdlib only — run it after editing a phase file.

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
