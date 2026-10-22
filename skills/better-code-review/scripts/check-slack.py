import re
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
REPO = SKILL.parents[1]
SKILL_MD = SKILL / "SKILL.md"
README = REPO / "README.md"

results = []


def check(name, ok, detail=""):
    results.append((name, bool(ok), detail))


def read(path):
    return path.read_text() if path.exists() else ""


def flatten(text):
    return " ".join(text.split()).lower()


def block(text, start, stop_pattern):
    begin = text.find(start)
    if begin < 0:
        return ""
    rest = text[begin + len(start):]
    stop = re.search(stop_pattern, rest, re.MULTILINE)
    return rest[:stop.start()] if stop else rest


def check_all(name, text, *phrases):
    lowered = flatten(text)
    missing = [phrase for phrase in phrases if phrase.lower() not in lowered]
    check(name, not missing, f"missing: {missing}" if missing else "")


def check_none(name, text, *phrases):
    lowered = flatten(text)
    present = [phrase for phrase in phrases if phrase.lower() in lowered]
    check(name, not present, f"must not say: {present}" if present else "")


def frontmatter_description(text):
    match = re.search(r"^description:\s*(.+)$", text, re.MULTILINE)
    return match.group(1) if match else ""


skill = read(SKILL_MD)
readme = read(README)
slack = block(skill, "\n## Slack\n", r"^## ")
default_mode = block(skill, "\n## Default mode\n", r"^## ")
comment_rule = block(slack, "### What gets a comment", r"^### ")

check("slack-section", slack.strip(), "SKILL.md has no ## Slack section")
check_all("slack-entry", slack, "--slack", "slack.com/archives")
check_all("slack-runs-headless", slack, "_headless_", "never asks")
check_all("slack-reads-message-only", slack, "only the linked message", "not the thread")
check_all("slack-fresh-clone", slack, "gh repo clone", "--filter=blob:none", "gh pr checkout", "base branch", "rm -rf")
check_all("slack-reads-config", slack, "../setup/references/config.md")
check_all("slack-review-mode", slack, "`better-code-review.reviewmode`", "`fast`", "`slow`", "lockfile", "not verified")
setup_files = [SKILL.parent / "setup" / name for name in ["SKILL.md", "references/config.md", "assets/bosi-skills.md", "scripts/check-config.py"]]
check_none("no-repos-dir", skill + readme + "".join(read(path) for path in setup_files), "reposdir")
check_all("slack-skips", slack, "closed", "merged", "your own", "already approved")
check_all("slack-comment-kinds", comment_rule, "`missing`", "`scope creep`", "`wrong`", "standards", "tests", "`hard`")
check_none("slack-no-soft-comments", comment_rule.replace("never get a comment", ""), "`judgement call` gets", "`missing test` gets")
check_all("slack-soft-excluded", comment_rule, "`judgement call`", "`missing test`", "never get a comment")
check_all("slack-one-review", slack, "\"event\": \"comment\"", "inline", "body of the review")
check_all("slack-body-only-findings", slack, "nothing the pr's author cannot act on", "no summary", "no count", "leave the body empty")
check_all("slack-approve", slack, "gh pr review", "--approve", "no finding")
check_all("slack-verifies-post", slack, "--input", "verify")
check_all("slack-reaction-browser", slack, "claude-in-chrome", "`better-code-review.commentreaction`", "`better-code-review.approvereaction`")
check_all("slack-one-reaction", slack, "one reaction per message", "any pr")
check_all("slack-reaction-fallback", slack, "not added")
check_all("slack-reply", slack, "reaction:", "skipped:")
check_all("default-mode-names-slack", default_mode, "slack")

check_all("description-slack", frontmatter_description(skill), "slack")
paragraph = block(readme, "### better-code-review", r"^### ")
check_all("readme-paragraph", paragraph, "--slack")
check_all("readme-validate-command", block(readme, "## Validate a change", r"^## "), "check-slack.py")

width = max(len(name) for name, _, _ in results)
for name, ok, detail in results:
    line = f"{'PASS' if ok else 'FAIL'}  {name.ljust(width)}"
    if detail and not ok:
        line += f"  {detail}"
    print(line)

failed = [name for name, ok, _ in results if not ok]
print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
sys.exit(1 if failed else 0)
