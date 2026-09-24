---
work-summary:
  outputDir: ~/work-sessions
  frontmatter: {}
  values: []
  valuesSource: ''
feature-recipe:
  cardsDir: ./recipes
  defaultMode: regular
better-code-review:
  defaultMode: conversation
---

# Settings for bosi-programming-skills

The skills in this plugin read the frontmatter above. This file applies to
every project when it sits at `~/.bosi-skills.md`, and to one project when it
sits at that project's root. Each setting falls back on its own: a project file
only needs the keys it changes.

- `work-summary.outputDir` — folder the session notes go to.
- `work-summary.frontmatter` — fixed keys added to every note, for example
  `{kind: work-session}`.
- `work-summary.values` — values to tag a session against, as a list of
  `{slug, text}`. Leave it empty to skip values.
- `work-summary.valuesSource` — link to where the values are defined.
- `feature-recipe.cardsDir` — folder recipe cards go in.
- `feature-recipe.defaultMode` — `regular` or `headless`.
- `better-code-review.defaultMode` — `conversation`, `page` or `headless`.

A request that names a mode, such as `--headless`, beats the default here.

## work-summary

Guidance `work-summary` follows when it tags a session. Leave this section out
if there is none.
