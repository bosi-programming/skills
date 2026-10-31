# Slack mode

The `--slack` mode of `../SKILL.md`. _Headless_ and step 5 below are that file's.

Reviews every PR a Slack message links to, posts the result on GitHub, and
comments on the message. Start it with `--slack <link>`, or put a
`slack.com/archives/...` link in the request. A Slack run is one _Headless_
run per PR plus the posting: it never asks, and it posts without asking,
because naming the mode is the go-ahead.

### 1. Read the message

Take the channel ID and the timestamp from the link. In
`.../archives/C0123ABCD/p1729600000123456` the channel is `C0123ABCD` and the
timestamp is `1729600000.123456`: put a dot before the last six digits.

Read the message with the Slack MCP `slack_read_thread` and keep only the
linked message, not the thread. Replies tend to hold answers and PRs someone
already reviewed. Collect every `github.com/<owner>/<repo>/pull/<n>` URL in
its text, once each. If there is none, return
`review not run: no PR link in the message` and stop.

### 2. Pick the PRs to review

For each PR, run `gh pr view <url> --json state,author,headRefOid,baseRefName,reviews`
and skip it when:

- it is closed or merged;
- it is your own, its author being the login `gh api user --jq .login`
  returns, because GitHub refuses an approval of your own PR;
- it is already approved by you, a review of yours in state `APPROVED`.

A skipped PR gets no review and no say in the Slack comment. Note why it was
skipped for the reply.

### 3. Review each PR

Each PR gets a fresh clone of its repo, made for this review and deleted after
it. Never use a clone you find on the machine: its working tree is someone's
work in progress. Clone into the session scratchpad, or into `$(mktemp -d)`,
check the PR out and fetch the base branch:

```bash
gh repo clone "$OWNER/$REPO" "$CLONE" -- --filter=blob:none
git -C "$CLONE" fetch origin "$BASE"
(cd "$CLONE" && gh pr checkout "$NUMBER" --detach)
```

`--filter=blob:none` downloads file contents only when a command needs them,
so a large repo clones in seconds. A clone that fails skips the PR with the
reason `clone failed: <error>`.

Confirm `git -C "$CLONE" rev-parse HEAD` equals `headRefOid`, then run the
review as _Headless_ from the clone with `origin/<baseRefName>` as the fixed
point. The spec is the issue the PR description links to, else the key in the
PR title, as the top of `../SKILL.md` says. When the review is done,
`rm -rf "$CLONE"`.

A fresh clone has no installed dependencies. `better-code-review.reviewMode`,
read as [`../../setup/references/config.md`](../../setup/references/config.md)
says, decides what happens:

- `fast`, the default: install nothing. Checks that need dependencies land in
  `Not verified` with that reason, as step 5 says.
- `slow`: before the review, install with the package manager the lockfile
  names (`pnpm-lock.yaml` → `pnpm install --frozen-lockfile`,
  `yarn.lock` → `yarn install --frozen-lockfile`, `package-lock.json` →
  `npm ci`, `uv.lock` → `uv sync`, `poetry.lock` → `poetry install`). With no
  lockfile, or an install that fails, carry on as `fast` and put the reason
  in `Not verified`.

Review the PRs one after another, not in parallel. Each review starts three
sub-agents and runs the project's checks, and two at once fight over ports and
the machine. A review that returns `review not run: <reason>` counts as a
skipped PR with that reason.

### What gets a comment

From the headless blocks:

- **Spec:** `missing`, a requirement that is missing or partial; `scope creep`;
  `wrong`, a requirement implemented with a defect.
- **Standards:** `hard`, a hard violation.
- **Tests:** `hard`, a hard violation.

`judgement call` and `missing test` findings never get a comment. They stay
in the reply only.

### 4. Post on GitHub

A PR with at least one finding that gets a comment gets one review with
`"event": "COMMENT"`. A finding whose `file:line` falls on a line the PR diff
shows becomes an inline comment on that line. GitHub refuses a comment on a
line outside the diff, so every other finding goes in the body of the review,
with its `file:line` written out. Each comment reads `<axis> · <kind>`, then
the finding's `What:` and `Fix:` lines.

Post nothing the PR's author cannot act on. The body holds the findings with
no line in the diff and nothing else: no summary of the review, no count of
findings, no list of axes, no note on how the review ran. With every finding
inline, leave the body empty.

Write the review to a file in the scratchpad and post it with `--input`:

```json
{
  "commit_id": "<headRefOid>",
  "event": "COMMENT",
  "body": "<findings with no line in the diff, or empty>",
  "comments": [
    {"path": "src/a.ts", "line": 42, "side": "RIGHT", "body": "<axis> · <kind>\n<What>\n<Fix>"}
  ]
}
```

```bash
gh api "repos/$OWNER/$REPO/pulls/$NUMBER/reviews" --method POST --input "$REVIEW_FILE"
```

A PR with no finding that gets a comment is approved:

```bash
gh pr review "$URL" --approve
```

Verify each post landed before the next PR: the last review from
`gh api "repos/$OWNER/$REPO/pulls/$NUMBER/reviews"` is yours, on `headRefOid`,
in state `COMMENTED` or `APPROVED`. When a post fails, check this before
posting again, since a post that did land and is sent twice leaves two
reviews.

### 5. Comment on Slack

Post one short comment in English as a reply in the thread of the linked
message, with the Slack MCP `slack_send_message`: `channel_id` from the link
and `thread_ts` set to the message timestamp. Say only the outcome:

- any PR got a review with comments: `Reviewed, left comments on GitHub.`
- every PR reviewed was approved: `Reviewed and approved.`
- more than one PR with mixed outcomes: one line per PR, as
  `<PR url> — approved` or `<PR url> — commented`.

With no PR reviewed, post nothing. If a comment by you is already in the
thread for this run, do not post a second one. If the post fails, the reply
says the comment was not posted.

### Reply

```
<PR url> · commented <n> · <m> not posted
<PR url> · approved · <m> not posted
Not verified: <PR number>: <gap>, one per line, or none
Slack: comment posted | not posted — <reason>
Skipped: <PR url> — <reason>, one per line, or none
```

`not posted` counts the `judgement call` and `missing test` findings that
stayed off GitHub. Print nothing else.
