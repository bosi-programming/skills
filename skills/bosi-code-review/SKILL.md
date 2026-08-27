---
name: bosi-code-review
description: Review the changes since a fixed point (commit, branch, tag, or merge-base) along two axes — Standards (does the code follow this repo's documented coding standards?) and Spec (does the code match what the originating issue/PRD asked for?). Runs both reviews in parallel sub-agents and renders them side by side as a dark-theme HTML page opened in the browser. Use when the user wants to review a branch, a PR, work-in-progress changes, or asks to "review since X".
---

Two-axis review of the diff between `HEAD` and a fixed point the user supplies:

- **Standards** — does the code conform to this repo's documented coding standards?
- **Spec** — does the code faithfully implement the originating issue / PRD / spec?

Both axes run as **parallel sub-agents** so they don't pollute each other's context, then this skill aggregates their findings and renders them as a single dark-theme HTML page it opens in the browser.

## Process

### 1. Pin the fixed point

Whatever the user said is the fixed point — a commit SHA, branch name, tag, `main`, `HEAD~5`, etc. If they didn't specify one, ask for it.

Capture the diff command once: `git diff <fixed-point>...HEAD` (three-dot, so the comparison is against the merge-base). Also note the list of commits via `git log <fixed-point>..HEAD --oneline`.

Before going further, confirm the fixed point resolves (`git rev-parse <fixed-point>`) and the diff is non-empty. A bad ref or empty diff should fail here — not inside two parallel sub-agents.

### 2. Identify the spec source

Look for the originating spec, in this order:

1. Issue references in the commit messages or branch name — Linear keys (`TICK-000`, `TICK-000`) fetched with the Linear MCP `get_issue`; GitHub issues and PRs (`#123`, `Closes #45`) fetched with `gh issue view` / `gh pr view`.
2. A path the user passed as an argument.
3. A PRD/spec file under `docs/`, `specs/`, or `.scratch/` matching the branch name or feature.
4. If nothing is found, ask the user where the spec is. If they say there isn't one, the **Spec** sub-agent will skip and report "no spec available".

### 3. Identify the standards sources

Anything in the repo that documents how code should be written, such as `CODING_STANDARDS.md` or `CONTRIBUTING.md`.

On top of whatever the repo documents, the Standards axis always carries the **smell baseline** below — a fixed set of Fowler code smells (_Refactoring_, ch.3) that applies even when a repo documents nothing. Two rules bind it:

- **The repo overrides.** A documented repo standard always wins; where it endorses something the baseline would flag, suppress the smell.
- **Always a judgement call.** Each smell is a labelled heuristic ("possible Feature Envy"), never a hard violation — and, like any standard here, skip anything tooling already enforces.

Each smell reads *what it is* → *how to fix*; match it against the diff:

- **Mysterious Name** — a function, variable, or type whose name doesn't reveal what it does or holds. → rename it; if no honest name comes, the design's murky.
- **Duplicated Code** — the same logic shape appears in more than one hunk or file in the change. → extract the shared shape, call it from both.
- **Feature Envy** — a method that reaches into another object's data more than its own. → move the method onto the data it envies.
- **Data Clumps** — the same few fields or params keep travelling together (a type wanting to be born). → bundle them into one type, pass that.
- **Primitive Obsession** — a primitive or string standing in for a domain concept that deserves its own type. → give the concept its own small type.
- **Repeated Switches** — the same `switch`/`if`-cascade on the same type recurs across the change. → replace with polymorphism, or one map both sites share.
- **Shotgun Surgery** — one logical change forces scattered edits across many files in the diff. → gather what changes together into one module.
- **Divergent Change** — one file or module is edited for several unrelated reasons. → split so each module changes for one reason.
- **Speculative Generality** — abstraction, parameters, or hooks added for needs the spec doesn't have. → delete it; inline back until a real need shows.
- **Message Chains** — long `a.b().c().d()` navigation the caller shouldn't depend on. → hide the walk behind one method on the first object.
- **Middle Man** — a class or function that mostly just delegates onward. → cut it, call the real target direct.
- **Refused Bequest** — a subclass or implementer that ignores or overrides most of what it inherits. → drop the inheritance, use composition.

### 4. Spawn both sub-agents in parallel

**Standards sub-agent prompt** — include:

- The full diff command and commit list.
- The list of standards-source files you found in step 3, **plus the smell baseline from step 3** pasted in full — the sub-agent has no other access to it.
- The brief: "Report — per file/hunk where relevant — (a) every place the diff violates a documented standard: cite the standard (file + the rule); and (b) any baseline smell you spot: name it and quote the hunk. Distinguish hard violations from judgement calls — documented-standard breaches can be hard, but baseline smells are always judgement calls, and a documented repo standard overrides the baseline. Skip anything tooling enforces. Under 400 words."

**Spec sub-agent prompt** — include:

- The diff command and commit list.
- The path or fetched contents of the spec.
- The brief: "Report: (a) requirements the spec asked for that are missing or partial; (b) behaviour in the diff that wasn't asked for (scope creep); (c) requirements that look implemented but where the implementation looks wrong. Quote the spec line for each finding. Under 400 words."

If the spec is missing, skip the Spec sub-agent and note this in the final report.

### 5. Aggregate

Hold the two reports under a `Standards` and a `Spec` heading, verbatim or lightly cleaned. Do **not** merge or rerank findings — the two axes are deliberately separate (see _Why two axes_).

Add a one-line summary: total findings per axis, and the worst issue _within each axis_ (if any). Don't pick a single winner across axes — that's the reranking the separation exists to prevent.

Stop here. The aggregate is a draft, not the report. It goes through the gate in step 6 before anything is written to disk.

### 6. Gate the aggregate through `objectum`

The aggregate is a draft. It does not become a file until it passes the gate.

Run the `objectum` skill on it at **Full** depth, six passes. This is a review the user will act on, so Sweep never applies.

What the gate is looking for here, specifically:

- Every finding a sub-agent handed you is IMAGINED until you open the file at that line yourself. Unveil each one, cut it, or mark it unverified on the page. Sub-agents cite lines that don't exist.
- Every quoted standard is IMAGINED until you grep it in its own file and read the surrounding rule. A rule quoted from memory is a rule invented.
- Every acceptance criterion marked met is IMAGINED until you read the code that meets it. "The PR body says so" is not unveiling.
- The affect gap: the scoreboard pills and the severity colours claim more certainty than prose does. A `hard` pill on a finding you inferred rather than read is an overclaim the page ships as fact.
- The borrowed pattern: a smell name applied because the shape looked familiar, not because you read this code.

Then run the fix loop. Rewrite the aggregate, re-run passes 4 and 5 on the rewrite. Stop after the second rewrite.

Gate verdicts, mapped to this skill:

- **SHIP** or **FIX THEN SHIP**: render the corrected aggregate.
- **CANNOT SHIP**: still render, but the residual goes in the footer's `Not run` line, in plain words: what you could not verify and what would verify it. Never render an unverified claim as a plain finding.

The user gets the page, never the audit. Don't narrate the passes, don't list the pulls, don't announce that you ran the gate.

### 7. Render the HTML report

The final deliverable is a web page, not a chat dump.

Build it from `assets/report-template.html`, which carries the whole dark-theme stylesheet plus a commented skeleton for every block: header, scoreboard, Standards, Spec, cross-axis note, worst-per-axis, footer.

- Copy the template, replace every `{{PLACEHOLDER}}` with real content, delete the blocks and groups you have no findings for, and repeat the `li.f` / `.ac` / `.commit` items as many times as you have findings.
- **Dark theme only.** Keep the `:root` palette as-is. No light mode, no `prefers-color-scheme`, no theme toggle.
- Keep the CSS inline in the one file. The page must render offline, from `file://`, with no network and no build step.
- No `<table>`. Use the template's `.acs` grid, `.findings` list, and `.commits` grid instead.
- Severity classes carry the meaning: `hard` (red) for documented-standard breaches and defects, `warn` (amber) for tensions and partials, `soft` (purple) for smell-baseline judgement calls, `ok` (green) for satisfied criteria.
- Escape `<`, `>`, and `&` inside every code snippet you quote, or the page breaks.
- Inline SVG only for icons, as in the template. No image files, no icon fonts, no CDN.

Write the page to the session scratchpad directory as `review-<pr-number-or-ref>.html`. If no scratchpad directory was given, use `.scratch/` in the repo root.

Then open it: `open <path>` on macOS.

Reply to the user with the `file://` URL, the per-axis tallies, and nothing else. The detail lives on the page.

## Why two axes

A change can pass one axis and fail the other:

- Code that follows every standard but implements the wrong thing → **Standards pass, Spec fail.**
- Code that does exactly what the issue asked but breaks the project's conventions → **Spec pass, Standards fail.**

Reporting them separately stops one axis from masking the other.
