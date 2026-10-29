---
name: open-restaurant
description: Take a parent issue and deliver every sub-issue under it through recipe-relay, one recipe card and one PR ready for review per sub-issue, cooked in parallel across repos and one at a time within a repo. Gates the parent on readiness first, writes the contract the sub-issues share, hands a blocked sub-issue its blocker's interfaces as soon as they exist, then integrates the branches, runs one QA pass on one env, fixes failures on the owning branch, writes proof, reviews each PR as it opens in its own sub-agent, and parks at human gates for review and merge. Use when the user names a parent issue, epic or story with sub-issues and wants all of it delivered, or says "open the restaurant".
---

# Open Restaurant

The parent issue is the order; each sub-issue is a dish. This session is the
kitchen's head: it never cooks a dish itself. Each sub-issue gets its own
recipe card and runs through `../recipe-relay/SKILL.md`, which runs
`../feature-recipe/` unit by unit in sub-agents. What belongs to the parent as
a whole — readiness, the contract, integration, QA, proof, merge — lives here,
in the service card, never in a sub-issue's card.

Sub-agents cannot start sub-agents of their own, so this session drives every
unit of every card itself. Start units in the background where the runtime
allows it, so cards in different repos cook at the same time, and act on each
unit as it returns.

The run never merges without a human, and opens every PR ready for review,
never as a draft. Merging waits at the gate in section 11.

## Settings

Read the settings file as `../setup/references/config.md` says, current folder
first, then `$HOME`, then the default:

- `open-restaurant.repoByLabel` — map from a sub-issue label to the folder of
  the repo it works in. Default `{}`: take the repo from the sub-issue's own
  text.
- `open-restaurant.implementedState` — tracker state a sub-issue moves to once
  its PR is open. Default `In Review`; `''` means no move.
- `open-restaurant.doneState` — state a merged sub-issue, and a parent with no
  open criterion, moves to. Default `Done`.
- `open-restaurant.envName` — name of the QA env; `{parent}` stands for the
  parent identifier in lower case. Default `{parent}`.
- `open-restaurant.reviewChannel` — chat channel the review request goes to.
  Default `''`: no request.
- `open-restaurant.judgeModel` — model for the readiness judge and the
  contract. Default `''`: the model this session runs on.
- `open-restaurant.qaModel` — model for the QA agent. Default `''`.
- `open-restaurant.fixModel` — model for the QA fix agent. Default `''`.

The settings file's `## open-restaurant` section, when present, is guidance
this skill follows on top of its own rules. It names the steps that differ
from team to team. Where this file says "the command the section names",
look there; where the section names nothing, take the default given here:

- **workspace** — how the user makes the repo checkouts, and what to do after
  a lockfile changes;
- **readiness standard** and **readiness lint** — the issue standard the gate
  holds the parent to, and a command that checks it;
- **bug marker** — how the tracker marks a bug sub-issue;
- **repos out of scope** — repos this skill must not work in;
- **QA scope**, **QA skill**, **QA env** and **QA checks** — which criteria
  the parent QA proves, the skill the QA agent follows, how to bring the env
  up and down, and the commands that check the QA's own output;
- **fix check** — a command that confirms a fix landed;
- **review ready** and **review groups** — how to wait for checks once PRs are
  ready, and how to map the team to the review groups to tag.

## 1. Take the order

1. The input is one parent issue: a key or a link. Read it, its comments and
   every sub-issue through the session's tracker tool: title, description,
   labels, state, the branch name the tracker gives, and every blocks /
   blocked-by relation. An issue with no sub-issues runs as one card, with no
   contract.
2. The session runs from a folder that holds one checkout per repo, as
   `./<repo>/`. This skill never creates or removes a checkout or a git
   worktree; no `git worktree` anywhere. Map each sub-issue to its one repo:
   a repo its text names wins, else its label through
   `open-restaurant.repoByLabel`. A sub-issue with
   no repo, or with more than one, gets a `## Blocked <id>` comment naming
   why. One in a repo the section lists as out of scope stops the run with
   `runStatus: needs-input`. If a checkout is missing for any repo the
   sub-issues touch, stop and print the command the section's workspace entry
   names for making it.
3. Open the service card at `{cardsDir}/{parent-slug}.service.md`, where
   `{cardsDir}` is `feature-recipe.cardsDir`. If one exists, resume it: read
   its frontmatter and go to the step `stage` names, as section 12 says. A new
   one holds:

   ```markdown
   ---
   parent: '<identifier>'
   stage: 'readiness'   # readiness | contract | cooking | closing | qa | proof | review | merge | closed
   runStatus: 'running' # running | needs-input | blocked | gate | terminal
   gate: ''             # unfinished | qa | review | merge, while runStatus is gate
   qaRounds: 0
   fixChecks: 0
   ---

   ## Sub-issues
   | id | repo | branch | base | blocked by | card | status | PR |

   ## Contract

   ## Unblock notes

   ## QA

   ## Merge

   ## Decisions

   ## Open Questions
   ```

   Log every choice this skill takes alone to `## Decisions` as `restaurant:`.

