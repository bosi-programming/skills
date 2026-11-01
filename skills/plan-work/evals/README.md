# plan-work scenarios

One JSON file per scenario: a `prompt` sent to the skill and the `assertions`
its reply must meet (`contains`, `contains_any`, `not_contains`,
`not_contains_any`). No scenario reads or writes a real tracker: each one gives
the feature in the prompt, says there is no tracker tool, and stops at the
draft, a question, or a review report.
