---
name: a11y-check
description: Reach each changed screen of the running app, scan it with axe-core through Playwright, walk it by keyboard against the accessibility standard, write an ## Accessibility section to the work card and end pass, fail or inconclusive. The stage after code when the change reaches a screen. Runs alone on a work card. Use when a changed screen needs its focus order, focus indicators, traps and contrast checked, or this check redone on a card.
---

# a11y-check

The stage after `code` when a change reaches a surface a person sees. It checks
the running screen, which `better-code-review` cannot do: that review reads
`../code-standards/Frontend/Accessibility.md` against the diff only.

It runs as an ordinary sub-agent stage under `assembly-line`, and also runs
alone. When a driver hands project rules, paste them word for word under a
`Project rules:` line at the end of the prompt. Prefix each log line `relay:`
under `recipe-relay`, `line:` under `assembly-line`, `unattended:` in a
headless run, and `a11y-check:` when run alone.

## Input

The path to a work card, the markdown file that carries a task from one stage
to the next, shaped `../feature-recipe/references/recipe-card-template.md`.
Its `task` names the ticket. Its `## Solution` names the changed screens as
routes, and any dialog or single-page route change among them.

With no card, stop and write nothing.

## Output

The same card, with this stage's parts written:

- `## Accessibility` — the first line is `Verdict: <pass|fail|inconclusive>`;
  `inconclusive` adds a `Reason: <text>` line; then one finding per line as
  `- <screen> — <rule> — <severity> — <detail>`. A second run on the same card
  appends a `### Round <n>` block instead of replacing the section.
- `## Quality Gate Results` — the `moderate` and `minor` findings.
- `## Decisions` — one line for the verdict, and the reason for `inconclusive`.
- `## Open Questions` — only when a headless run stops.
- `lastTouched`.

The verdict is `pass`, `fail` or `inconclusive`. The stage leaves `phase`
and `phasesCompleted` alone, and never edits code.

## Settings

Resolve the keys the settings file `../setup/references/config.md` describes,
without opening that file:
`grep -n -A8 '^a11y-check:' .bosi-skills.md ~/.bosi-skills.md`, the current
folder first, then `$HOME`, then the default:

- `a11y-check.devCommand` — the command that starts the app. Default `''`.
- `a11y-check.baseUrl` — where the app answers. Default `''`.

## 1. Reach the app

1. Either key empty: the verdict is `inconclusive` and the reason names the
   empty key. Start no process.
2. Read the routes `## Solution` names and join each to `a11y-check.baseUrl`.
   None named: `inconclusive`, reason "`## Solution` names no route".
3. Start `a11y-check.devCommand` in the background. Poll
   `a11y-check.baseUrl` for up to 120 s. If it never answers: `inconclusive`.
4. The stage stops the process it started when it ends, whatever the verdict.

## 2. Scan

Per screen, run axe-core through Playwright in Chromium. Use the project's own
`playwright` and `@axe-core/playwright` when installed; otherwise install them
in a throwaway folder, `{scratch}/a11y-check/`. If either cannot be loaded or
installed, the verdict is `inconclusive`, with a reason naming the tool.

Open the page from `browser.newContext()`, because `@axe-core/playwright` rejects a page from `browser.newPage()`. When the installed Playwright wants a Chromium build the machine lacks, launch the cached one by `executablePath`.

Each axe violation becomes one finding, with axe's rule id as the rule and its
`impact` as the severity. This covers colour contrast.

## 3. Keyboard walk

Tab through each screen, record the focus order, and check it against
`../code-standards/Frontend/Accessibility.md`. Each finding carries one rule id:

- `keyboard-reach` — an element with a click listener (found by
  `DOMDebugger.getEventListeners` over the Chrome DevTools Protocol, or by
  `[onclick]`) or a native control that Tab never reaches, or a `tabindex`
  other than `0` or `-1`. `serious`. Sections 1 and 4.
- `keyboard-trap` — focus stops moving. `critical`. Section 4.
- `aria-hidden-focusable` — focus lands inside `aria-hidden="true"`.
  `critical`. Section 4.
- `focus-indicator` — no visible change between the focused and unfocused
  styles. `serious`. Section 5.
- `modal-focus` — a dialog `## Solution` names fails to move focus in, hold
  it, close on `Escape` or return focus. `critical`. Section 6. Else `n/a`.
- `route-focus` — a single-page route change `## Solution` names leaves focus
  off `<main>` or `<h1>`. `serious`. Section 7. Else `n/a`.

## 4. Verdict

Severities are `critical`, `serious`, `moderate` and `minor`. Any `critical`
or `serious` finding: `fail`. None: `pass`. The reasons in sections 1 and 2:
`inconclusive`.

`moderate` and `minor` findings never send work back: log them to
`## Quality Gate Results`. On `fail` the line goes back to the latest `code`
with the findings, and runs this stage again; at most twice, then
`needs-input`. This stage does not run `code` itself.

Write the verdict and findings to `## Accessibility`; a second run on the
same card appends a block headed `### Round <n>`, `Round <n>` counting from 2, instead of replacing it.
Log the verdict to `## Decisions`, update `lastTouched`, and end with the verdict.

## Headless

Read `../feature-recipe/references/headless.md`. In a headless run:

- Nothing in it waits on a person.
- Prefix each log line `unattended:`.
- It never edits code, merges, force-pushes or deletes work written on purpose.

### Ending a run

This applies to a person's headless run of this skill, not under
`recipe-relay`. On a third `fail`, or a question with no reasonable default:

1. Write an entry to `## Open Questions`.
2. Set `runStatus: needs-input` and `runQuestion` to its id.
3. Leave `runNext`, `phase` and `phasesCompleted` alone.
4. Log the stop to `## Decisions`.
