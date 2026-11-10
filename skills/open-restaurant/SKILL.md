---
name: open-restaurant
description: Deliver a parent issue and every sub-issue under it by running each ticket's line through assembly-line, one recipe card and one PR ready for review per sub-issue. Reads every line first, seats the sub-issue cards across repos, cooks them, unblocks early across repos, and parks at the human gates the lines name. Use when the user names a parent issue, epic or story with sub-issues and wants all of it delivered, or says "open the restaurant".
---

# Open Restaurant

The parent issue is the order; each sub-issue is a dish. This session is the
kitchen's head: it never cooks a dish itself. It reads the line of the parent
and of every sub-issue, runs the parent's line through
`../assembly-line/SKILL.md`, and at the line's `{"group": "sub-issues"}` step
seats and cooks the sub-issues, each through its own line. Only the stages the
parent's line names run for the parent as a whole; the stage skills hold what
each one does. The state of the whole order lives in the service card, never in
a sub-issue's card.

Start sub-agents in the background where the runtime allows it, so cards in
different repos cook at the same time, and act on each one as it returns.

The run never merges without a human, and opens every PR ready for review,
never as a draft. Merging waits at the parent line's `merge` gate.

## Settings

Read the settings file as `../setup/references/config.md` says, current folder
first, then `$HOME`, then the default. The stages read the keys they need;
this skill reads the rest:

- `open-restaurant.repoByLabel` — map from a sub-issue label to the folder of
  the repo it works in. Default `{}`: take the repo from the sub-issue's own
  text.
- `open-restaurant.implementedState` — tracker state a sub-issue moves to once
  its PR is open. Default `In Review`; `''` means no move.
- `open-restaurant.doneState` — state a merged sub-issue, and a parent with no
  open criterion, moves to (through `merge`). Default `Done`.
- `open-restaurant.envName` — name of the QA env; `{parent}` stands for the
  parent identifier in lower case. Default `{parent}`.
- `open-restaurant.reviewChannel` — chat channel the review request goes to.
  Default `''`: no request.
- `open-restaurant.judgeModel` — model for the readiness judge (run through `judge`)
  and the contract (run through `contract`). Default `''`: the model this session runs on.
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
   labels, state, the branch name the tracker gives, every blocks /
   blocked-by relation, and the line comment (the last comment whose json
   block has `"format"` of `assembly-line/1`). An issue with no sub-issues
   runs alone through `../assembly-line/SKILL.md`, as one ticket.
2. Lines first. Stop before any card exists, with `runStatus: needs-input`
   and naming `plan-assembly-line`, when the parent has no line comment, when
   any sub-issue has no line comment, when a line fails `validate-line.py`
   (in `../assembly-line/scripts/`; write each line to `{scratch}` and run it
   on that file), or when the parent's line holds no `{"group": "sub-issues"}`.
   Gaps are never answered on the parent's behalf. Validate every line before
   any card exists.
3. The session runs from a folder that holds one checkout per repo, as
   `./<repo>/`. This skill never creates or removes a checkout or a git
   worktree; no `git worktree` anywhere. Map each sub-issue to its one repo:
   a repo its text names wins, else its label through
   `open-restaurant.repoByLabel`. A sub-issue with no repo, or with more than
   one, gets a `## Blocked <id>` comment naming why. One in a repo the section
   lists as out of scope stops the run with `runStatus: needs-input`. If a
   checkout is missing for any repo the sub-issues touch, stop and print the
   command the section's workspace entry names for making it.
4. Open the service card at `{cardsDir}/{parent-slug}.service.md`, where
   `{cardsDir}` is `feature-recipe.cardsDir`. If one exists, resume it, as
   section 7 says. A new one holds:

   ```markdown
   ---
   parent: '<identifier>'
   stage: ''            # the parent-line step in flight, or closed
   runStatus: 'running' # running | needs-input | blocked | gate | terminal
   runQuestion: ''      # the id in ## Open Questions that stopped the run
   gate: ''             # the gate name, while runStatus is gate
   qaRounds: 0
   fixChecks: 0
   ---

   ## Sub-issues
   | id | repo | branch | base | blocked by | line | card | status | PR |

   ## Unblock notes

   ## Decisions

   ## Open Questions
   ```

   The stages add their own sections, such as `## Contract`, `## QA` and
   `## Merge`. Log every choice this skill takes alone to `## Decisions` as
   `restaurant:`.

