---
name: better-code-review
description: Review the changes since a fixed point (commit, branch, tag or merge-base) on three axes, Standards, Spec and Tests, in parallel sub-agents. Renders a three-tab HTML page, or with `--headless` returns plain text. With `--slack <link>` reviews every PR a Slack message links to and comments or approves on GitHub. Use to review a branch, a PR or work in progress, on "review since X", or when another skill needs a review it can act on.
metadata:
  based-on: "Matt Pocock's code-review skill"
  adapted-by: Felipe Bosi
---

Three-axis review of the diff between `HEAD` and a fixed point the user supplies:

- **Standards** — does the code conform to this repo's documented coding standards, and to the bundled `code-standards` catalog wherever the repo is silent? Standards sources are located in step 3 (`CODING_STANDARDS.md`, `CONTRIBUTING.md`, or whatever the repo documents).
- **Spec** — does the code faithfully implement the originating issue / PRD / spec? The specs can be found inside the PR description as a link to an issue tracker. If not found there, search on the PR title for a string that is CCCC*-DDD* where c is a character and d is a digit, like ABC-123.

- **Tests** — are the tests in the diff sound by this repo's documented test rules, and by the bundled `code-standards` test standard wherever the repo is silent? And does every behaviour the diff changes have a test that would catch it breaking?

All three axes run as **parallel sub-agents** so they don't pollute each other's context, then this skill aggregates their findings and renders them as a single dark-theme HTML page it opens in the browser. The page keeps the axes in **three tabs**, Spec first, so a reader lands on one axis at a time instead of scanning them all at once.

## Process

Before step 1, resolve the mode as _Default mode_ says and state it in one
line, with where it came from:

```
defaultMode: page (from ~/.bosi-skills.md:43)
```

The source is the `file:line` the grep printed, `request` when the request or
a caller named the mode, or `built-in default` when neither file sets it. A
headless run skips this line, since _Headless_ allows nothing but findings.

### 1. Pin the fixed point

Whatever the user said is the fixed point — a commit SHA, branch name, tag, `main`, `HEAD~5`, etc. If they didn't specify one, ask for it. A headless run takes a default instead; see _Headless_.

Capture the diff command once: `git diff <fixed-point>...HEAD` (three-dot, so the comparison is against the merge-base). Also note the list of commits via `git log <fixed-point>..HEAD --oneline`.

Before going further, confirm the fixed point resolves (`git rev-parse <fixed-point>`) and the diff is non-empty. A bad ref or empty diff should fail here — not inside three parallel sub-agents.

### 2. Identify the spec source

Look for the originating spec, in this order:

1. Issue references in the commit messages or branch name — Linear keys (`ABC-123`, `XYZ-42`) fetched with the Linear MCP `get_issue`; GitHub issues and PRs (`#123`, `Closes #45`) fetched with `gh issue view` / `gh pr view`.
2. A path the user passed as an argument.
3. A PRD/spec file under `docs/`, `specs/`, or `.scratch/` matching the branch name or feature.
4. If nothing is found, ask the user where the spec is. A headless run skips the Spec axis instead; see _Headless_. If they say there isn't one, the **Spec** sub-agent will skip and report "no spec available".

### 3. Identify the standards sources

Anything in the repo that documents how code should be written, such as `CODING_STANDARDS.md` or `CONTRIBUTING.md`.

Wherever the repo is silent, the Standards axis falls back to the bundled [`code-standards`](../code-standards/SKILL.md) catalog. Its files sit beside this skill, so resolve them from `../code-standards/` and pass the paths you need to the sub-agent in step 4:

- `Common/Clean Code.md` — every review.
- `Typescript/Imports.md` and `Typescript/Exports.md` — when the diff touches `.ts` / `.tsx`.
- `Frontend/Accessibility.md` — when the diff touches UI that renders in a browser.

Skip the files the diff cannot violate; a backend-only change gets `Common/Clean Code.md` and nothing else. If that sibling path is not where the catalog is, load the `code-standards` skill by name and take the paths it reports.

The **Tests axis** reads its own sources: anything the repo documents about how tests are written, such as `TESTING.md` or a testing section in `CONTRIBUTING.md`, then [`../code-standards/Testing/Tests.md`](../code-standards/Testing/Tests.md) wherever the repo is silent. It also needs the project's test layout, so note where the tests live and what the runner is.

