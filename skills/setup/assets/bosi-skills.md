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
  bragFile: ''
feature-recipe:
  cardsDir: ./recipes
  defaultMode: regular
  runWorkSummary: true
  docsDestination: ''
ship-pr:
  titleFormat: type(scope): subject [KEY]
  approvalGate: true
  draft: false
  validateCommands: []
  trackerServer: ''
a11y-check:
  devCommand: ''
  baseUrl: ''
better-code-review:
  defaultMode: conversation
  reviewerModel: ''
  reviewMode: fast
recipe-relay:
  codingModel: ''
  reviewState: In Review
  doneState: Done
  uiReviewerModel: ''
  routineModel: ''
assembly-line:
  codingModel: ''
  routineModel: ''
  uiReviewerModel: ''
  reviewState: In Review
  doneState: Done
  runLog: ~/.bosi-skills/runs.jsonl
  lineFile: '{cardsDir}/{ticket}.line.json'
  lineDestination: ticket
uml:
  outputDir: docs/uml
  plantumlJar: ''
  plantumlServer: local
  idleMinutes: 30
non-functional-requirements:
  docsDir: docs/projects
open-restaurant:
  repoByLabel: {}
  implementedState: In Review
  doneState: Done
  envName: '{parent}'
  reviewChannel: ''
  judgeModel: ''
  qaModel: ''
  fixModel: ''
pause-work:
  destination: ''
  project: ''
  due: tomorrow
  labels: []
weekly-planning:
  destination: ''
  source: ''
  workHours: 09:00-18:00
  hoursPerPoint: 4
  maxTickets: 2
plan-work:
  standard: ''
  lint: ''
  team: ''
  labels: {}
  repos: []
  featureFlags: false
  flagEngine: ''
  role: ''
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
- `week-summary.bragFile` — brag file whose entries dated inside the week
  become the Weekly Update's last answer; empty leaves it for you to fill.
- `feature-recipe.cardsDir` — folder recipe cards go in.
- `feature-recipe.defaultMode` — `regular` or `headless`.
- `feature-recipe.runWorkSummary` — `true` or `false`: write a session note
  when the recipe ends.
- `feature-recipe.docsDestination` — where the feature's docs go; empty means
  ask.
- `ship-pr.titleFormat` — shape of commit headers and PR titles.
- `ship-pr.approvalGate` — `true` pauses before push and PR; `false` does not.
- `ship-pr.draft` — `true` opens PRs as drafts.
- `ship-pr.validateCommands` — commands run before each repo's commits, such
  as lint or tests.
- `ship-pr.trackerServer` — MCP server that reads tickets; empty skips it.
- `a11y-check.devCommand` — the command that starts the app for `a11y-check`;
  empty makes that stage end `inconclusive`.
- `a11y-check.baseUrl` — the URL the app answers on; empty makes that stage
  end `inconclusive`.
- `better-code-review.defaultMode` — `conversation`, `page` or `headless`.
- `better-code-review.reviewerModel` — the model for the three review
  sub-agents; empty keeps the model the review runs on.
- `better-code-review.reviewMode` — `fast` reviews a PR taken from Slack
  without installing its dependencies; `slow` installs them first.
- `recipe-relay.codingModel` — the model for the sub-agents that write tests
  and code; empty keeps the model the relay runs on.
- `recipe-relay.reviewState` and `recipe-relay.doneState` — tracker states
  the relay moves a task to once its PR is open and when Documentation closes
  it; empty skips the move.
- `recipe-relay.uiReviewerModel` — the model for the UI reviewer; empty keeps
  the model the relay runs on.
- `recipe-relay.routineModel` — the model for the Plating and Documentation
  units and the sub-agent that runs the closing review; empty keeps the model
  the relay runs on.
- `assembly-line.codingModel` — the model for the sub-agents that write tests
  and code and fix; empty keeps the model the line runs on.
- `assembly-line.routineModel` — the model for `prepare-pr`, `code-docs` and
  the sub-agent that runs the closing review; empty keeps the model the line
  runs on.
- `assembly-line.uiReviewerModel` — the model for the UI reviewer; empty keeps
  the model the line runs on.
- `assembly-line.reviewState` and `assembly-line.doneState` — tracker states
  the line moves a ticket to once its PR is open and once `merge` merges it;
  empty skips the move.
