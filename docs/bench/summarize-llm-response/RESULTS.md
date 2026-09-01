# summarize-llm-response benchmark — results

- Date: 2026-09-01
- Skill under test: `summarize-llm-response` (output shape gate)
- Harness: `skills/summarize-llm-response/evals/` (`trigger.py`, `run.py` + `score.py`)
- Model: `claude-sonnet-5`
- Isolation: `--safe-mode` (behaviour) and `--setting-sources project --strict-mcp-config` (trigger), so the operator's own CLAUDE.md, skills, plugins and MCP servers are out of the picture

Two questions, measured separately, because a formatting skill can fail at either
one on its own: does it fire, and once fired does it produce the right shape?

## Headline — the skill does not self-trigger

`trigger.py`, 13 prompts (7 that should fire, 6 that should not), 2-3 trials each.

| condition | recall | false positives |
|---|---|---|
| description only — vague stub ("Use on any communication…") | 3/14 = 21% | 0/12 |
| description only — original explicit list of surfaces | 0/14 = 0% | 0/12 |
| description only — gate-framed, surfaces + exclusions | 0/21 = 0% | 0/18 |
| gate-framed description **+ a CLAUDE.md line naming the skill** | 13/14 = **93%** | 12/12 |

Three descriptions spanning vague, explicit and gate-framed all land at or near
zero. Claude sees the skill in its list and declines to invoke it: it does not
read "format your reply" as a task worth a tool call. Confirmed directly — with
the skill installed and no directive, the model produced a Linear issue draft
with no attribution tag, no `[Category]` title and no checklist.

**Rewriting the description is not the lever.** The skill needs a directive
naming it, or an explicit `/summarize-llm-response` call.

The cost of the directive is the fourth row: it fires on 12/12 of the prompts it
should skip, because "before any communication" carries no exclusions. That is
what the skill's `## First, check this applies` section is for — it bails out
after loading. Cases 7 and 8 below measure that bail-out, and it holds 12/12.

## Behaviour — with vs without

`run.py` + `score.py`, 8 cases × 2 arms × 3 trials. `with` injects the SKILL.md
body; `without` is the bare prompt. Same model, same isolation.

**Total: with 167/174 (96%), without 110/174 (63%).**

Assertions where the skill is doing the work (with → without):

| case | assertion | with | without |
|---|---|---|---|
| 1 | `tldr_present` / `tldr_is_last_section` | 3/3 | 0/3 |
| 1 | `within_line_budget` | 2/3 | 0/3 |
| 2 | `attribution_tag_present` | 3/3 | 0/3 |
| 2 | `action_items_as_checklist` | 3/3 | 0/3 |
| 2 | `title_has_category_prefix` | 3/3 | 0/3 |
| 4 | `section_update_tag_used` | 3/3 | 0/3 |
| 5 | `uses_mrkdwn_bold` | 3/3 | 0/3 |
| 6 | `title_verb_first`, `title_max_8_words` | 3/3 | 0/3 |
| 6 | `description_has_attribution` | 3/3 | 0/3 |

Ceilings, no discrimination: case 3 (factual one-liner) and cases 7-8 (commit
message, code-only) score 3/3 in both arms. The baseline already answers those
plainly, so the bail-out costs nothing but proves nothing either.

## What the run changed in the skill

Each of these was a measured failure, not a review opinion.

1. **Description was a one-line stub.** Replaced with the gate-framed version.
   Worth doing for the `/`-invoked path even though, per the headline, no
   description fixes triggering.
2. **"A line/sentence must have between 1 to 10 words."** Scored 0/2 in five of
   six cases in both arms — never once satisfied. It also contradicted the
   file's own `TL;DR: max 20 words` rule, and 5 of the skill's own 29 example
   lines broke it (16/29 broke the companion "warning above 5 words"). Raised to
   20 words, which agrees with the TL;DR cap and with every example in the file.
   Now 14/17 with the skill, 8/17 without. The tighter title caps (8 for
   Todoist, 10 for Linear) are stated in their own format sections and still
   win where they apply.
3. **"Every external post must include the tag"** contradicted the Slack section
   two screens down, which exempts Slack. Scoped to Linear/Todoist/Notion.
4. **No rule for drafting when the destination has no integration.** The model
   wrapped drafts in "here's the exact content I'd post", which leaked `**bold**`
   into a Slack draft and buried the attribution tag. Added a content-only rule.
5. **No bail-out.** Added, because the directive that makes the skill fire also
   makes it fire on every skip-list case.

## Known weak spots

- **`content_only_no_wrapper`, case 2: 1/3.** The model still prefaces drafts
  with "No Linear integration available — here's the exact content to submit."
  Partly the harness talking: safe mode has no Linear tool, so the
  runner has to tell the model so, and the model echoes it back. In real use the
  MCP server exists and the model posts directly. Real but amplified.
- **`content_only_no_wrapper`, case 6: 1/3.** Same cause as case 2.
- **`within_line_budget`, case 1: 2/3.** One 22-word summary line.
- **`no_markdown_bold`, case 5: 2/3.** One trial put a `**Channel:** #eng`
  header above the message — the wrapper again, leaking markdown into a Slack
  draft.

## Reproduce

```bash
cd skills/summarize-llm-response/evals
python3 trigger.py --trials 3 --model claude-sonnet-5
python3 trigger.py --trials 3 --model claude-sonnet-5 --memory
python3 run.py --trials 3 --model claude-sonnet-5
python3 score.py --model claude-sonnet-5
```
