# Bosi Programming Skills

Five Claude Code skills, packaged as an installable plugin. Three do work on a diff. Two check the model's own writing or reasoning before it reaches you.

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
```

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