- `assembly-line.runLog` — the file the line appends one JSON line to per stage run.
- `assembly-line.lineFile` — the local line file; `{cardsDir}` is
  `feature-recipe.cardsDir` and `{ticket}` the ticket id. The line reads it
  before the ticket's line comment.
- `assembly-line.lineDestination` — `ticket` saves a planned line as a
  comment on the ticket, `file` writes it to `assembly-line.lineFile`.
- `uml.outputDir` — folder the UML sources and `uml.json` go in.
- `uml.plantumlJar` — path to the PlantUML jar; empty means the cache folder.
- `uml.plantumlServer` — `local` for the jar, or the URL of a PlantUML
  server.
- `uml.idleMinutes` — minutes with no request before the page server stops.
- `non-functional-requirements.docsDir` — folder that holds one folder per
  project; the NFR doc goes in `<docsDir>/<project>/nfr.md`.
- `open-restaurant.repoByLabel` — map from a sub-issue label to its repo's
  folder; empty takes the repo from the sub-issue's text.
- `open-restaurant.implementedState` — state a sub-issue moves to once its
  PR is open; empty means no move. The default is `In Review`.
- `open-restaurant.doneState` — state merged sub-issues and a fully proved
  parent move to.
- `open-restaurant.envName` — name of the QA env; `{parent}` is the parent
  identifier in lower case.
- `open-restaurant.reviewChannel` — chat channel for the review request;
  empty skips it.
- `open-restaurant.judgeModel`, `open-restaurant.qaModel`,
  `open-restaurant.fixModel` — models for the readiness judge and contract,
  the QA agent and the QA fix agent; empty keeps the session's model.
- `pause-work.destination` — MCP server or CLI the paused-work task goes
  to, such as `Todoist`, `Linear` or `gh`; empty asks, or prints the task.
- `pause-work.project` — project, list or team in that tool; empty is its
  inbox or default.
- `pause-work.due` — due date in the tool's own words.
- `pause-work.labels` — labels added to the task.
- `weekly-planning.destination` — folder (starts with `/` or `~`) or MCP
  server or CLI the week plan goes to; empty prints the plan.
- `weekly-planning.source` — tool and filter the tickets come from; empty is
  the session's tracker, open tickets assigned to you.
- `weekly-planning.workHours` — work window of each day.
- `weekly-planning.hoursPerPoint` — hours one estimate point stands for.
- `weekly-planning.maxTickets` — most tickets in progress at once.
- `plan-work.standard` — the team's planning standard: a path, a URL or
  `owner/repo@ref:path`; empty uses the standard bundled with the skill.
- `plan-work.lint` — command that lints a plan against that standard; empty
  uses the bundled lint with the bundled standard, and no lint otherwise.
- `plan-work.team` — tracker team or project new tickets go in; empty asks.
- `plan-work.labels` — map from Kind or area to the tracker's label name,
  such as `{Feature: 'type: feature'}`; empty writes no labels.
- `plan-work.repos` — repos the work may touch, used to split sub-issues;
  empty takes them from the sources.
- `plan-work.featureFlags` — `true` puts every new Feature behind a flag;
  `false` plans a flag only when a source asks for one.
- `plan-work.flagEngine` — the flag tool, such as a flag service or an env
  var; empty writes "feature flag" and asks which tool.
- `plan-work.role` — `engineer` hands the tickets to `plan-assembly-line`
  when planning ends; `other` stops there; empty asks once.

A request that names a mode, such as `--headless`, beats the default here.

## work-summary

Guidance `work-summary` follows when it tags a session. Leave this section out
if there is none.

## ship-pr

Guidance `ship-pr` follows when it ships, such as which validate command
belongs to which repo. Leave this section out if there is none.

## better-code-review

Rules the review's three sub-agents follow, such as a kind of file that needs
no tests. Leave this section out if there is none.

## recipe-relay

Rules every `recipe-relay` sub-agent follows in this project, such as a check
each PR needs while a migration runs. Put it in the project's own file and
delete it when the project ends. Leave this section out if there is none.

## open-restaurant

The team's own steps: how to make the repo checkouts, the readiness standard
and lint command, the bug marker, repos out of scope, the QA scope, skill, env
and checks, the fix check, and how to wait for checks and map review groups.
Leave this section out to take the skill's defaults.

## plan-work

The team's own planning rules on top of the standard, such as a label every
ticket needs or a state new tickets start in. Leave this section out if there
is none.

## week-summary

Guidance `week-summary` follows when it writes a review, such as where the
Weekly Update gets pasted. Leave this section out if there is none.
