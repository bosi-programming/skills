# Change-model schema

A worked model sits in `example-model.json` beside this file.

One JSON object. Only `nodes` is required, but a model without `summary`,
`edges` and honest `patterns` wastes the page.

```json
{
  "title": "PR #482 — notification fan-out",
  "source": "gh pr diff 482 (acme/services)",
  "summary": "Two or three sentences: what the change does and why it is shaped this way.",
  "stats": {"files_changed": 6, "insertions": 412, "deletions": 96},
  "nodes": [],
  "edges": [],
  "patterns": []
}
```

## Top level

- `title` : string. Shown in the header and the browser tab. Include the PR
  number or branch so an open tab is identifiable later.
- `source` : string. How the diff was obtained, verbatim command if possible.
  This is what makes the page reproducible.
- `summary` : string. Top of the side panel.
- `stats` : object with `files_changed`, `insertions`, `deletions`. Take these
  from `git diff --numstat`, do not estimate.

## nodes[]

- `id` : string, required, unique. For files use the repo-relative path. For
  code use a stable name (`ClassName`, `ClassName.method`, `moduleFn`). Every
  `edges[].from` / `.to` and every `patterns[].participants[].node` must match
  an `id` exactly - the checker fails otherwise.
- `label` : string. What shows in the box. Defaults to the last path segment.
- `sublabel` : string. Second line. For file nodes use the directory; for code
  nodes use the file it lives in. The renderer prefixes the `kind` for you on
  code nodes, so do not repeat it here.
- `kind` : `file` | `class` | `interface` | `function` | `method` | `component` |
  `module` | `test` | free text. Cosmetic, but it orients the reader.
- `layer` : `file` | `code`. Defaults to `file` when `kind` is `file`, else
  `code`. Decides which view the node appears in.
- `status` : `added` | `modified` | `deleted` | `related`. Drives the colour.
  `related` means untouched but included for context.
- `insertions`, `deletions` : integers, file nodes mainly. Rendered as `+n −n`.
- `line` : integer. Where the thing starts, for code nodes.
- `summary` : string. Two to four sentences, shown in the explanation strip under
  the graph when the box is clicked. This is the most-read text on the page after
  the top-level summary, so write it as an explanation, not a label: what this
  file or symbol is for, and what this change did to it. A collapsed node says
  here what it collapsed.
- `details` : array of short strings. Rendered as bullets beside the summary in
  the explanation strip. Use them for the specifics a reviewer would otherwise
  have to dig for - the line a thing happens on, a removed behaviour, a missing
  guard. Three or four is plenty.
- `parent` : string, optional but worth filling in. The file node id a code node
  belongs to. It is how selecting a file narrows the pattern list in the side
  panel to that file's patterns - without it the page falls back to matching the
  `sublabel` and the evidence paths, which is guesswork.

## edges[]

- `from`, `to` : node ids, required, same layer.
- `kind` : `imports` | `calls` | `extends` | `implements` | `injects` | `emits` |
  `listens` | `renders` | `queries` | `reads` | `other`. Each gets its own
  colour and legend row. Unknown values fall back to `other`.
- `status` : `added` | `existing` | `removed`. `added` draws thicker, `removed`
  draws faded and dashed.
- `label` : short string, shown on hover. Use it for the detail the `kind` loses
  - the event name, the query, the HTTP route.
- `evidence` : `path:line`. Shown on hover and in the selection panel.

Direction is meaning, so get it right: `A imports B` means A depends on B.
Layers are computed from direction, and an edge that ends up pointing
right-to-left is drawn dashed and backwards on purpose - that is how a cycle or
a back reference becomes visible.

## patterns[]

- `name` : string, required. The catalog name from `patterns.md`.
- `confidence` : `high` | `medium` | `low`.
- `intent` : one sentence on what the pattern buys the code here. Not the
  textbook definition - what it does in this diff.
- `participants[]` : `{ "role": "Context", "node": "<node id>" }`. Use the
  catalog's role names so a reader can map the picture onto the pattern.
- `evidence[]` : `{ "ref": "file.ts:12-40", "note": "why this line proves it" }`.
  Required. A pattern with no evidence fails validation.
- `note` : the caveat. Why confidence is not `high`, what would raise it, or -
  for a pattern the change breaks - what the violation is.
