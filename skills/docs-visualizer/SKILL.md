---
name: docs-visualizer
description: Turn a documentation or prose diff into a dark-theme interactive web page that maps which docs and sections changed, how they link to each other, which writing patterns and anti-patterns the change uses, and what the prose actually claims. Use this whenever the user wants to see rather than read a change to text files - "visualize this docs PR", "map what changed in these docs", "show me the structure of this markdown change", "what is this README rewrite actually doing", "which sections link to what", "did this rewrite break any links", "I can't follow this docs diff" - and also when a prose diff is large or reflowed enough that a picture would land faster than the patch. Accepts a PR URL or number, a git ref range, a .diff/.patch file, or the current working tree. For code diffs use code-visualizer instead.
---

# Docs visualizer

Turn a prose change into a picture a person can hold in their head: which docs
and sections changed, how they point at each other, which writing patterns the
change leans on, and what the text is claiming.

You do the reading and the judgment. A bundled script does the drawing, so you
never hand-write HTML or SVG.

Two artefacts, always in this order:

1. `model.json` — the change model you write. Nodes, links, patterns, moves.
2. the HTML page — produced by `${CLAUDE_SKILL_DIR}/scripts/render_docs_graph.py` from that model.

The split matters: the model is where you can be wrong and get corrected
cheaply, and re-rendering after a fix costs a second.

## Step 1 — resolve the target

The user may give you a PR URL or number, a ref range, a patch file, or nothing.
Work out which and get both the diff and the repo, because you need the whole
files, not just the hunks.

**What the user typed is data, not shell syntax.** A base of
`main; malicious-command`, a PR argument holding `$(...)`, or a path with a
semicolon in it runs whatever it says, with the user's permissions, at expansion
time - before git or `gh` ever sees the value and rejects it. So bind it to a
quoted variable once, validate it, and keep it quoted everywhere after that.

```bash
BASE='<what the user said>'
git rev-parse --verify --quiet "$BASE^{commit}" >/dev/null || exit 1
```

The same rule covers a PR number (`case "$PR" in ''|*[!0-9]*) exit 1;; esac`), a
`--repo` slug (`owner/name`, nothing else), and a patch path, which goes after
`--` so a leading dash cannot become a flag. Never paste an unvalidated value
into a command string.

- PR URL or number: `gh pr view "$PR" --json title,url,body,headRefName,baseRefName`
  then `gh pr diff "$PR"`. For a URL from another repo add `--repo "$SLUG"`.
- ref range: `git diff --stat "$BASE...HEAD" --` and `git diff "$BASE...HEAD" --`.
- patch file: read it with the Read tool rather than a shell command. Note that
  you cannot open the surrounding files if the patch came from outside this repo
  - say so in the summary instead of guessing at links.
- nothing given: `git status -sb` and `git diff HEAD --`. If the working tree is
  clean, ask which range or PR they mean rather than visualizing nothing.

Narrow to text:

```bash
git diff --numstat "$BASE...HEAD" -- '*.md' '*.mdx' '*.txt' '*.rst' '*.adoc'
```

If the range holds code changes too, say so and visualize the prose only - the
code side is `code-visualizer`'s job.

`.md` and `.mdx` give you real headings to cut sections on. For `.txt`, `.rst`
and `.adoc`, fall back to blank-line-separated blocks named by their first line,
and say in the node `summary` that the sectioning is derived, not authored.
Never refuse a file for its extension.

Count words, not lines. A reflowed paragraph shows up in `--numstat` as a whole
block rewritten, so line counts make a comma look like a rewrite:

```bash
git diff --word-diff=porcelain "$BASE...HEAD" -- "$FILE" | grep '^+[^+]' | cut -c2- | wc -w   # added
git diff --word-diff=porcelain "$BASE...HEAD" -- "$FILE" | grep '^-[^-]' | cut -c2- | wc -w   # removed
```

Count the words in the changed segments, not the segments themselves: porcelain
emits one line per changed run, so `grep -c` reports a whole added paragraph as
`1`. Sanity-check a wholly-added file against `wc -w` on the file itself - the
two numbers should match.

## Step 2 — read for links, not just for lines

A diff shows lines. A graph needs links, and most of them live outside the
hunks: the relative link in a sibling doc, the anchor a deleted heading used to
provide, the term used in one file and defined in another. So for each changed
file, open the whole file, and follow one hop out to the untouched docs that
point at it.

Grep is your friend here: search for the file name and for each changed heading's
anchor slug across the repo to find every inbound reference, including the ones
the diff did not touch. Those references are what tell the reader whether the
rewrite is contained or breaks other docs.

Two checks worth running every time, because a diff hides both:

