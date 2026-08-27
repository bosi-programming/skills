---
name: code-visualizer
description: Turn a code diff or pull request into a dark-theme interactive web page that maps what changed, how the changed pieces relate, and which design patterns the change uses or breaks. Use this whenever the user wants to see, picture, map, diagram or visualize a change rather than read it - "visualize this PR", "show me what this diff touches", "draw the relations in this branch", "what patterns does this PR use", "map this change", "I can't follow this diff", "graph the dependencies of these commits" - and also when a diff is large or unfamiliar enough that a picture would land faster than prose. Accepts a PR URL or number, a git ref range, a .diff/.patch file, or the current working tree. This one is for code diffs; for a change to documentation or other prose files use docs-visualizer instead.
---

# Code visualizer

Turn a change into a picture a person can hold in their head: what changed, how
the changed pieces talk to each other, and which design patterns the change
leans on.

You do the reading and the judgment. A bundled script does the drawing, so you
never hand-write HTML or SVG.

Two artefacts, always in this order:

1. `model.json` — the change model you write. Nodes, relations, patterns.
2. the HTML page, produced by `${CLAUDE_SKILL_DIR}/scripts/render_graph.py` from that model.

The split matters: the model is where you can be wrong and get corrected
cheaply, and re-rendering after a fix costs a second.

## Step 1 — resolve the target

The user may give you a PR URL or number, a ref range, a patch file, or nothing.
Work out which and get both the diff and the repo, because you need the full
files, not just the hunks.

- PR URL or number: `gh pr view <n> --json title,url,body,headRefName,baseRefName`
  then `gh pr diff <n>`. For a URL from another repo add `--repo owner/name`.
- ref range: `git diff --stat <base>...HEAD` and `git diff <base>...HEAD`.
- patch file: read it. Note that you cannot open the surrounding files if the
  patch came from outside this repo - say so in the summary instead of guessing
  at relations.
- nothing given: `git status -sb` and `git diff HEAD`. If the working tree is
  clean, ask which range or PR they mean rather than visualizing nothing.

Also grab `git diff --numstat <range>` (or `gh pr diff --patch | diffstat`) so
the per-file insertion and deletion counts in the model are real numbers rather
than eyeballed ones.

## Step 2 — read for relations, not just for lines

A diff shows lines. A graph needs relations, and most relations live outside the
hunks: the import at the top of the file, the constructor that takes the new
service, the event name the listener is bound to. So for each changed file, open
the whole file, and follow one hop out to the untouched files it now depends on.

Grep is your friend here: search for the new class or function names to find
every call site, including the ones the diff did not touch. Those call sites are
what tell the reader whether the change is contained or spreads.

Relations worth drawing, with the `kind` to use:

- `imports` — module level dependency
- `calls` — function or method invocation
- `extends`, `implements` — type hierarchy
- `injects` — constructor or DI container wiring
- `emits`, `listens` — events, queues, webhooks
- `renders` — a component rendering another
- `queries`, `reads` — database, cache or HTTP data access
- `other` — anything real that does not fit; put the detail in `label`

Stop at one hop. A graph of everything is a graph of nothing: the point is to
show the blast radius of this change, not to redraw the codebase.

Include untouched files as `related` nodes only when they explain the change -
the interface the new class implements, the service it now calls. Two or three
of these add a lot; ten of them bury the diff.

## Step 3 — name the design patterns, with evidence

For every pattern you name, you must be able to point at the lines that justify
it. A pattern name with no `file:line` behind it is a guess dressed as an
insight, and the renderer rejects a pattern with no evidence for exactly that
reason.

Read `${CLAUDE_SKILL_DIR}/references/patterns.md` for the catalog: what each pattern's participants
are called, and the concrete signals in code that distinguish it from a
look-alike. Consult it rather than pattern-matching on names - a class called
`UserFactory` that only holds static helpers is not a Factory.

Three things to hold on to:

- **Confidence is information.** `high` when the roles are all present and named
  in the code, `medium` when the shape is there but partial, `low` when you are
  reading intent into it. Use the `note` field to say what would raise it. A
  `medium` with an honest caveat is far more useful to a reviewer than a
  confident `high` they later find is wrong.
- **Patterns the change breaks count too.** If the diff adds a second reason for
  a class to change, bypasses the strategy interface with an `if`, or reaches
  through a facade, name that. Use the pattern's real name and say in `note`
  that the change violates rather than applies it.
- **No pattern is a valid answer.** Plenty of good diffs are plain procedural
  code. Report zero patterns and let the summary carry the meaning; do not
  inflate a helper function into a Factory to fill the panel.

Each piece of evidence gets a whole page of its own, so give it something to
show. Alongside the `ref`, capture the `diff` hunk those lines sit in - you have
the diff open already, so this is a copy, not a lookup - and write the
`explanation` as two or three sentences rather than the fragment that used to
fit on a card.

You do not need to supply a `reference` URL. The renderer maps every name in the
catalog to its source, refactoring.guru for the classic patterns and the primary
source for the architectural, frontend and resilience ones, and adds the
pattern's own patterns.dev page as a second link where it has one. Set `reference`
yourself only to override the first link, or when you name a pattern the catalog
does not carry.

