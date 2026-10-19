# pause-work scenarios

One JSON file per scenario: a `prompt` sent to the skill and the `assertions`
its reply must meet (`contains`, `contains_any`, `not_contains`,
`not_contains_any`). No scenario saves to a real tool: each one either has no
destination, so the skill prints the task, or asks for the task without saving
it.
