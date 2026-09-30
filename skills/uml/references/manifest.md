# The manifest, `uml.json`

The LLM writes `uml.json` beside the `.puml` files, in the folder
`uml.outputDir` names. The page script reads it to know which sections to draw,
in which order, and which file each editor saves to. A manifest that breaks
these rules makes `status` report `unreadable`.

```json
{
  "origin": "code",
  "source": "src/orders",
  "diagrams": [
    { "type": "class", "file": "class.puml", "why": null, "noBasis": null },
    {
      "type": "sequence",
      "file": "sequence.puml",
      "why": "Checkout: every order passes through it, and it touches the most classes.",
      "noBasis": null
    },
    {
      "type": "profile",
      "file": null,
      "why": null,
      "noBasis": "The code defines no stereotypes or tagged values."
    }
  ]
}
```

## Fields

| Field | Value | Rule |
|---|---|---|
| `origin` | `code` or `description` | `code` when the person gave no text or a path; `description` when they described a system in words. |
| `source` | string | The path drawn from (`.` for the whole repo), or the description word for word. |
| `diagrams` | list | One entry per selected type. Order does not matter; the page sorts them. |
| `diagrams[].type` | one of the nine types | `class`, `sequence`, `state`, `profile`, `composite`, `component`, `deployment`, `object`, `package`. Each type at most once. |
| `diagrams[].file` | file name or `null` | A `.puml` file inside `uml.outputDir`, such as `class.puml`. `null` when `noBasis` is set. |
| `diagrams[].why` | string or `null` | Required for `sequence` and `state` when they are drawn: the flow or entity chosen and why. Optional for the rest. |
| `diagrams[].noBasis` | string or `null` | Set when the source gives no basis for this type: one sentence on what is missing. The page then shows "Nothing in the code supports this diagram" (or "in the description") and this note, and no drawing. |

## What gets refused

- An `origin` other than `code` or `description`.
- A type outside the nine, or the same type twice.
- A `file` and a `noBasis` on the same entry, or neither.
- A drawn `sequence` or `state` with no `why`.
- A `file` that is not `.puml`, or that resolves outside `uml.outputDir`: the page shows the error in that section and the server refuses to save to it.
