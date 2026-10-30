---
name: pause-work
description: Park half-done work for tomorrow as one task in the to-do list or tracker the settings file names, due the next day, holding the ticket key, working folder, what is left and open questions. Use when the user stops before the work is done and says "pause work", "park this", "continue tomorrow", or ends the day with work left.
---

You write the note the user reads tomorrow morning to pick the work back up.
Facts only, nothing invented, short enough to read in a minute.

## 1. Read the settings

Read `../setup/references/config.md` and resolve these keys from the settings
file, current folder first, then `$HOME`, then the default:

- `pause-work.destination` — the to-do or ticket tool the task goes to: the
  name of an MCP server or a CLI, such as `Todoist`, `Linear` or `gh`. Default
  `''`: if the session has exactly one to-do or tracker tool, ask once whether
  to use it; if it has none or the user says no, print the task for the user to
  copy.
- `pause-work.project` — project, list or team in that tool. Default `''`, the
  tool's inbox or default project.
- `pause-work.due` — due date, in the words the tool takes. Default `tomorrow`.
- `pause-work.labels` — labels added to the task. Default `[]`.
- The `## pause-work` section of the settings file's body, if there is one:
  guidance that applies on top of the rules below.

## 2. Gather the facts

Read them; do not take them from memory of the conversation.

- Folder: `pwd`, as an absolute path. In a folder of several repos, list each
  repo the session touched.
- Branch and state: `git branch --show-current`, `git status -sb`,
  `git log -1 --oneline`. Not a git repo: write `not a git repo`.
- Ticket: look in the branch name, then the conversation, for keys of two to
  five capital letters, a hyphen and digits, such as `ABC-123`.
  - Exactly one: use it. Fetch its title and link with the tracker tool if the
    session has one.
  - More than one: ask which one the work is for.
  - None: write `none`. Never make one up.

## 3. Write the task

From the conversation, work out where the work stopped, what is left and what
is still open.

- **Title**: `{TICKET} {what is left}`, at most 8 words. No ticket: leave the
  key out.
- **Body**, these sections in this order:

~~~
Ticket: {KEY — title — link, or none}
Folder: {absolute path} ({branch}, {clean|N files changed, uncommitted})

Where it stopped:
{one or two lines: the last thing done and its state}

What's left:
- [ ] {the very next action, concrete enough to start without rereading}
- [ ] {each later step}

Open questions:
1. {a question only the user or someone else can answer, and who}
{or: none}
~~~

- An open question is something unknown, not a step. A choice the user still
  has to make, a reply someone owes, a test that fails for a reason not yet
  found.
- Run the body through `summarize-llm-response` when the session has it; it
  adds the attribution line the destination needs.
- Never put an API key, token or password in the task; write `[REDACTED]` and
  say in the reply that it should be rotated, without quoting it.

## 4. Save it

Save straight away; do not show a draft first. A request that says "ask me
first" or "show me first" shows the draft and waits.

- **To-do tool** (such as Todoist): create one task with the title, the body as
  its description, `pause-work.project`, `pause-work.due` and
  `pause-work.labels`.
- **Ticket tool** (such as Linear or GitHub): with a ticket key, add the body as
  a comment on that ticket, under a first line `Paused — next: {title}`. With no
  ticket, open a new issue with the title and body in `pause-work.project`, and
  set the due date when the tool has one.
- **No destination**: print the title and body in the reply.

## 5. Check it landed

Read the task or comment back from the tool. Reply with one line:
`Saved to {destination}: {link or id}`, and say whether it is a new task, a
comment or a new issue.

If the save fails, say what broke in one line and print the full title and
body so the work is not lost.

## Example

~~~
ABC-42 Finish retry backoff tests

Ticket: ABC-42 — Fix partner sync timeout — https://tracker.example/ABC-42
Folder: /home/dev/projects/partner-sync (fix/abc-42-backoff, 3 files changed, uncommitted)

Where it stopped:
Backoff is in PartnerSyncService.retry(); the circuit breaker test fails on the
fifth call.

What's left:
- [ ] Find why the breaker opens one call late in retry.spec.ts
- [ ] Lower the default timeout in config.yaml to 10s
- [ ] Commit and open the PR

Open questions:
1. Should the breaker reset after 30s or 60s? Ask the team lead.
~~~
