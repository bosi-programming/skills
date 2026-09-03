---
name: bosi-code-review
description: Review the changes since a fixed point (commit, branch, tag, or merge-base) along two axes — Standards (does the code follow this repo's documented coding standards?) and Spec (does the code match what the originating issue/PRD asked for?). Runs both reviews in parallel sub-agents and renders them as a two-tab dark-theme HTML page opened in the browser. Use when the user wants to review a branch, a PR, work-in-progress changes, or asks to "review since X".
metadata:
  based-on: "Matt Pocock's code-review skill"
  adapted-by: Felipe Bosi
---

Two-axis review of the diff between `HEAD` and a fixed point the user supplies:

- **Standards** — does the code conform to this repo's documented coding standards? Standards sources are located in step 3 (`CODING_STANDARDS.md`, `CONTRIBUTING.md`, or whatever the repo documents).
- **Spec** — does the code faithfully implement the originating issue / PRD / spec? The specs can be found inside the PR description as a link to an issue tracker. If not found there, search on the PR title for a string that is CCCC*-DDD* where c is a character and d is a digit, like ABC-123.

Both axes run as **parallel sub-agents** so they don't pollute each other's context, then this skill aggregates their findings and renders them as a single dark-theme HTML page it opens in the browser. The page keeps the axes in **two tabs**, Spec first, so a reader lands on one axis at a time instead of scanning both at once.

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

Add a one-line summary: total findings per axis. Don't pick a single winner across axes — that's the reranking the separation exists to prevent. The severity ordering on the page carries the rest; the page has no worst-per-axis section, because a summary of a page that already sorts worst-first only repeats its own first card.

Before the aggregate becomes a file, verify it yourself: open every file at the line a finding cites, grep every quoted standard in its own file, and read the code behind every acceptance criterion marked met. A finding you have not read at its source is a claim, not a finding — cut it or fix the citation before it reaches the page.

### 6. Render the HTML report

If the user asked for visualization or verbose, run this section. If not, ignore and print the result on the conversation instead.

The final deliverable is a web page, not a chat dump.

Build it from `${CLAUDE_SKILL_DIR}/assets/report-template.html`, which carries the whole dark-theme stylesheet, the tab machinery, and a commented skeleton for every block: header, scoreboard, tabs, Spec panel, Standards panel, cross-axis note, `Not verified`.

- Copy the template, replace every `{{PLACEHOLDER}}` with real content, delete the blocks and groups you have no findings for, and repeat the `li.f` / `.ac` / `.commit` items as many times as you have findings.
- **Dark theme only.** Keep the `:root` palette as-is. No light mode, no `prefers-color-scheme`, no theme toggle.
- Keep the CSS and the script inline in the one file. The page must render offline, from `file://`, with no network and no build step.
- No `<table>`. Use the template's `.acs` grid, `.findings` list, and `.commits` grid instead.
- Severity classes carry the meaning: `hard` (red) for documented-standard breaches and defects, `warn` (amber) for tensions and partials, `soft` (purple) for smell-baseline judgement calls, `ok` (green) for satisfied criteria.

**Order the groups by severity, worst first.** Red at the top, amber in the middle, purple at the bottom, in both tabs. A reader opening a tab should hit the bad news before anything else.

Spec tab, in order: `Implementation defects` (red), `Partial` (amber), `Acceptance criteria · N of N met`, `Scope`, `Notes` (purple).

Both problem groups sit **above** the criteria list on purpose. Someone opening this tab wants what broke and what fell short before the list of what passed, and a green `7 of 7` at the top buries everything underneath it. The criteria are the receipt, not the headline: they answer "did you actually check" once the reader already knows the verdict.

Standards tab, in order: `Hard violations` (red), `Flagged, not condemned` (amber), `Judgement calls · smell baseline` (purple).

Drop any group with nothing in it rather than shipping an empty heading.

Each group title is an `h2` in 24px bold, carrying 40px of padding above and 20px below, with no rule after it. At 24px the title separates the sections on its own, which is why the hairline that used to trail it is gone.

**That 40px is the page's only vertical separator, so nothing may stack on top of it.** `.group`, `section` and `.panels > section` all carry `margin-bottom:0`, and `.tabs` has no bottom margin either. Leave one of those in and the gap above a heading silently becomes 70 or 90px, which is how the tabs ended up a screen away from the first finding. The one exception is `#cross`, which has no `h2` of its own: it carries `padding-top:40px` to earn the same gap.

**Every finding card collapses.** Each `li.f` wraps its body in `<details>` with the title as `<summary class="t">`. Native `<details>`, no JavaScript, so folding still works when the script is blocked.

- **Every card ships shut**, red included. The page is a list of titles you skim, then open what you want. One card left open pulls the eye to itself and buries whatever sits under it, which is the same reason the criteria fold.
- That puts the weight on the summary line. A title has to say what is wrong on its own, because for most readers it is the only part they read. `An empty partner override now blanks the sentence, and one partner already ships one` works shut. `Empty string handling` does not.
- The `.ac` criteria cards fold too, and every one of them ships shut. Their summary is the mark plus the label, `AC4 · partner override wins`, which is the whole verdict. Seven collapsed criteria read as a checklist at a glance; seven expanded ones push the defect above them off the screen.
- **One criterion per row**, `.acs` at a single column. The labels run to different lengths, so side by side they make a ragged block that has to be read in two directions at once. Stacked, the marks line up down the left edge and a failing criterion is visible without reading a word.
- Give every criterion a short name after its number in the summary. `AC4` on its own makes a reader open the card to find out which criterion it is, which defeats folding it.
- The evidence and the `file:line` go in the folded `.body`, never in the summary.
- Nothing on the page is exempt. Every finding card and every criterion folds, and every one ships shut.
- Everything after `<summary>` is the folded body: the `.d` blocks and the `.rule` line. Nothing that earns a finding, no file:line and no quoted rule, belongs in the summary where it would be read as the whole story.

**The page ends with a `Not verified` section.** Whatever the verification pass in step 5 could not unveil goes there, below the cross-axis note, outside both tabs, because it applies to the whole review.

- One collapsible card per gap, shut like every other card, with a **single-line title that names the gap on its own**: `No test suite, type-check or lint was run against this branch`. A reader who never opens the card should still know what is missing.
- Two kinds belong here. A claim you could not verify, and a check you did not run. Both are `warn`, not `soft`, because either can change what a finding means.
- Every card ends with **What would settle it**, naming the action: the file to read, the command to run, the person to ask. An unverified claim with no route to verifying it is a shrug, and it will sit on the page forever.
- Where a gap sits under a specific finding, say which one. The reader deciding whether to act on that finding is the person who needs this.
- Delete the section only when there is genuinely nothing unverified and nothing unrun. That is rare enough to be worth doubting: a review that ran no tests has at least one card.

**Every Spec card opens with "How this affects the final user".** It is the first section inside `<details>`, `<h4 class="user">`, before any code. Nothing else goes above it.

Write it about a person at a keyboard, not about the code. Who sees this, on which screen, and what do they read instead of what they should read? Name the partner if a config puts a name on it. The Spec axis exists to ask whether the change did what someone asked for, and the answer is worthless in terms of call stacks.

- **When the answer is "nobody, today", say that in the first sentence** and then say what it costs later. "Nothing, today. Every screen shows the same words. The bill comes due when someone edits one of the two copies." An honest no-impact beats an invented one, and it tells the reader which findings they can leave alone.
- Ground it the same way as any other claim. If you say staff at a named credit union see a blank paragraph, a config in the repo has to put it there. If no config does, say the impact is hypothetical and say so in that section, not in a footnote.
- Don't hedge it into nothing. "This could potentially affect some users" is not an impact statement, it is a refusal to write one.

**After that section, one `<h4>` per section, prose below it, a blank line between sections.** Sentence case, not title case. Name what the section does rather than labelling it: `What happened before`, `What happens now`, `A config already does this`, `The fix`, `Why the branch cannot run`, `Why it is amber and not red`. Two sections is fine, six is fine. Use the number the finding needs.

Every heading renders identically, `.user` included. Keep the class on the first one, since it marks the section that has to be there, but don't add styling to set it apart. Its position does that already, and a heading in its own colour reads as the only part worth reading.

This structure is for the **Spec** tab. Standards cards keep their `.d` blocks and their bold lead-ins, because a standards finding is about the code and has no user on the other end of it.
- Escape `<`, `>`, and `&` inside every code snippet you quote, or the page breaks.
- Inline SVG only for icons, as in the template. No image files, no icon fonts, no CDN.

**The two tabs.** The template ships them wired. Fill them and leave the wiring alone.

- **Spec is tab one and opens by default.** It is the axis the reader came for. Standards is tab two.
- Only the two axis `<section>`s go inside `.panels`. The header, the scoreboard and the cross-axis note stay outside, visible from both tabs, because they span the axes.
- Put each axis's tally in its own `.tab-count` as well as its scoreboard card, so both scores read without a click.
- Never delete a tab. An axis with no findings keeps its tab and says so inside, the way the scoreboard card does. Two tabs always, or the page stops being a two-axis review and nobody notices.
- Leave `role="tablist"`, `role="tabpanel"`, `aria-selected` and `aria-controls` as they are, keep the arrow-key handler, and keep the `<noscript>` block that reveals both panels. The page has to work with the script blocked.
- **No heading inside a panel.** No axis title, no icon, no source note. The tab label already says which axis this is, and repeating it costs a screen of height on a page whose whole point is that the first finding is visible. The panel starts at its first group.
- The provenance those notes carried does not move somewhere else on the page. The page is findings; it does not narrate how it was made. Which standards documents you read, and what tooling you skipped, go in your reply if they change what the reader should do. What you could **not** check is different, and it has its own section below.

Write the page to the session scratchpad directory as `review-<slug>.html`. If no scratchpad directory was given, use `.scratch/` in the repo root.

Two things to do before the first byte, both of which have failed a run:

- **Build `<slug>` from the PR number or ref by replacing every character outside `[A-Za-z0-9._-]` with a dash.** A branch called `feature/foo` otherwise makes the path `review-feature/foo.html`, and the write fails because `review-feature/` does not exist. The slug is also what the companion page is named after, so a bad one loses both files.
- **`mkdir -p` the directory.** A fresh worktree has no `.scratch/`, so the fallback path writes into a directory that is not there and the whole review ends with no report.

### 7. Build the companion code page and link every reference

A finding that cites `foo.ts:49-53` and makes the reader go find `foo.ts:49-53` has done half its job. **Every `file:line` on the report is a link**, and it lands on an excerpt of that exact code.

Build it from `${CLAUDE_SKILL_DIR}/assets/refs-template.html`, writing it beside the report as `review-<slug>-refs.html`, the same slug the report used, one excerpt per distinct reference, each with an `id` the report links to. Paste the report's stylesheet into it first, so the two pages match.

Do not hand this to GitHub's line anchors instead. A blob link at least shows the file, but a PR diff anchor collapses unchanged regions, so a reference to an untouched line inside a changed file lands on a "expand" control and the reader sees nothing. Every excerpt on your own page is guaranteed to render.

**Each excerpt carries at least three lines above and three below the range the finding names.** The finding is about code in context, and one line on its own is quotable in a way that misleads. Two rules on top:

- **Mark what the PR changed.** Lines the diff added get a `+` and their own background, so a reader can see at a glance whether the finding is about new code or about code the change merely leans on. Get the added line numbers from `git diff <fixed-point>...HEAD --unified=0`, numbered against `HEAD`.
- **Say when the file runs out.** A range near the top or bottom of a file cannot have three lines on that side. Print that in the excerpt header, in words: `short of three lines, end of file`. Silently showing two is how a page starts lying about its own rule.

Read every excerpt from the worktree at the reviewed commit, not from the diff hunks, so the line numbers on the page are the line numbers in the file.

Give each excerpt a link out to the same lines on GitHub, pinned to the head SHA. That is the version someone can paste into a comment.

**A reference you cannot resolve stays unlinked, and the companion page says why.** Cross-repo citations are the usual case: a path in another repository with no checkout has no code to quote. Do not guess at it, do not link it to a path that might exist, and do not quietly drop the reference from the prose. Name the file at the bottom of the companion page and say what is missing.

Then open the report with the platform's opener, so the page lands in a browser rather than in a sentence telling the user to open it themselves.

In a POSIX shell, macOS then Linux:

```bash
open "$REPORT" 2>/dev/null || xdg-open "$REPORT" 2>/dev/null || printf 'file://%s\n' "$REPORT"
```

`start` does not belong in that chain. It is a `cmd.exe` builtin, so on Windows the shell never expands `$REPORT` and `2>/dev/null` is not a redirect it understands. Windows gets its own line:

```bat
start "" "%REPORT%"
```

Pick the one for the platform you are on rather than running both. **If the opener you tried did not report success, print the `file://` URL and say the page is written but not opened.** A silent failure here is how a review ends with the user believing there was no page.

Reply to the user with the `file://` URL and the per-axis tallies. The detail lives on the page, so nothing else belongs in the reply except the two cases where the reader would otherwise act on a page that cannot tell them:

- **Anything left unverified from step 5.** Name each gap in one line, the same wording as its `Not verified` card. The reader deciding whether to act on a finding needs to know a claim behind it went unverified, and a section they may never scroll to does not tell them.
- **Provenance that changes what they should do**, from the note in step 6: which standards documents you read, and what tooling you skipped.

Nothing else. No summary of the findings, no worst-per-axis.

## Why two axes

A change can pass one axis and fail the other:

- Code that follows every standard but implements the wrong thing → **Standards pass, Spec fail.**
- Code that does exactly what the issue asked but breaks the project's conventions → **Spec pass, Standards fail.**

Reporting them separately stops one axis from masking the other.
