# Change-model schema

A worked model sits in `example-model.json` beside this file.

One JSON object. Only `nodes` is required, but a model without `summary`,
`edges`, `surface` and honest `patterns` wastes the page.

```json
{
  "title": "PR #482 — notification fan-out",
  "source": "gh pr diff 482 (acme/services)",
  "summary": "Two or three sentences: what the change does and why it is shaped this way.",
  "stats": {"files_changed": 6, "insertions": 412, "deletions": 96},
  "surface": [],
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

## surface[]

What the change asks of callers. `patterns[]` says how the code is shaped;
this says what a name outside the diff has to do about it.

```json
{
  "kind": "event name",
  "name": "mail.sent",
  "change": "removed",
  "breaking": true,
  "ref": "src/audit/audit.listener.ts:50",
  "note": "Renamed to notification.sent. A listener outside this repo goes quiet with no error."
}
```

- `kind` : `exported symbol` | `http route` | `db migration` | `env var` |
  `config key` | `feature flag` | `event name` | `queue topic` | `cli flag` |
  free text. Cosmetic, like an edge kind: an unknown value is kept, not rejected,
  because every codebase has a contract this list does not name.
- `name` : required. The thing that moved, spelled the way a caller would search
  for it: `POST /notifications`, `TWILIO_AUTH_TOKEN`, `NotificationChannel`.
- `change` : `added` | `removed` | `changed`. Required, and an unknown value
  fails, because it decides what the row means.
- `breaking` : boolean, default false. True when someone outside this diff has to
  change something, or will break if they do not. A breaking row is marked in the
  panel, counted in the header, and listed in the overview strip before anything
  is clicked.
- `ref` : `path:line`, required. A contract claim with no line is a guess. When
  the file is a node in the graph the ref becomes a jump to it.
- `node` : optional node id, to attach the entry to a node whose path the `ref`
  does not name.
- `note` : who has to change, and what happens if they do not. This is the field
  a reviewer reads; write the consequence, not the restatement.

An empty list is a real answer: you looked and nothing in the public surface
moved. Leaving the key off is a different claim, and `--check` warns about it.

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
- `hunks` : array. The change itself, so a reader can see it without a pattern
  having to claim the file first. Expected on every node with a `status` of
  `added`, `modified` or `deleted`; `--check` warns when one is missing. Each
  entry is the same shape as `patterns[].evidence[]`:

  ```json
  {
    "ref": "dispatcher.service.ts:38-52",
    "diff": "@@ -0,0 +38,15 @@\n+  async dispatch(payload) {\n+    const impl = this.channelFor(payload.channel);",
    "explanation": "The whole delivery path in one method: pick a channel, send, announce it."
  }
  ```

  - `ref` : `path:line` or `path:line-line`. This is the button the strip shows.
    Defaults to the node id.
  - `diff` : required. The hunk, newline-separated, copied out of the diff you
    already have open. Keep the `@@` header and a line or two of context. A hunk
    with no diff fails validation, because the ref alone opens an empty page.
    A bare string in place of the object is read as the diff.
  - `explanation` : what this hunk does, two or three sentences. Optional, but it
    is the sentence a reviewer reads next to the code. `note` is read as an alias.

  One to three hunks per file. This is the reviewer's path through the change,
  not a second copy of the patch: pick the hunks that carry the decision and let
  the rest stay in the diff.
- `tests` : object. Whether a test asserts what this node changed. Expected on
  every changed file node that is not itself a test; `--check` warns when one is
  missing, because leaving the field off reads as nobody looked.

  ```json
  {
    "status": "added",
    "refs": ["dispatcher.service.spec.ts:18", "dispatcher.service.spec.ts:64"],
    "note": "The notification.sent emit is asserted at line 64. The retry path is not."
  }
  ```

  - `status` : `added` when this diff adds or changes a test covering the node,
    `existing` when a test the diff did not touch covers it, `none` when nothing
    does. `none` is a real answer and a useful one. An absent field is not the
    same answer: it means the question was never asked.
  - `refs` : `path:line`, a list. Required for `added` and `existing`, and
    validation fails without them, the same rule patterns follow: a coverage
    claim with no `file:line` is a guess. A ref whose file is a node in the graph
    becomes a jump to it; one outside the diff stays plain text.
  - `note` : optional, and the most useful part on a partial answer. Say what is
    covered and what is not, or why `none` is fine.

  Two shorthands: a bare string is the status (`"tests": "none"`), and a bare
  list is `existing` plus those refs.

  The status drives the page in four places. A `none` node gets a red `no test`
  mark on its box and in the file list, the header counts them, and a chip in the
  toolbar dims everything else.
- `history` : object. Churn and ownership, the context a diff cannot show. Every
  field is optional, but a model where no node carries history gets one warning
  from `--check`, because two `git log` calls per file are cheap.

  ```json
  {
    "commits_90d": 34,
    "authors_90d": 6,
    "last_change": "2026-08-19",
    "owners": ["@acme/notifications"],
    "hotspot": true,
    "note": "Six authors in three months, and every notification feature lands here first."
  }
  ```

  - `commits_90d`, `authors_90d` : counts, from git and not from memory. Measure
    them on the base branch, not on the PR, or the change inflates its own churn.
  - `last_change` : the date of the last commit before this change. Any string,
    but an ISO date reads best.
  - `owners` : list, from CODEOWNERS. A diff that crosses two owners is worth
    saying out loud, since it decides who has to review it.
  - `hotspot` : boolean, default false. Your judgment, not a threshold the
    renderer computes: a hotspot box gets an amber `hot` mark and the header
    counts it. Set it when the numbers say a file is fragile, and say why in
    `note`. A file with 40 commits by one author is busy; 40 commits by seven
    authors is fragile.
  - `note` : what the numbers mean here. This is the field worth writing.
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
- `reference` : a URL, or a list of them, for what the pattern is. Shown under
  the name in the card. Optional, and usually leave it out: the renderer already
  maps every catalog name to a source, refactoring.guru for the classic patterns
  and the primary source for the rest. Set it only to override that, or for a
  pattern the catalog does not carry.

  The card also carries a second link to the pattern's own patterns.dev page,
  for the dozen entries that have one. It answers a different question, what the
  pattern looks like in JavaScript or React, so it stays even when `reference`
  overrides the first link.
- `evidence[]` : required, and a pattern with no evidence fails validation. Each
  entry is:

  ```json
  {
    "ref": "dispatcher.service.ts:44",
    "diff": "@@ -38,9 +41,7 @@\n-    if (channel === 'email') …\n+    const impl = this.channelFor(channel);",
    "explanation": "The three-branch if is gone. The dispatcher now asks for an implementation and calls it."
  }
  ```

  - `ref` : `path:line` or `path:line-line`. This is all the card shows, and it
    is a button: clicking it opens the evidence view - the same view a node's
    `hunks` open.
  - `diff` : the hunk itself, newline-separated, copied out of the diff you
    already have open. Keep the `@@` header, keep a line or two of context.
    Optional, but a ref with no diff opens a view that has nothing to look at.
  - `explanation` : why these lines prove the pattern. It used to sit on the
    card as a dash-note; it now has a whole panel, so write two or three
    sentences rather than a fragment. `note` is still read as an alias.
- `note` : the caveat on the pattern as a whole. Why confidence is not `high`,
  what would raise it, or - for a pattern the change breaks - what the violation
  is.
