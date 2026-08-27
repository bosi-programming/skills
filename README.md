# Bosi Programming Skills

Six Claude Code skills, packaged as an installable plugin. Three do work on a diff. Three check the model's own writing before it reaches you.

## Install

```
/plugin marketplace add bosi-programming/skills
/plugin install bosi-programming-skills@bosi-programming
```

Then run `/reload-plugins` if the install summary asks for it.

Plugin skills are namespaced, so the commands are `/bosi-programming-skills:objectum`, `/bosi-programming-skills:bosi-code-review`, and so on. Claude also loads them on its own when a description matches.

## The skills

### bosi-code-review

Reviews the diff between `HEAD` and a fixed point you name, along two axes at once. Standards asks whether the code follows the repo's documented coding standards. Spec asks whether the code does what the originating issue or PRD asked for. Both axes run as parallel sub-agents so neither pollutes the other's context, then the findings render side by side as a dark-theme HTML page that opens in your browser.

Based on Matt Pocock's code-review skill.

### code-visualizer

Turns a diff or pull request into an interactive web page that maps what changed, how the changed pieces relate, and which design patterns the change uses or breaks. Pattern cards collapse to a name, carry a link to what the pattern is, and list evidence refs you can click through to the hunk itself. It writes a `model.json` first, so you can correct the model cheaply, then renders. Accepts a PR URL or number, a git ref range, a `.diff`/`.patch` file, or the working tree.

Needs `python3`. The renderer uses the standard library only.

### docs-visualizer

The same idea, aimed at prose. Turns a documentation diff into an interactive page that maps which docs and sections changed, how they link to each other, which writing patterns and anti-patterns the rewrite uses, and what the text actually claims. The side panel holds the writing patterns; the strip under the graph holds the rhetorical moves, so a claim with no evidence under it is visible at a glance. It counts words rather than lines, because a reflowed paragraph makes line counts lie.

Handles `.md` and `.mdx` fully, and `.txt`, `.rst` and `.adoc` with sectioning derived from blank-line blocks.

Needs `python3`. The renderer uses the standard library only.

### objectum

A gate the model runs on its own draft before emitting anything. It holds the draft as an object, names the pulls that wrote it, converts each pull into a claim that could be proven false, marks every claim as verified or imagined, and either verifies, cuts, or flags the imagined ones. You get the corrected draft, never the audit.

### un-ai

Strips the tells that give machine writing away: the puffery, the fancy ways of saying "is", the rule of three, the em dash every other line. The two visualizers call it on every sentence they put into a page, so the prose on a graph reads like a person wrote it. You can also point it at any text of your own.

### epistemic-action

The companion to `objectum`. Where `objectum` finds an unverified claim, this one says go find out: read the file, run the command, probe the thing. Use it whenever you catch yourself writing "should", "probably", or "typically" about a codebase you have not opened.

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
  objectum/           SKILL.md
  un-ai/              SKILL.md
```

Skills reference their own bundled files through `${CLAUDE_SKILL_DIR}`, so the paths resolve whether the skill is installed personally, in a project, or as part of this plugin.

## Validate a change

```
claude plugin validate .
claude plugin validate skills
```

## License

MIT. See `LICENSE`.