## 2. Run the parent's line

Follow `../assembly-line/SKILL.md` on the service card: its sections 1, 3, 4, 5
and 6, with the overrides below. The stages run only on the parent, so the
service card is the card.

- Its section 2 does not apply: the service card is the card.
- The `{"group": "sub-issues"}` step does not stop the read. The group step
  runs this skill's sections 3 to 6.
- Run only the stages the parent's line names, in its order.
- Log prefix: `restaurant:` in place of `line:`. Each stage still sees its own
  `restaurant:` mode, so `qa` runs its own fix rounds and human gate.
- Log each finished step as `restaurant: step <n>/<total> <stage> <verdict>`.
- A return whose `to` stage is not on the parent's line counts as its limit
  used: `past` decides. So `qa` `fail` to `code` goes past, and `merge`
  `threads-open` to `review-fix` stays at the merge gate with the open
  threads listed.
- `merge` has `gate: human`, so the run stops with `runStatus: gate`. On
  resume with approval, `merge` runs in this session with
  `open-restaurant.doneState` in place of `assembly-line.doneState`. On
  `merged`, delete each local `integration/<parent>` branch and set
  `stage: closed`.

## 3. Seat the cards

One card and one PR per sub-issue. Fill `## Sub-issues` first, one row per
sub-issue, then decide when each may start.

1. **Card.** Make each sub-issue's card as `../assembly-line/SKILL.md` section 2
   says, with `task` set to the sub-issue identifier. Add a `## Parent contract`
   section holding the contract entries where this sub-issue is producer or
   consumer; its `## Interfaces` must match them, and its `plan-code` stage
   logs any difference to `## Decisions`.
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
     blocker's unblock note reaches it, as section 5 says. Sub-issues in
     different repos run in parallel.
   - No blocker: it starts at once, subject to its repo being free.

## 4. Cook the cards

Run each card through `../assembly-line/SKILL.md` as written, on its own line
and in its repo's checkout, without its `merge`: the parent's line holds the
merge. Read the shared stage files once per session; for each later card, read
only its frontmatter to route it. On top of `assembly-line`:

- **Plating.** `prepare-pr` delivers one PR, no chunks, open and ready for
  review, never as a draft, from `{branch}` against base `{base}` (the default
  branch, or the blocker's branch when it stacks). Title starts with
  `{sub-issue id}`; the body names the sub-issue and the parent `{parent id}`.
  Put no closing word, such as `Closes` or `Fixes`, before an identifier: the
  parent's `merge` moves the sub-issue itself. Log it to `## Decisions` as
  `restaurant:`.
- **Review per PR.** `review-fix` runs for each PR the moment it is open, one
  per PR, as its own background sub-agent. Never batch PRs into one review and
  never wait for other cards: reviews of different PRs run at the same time.
- **PR to sub-issue.** Each PR links to its own sub-issue, never to the
  parent; the parent gets links only through the `proof` stage's parent
  comment. After `prepare-pr`, check through the tracker that the sub-issue
  shows the PR as an attachment; if not, attach the PR URL to it. Then move
  the sub-issue to `open-restaurant.implementedState` in place of
  `assembly-line.reviewState`, unless it is empty, and write the PR into its
  row.
- **Documentation** (`code-docs`). Tell the stage to skip `work-summary`; this
  session runs it once at the end, when `feature-recipe.runWorkSummary` says
  to. Tell it also to leave the tracker state alone: `merge` moves it to
  `open-restaurant.doneState`.
- **Lockfiles.** After a card changes a lockfile, do what the section's
  workspace entry says before the next card in that repo, or the `integrate`
  stage, starts.
- **Status.** When a card stops on `blocked` or `needs-input`, do not answer
  for it: mark its row, comment `## Blocked <id>` with the card's open
  question, and keep cooking every card that does not depend on it.

A card is finished when its PR's `review-fix` and the fixes it led to are
done. Mark the row `done`, then free the repo for the next card in it.

## 5. Early unblock

When B is blocked by A in another repo, B needs A's shapes, not A's code, so
it starts long before A's PR.

1. **The ask.** When A's `plan-code` stage starts, tell it who A blocks and
   what each needs, read from the parent's `## Contract` (A the producer, B a
   consumer). Besides `## Interfaces`, it writes, for each such B,
   `{scratch}/unblock/<A>-to-<B>.md` holding: the shapes B consumes, copied
   from A's `## Interfaces` and checked against the contract; each difference
   from the contract on its own line; and what B still cannot rely on, such as
   an endpoint not deployed until A's PR merges.