## Step 4 — run the prose through un-ai

Everything you are about to write into the model that a person will read has to
go through the `un-ai` skill first.

**Invoke `un-ai` with the Skill tool. Do not apply it from memory.** Rewriting
from what you remember the rules say is the failure this step exists to prevent:
it feels like editing and changes nothing.

- Skill name: `un-ai`. A plugin install namespaces its siblings, so use
  `bosi-programming-skills:un-ai` and fall back to bare `un-ai` if that name is
  not listed.
- The call is mandatory on every run. No model is small enough to skip it.

What goes through it: the top-level `summary`, every node `summary`, every
`details` bullet, every `patterns[].intent`, every `patterns[].note`, and every
`evidence[].explanation`.

What must not, because rewriting them would make the page wrong: `id`, `label`,
`sublabel`, `kind`, `role`, `status`, `source`, every `ref` and `evidence` path,
every line number, and every line of the captured `diff`.

## Step 5 — write the model

Write `model.json` next to the output HTML. The full field list, with types and
defaults, is in `${CLAUDE_SKILL_DIR}/references/model-schema.md`; read it before writing the file so
you are not guessing at field names. `${CLAUDE_SKILL_DIR}/references/example-model.json` holds a
finished model for a small refactor PR - skim it for the density that reads well.

Two layers of nodes, both in the same `nodes` array, told apart by `layer`:

- `layer: "file"` — one node per changed file, plus the few `related` ones. This
  is the default view and it should stay readable at a glance.
- `layer: "code"` — classes, interfaces, functions, methods, components. This is
  where the pattern participants live, so every node named in a `participants`
  list should exist here.

Keep edges within a layer: file nodes link to file nodes, code nodes to code
nodes. The renderer lays out each layer separately, so a cross-layer edge is
silently dropped.

Set `parent` on every code node to the file node it lives in. That link is what
lets a reader click a file and see only that file's patterns, so leaving it out
quietly costs the page a feature.

Aim for 25 or fewer nodes per layer. Past that, collapse: a directory of small
files becomes one node, five sibling components become one. Say what you
collapsed in the node's `summary` so nothing looks hidden.

The page has one explanation strip under the graph, and it is the surface people
actually read. It shows the top-level `summary` until something is selected, then
swaps to that node's or pattern's explanation. So write for it:

- the top-level `summary` answers "what did this change actually do" in two or
  three sentences - what a reviewer wants before they look at anything;
- every node that carries meaning gets its own `summary` (two to four sentences:
  what this file or symbol is for, and what the change did to it) plus a few
  `details` bullets for the specifics - the line an event is emitted on, the
  behaviour that was removed, the guard that is missing.

A node with no summary still renders: the strip falls back to a line derived from
the graph (kind, status, line counts, relation counts). That fallback is a
reminder, not a target - a graph where every box falls back is a graph nobody
learns anything from.

Validate before rendering, since a bad node reference is much easier to read
from the checker than from a wrong-looking picture:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/render_graph.py" model.json --check
```

## Step 6 — render and open

```bash
OUT=$(python3 "${CLAUDE_SKILL_DIR}/scripts/render_graph.py" model.json -o <name>.html)
open "$OUT"
```

Default the output to a scratch path outside the repo, e.g.
`$TMPDIR/diff-visualizer/<pr-or-branch-slug>/`, so nothing lands in the user's
working tree uninvited. Keep `model.json` beside the HTML - it is the thing you
edit when the user asks for a correction.

The page needs no server: it is one self-contained file, dark theme only, and it
works offline. The side panel takes a third of the width, the explanation strip a
quarter of the height (draggable), and nothing on the page is smaller than 14px.

What the reader gets: pan and drag, wheel zoom, `Fit`; click a box and the strip
under the graph explains it, in prose and bullets, with the relations left to the
graph where they are already drawn; the side panel narrows its pattern cards to
that selection at the same time, with `show all` to widen again; every pattern
card is collapsed to its name and confidence until it is opened, and inside it
carries a link to what the pattern is, an `Isolate on graph` checkbox that dims
everything but the participants, and its evidence refs; click a ref and the whole
page turns into that piece of evidence - the diff hunk, coloured, with the
explanation under it - and `Back` or `Escape` returns; chips filter by change
status and relation kind; a text filter; `1` and `2` switch layers, `Escape`
resets.

Deep links, worth handing to someone in a review comment: `#code` opens the code
layer, `#node=<node id>` opens with that box selected and explained,
`#pattern=<index>` opens with that card open and isolated, and
`#evidence=<index>` opens straight into one piece of evidence.

## Step 7 — report back

Give the user the path, then the three or four things you would say out loud if
you were sitting next to them: what the change does, the patterns you found and
your confidence, and anything the graph made obvious that the diff hid - a cycle
drawn right-to-left, a new dependency pointing the wrong way, a file that
everything now touches.

If the user asks for a fix, edit `model.json` and re-render. Do not hand-edit
the HTML; it is generated, so the next render would throw the edit away.
