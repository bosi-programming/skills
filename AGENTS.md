# AGENTS.md

Conventions for anything editing this repository.

## Referencing a skill's own bundled files

Never write `${CLAUDE_SKILL_DIR}`. It names one runtime, and these skills have to
read the same under any of them.

Point at a bundled file by a path relative to the `SKILL.md` that mentions it:

- `./references/patterns.md` — a file this skill owns.
- `../code-standards/SKILL.md` — a sibling skill in this plugin.

A shell command is the exception, because it runs from the repository under
work, not from the skill directory. There, use `$SKILL_DIR` and say in the prose
above the block what it is:

```bash
python3 "$SKILL_DIR/scripts/render_graph.py" model.json --check
```

Every path you write must resolve to a file that exists. A reference to a
missing file is worse than no reference: it sends the reader somewhere empty.

## Settings

A value that differs from person to person — a folder, a login, a default
mode, a list of values — never goes into a skill as a literal. It goes into the
settings file, `.bosi-skills.md`, which a skill reads from the current folder,
then `~/.bosi-skills.md`, then its own default. The `setup` skill writes it.
This repository is public: a person's paths, employer, email or values belong
in their own settings file, never here.

Every setting has a default, so a skill works for someone who never ran
`setup`. The default is what the skill did before the setting existed, unless
that was private to one person; then it is a neutral stand-in, and the old
value goes in that person's `~/.bosi-skills.md`.

To add a setting:

1. Add the key to `KEYS` in `skills/setup/scripts/check-config.py`, with its
   default, or to `DERIVED` when the default is worked out at run time, and to
   the skill's entry in `CONSUMERS`. Run the check and watch it fail.
2. Add a row to the key table in `skills/setup/references/config.md`: key,
   default, what it does. Keys are `{skill}.{camelCaseName}`.
3. Add the key with its default to the frontmatter of
   `skills/setup/assets/bosi-skills.md`, and a line saying what it does to the
   body.
4. Add a question for it to step 2 of `skills/setup/SKILL.md`.
5. In the skill that reads it, link `../setup/references/config.md` (or the
   right relative path) and name the key in backticks with its default.
6. Run `python3 skills/setup/scripts/check-config.py` until it passes.

Guidance too long for a key goes in a section of the settings file's body
named after the skill, such as `## week-summary`.