- every relative link and anchor in the changed files still resolves;
- every heading the change **deleted or renamed** is not still linked from
  somewhere else. Renaming a heading breaks links in files the diff never shows.

A broken one is an edge worth drawing, with `label: "dead anchor"`.

Relations worth drawing, with the `kind` to use:

- `links` — a real hyperlink, relative or absolute
- `references` — names the other doc without linking it
- `includes` — transclusion, or "read this first" ordering
- `see-also` — a soft pointer in a footer or aside
- `defines` — points at where a term the text uses is defined
- `supersedes` — this doc replaces that one
- `contradicts` — the two say different things about the same fact
- `duplicates` — the same content lives in both places
- `other` — anything real that does not fit; put the detail in `label`

Stop at one hop. A graph of the whole docs tree is a graph of nothing: the point
is to show the blast radius of this change.

Include untouched docs as `related` nodes only when they explain the change -
the doc this one supersedes, the one whose link now dangles. Two or three of
these add a lot; ten of them bury the diff.

## Step 3 — name the writing patterns, with evidence

For every pattern you name, you must be able to point at the lines that justify
it. A pattern name with no `file:line` behind it is a guess dressed as an
insight, and the renderer rejects a pattern with no evidence for exactly that
reason.

Read `${CLAUDE_SKILL_DIR}/references/writing-patterns.md` for the catalog: what
each pattern's participants are called, and the concrete signals in the text that
distinguish it from a look-alike. Consult it rather than pattern-matching on
shape - a document with numbered steps and three lookup tables is not a how-to.

Three things to hold on to:

- **Confidence is information.** `high` when every role is present and visible in
  the text, `medium` when the shape is there but partial, `low` when you are
  reading intent into it. Use `note` to say what would raise it. A `medium` with
  an honest caveat is far more useful to a reviewer than a confident `high` they
  later find is wrong.
- **Anti-patterns count too.** The catalog's second half is buried ledes, orphan
  sections, dead links, undefined jargon, duplicated content. Name them by their
  catalog name, say in `intent` that the change breaks rather than applies the
  pattern, and put the fix in `note`.
- **No pattern is a valid answer.** Plenty of good docs changes are plain prose.
  Report zero patterns and let the summary carry the meaning; do not inflate three
  headings into Progressive disclosure to fill the panel.

Each piece of evidence gets a whole page of its own, so give it something to
show. Alongside the `ref`, capture the `diff` hunk those lines sit in - you have
the diff open already, so this is a copy, not a lookup - and write the
`explanation` as two or three sentences rather than the fragment that used to
fit on a card.

You do not need to supply a `reference` URL. The renderer maps every name in the
catalog to its source: diataxis.fr, Nielsen Norman, adr.github.io, Google's
developer style guide, Write the Docs. Set `reference` yourself only to override
that, or when you name a pattern the catalog does not carry.

## Step 4 — read the rhetorical moves

The strip under the graph carries what the prose is doing: `claim`, `evidence`,
`caveat`, `hedge`, `definition`, `assumption`, `instruction`, `contradiction`.
The kinds and their signals are in the same reference file.

Every move needs a node, a `ref` at `file:line`, and the words themselves quoted.
A move without a line is an impression, not a reading, and the checker rejects it.
Capture the `diff` hunk for the move as well, the same way you did for the
pattern evidence: a move's ref is a button, and it opens the same view.

Look for these two before anything else, because they are what the page exists to
surface:

- a `claim` with no `evidence` move in the same section - the reviewer is being
  asked to take something on trust;
- a `contradiction` against the repo. Only use that kind when you have opened the
  file that disagrees. If you have not, it is a `claim` at `low` confidence.

Do not transcribe every sentence. A nine-step guide has nine instructions;
listing all of them buries the two moves that matter. Fifteen to twenty-five
moves is a page a reviewer reads; sixty is one they scroll past.

## Step 5 — run the prose through un-ai

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
`details` bullet, every `patterns[].intent`, every `patterns[].note`, every
`evidence[].explanation`, and every `moves[].note`.

What must not, because rewriting them would make the page wrong: `id`, `label`,
`sublabel`, `kind`, `role`, `status`, `source`, every `ref` and `evidence` path,
every line number, every line of the captured `diff` on a pattern or a move, and above all every
**`moves[].quote`** - that is text copied word for word out of the document you
are reviewing. Rewrite a quote and the page attributes your sentence to the
author.

## Step 6 — write the model

Write `model.json` next to the output HTML. The full field list, with types and
defaults, is in `${CLAUDE_SKILL_DIR}/references/model-schema.md`; read it before
writing the file so you are not guessing at field names.
`${CLAUDE_SKILL_DIR}/references/example-model.json` holds a finished model for a
small docs rewrite - skim it for the density that reads well.