## 2. Readiness gate

A hard gate, before any card exists. Gaps stop the run; they are never
answered on the parent's behalf.

1. **Lint.** Run the readiness lint the section names, with the input it
   asks for. With none named, skip to the judge and have it check the lint's
   ground too: every sub-issue has acceptance criteria, one repo, and a
   blocks graph with no cycle.
2. **Judge.** One sub-agent on `open-restaurant.judgeModel`, with no tools,
   reads the parent and its sub-issues against the readiness standard the
   section names and checks only what a lint cannot: `open-decision` (a choice
   the text leaves open), `parity-shorthand` (a "same as X" with no criteria
   of its own), `missing-contract` (a shape passed between sub-issues that
   neither states), `manual-reason` (a manual check with no reason). It
   returns `{ ready, gaps: [{ issue, items: [{ rule, message }] }] }`.
3. **Not ready.** On any gap, create a "Readiness gaps: <id> — <title>"
   issue that blocks the parent and lists each gap, comment `## Not ready <id>`
   on the parent with every gap, set `runStatus: blocked`, and stop.
4. **Ready.** Comment `## Ready <id>` on the parent and move on.

## 3. Contract

Parents only. One sub-agent on `open-restaurant.judgeModel`, allowed to write
files and nothing else, lists each shape one sub-issue produces and another
consumes: `{ name, kind: api|event|config, producer, consumers, shape }`. It
copies each shape word for word from the issues and must never invent one; a
part no issue states goes to `gaps`. It writes `contract.json` at the folder
root, and this session posts it as `## Contract <id>` on the parent and copies
it into the service card.

Every later step reads the latest `## Contract` comment on the parent, not the
file: the latest `## Contract` comment wins, since a person may have edited
it.

## 4. Seat the cards

One recipe card and one PR per sub-issue. Fill `## Sub-issues` first, one row
per sub-issue, then decide when each may start.

1. **Card.** Create `{cardsDir}/{sub-slug}.md` from
   `../feature-recipe/references/recipe-card-template.md`, with `task` set to
   the sub-issue identifier. Add a `## Parent contract` section holding the
   contract entries where this sub-issue is producer or consumer; its
   Interfaces unit must match them, and logs any difference to `## Decisions`.
2. **Branch.** The branch is the one the tracker gives for the sub-issue, so
   the tracker links the PR to it. When the card starts, switch its repo's
   checkout to it: `git switch -c <branch> origin/<default branch>`, or off
   the blocker's branch when it stacks.
3. **When it starts.** A sub-issue starts when each of its blockers lets it:
   - **Same repo.** Sub-issues that share a repo run one at a time in that
     repo's checkout, in blocks order, since two runs in one checkout would
     break each other. A blocker in the same repo lets it start once the
     blocker's card is finished and its branch pushed; the dependent's branch
     and PR stack on the blocker's branch, and `base` in its row is that
     branch. Two same-repo blockers that do not form a chain stop the run with
     `runStatus: needs-input`: there is no one branch to stack on.
   - **Other repo.** A blocker in another repo lets it start once the
     blocker's unblock note reaches it, as section 6 says. Sub-issues in
     different repos run in parallel.
   - No blocker: it starts at once, subject to its repo being free.
4. **Bugs.** A sub-issue the section's bug marker flags gets one sub-agent
   before its Phase 1 that tries to reproduce it on
   `origin/<default branch>`. Not reproduced: comment `## Blocked <id>` with
   what it tried, mark the row `blocked`, and start nothing that depends on it.

## 5. Cook the cards

Run each card through `../recipe-relay/SKILL.md` as written: Phase 0, the
units, the UI review, the stop conditions and the closing `better-code-review`
pass with its fixes. Run the fixes in a sub-agent on
`recipe-relay.codingModel`, under that pass's own rules, so this session stays
free for the other cards. Every unit's prompt names the card's repo checkout
as where it works. On top of recipe-relay:

- **Cooking.** The Interfaces unit of a card that blocks a sub-issue in
  another repo gets section 6's extra instruction.