**Read what tooling already enforces.** Open the project's lint, format and type-check config (`eslint.config.*`, `.eslintrc*`, `biome.json`, `.prettierrc*`, `tsconfig.json`, `ruff.toml`, `pyproject.toml`, or whatever the repo uses) and list the enabled rules. That list is what "tooling enforces" means for every sub-agent. When the repo has no such config, say so, and the sub-agents skip nothing on tooling's behalf.

A breach of the catalog is a **hard violation** only where the project documents the same rule. Where it rests on the catalog alone it is a judgement call, like every smell below.

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

### 4. Spawn the three sub-agents in parallel

Run them on the model `better-code-review.reviewerModel` names, read from the settings file as `../setup/references/config.md` says. Its default, `''`, keeps the model this review runs on. They read and report, and step 5 checks every finding at its source, so a faster model does the job.

Read the settings file's `## better-code-review` section, the current folder's file first, then `$HOME`'s: `sed -n '/^## better-code-review$/,/^## /p' <file>`. Paste it word for word under a `Project rules:` line at the end of every sub-agent prompt below, and hold step 5 to it. A rule there beats the catalog and the smell baseline. No section means no rules.

**Standards sub-agent prompt** — include:

- The full diff command and commit list.
- The enabled rules from the tooling config in step 3.
- The list of standards-source files you found in step 3, the absolute paths of the `code-standards` files that apply to what the diff touches, **plus the smell baseline from step 3** pasted in full — the sub-agent has no other access to it.
- The brief: "Report — per file/hunk where relevant — (a) every place the diff violates a standard: cite the standard (file + the rule) and say whether it came from the repo or from the `code-standards` catalog you were given; and (b) any baseline smell you spot: name it and quote the hunk. Distinguish hard violations from judgement calls — a breach of a standard the repo documents is hard, a breach of the catalog alone is a judgement call, baseline smells are always judgement calls, and a standard documented in the repo overrides both. Skip anything on the enabled-rules list. Under 400 words."

**Spec sub-agent prompt** — include:

- The diff command and commit list.
- The path or fetched contents of the spec.
- The brief: "Report: (a) requirements the spec asked for that are missing or partial; (b) behaviour in the diff that wasn't asked for (scope creep); (c) requirements that look implemented but where the implementation looks wrong. Quote the spec line for each finding. Under 400 words."

**Tests sub-agent prompt** — include:

- The diff command and commit list.
- The enabled rules from the tooling config in step 3.
- The test-standards files you found in step 3 and the absolute path of `../code-standards/Testing/Tests.md`, plus where the tests live and what the runner is.
- The brief: "Report two things. (a) Every place a test file in the diff breaks a test standard: cite the standard (file + the rule), say whether it came from the repo or from the catalog, and quote the hunk. A breach of a standard the repo documents is hard; a breach of the catalog alone is a judgement call. (b) Every behaviour the diff adds or changes in source code that no test in the diff or the existing suite would catch breaking: name the behaviour, give its `file:line`, and mark it missing test. Read the existing tests before you call a test missing. Skip anything on the enabled-rules list. Under 400 words."

If the spec is missing, skip the Spec sub-agent and note this in the final report. If the diff touches no test file and changes no behaviour, such as a docs-only change, skip the Tests sub-agent and report "no tests to review".

### 5. Aggregate

Hold the three reports under a `Spec`, a `Standards` and a `Tests` heading, verbatim or lightly cleaned. Do **not** merge or rerank findings — the three axes are deliberately separate (see _Why three axes_).

Add a one-line summary: total findings per axis. Don't pick a single winner across axes — that's the reranking the separation exists to prevent. The severity ordering on the page carries the rest; the page has no worst-per-axis section, because a summary of a page that already sorts worst-first only repeats its own first card.

Before the aggregate becomes a file, verify it yourself: open every file at the line a finding cites, grep every quoted standard in its own file, and read the code behind every acceptance criterion marked met. A finding you have not read at its source is a claim, not a finding — cut it or fix the citation before it reaches the page.

Reading is the floor, not the ceiling. Verify by the rule in [`../epistemic-action/SKILL.md`](../epistemic-action/SKILL.md): only a run or a read of the source counts as evidence, and a run outranks a read. Tag every finding with the strongest evidence behind it: `ran`, `read`, or `no`.

