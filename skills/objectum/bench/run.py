#!/usr/bin/env python3
import argparse
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

BENCH = Path(__file__).resolve().parent
SKILL_DIR = BENCH.parent
SKILL_MD = SKILL_DIR / "SKILL.md"
STEPS_DIR = SKILL_DIR / "steps"
DEFAULT_MODEL = "opencode-go/deepseek-v4-pro"
CLEAN_BASE = Path("/tmp/oc-bench")

TASKS = ["1-unverifiable-green", "2-probe-residue", "3-factual-overclaim"]
CONDITIONS = ["with", "without"]
ENVS = ["clean", "realistic"]

STEP_FILES = [
    "1.putting-it-in-front.md",
    "2.what-it-gives.md",
    "3.your-own-affect.md",
    "4.judgement.md",
    "5.unveiling.md",
    "6.counter-unveiling.md",
]

BLOCK_RE = re.compile(
    r"1\. Run file `\$\{CLAUDE_SKILL_DIR\}/steps/1\.putting-it-in-front\.md`\n"
    r"2\. Run file `\$\{CLAUDE_SKILL_DIR\}/steps/2\.what-it-gives\.md`\n"
    r"3\. Run file `\$\{CLAUDE_SKILL_DIR\}/steps/3\.your-own-affect\.md`\n"
    r"4\. Run file `\$\{CLAUDE_SKILL_DIR\}/steps/4\.judgement\.md`\n"
    r"5\. Run file `\$\{CLAUDE_SKILL_DIR\}/steps/5\.unveiling\.md`\n"
    r"6\. Run file `\$\{CLAUDE_SKILL_DIR\}/steps/6\.counter-unveiling\.md`\n"
)


def build_with_block():
    skill = SKILL_MD.read_text()
    skill = BLOCK_RE.sub("The six passes are listed below, in order.\n", skill)
    steps = ["The six steps:", ""]
    for f in STEP_FILES:
        steps.append((STEPS_DIR / f).read_text().rstrip())
        steps.append("")
    return skill + "\n" + "\n".join(steps)


def prepare_clean_env():
    cfg = CLEAN_BASE / "config"
    data = CLEAN_BASE / "data"
    state = CLEAN_BASE / "state"
    (cfg / "opencode").mkdir(parents=True, exist_ok=True)
    (data / "opencode").mkdir(parents=True, exist_ok=True)
    state.mkdir(parents=True, exist_ok=True)
    (cfg / "opencode" / "opencode.json").write_text(
        '{"$schema": "https://opencode.ai/config.json"}'
    )
    auth = Path.home() / ".local/share/opencode/auth.json"
    if auth.exists():
        shutil.copy(auth, data / "opencode" / "auth.json")
    return cfg, data, state


def trial_dir(task, env, condition, model, trial):
    m = model.replace("/", "__")
    if env == "clean":
        root = CLEAN_BASE / "runs"
    else:
        root = BENCH / "runs"
    return root / task / env / condition / m / f"trial{trial}"


def run_trial(task_dir, dest, prompt, env, condition, trial, model, clean_env):
    dest.mkdir(parents=True, exist_ok=True)
    for p in (task_dir / "fixture").iterdir():
        if p.is_file():
            shutil.copy(p, dest)
    cmd = ["opencode", "run", prompt, "--format", "json", "--dir", str(dest), "--auto", "-m", model]
    e = dict(os.environ)
    if env == "clean":
        cfg, data, state = clean_env
        e["XDG_CONFIG_HOME"] = str(cfg)
        e["XDG_DATA_HOME"] = str(data)
        e["XDG_STATE_HOME"] = str(state)
    try:
        proc = subprocess.run(cmd, env=e, capture_output=True, text=True, timeout=600)
    except subprocess.TimeoutExpired:
        (dest / "stderr.log").write_text("TIMEOUT\n")
        return "timeout"
    (dest / "transcript.jsonl").write_text(proc.stdout or "")
    (dest / "stderr.log").write_text(proc.stderr or "")
    (dest / "meta.json").write_text(
        json.dumps(
            {
                "task": task_dir.name,
                "env": env,
                "condition": condition,
                "trial": trial,
                "model": model,
                "returncode": proc.returncode,
                "prompt": prompt,
            },
            indent=2,
        )
    )
    return "ok"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", nargs="*", default=TASKS)
    ap.add_argument("--env", nargs="*", default=ENVS)
    ap.add_argument("--condition", nargs="*", default=CONDITIONS)
    ap.add_argument("--trials", type=int, default=5)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--smoke", action="store_true", help="1 trial each, print manifest")
    args = ap.parse_args()

    with_block = build_with_block()
    clean_env = prepare_clean_env() if "clean" in args.env else None

    manifest_path = BENCH / "runs" / "manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
    else:
        manifest = []
    seen = {(m["task"], m["env"], m["condition"], m["trial"], m.get("model", DEFAULT_MODEL)) for m in manifest}

    trials = 1 if args.smoke else args.trials
    for task in args.task:
        task_dir = BENCH / "tasks" / task
        task_prompt = (task_dir / "prompt.txt").read_text().strip()
        for env in args.env:
            for condition in args.condition:
                for t in range(1, trials + 1):
                    key = (task, env, condition, t, args.model)
                    if key in seen:
                        print(f"skip {key}", flush=True)
                        continue
                    dest = trial_dir(task, env, condition, args.model, t)
                    if condition == "with":
                        prompt = (
                            "Apply the following instructions to yourself, then complete the task.\n\n"
                            + with_block
                            + "\n\nTASK:\n"
                            + task_prompt
                        )
                    else:
                        prompt = task_prompt
                    print(f"run {task} {env} {condition} {t} {args.model}", flush=True)
                    status = run_trial(task_dir, dest, prompt, env, condition, t, args.model, clean_env)
                    manifest.append(
                        {
                            "task": task,
                            "env": env,
                            "condition": condition,
                            "trial": t,
                            "model": args.model,
                            "dir": str(dest),
                            "status": status,
                        }
                    )
                    manifest_path.parent.mkdir(parents=True, exist_ok=True)
                    manifest_path.write_text(json.dumps(manifest, indent=2))
                    if args.smoke:
                        break

    print(f"\nmanifest: {manifest_path} ({len(manifest)} trials)")


if __name__ == "__main__":
    main()
