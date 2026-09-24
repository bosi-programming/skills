---
work-summary:
  outputDir: ~/work-sessions
  frontmatter: {}
  values: []
  valuesSource: ''
week-summary:
  reviewsDir: ~/week-reviews
  workSessionsDir: ''
  githubLogin: ''
  email: ''
  sessionCitation: '`{basename}.md`'
  weekStart: saturday
  proseSkill: un-ai
  logicSymbols: true
  valuesHeading: Values
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
- `week-summary.reviewsDir` — folder the weekly reviews go to.
- `week-summary.workSessionsDir` — folder of session notes to read; empty
  means `work-summary.outputDir`.
- `week-summary.githubLogin` and `week-summary.email` — who you are on GitHub
  and in chat; empty means `gh api user` and `git config user.email`.
- `week-summary.sessionCitation` — how a review cites a note, with
  `{basename}` for its file name.
- `week-summary.weekStart` — day a week starts on.
- `week-summary.proseSkill` — skill the Weekly Update prose goes through;
  empty skips it.
- `week-summary.logicSymbols` — `true` or `false`.
- `week-summary.valuesHeading` — heading of the values section.
- `feature-recipe.cardsDir` — folder recipe cards go in.
- `feature-recipe.defaultMode` — `regular` or `headless`.
- `better-code-review.defaultMode` — `conversation`, `page` or `headless`.

A request that names a mode, such as `--headless`, beats the default here.

## work-summary

Guidance `work-summary` follows when it tags a session. Leave this section out
if there is none.

## week-summary

Guidance `week-summary` follows when it writes a review, such as where the
Weekly Update gets pasted. Leave this section out if there is none.
