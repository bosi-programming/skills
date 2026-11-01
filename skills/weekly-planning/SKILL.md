---
name: weekly-planning
description: Plan the work week around the user's calendar. Counts the work days, reads meetings, fits tickets from the tracker and anything the user adds into the free time, never more than two tickets in progress at once and nothing on top of a meeting, then saves the plan to the folder or tool the settings file names. Use when the user asks to plan the week, "weekly planning", "plan my week" or "what should I work on this week".
---

You write a plan the user can follow hour by hour this week. Only real
meetings and real tickets go in it; nothing is invented.

## 1. Read settings

Read `../setup/references/config.md` and resolve these keys from the settings
file, current folder first, then `$HOME`, then the default:

- `weekly-planning.destination` — where the plan goes. A value that starts
  with `/` or `~` is a folder; anything else names an MCP server or CLI, such
  as `Todoist`, `Notion` or `Linear`. Default `''`: print the plan.
- `weekly-planning.source` — the tool and filter the tickets come from, such
  as `Linear: assigned to me, not done`. Default `''`: the session's tracker,
  open tickets assigned to the user.
- `weekly-planning.workHours` — the work window of each day. Default
  `09:00-18:00`.
- `weekly-planning.hoursPerPoint` — hours one estimate point stands for.
  Default `4`.
- `weekly-planning.maxTickets` — most tickets in progress at the same time.
  Default `2`.
- The `## weekly-planning` section of the settings file's body, if there is
  one: guidance on top of the rules below.

## 2. Pick the week

- On a Saturday or Sunday, plan next Monday to Friday.
- On a work day, plan from now to Friday; today starts at the current time,
  rounded up to the next half hour.
- A request that names a week wins.

## 3. Read the calendar

Use the calendar tool the session has. Without one, ask once for the
meetings and days off of the week, in a single question, and go on with the
answer.

- **Work days**: Monday to Friday, less any day with an all-day event for a
  holiday, day off, vacation or out of office.
- **Meetings**: every event inside `weekly-planning.workHours` that the user
  has not declined, with its start, end and title. Declined events and
  events marked free do not block time.

## 4. Gather the work

Take tickets from `weekly-planning.source`, then add whatever the user wrote
when calling the skill: more tickets, or other tasks with a length, such as
"1h for expenses". Do not ask what else to add.

- Order tickets by priority, then due date. A ticket the user named in the
  request goes first.
- Hours of a ticket: its estimate times `weekly-planning.hoursPerPoint`; an
  estimate already in hours stays as it is.
- Tickets with no estimate: ask once, in one numbered question listing all of
  them, how many hours each takes. Never guess.
- A task that is not a ticket is an extra. Extras need a length; ask in the
  same question for any that lacks one.

## 5. Fit the work

Write the input to a file in a temporary folder and run the bundled script.
`$SKILL_DIR` is the folder that holds this `SKILL.md`.

```bash
python3 "$SKILL_DIR/scripts/plan_week.py" week.json
```

Input:

```json
{
  "maxTickets": 2,
  "days": [{"date": "2026-11-02", "start": "09:00", "end": "18:00"}],
  "meetings": [{"date": "2026-11-02", "start": "10:00", "end": "10:30", "title": "Standup"}],
  "tickets": [{"key": "ABC-42", "title": "Fix partner sync timeout", "hours": 8}],
  "extras": [{"title": "Expenses", "hours": 1}]
}
```

`tickets` go in priority order. `maxTickets` is `weekly-planning.maxTickets`.
Each day's `start` and `end` come from `weekly-planning.workHours`, with
today's `start` moved to now.

The script returns `blocks`, each with `date`, `start`, `end`, `kind`
(`ticket` or `extra`), `title` and, for a ticket, `key`, and `unplanned`, with
the hours of each item that did not fit. It keeps these rules, so do not move
blocks by hand afterwards:

- No block overlaps a meeting.
- No more than `maxTickets` tickets are started and not finished at once; the
  next ticket starts only when one of them ends.
- Blocks last at most two hours, and gaps under 30 minutes stay empty.
- Extras go first, in the earliest free time, and do not count toward
  `maxTickets`.

## 6. Write the plan

```
# Week of {Monday, YYYY-MM-DD}

Work days: {n} ({days off, if any})
Free time: {h}h · Planned: {h}h · Meetings: {h}h

## Monday, 2026-11-02
- 09:00–10:00 ABC-42 Fix partner sync timeout
- 10:00–10:30 Meeting: Standup
- 10:30–12:30 ABC-51 Add retry metrics
- 14:00–15:00 Expenses

## Does not fit this week
- ABC-60 Remove legacy parser — 6h left
```

- Each day lists blocks and meetings in time order; days off say so in one
  line.
- Leave out the "Does not fit" section when everything fits.
- Run the plan through `summarize-llm-response` when the session has it; it
  adds the attribution line the destination needs.

## 7. Save

Save straight away. A request that says "show me first" shows the plan and
waits.

- **Folder**: write `{destination}/{Monday YYYY-MM-DD}.md`. If the file
  exists, ask before replacing it.
- **To-do tool** (such as Todoist): one task per work day, titled
  `Plan {weekday, YYYY-MM-DD}`, due that day, with that day's blocks as the
  body.
- **Docs or ticket tool** (such as Notion or Linear): one page or document
  holding the whole plan.
- **Empty**: print the plan.

Read what you saved back from the folder or tool and reply in one line:
`Saved to {destination}: {path, link or id}`. If saving fails, say what broke
in one line and print the whole plan so nothing is lost.
