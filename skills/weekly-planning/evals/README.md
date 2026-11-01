# weekly-planning scenarios

One JSON file per scenario: a `prompt` sent to the skill and the `assertions`
its reply must meet (`contains`, `contains_any`, `not_contains`,
`not_contains_any`). No scenario reads a real calendar or saves to a real
tool: each one gives the meetings and tickets in the prompt and has no
destination, asks to see the plan first, or stops at a question.