- **Plating.** Add to its prompt: "Deliver one PR, no chunks, open and ready
  for review, never as a draft, from `{branch}` against base `{base}` (the
  default branch, or the blocker's branch when it stacks). This overrides
  Plating's draft rule. Title starts with `{sub-issue id}`; the body names
  the sub-issue and the parent `{parent id}`. Put no closing word, such as
  `Closes` or `Fixes`, before an identifier: the merge gate moves the
  sub-issue itself. Skip section 6 of Plating: the review gate asks for review.
  Leave the sub-issue's tracker state alone: the session moves it. Log all of
  it to `## Decisions` as `relay:`."
- **Review per PR.** The moment a card's PR is open, start recipe-relay's
  review and fix section for that PR as its own background sub-agent, one per
  PR, running `../better-code-review/SKILL.md` with `--headless`. Never batch
  PRs into one review and never wait for other cards: reviews of different
  PRs run at the same time. Fixes follow recipe-relay's rules and push to the
  open PR.
- **PR to sub-issue.** Each PR links to its own sub-issue, never to the
  parent; the parent gets links only through `## Proof <parent>`. After
  Plating, check through the tracker that the sub-issue shows the PR as an
  attachment; if not, attach the PR URL to it. Then move the sub-issue to
  `open-restaurant.implementedState`, unless it is empty, and write the PR into its row.
- **Documentation.** Tell the unit to skip `work-summary`; this session runs
  it once at the end, when `feature-recipe.runWorkSummary` says to. Tell it
  also to leave the tracker state alone: the merge gate moves it to
  `open-restaurant.doneState`.
- **Lockfiles.** After a card changes a lockfile, do what the section's
  workspace entry says before the next card in that repo, or the integrate
  step, starts.
- **Status.** When a card stops on `blocked` or `needs-input`, do not answer
  for it: mark its row, comment `## Blocked <id>` with the card's open
  question, and keep cooking every card that does not depend on it.

A card is finished when its PR's review sub-agent and the fixes it led to are done. Mark the
row `done`, then free the repo for the next card in it.

## 6. Early unblock

When B is blocked by A in another repo, B needs A's shapes, not A's code, so
it starts long before A's PR.

1. **The ask.** When A's Interfaces unit starts, tell it who A blocks and
   what each needs, read from the parent's `## Contract` (A the producer, B a
   consumer). Besides `## Interfaces`, it writes, for each such B,
   `{scratch}/unblock/<A>-to-<B>.md` holding: the shapes B consumes, copied
   from A's `## Interfaces` and checked against the contract; each difference
   from the contract on its own line; and what B still cannot rely on, such as
   an endpoint not deployed until A's PR merges.
2. **Earliest point.** The end of A's Interfaces unit is the earliest point,
   since A's names, signatures and files are fixed there. When the unit cannot
   give B what it needs — A's plan too vague, or a thing that only exists once
   A's code runs, such as a generated client — the note says so and names the
   later point at which A can: the end of Cooking, or A's pushed branch. Ask
   again at that point, through the same file.
3. **Follow-up.** When a note leaves B a gap, ask the agent that wrote it a
   follow-up question, by continuing that sub-agent where the runtime allows it
   (in Claude Code, `SendMessage`), else by a new sub-agent that reads A's
   card. Never guess on B's behalf.
4. **The handoff.** Copy the note into B's card as
   `## Upstream interfaces (<A>)` before B's Phase 1 starts, log
   `relay: started <B> early on <A>'s interfaces` to B's `## Decisions`, and
   start B at once, beside A's writers. B's Interfaces unit and both writers
   code to that section as fixed input; B's tests stub A's side at that shape
   and never call A's unfinished code. Record the note in the service card's
   `## Unblock notes`.
5. **A change.** A's agents never change a shape they handed off without
   saying so: the change goes into the unblock file as a new dated entry and
   into A's `## Decisions`. Read the file each time one of A's units returns.
   On a change, update B's `## Upstream interfaces (<A>)` and tell B's current
   or next unit to adapt; if B already reached Plating, send B through one
   more fix and taste round.
6. **Chains.** In a chain where A blocks B and B blocks C, C waits for B's
   note, which B writes at the end of its own Interfaces unit, already built
   on A's note. Each hop happens at the earliest point, never at PR time.

## 7. Close the cards

Once no card can start or move:

1. **Unfinished park.** If any row is not `done`, write a park summary: each
   unfinished sub-issue, with the reason quoted from its latest `## Blocked`
   comment. Set `runStatus: gate`, `gate: unfinished`, and stop for the user.
   On approve, go on to integrate and QA with the branches as they are; on
   cancel, leave the parent for a later run.
2. **Interfaces check.** Compare each producer's final `## Interfaces` with
   every note it sent. A mismatch nobody handled stops the run with
   `runStatus: needs-input`, naming both cards.

## 8. Integrate, QA and fix