2. **Earliest point.** The end of A's `plan-code` stage is the earliest point,
   since A's names, signatures and files are fixed there. When the stage cannot
   give B what it needs — A's plan too vague, or a thing that only exists once
   A's code runs, such as a generated client — the note says so and names the
   later point at which A can: the end of A's `code` stage, or A's pushed
   branch. Ask again at that point, through the same file.
3. **Follow-up.** When a note leaves B a gap, ask the agent that wrote it a
   follow-up question, by continuing that sub-agent where the runtime allows it
   (in Claude Code, `SendMessage`), else by a new sub-agent that reads A's
   card. Never guess on B's behalf.
4. **The handoff.** Copy the note into B's card as
   `## Upstream interfaces (<A>)` before B's `plan-code` starts, log
   `restaurant: started <B> early on <A>'s interfaces` to B's `## Decisions`,
   and start B at once, beside A's writers. B's `plan-code` stage and both
   writers code to that section as fixed input; B's tests stub A's side at that
   shape and never call A's unfinished code. Record the note in the service
   card's `## Unblock notes`.
5. **A change.** A's agents never change a shape they handed off without
   saying so: the change goes into the unblock file as a new dated entry and
   into A's `## Decisions`. Read the file each time one of A's stages returns.
   On a change, update B's `## Upstream interfaces (<A>)` and tell B's current
   or next stage to adapt; if B already opened its PR, send B back to its
   `code` stage.
6. **Chains.** In a chain where A blocks B and B blocks C, C waits for B's
   note, which B writes at the end of its own `plan-code` stage, already built
   on A's note. Each hop happens at the earliest point, never at PR time.

## 6. Close the cards

Once no card can start or move:

1. **Unfinished park.** If any row is not `done`, write a park summary: each
   unfinished sub-issue, with the reason quoted from its latest `## Blocked`
   comment. Set `runStatus: gate`, `gate: unfinished`, and stop for the user.
   On approve, go on to the next step of the parent's line with the branches
   as they are; on cancel, leave the parent for a later run.
2. **Interfaces check.** Compare each producer's final `## Interfaces` with
   every note it sent. A mismatch nobody handled stops the run with
   `runStatus: needs-input`, naming both cards.
3. When every row is `done` and no mismatch stands, the group ends and the
   run goes on to the next step of the parent's line.

## 7. Stops and resume

The run stops only at a gate, at `blocked`, at `needs-input`, or at the end.
On a stop, write `stage`, `runStatus` and `gate` to the service card, and
report the question or the gate in chat. A gate stops with `runStatus: gate`.
Re-invoking this skill on the same parent reads the service card and goes on
after its last `restaurant: step` line, as `../assembly-line/SKILL.md` section 6
says: a gate with the user's answer in chat continues past it; each sub-issue
card resumes through its own line.

## 8. Report

In short bullets: each sub-issue with its PR and status; the unblock notes
and any shape change after a handoff; each QA round's verdict; what proof
leaves open; every `restaurant:` choice worth a look; the gate or question the
run stopped at.