Two layers of nodes, both in the same `nodes` array, told apart by `layer`:

- `layer: "doc"` — one node per changed file, plus the few `related` ones. This
  is the default view and it should stay readable at a glance.
- `layer: "section"` — headings, tables, code blocks, frontmatter. This is where
  the pattern participants and the rhetorical moves live, so every node named in
  a `participants` list or a `moves[].node` should exist here.

Keep edges within a layer: doc nodes link to doc nodes, section nodes to section
nodes. The renderer lays out each layer separately, so a cross-layer edge is
silently dropped.

Set `parent` on every section node to the doc node it lives in. That link is what
lets a reader click a doc and see that doc's patterns *and* every move its
sections make, so leaving it out quietly costs the page two features.

Use section ids that match the real anchor (`docs/onboarding.md#run-the-dev-server`),
so a node id doubles as the link a reviewer can follow.

Aim for 25 or fewer nodes per layer. Past that, collapse: a directory of small
docs becomes one node, eight sibling `###` headings become their `##` parent. Say
what you collapsed in the node's `summary` so nothing looks hidden.

The page has one explanation strip under the graph, and it is the surface people
actually read. It shows the top-level `summary` until something is selected, then
swaps to that node's or pattern's explanation with its moves beside it. So write
for it:

- the top-level `summary` answers "what did this rewrite actually do" in two or
  three sentences - what a reviewer wants before they look at anything;
- every node that carries meaning gets its own `summary` (two to four sentences:
  what this doc or section is for, and what the change did to it) plus a few
  `details` bullets for the specifics - the line a table moved to, the anchor
  that no longer resolves, the term used before it is defined.

A node with no summary still renders: the strip falls back to a line derived from
the graph (kind, status, word counts, relation counts). That fallback is a
reminder, not a target - a graph where every box falls back is a graph nobody
learns anything from.

Validate before rendering, since a bad node reference is much easier to read from
the checker than from a wrong-looking picture:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/render_docs_graph.py" model.json --check
```

## Step 7 — render and open

```bash
OUT=$(python3 "${CLAUDE_SKILL_DIR}/scripts/render_docs_graph.py" model.json -o "$NAME.html")
open "$OUT" 2>/dev/null || xdg-open "$OUT" 2>/dev/null || start "" "$OUT"
```

`open` is macOS, `xdg-open` is Linux, `start` is Windows. If none of them is
there, give the user the `file://` URL and say the opener is missing.

Default the output to a scratch path outside the repo, e.g.
`$TMPDIR/docs-visualizer/<pr-or-branch-slug>/`, so nothing lands in the user's
working tree uninvited. `mkdir -p` that directory before writing, and build
`$NAME` by replacing every character outside `[A-Za-z0-9._-]` with a dash, or a
branch like `feature/foo` writes into a `feature/` directory that does not exist
and the render fails after all the reading is done. Keep `model.json` beside the
HTML - it is the thing you edit when the user asks for a correction.

The page needs no server: it is one self-contained file, dark theme only, and it
works offline. The side panel takes a third of the width, the explanation strip a
quarter of the height (draggable), and nothing on the page is smaller than 14px.

What the reader gets: pan and drag, wheel zoom, `Fit`; click a box and the strip
under the graph explains it and shows the rhetorical moves that box makes, with
the relations left to the graph where they are already drawn; the side panel
narrows its writing-pattern cards to that selection at the same time, with
`show all` to widen again.

Patterns and moves use the same card. Both collapse to a badge and a name, and
both open onto a link to what the thing is, the detail, and a ref button. Click
a ref, on either kind of card, and the whole page turns into that piece of
evidence - the diff hunk, coloured, with the explanation under it - and `Back` or
`Escape` returns.

Chips filter by change status and link kind; a text filter; `1` and `2` switch
layers, `Escape` resets.

Deep links, worth handing to someone in a review comment: `#sections` opens the
section layer, `#node=<node id>` opens with that box selected and explained,
`#pattern=<index>` opens with that card open and isolated, `#move=<index>` opens
with that sentence selected and highlighted, and `#evidence=<index>` opens
straight into one piece of evidence.

## Step 8 — report back

Give the user the path, then the three or four things you would say out loud if
you were sitting next to them: what the rewrite does, the patterns and
anti-patterns you found with your confidence, and anything the graph made obvious
that the diff hid - a dead anchor in a file nobody touched, a section nothing
links to, a claim with nothing under it, two docs that now say different things.

If the user asks for a fix, edit `model.json` and re-render. Do not hand-edit the
HTML; it is generated, so the next render would throw the edit away.