1. **Scope.** List the criteria the parent QA proves: every criterion of the
   parent, plus each sub-issue criterion the section's QA scope names; with
   none named, each sub-issue criterion its card says needs the running,
   integrated system. If the list is empty, go to section 9.
2. **Integrate.** In each repo checkout, create `integration/<parent>` from
   `origin/<default branch>` and merge the sub-issue branches into it in
   blocks order. Never push it. A merge conflict stops the run with
   `runStatus: needs-input`, naming the two branches.
3. **QA.** Bring up one env named from `open-restaurant.envName`, the way the
   section's QA env entry says: one env for the parent, never per sub-issue.
   One sub-agent on `open-restaurant.qaModel` follows the QA skill the section
   names, or, with none, proves each criterion by running the integrated
   system. It saves evidence under `./qa-proof/<parent>/`, one
   `proof/<issue>/<n>/verdict.json` per criterion, and a manual criterion
   stays pending with its owner. It never edits the checkouts. It returns
   `pass`, `fail`, `inconclusive` or `blocked`. Run the section's QA checks on
   its output, and post the round as `## QA <parent>` on the parent and under
   `## QA` in the service card.
4. **On fail.** Save the proof bundle, tear the env down, switch every
   checkout off `integration/<parent>`, then fix.
5. **Fix.** One sub-agent on `open-restaurant.fixModel`. For each failed
   criterion it picks one owning sub-issue: the criterion's own, else the
   contract's producer, else the branch that touched the failing files. It
   fixes on a detached HEAD of `origin/<owner branch>`, commits
   `fix(<owner>): <criterion id> <summary>`, and pushes fast-forward only:
   never `--force`, and never on `integration/<parent>`. It returns
   `{ fixes: [{ criterion, owner, branch, repo, sha, summary }] }`.
6. **Fix check.** Run the section's fix check, or, with none: each sha sits
   on `origin/<owner branch>` and each checkout is clean. A refused fix goes
   back to the fix agent. Once all land, delete and rebuild
   `integration/<parent>` from the new tips, bring the env back up and re-run
   every criterion in scope.
7. **Limits.** QA to fix runs at most 2 times, and fix to fix check at most 4
   times; past either, stop at a human gate (`gate: qa`). `inconclusive` and
   `blocked` also go to the human gate. A `blocked` the human approves goes to
   fix, with the blocker counted in scope.
8. **On pass.** Tear the env down and go on to proof.

## 9. Proof

Write `## Proof` on each sub-issue's PR: the criteria it owns, each with its
verdict and evidence. Write one `## Proof <parent>` comment on the parent: one
entry per parent criterion with its evidence uploaded to the tracker, then a
`### Sub-issues` list with each PR and how many of its criteria are met.

## 10. Review gate

Stop for a human: set `runStatus: gate`, `gate: review`, and report the PRs,
their proof, what each PR's review found and fixed, and what stays open. The
PRs are already ready for review. On approve:

1. Wait for each sub-issue PR's checks, the way the section's review ready
   entry says. Green goes on; red or a timeout skips the request and reports
   why.
2. When `open-restaurant.reviewChannel` is set, post one message there with
   every PR, tagging the review groups the section's review groups entry maps
   from the team. Never guess a group: an unmapped team gets no tag and a line
   in the report. A chat failure does not stop the run.

## 11. Merge gate

Stop for a human: set `runStatus: gate`, `gate: merge`. This skill never merges
without a human approving at this gate. On approve:

1. Merge in blocks order. A sub-issue's PRs come one after another; a stacked
   PR gets its retarget to the default branch once its blocker merges, and
   merges after it.
2. A failed merge stops at the gate again, with the merged, failed and pending
   lists in the service card's `## Merge`. On approve, resume from the failed
   one.
3. After the last merge: delete each local `integration/<parent>` branch,
   move every merged sub-issue to `open-restaurant.doneState`, and move the
   parent there only if proof leaves no criterion open; else comment
   `## Open criteria <parent>` listing each one. Set `stage: closed`,
   `runStatus: terminal`.

## 12. Stops and resume

The run stops only at a gate, at `blocked`, at `needs-input`, or at the end.
On a stop, write `stage`, `runStatus` and `gate` to the service card, and
report the question or the gate in chat. Re-invoking this skill on the same
parent reads the service card and goes on from `stage`: a gate with the
user's answer in chat continues past it; each card resumes through its own
Phase 0.

## 13. Report

In short bullets: each sub-issue with its PR and status; the unblock notes
and any shape change after a handoff; each QA round's verdict; what proof
leaves open; every `restaurant:` and `relay:` choice worth a look; the gate or
question the run stopped at.
