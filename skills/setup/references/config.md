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
skill follows on top of its own rules. A project file is the place for guidance
that lasts only while a project does: `## recipe-relay` in one project's
`.bosi-skills.md` reaches every sub-agent the relay runs there, and deleting
the section ends it.

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
| `week-summary.bragFile` | `''` | Brag file whose entries dated inside the week become the Weekly Update's Q4. Empty keeps Q4 as `{USER WILL FILL}`. |
| `feature-recipe.cardsDir` | `./recipes` | Folder recipe cards go in, relative to the project root. |
| `feature-recipe.defaultMode` | `regular` | Mode a recipe runs in when the request names none: `regular` or `headless`. |
| `feature-recipe.runWorkSummary` | `true` | Run `work-summary` at the end of Documentation, when the session has it. `false` skips it. |
| `feature-recipe.docsDestination` | `''` | Where Documentation writes the feature's docs, such as `./docs/features/` or "the team's Notion space". Empty means work it out from the project, or ask. |
| `maestri-workflow.planningModel` | `''` | Model for the planning lane. Empty means the most capable reasoning model the presets offer. |
| `maestri-workflow.codingModel` | `''` | Model for the coding lane. Empty means a faster coding model from the presets. |
| `ship-pr.titleFormat` | `type(scope): subject [KEY]` | Shape of every commit header and PR title; the other common shape is `[KEY] type(scope): subject`. |
| `ship-pr.approvalGate` | `true` | Pause for approval before `git push` and `gh pr create`. `false` pushes and opens the PR without asking. |
| `ship-pr.draft` | `false` | Open the PR as a draft. |
| `ship-pr.validateCommands` | `[]` | Commands run from each repo's root before its commits, such as lint or tests; a failure aborts the commit. |
| `ship-pr.trackerServer` | `''` | MCP server that reads tickets. Empty skips the ticket lookup and describes the problem from the diff. |
| `better-code-review.defaultMode` | `conversation` | Output a review gives when the request names none: `conversation`, `page` or `headless`. |
| `better-code-review.reviewerModel` | `''` | Model for the Spec, Standards and Tests sub-agents. Empty means the model the review runs on. |
| `better-code-review.reviewMode` | `fast` | How the Slack mode treats the fresh clone of each PR: `fast` installs nothing and lists the checks that need dependencies as not verified; `slow` installs from the lockfile first so those checks run. |
| `recipe-relay.codingModel` | `''` | Model for the sub-agents that write tests and code in Cooking. Empty means the model the relay runs on. |
| `recipe-relay.uiReviewerModel` | `''` | Model for the UI reviewer that compares screenshots with the design. Empty means the model the relay runs on. |
| `uml.outputDir` | `docs/uml` | Folder, relative to the project root, where `uml` keeps its `.puml` sources and `uml.json`. |
| `uml.plantumlJar` | `''` | Path to the PlantUML jar. Empty means the cache folder: `$XDG_CACHE_HOME/bosi-skills/uml/plantuml.jar`, else `~/.cache/bosi-skills/uml/plantuml.jar`. |
| `uml.plantumlServer` | `local` | `local` renders through the jar and Java; a URL, such as `https://www.plantuml.com/plantuml`, renders through that PlantUML server instead. |
| `uml.idleMinutes` | `30` | Minutes with no request before the `uml` page server stops itself. |
| `non-functional-requirements.docsDir` | `docs/projects` | Folder, relative to the docs repo root, that holds one folder per project; the NFR doc is `<docsDir>/<project>/nfr.md`. |
| `open-restaurant.repoByLabel` | `{}` | Map from a sub-issue label to the folder of the repo it works in. Empty means take the repo from the sub-issue's text. |
| `open-restaurant.implementedState` | `''` | Tracker state a sub-issue moves to once its PR is open. Empty means no move. |
| `open-restaurant.doneState` | `Done` | State a merged sub-issue, and a parent with no open criterion, moves to. |
| `open-restaurant.envName` | `{parent}` | Name of the one QA env per parent; `{parent}` stands for the parent identifier in lower case. |
| `open-restaurant.reviewChannel` | `''` | Chat channel the review request goes to once the PRs are ready. Empty skips the request. |
| `open-restaurant.judgeModel` | `''` | Model for the readiness judge and the contract. Empty means the model the session runs on. |
| `open-restaurant.qaModel` | `''` | Model for the parent QA agent. Empty means the model the session runs on. |
| `open-restaurant.fixModel` | `''` | Model for the agent that fixes failed QA criteria. Empty means the model the session runs on. |
| `pause-work.destination` | `''` | MCP server or CLI the paused-work task goes to, such as `Todoist`, `Linear` or `gh`. A ticket tool gets a comment on the ticket. Empty means ask to use the one to-do or tracker tool the session has, else print the task. |
| `pause-work.project` | `''` | Project, list or team the task goes in. Empty means the tool's inbox or default. |
| `pause-work.due` | `tomorrow` | Due date of the task, in the words the tool takes. |
| `pause-work.labels` | `[]` | Labels added to the task. |

## What the request says wins

A mode set in the file is only the default. A request that names a mode
overrides it: `--headless` or "headless" gives a headless run, "regular" or
"interactive" gives a regular one, "page", "visualize" or "verbose" gives
`better-code-review` its page. "Ask me first" or "just push it" overrides
`ship-pr.approvalGate`, and "draft" overrides `ship-pr.draft`. A driver that runs a skill in a stated mode,
the way `recipe-relay` runs `feature-recipe` as an interactive invocation,
counts as the request naming it.

## Reading it

To read a key: check `./.bosi-skills.md`, then `~/.bosi-skills.md`, and take
the first that sets it. Expand a leading `~` to `$HOME`. Log nothing when a
default is used; log the file a value came from only when the skill already
keeps a decision log, such as a recipe card's `## Decisions`.