- **Run the project's checks.** Run the project's own test, lint and type-check commands at the reviewed commit, scoped to the change the way the project scopes them. A failure the diff caused is a finding on its axis. A pass settles the claims it covers. A command you could not run goes to `Not verified`, with the reason.
- **Probe every `missing test` finding and every tautological test.** Add a throwaway worktree at the reviewed commit, `git worktree add --detach <scratch>/probe HEAD`, where `<scratch>` is a directory outside the repo: the session scratchpad, or `$(mktemp -d)`. If the tests cannot run there, say for want of installed dependencies, the probe goes to `Not verified` with the reason. For each finding, break the line it names (invert the condition, return a wrong value), run the tests that cover it, read the result, and restore the line before the next probe. Tests that stay green on broken code prove the finding: tag it `ran`. Tests that go red mean a test does catch it: cut the finding. When the probes are done, `git worktree remove --force <scratch>/probe`. Never probe in the user's working tree.
- **Record the conditions.** Note the commit SHA and branch every run and probe used. The page footer and the headless `Reviewed:` line carry them, so a reader can tell what a finding does not cover.

### 6. Render the HTML report

If the user asked for visualization or verbose, run this section. If not, ignore and print the result on the conversation instead, unless the mode is `page` (see _Default mode_). A headless run never runs it; see _Headless_.

Then read and follow `./references/page.md`, which holds this step and step 7.

## Default mode

When the request names no output, the settings file decides. Read
`../setup/references/config.md` and resolve `better-code-review.defaultMode`,
current folder first, then `$HOME`: `conversation` prints the result in the
conversation, `page` runs steps 6 and 7, `headless` runs as _Headless_ below.
The default is `conversation`. A request that asks for a page, for verbose, or
for headless, or a caller that names a mode, wins over the file. A Slack link
or `--slack` runs _Slack_ below, whatever the file says.

Look the key up with this command, from the repository under review:

```bash
grep -n -A3 '^better-code-review:' .bosi-skills.md ~/.bosi-skills.md
```

Take the `defaultMode:` line under the first file that has one. Do not read
the files with `head` or `sed -n 1,40p`: those stop at a fixed line, and the
key can sit below it. A grep for the key cannot be cut off that way.

## Headless

For a caller with nobody to answer questions: another skill, a sub-agent, an
agent on a canvas. Start one with `--headless`, or say "headless" in the
request, or set `better-code-review.defaultMode` to `headless`. A headless run never asks; where the steps above would ask, it takes
the default below.

- **No fixed point given:** use the merge base of `HEAD` and the default
  branch, `git merge-base HEAD origin/<default branch>`.
- **Bad ref or empty diff:** return one line, `review not run: <reason>`, and
  stop.
- **No spec found** by step 2's first three sources: skip the Spec axis and
  report "no spec available". A spec the caller passes counts as step 2's
  second source.
- **Nothing to test:** when the diff touches no test file and changes no
  behaviour, skip the Tests axis and report "no tests to review".
- **Step 5 still runs**, checks and probes included. Every finding is read
  at its source, and run where step 5 says, before it goes out.
- **No HTML.** Skip steps 6 and 7, even if the request says verbose or asks
  for a picture.

The result is the whole reply, one block per finding, Spec first, then Standards, then Tests:

```
<axis: Spec | Standards | Tests> · <kind> · <file:line>
What: <the problem, one or two lines>
Fix: <the change that settles it>
Verified: ran | read | no — <what was not run or read>
```

`<kind>` is `hard` or `judgement call` for Standards; `missing`,
`scope creep` or `wrong` for Spec; and `hard`, `judgement call` or
`missing test` for Tests. Close with three lines:

```
Reviewed: <sha> on <branch>
Totals: Spec <n>, Standards <n>, Tests <n>
Not verified: <one gap per line, or none>
```

Print nothing else: no greeting, no summary, no per-axis winner. A caller
parses the blocks, and prose between them is what breaks that.

## Slack

Reviews every PR a Slack message links to and posts the result on GitHub. Start
it with `--slack <link>`, or put a `slack.com/archives/...` link in the request,
then read and follow `./references/slack.md`. `better-code-review.reviewMode`
decides there whether a PR's fresh clone installs its dependencies.

## Why three axes

A change can pass one axis and fail another:

- Code that follows every standard but implements the wrong thing → **Standards pass, Spec fail.**
- Code that does exactly what the issue asked but breaks the project's conventions → **Spec pass, Standards fail.**
- Code that does what the issue asked and follows every standard, with tests that could not fail if it broke → **Spec and Standards pass, Tests fail.**

Reporting them separately stops one axis from masking another.
