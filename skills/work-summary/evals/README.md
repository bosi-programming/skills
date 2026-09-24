# work-summary scenarios

One JSON file per scenario: a `prompt` sent to the skill and the `assertions`
its reply must meet (`contains`, `contains_any`, `not_contains`,
`not_contains_any`, `file_exists`). A scenario with `seed_files` and
`allow_tools` runs against a sandbox folder, `{SANDBOX}`, and checks the files
it leaves there. Each run assumes a settings file with no values set.
