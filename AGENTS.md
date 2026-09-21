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
