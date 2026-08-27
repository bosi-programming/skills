# Docs-change model schema

A worked model sits in `example-model.json` beside this file.

One JSON object. Only `nodes` is required, but a model without `summary`,
`edges`, honest `patterns` and real `moves` wastes the page.

```json
{
  "title": "PR #118 — rewrite the onboarding docs",
  "source": "gh pr diff 118 (acme/handbook)",
  "summary": "Two or three sentences: what the rewrite does and why it is shaped this way.",
  "stats": {"files_changed": 4, "words_added": 1180, "words_removed": 604},
  "nodes": [],
  "edges": [],
  "patterns": [],
  "moves": []
}
```

## Top level

- `title` : string. Shown in the header and the browser tab. Include the PR
  number or branch so an open tab is identifiable later.
- `source` : string. How the diff was obtained, verbatim command if possible.
  This is what makes the page reproducible.
- `summary` : string. Shown in the strip until something is selected.
- `stats` : object with `files_changed`, `words_added`, `words_removed`. Count
  the words, do not estimate, and do not reuse `git diff --numstat` line counts
  - a reflowed paragraph reports as a whole rewritten block and the number lies.

## nodes[]

- `id` : string, required, unique. For docs use the repo-relative path. For
  sections use `path#heading-slug`, which is also the anchor a reader would
  link to. Every `edges[].from` / `.to`, every `patterns[].participants[].node`
  and every `moves[].node` must match an `id` exactly - the checker fails
  otherwise.
- `label` : string. What shows in the box. Defaults to the last path segment.
  For a section, the heading text as written.
- `sublabel` : string. Second line. For doc nodes use the directory; for section
  nodes use the file it lives in. The renderer prefixes the `kind` for you on
  section nodes, so do not repeat it here.
- `kind` : `doc` | `section` | `list` | `table` | `codeblock` | `frontmatter` |
  free text. Cosmetic, but it orients the reader - a `table` node reads
  differently from a `section` one.
- `layer` : `doc` | `section`. Defaults to `doc` when `kind` is `doc`, else
  `section`. Decides which view the node appears in.
- `status` : `added` | `modified` | `deleted` | `related`. Drives the colour.
  `related` means untouched but included for context - the doc that links in,
  the doc this one now supersedes.
- `words_added`, `words_removed` : integers. Rendered as `+n −n w`. Doc nodes
  mainly, but section nodes carry them too when the rewrite is uneven.
- `heading_level` : integer, 1-6. Section nodes.
- `line` : integer. Where the heading or block starts.
- `summary` : string. Two to four sentences, shown in the explanation strip when
  the box is clicked. This is the most-read text on the page after the top-level
  summary, so write it as an explanation, not a label: what this doc or section
  is for, and what the change did to it. A collapsed node says here what it
  collapsed.
- `details` : array of short strings. Rendered as bullets beside the summary.
  Use them for the specifics a reviewer would otherwise have to dig for - the
  line a table moved to, the anchor that no longer exists, the term used before
  it is defined. Three or four is plenty.
- `parent` : string, optional but worth filling in. The doc node id a section
  node belongs to. It is how selecting a doc narrows the pattern list *and*
  gathers every section's rhetorical moves into one column - without it the page
  falls back to matching the `sublabel` and the evidence paths, which is
  guesswork.

## edges[]

- `from`, `to` : node ids, required, same layer.
- `kind` : one of the below. Each gets its own colour and legend row. Unknown
  values fall back to `other`.

  - `links` — a real hyperlink, relative or absolute
  - `references` — names the other doc without linking it
  - `includes` — transclusion, or "read this first" ordering within a doc
  - `see-also` — a soft pointer in a footer or aside
  - `defines` — points at where a term the text uses is defined
  - `supersedes` — this doc replaces that one
  - `contradicts` — the two say different things about the same fact
  - `duplicates` — the same content lives in both places
  - `other` — anything real that does not fit; put the detail in `label`

- `status` : `added` | `existing` | `removed`. `added` draws thicker, `removed`
  draws faded and dashed. A link the change deleted is worth drawing as
  `removed` rather than leaving out.
