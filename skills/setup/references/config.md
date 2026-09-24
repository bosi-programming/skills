# The settings file

One markdown file, `.bosi-skills.md`, holds the choices a person makes once
instead of on every run: where notes go, where recipe cards live, which mode
runs when nobody names one. The skills in this plugin read it; the `setup`
skill writes it.

## Where it lives

A skill looks in two places, in this order:

1. The current folder: `./.bosi-skills.md` in the directory the session runs
   from.
2. `$HOME`: `~/.bosi-skills.md`.

Each setting falls back on its own. For every key a skill needs, it takes the
value from the current folder if that file sets it, from `$HOME` if that one
does, and from the default below if neither does. So a project file can change
one setting and leave the rest to `$HOME`. A list or map is one value: the
nearer file's list replaces the other's whole, it does not merge into it.

No file at all is fine. Every key has a default, and no skill stops or asks
because the file is missing. A key a skill does not know is ignored.

## Format

The settings are YAML frontmatter, grouped by the skill that reads them. The
body under the frontmatter is prose for people, with one exception: a section
named after a skill, `## work-summary` or `## week-summary`, is guidance that
skill follows on top of its own rules.

```markdown
---
work-summary:
  outputDir: ~/work-sessions
week-summary:
  reviewsDir: ~/week-reviews
feature-recipe:
  cardsDir: ./recipes
  defaultMode: regular
better-code-review:
  defaultMode: conversation
---
```

`./assets/bosi-skills.md`, beside the `setup` skill, is the full template with
every key.

## Keys

| Key | Default | What it does |
|---|---|---|
| `work-summary.outputDir` | `~/work-sessions` | Folder `work-summary` writes its notes to. |
| `work-summary.frontmatter` | `{}` | Fixed keys added to every note's frontmatter, word for word, such as a document type another tool reads. |
| `work-summary.values` | `[]` | Values to tag a session against, each a `slug` and the `text` that defines it. Empty drops the `values` key and the `## Values` section. |
| `work-summary.valuesSource` | `''` | Where the values come from, so the skill can re-read them if they may have changed. |
| `week-summary.reviewsDir` | `~/week-reviews` | Folder `week-summary` writes its weekly reviews to. |
| `week-summary.workSessionsDir` | `work-summary.outputDir` | Folder `week-summary` reads the week's session notes from. |
| `week-summary.githubLogin` | `gh api user --jq .login` | GitHub login whose PRs and reviews count as yours. |
| `week-summary.email` | `git config user.email` | Email used to find you in the chat tool. |
| `week-summary.sessionCitation` | `` `{basename}.md` `` | How a review cites a session note; `{basename}` is the file name without `.md`, e.g. `[[notes/{basename}]]` for a wiki. |
| `week-summary.weekStart` | `saturday` | Day a week starts on when the request gives no dates. |
| `week-summary.proseSkill` | `un-ai` | Skill the Weekly Update prose goes through, when the session has it. Empty skips it. |
| `week-summary.logicSymbols` | `true` | Write the terse sections with logical symbols (`&`, `->`, `=/`). |
| `week-summary.valuesHeading` | `Values` | Heading of the section that sums up `work-summary.values` across the week. |
| `feature-recipe.cardsDir` | `./recipes` | Folder recipe cards go in, relative to the project root. |
| `feature-recipe.defaultMode` | `regular` | Mode a recipe runs in when the request names none: `regular` or `headless`. |
| `better-code-review.defaultMode` | `conversation` | Output a review gives when the request names none: `conversation`, `page` or `headless`. |

## What the request says wins

A mode set in the file is only the default. A request that names a mode
overrides it: `--headless` or "headless" gives a headless run, "regular" or
"interactive" gives a regular one, "page", "visualize" or "verbose" gives
`better-code-review` its page. A driver that runs a skill in a stated mode,
the way `recipe-relay` runs `feature-recipe` as an interactive invocation,
counts as the request naming it.

## Reading it

To read a key: check `./.bosi-skills.md`, then `~/.bosi-skills.md`, and take
the first that sets it. Expand a leading `~` to `$HOME`. Log nothing when a
default is used; log the file a value came from only when the skill already
keeps a decision log, such as a recipe card's `## Decisions`.