- `label` : short string, shown on hover. Use it for the detail the `kind` loses
  - the anchor text, the term, "dead anchor".
- `evidence` : `path:line`. Shown on hover and in the selection panel.

Direction is meaning, so get it right: `A links B` means A points at B. Layers
are computed from direction, and an edge that ends up pointing right-to-left is
drawn dashed and backwards on purpose - that is how a circular "see the other
doc" reference becomes visible.

## patterns[]

The side panel. Catalog and role names are in `writing-patterns.md`.

- `name` : string, required. The catalog name.
- `confidence` : `high` | `medium` | `low`.
- `intent` : one sentence on what the pattern buys the reader here. Not the
  textbook definition - what it does in this diff.
- `participants[]` : `{ "role": "How-to", "node": "<node id>" }`. Use the
  catalog's role names so a reader can map the picture onto the pattern.
- `reference` : a URL for what the pattern is, shown under the name in the card.
  Optional, and usually leave it out: the renderer already maps every catalog
  name to a source. Set it only to override that, or for a pattern the catalog
  does not carry.
- `evidence[]` : required, and a pattern with no evidence fails validation. Each
  entry is:

  ```json
  {
    "ref": "docs/onboarding.md:96",
    "diff": "@@ -0,0 +1,4 @@\n+## Tokens and sessions\n+\n+Local tokens never expire.",
    "explanation": "Grep across the repo finds nothing pointing at this anchor, so a reader following the guide never arrives here."
  }
  ```

  - `ref` : `path:line` or `path:line-line`. This is all the card shows, and it
    is a button: clicking it opens the evidence view.
  - `diff` : the hunk itself, newline-separated, copied out of the diff you
    already have open. Keep the `@@` header, keep a line or two of context.
    Optional, but a ref with no diff opens a view that has nothing to look at.
  - `explanation` : why these lines prove the pattern. It used to sit on the
    card as a dash-note; it now has a whole panel, so write two or three
    sentences rather than a fragment. `note` is still read as an alias.
- `note` : the caveat on the pattern as a whole. Why confidence is not `high`,
  what would raise it, or - for an anti-pattern - what the fix is.

Anti-patterns go in this same array, named from the anti-pattern catalog. Say in
`intent` that it is an anti-pattern and in `note` what to do about it.

## moves[]

The rhetorical moves, shown in the explanation strip: the selected node's moves
when something is selected, the five least-confident ones on the overview.

- `kind` : one of `claim` | `evidence` | `caveat` | `hedge` | `definition` |
  `assumption` | `instruction` | `contradiction`. Required, and each gets its own
  badge colour. The signals that tell them apart are in `writing-patterns.md`.
- `node` : node id, required. The section the move lives in. A doc node inherits
  every move of its `parent`-linked sections, so prefer the section.
- `ref` : `path:line`, required. A move without a line is an impression, not a
  reading, and the checker rejects it. On the card it is a button, and clicking
  it opens the same evidence view a pattern ref opens.
- `diff` : the hunk those lines sit in, newline-separated, same shape as
  `patterns[].evidence[].diff`. Optional, but without it the move's ref opens a
  view with nothing to look at.
- `quote` : the words themselves, verbatim, trimmed to one sentence. This is
  what makes the strip worth reading rather than a list of labels.
- `confidence` : `high` | `medium` | `low`. Low sorts to the top of the overview
  column, which is where a reviewer should look first.
- `note` : what is wrong or right about the move - the claim with no evidence
  under it, the hedge that should be a number, the file that contradicts it. It
  shows on the card, and again as the explanation in the evidence view.

Each move renders as a collapsed card in the strip, the same shape as a writing
pattern: kind badge, node and confidence on the closed row; the link to what the
move is, the quote, the note, a jump to the node and the ref button inside. The
link comes from a built-in map of the eight kinds, so nothing in the model
supplies it.

Two moves earn their place more than any others: a `claim` with no `evidence`
move in the same section, and a `contradiction` against something in the repo.
Look for both before you look for anything else.
