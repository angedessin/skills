#!/usr/bin/env python3
"""settings.json の静的検査（課金なし・sandbox の外でも動く）。

Usage: mise exec -- pnpm run test:sandbox
       python3 tests/sandbox/check_settings.py --settings <file> --hook <guard-gated-write.sh> --template <file>

旧 check_asset_consistency.py の契約 (s)(t)(j) と、sandbox の設定の形を確かめる。
実際に sandbox の中で動くかは probe.py が確かめる。
Exit 0 = all pass. Exit 1 = failure.
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[2]
GATED_MARKER_RE = re.compile(r"^# GATED_PATHS:[ \t]*(.+)$", re.MULTILINE)

# sandbox の外に出す git の操作と gh。公式の記載と design.md の理由:
#   作業ツリーを書き換える操作: .claude/ の標準の書き込み禁止に当たる
#   fetch / pull / push: macOS では SSH のリモートが sandbox の中で失敗する
#   gh: Seatbelt の下で TLS の検証に失敗しうる
REQUIRED_EXCLUDED = {
    "git checkout *", "git switch *", "git merge *", "git rebase *", "git stash *",
    "git restore *", "git rm *", "git mv *", "git cherry-pick *", "git revert *",
    "git fetch *", "git pull *", "git push *", "gh *",
}
REQUIRED_DENY_READ = {"./**/.env*", "./**/*.env", "~/.ssh", "~/.aws"}
REQUIRED_DOMAINS = {"github.com", "*.github.com", "registry.npmjs.org"}
REMOVED_HOOKS = {"guard-env-read.sh"}
MASTER_ONLY_HOOKS = {"validate-skill-edit.sh"}
HOOK_PATH_RE = re.compile(r"\.claude/hooks/([\w.-]+)")


def ask_paths(settings: dict) -> set[str]:
    """permissions.ask の Edit(./...) を GATED_PATHS の書き方に直す。"""
    out = set()
    for rule in settings.get("permissions", {}).get("ask", []):
        m = re.fullmatch(r"Edit\(\./(.+)\)", rule)
        if m:
            out.add(re.sub(r"\*\*(/\*)?$", "", m.group(1)))
    return out


def rules(settings: dict) -> list[str]:
    perms = settings.get("permissions", {})
    return [r for key in ("allow", "ask", "deny") for r in perms.get(key, [])]


def hook_files(settings: dict) -> set[str]:
    return set(HOOK_PATH_RE.findall(json.dumps(settings.get("hooks", {}))))


def expected_template(settings: dict) -> dict:
    """マスターの settings から、配置先の雛形にあるべき形を作る（違いは決めた 2 点だけ）。"""
    want = copy.deepcopy(settings)
    want["sandbox"]["failIfUnavailable"] = False
    for groups in want.get("hooks", {}).values():
        for group in groups:
            group["hooks"] = [
                h for h in group["hooks"]
                if not set(HOOK_PATH_RE.findall(h.get("command", ""))) & MASTER_ONLY_HOOKS
            ]
    return want


def check_template(settings: dict, template: dict) -> str | None:
    if template == expected_template(settings):
        return None
    want = expected_template(settings)
    keys = sorted(k for k in want.keys() | template.keys() if want.get(k) != template.get(k))
    return f"雛形がマスターと決めた 2 点以外でも違う（failIfUnavailable: false と {sorted(MASTER_ONLY_HOOKS)} の除外だけのはず）: {keys}"


def check_s(settings: dict, gated: set[str]) -> str | None:
    asks = ask_paths(settings)
    return None if asks == gated else f"GATED_PATHS {sorted(gated)} と ask {sorted(asks)} が違う"


def check_t(settings: dict, gated: set[str]) -> str | None:
    bad = [r for r in settings.get("permissions", {}).get("allow", []) if re.match(r"Bash\(git\b", r)]
    return f"allow に git のルールがある: {bad}" if bad else None


def check_j(settings: dict, gated: set[str]) -> str | None:
    bad = [r for r in rules(settings) if re.match(r"(Write|NotebookEdit|MultiEdit)\(", r)]
    return f"効かないルールがある（ファイルの規則は Edit が覆う）: {bad}" if bad else None


def check_sandbox_flags(settings: dict, gated: set[str]) -> str | None:
    sb = settings.get("sandbox", {})
    want = {"enabled": True, "allowUnsandboxedCommands": False, "failIfUnavailable": True}
    bad = {k: sb.get(k) for k, v in want.items() if sb.get(k) is not v}
    return f"sandbox の値が違う: {bad}" if bad else None


def check_excluded(settings: dict, gated: set[str]) -> str | None:
    missing = REQUIRED_EXCLUDED - set(settings.get("sandbox", {}).get("excludedCommands", []))
    return f"excludedCommands に無い: {sorted(missing)}" if missing else None


def check_deny_read(settings: dict, gated: set[str]) -> str | None:
    fs = settings.get("sandbox", {}).get("filesystem", {})
    missing = REQUIRED_DENY_READ - set(fs.get("denyRead", []))
    return f"denyRead に無い: {sorted(missing)}" if missing else None


def check_domains(settings: dict, gated: set[str]) -> str | None:
    net = settings.get("sandbox", {}).get("network", {})
    got = set(net.get("allowedDomains", []))
    return None if got == REQUIRED_DOMAINS else f"allowedDomains が違う: {sorted(got)}"


def check_meta(settings: dict, gated: set[str]) -> str | None:
    if "$schema" not in settings:
        return "$schema が無い"
    if settings.get("permissions", {}).get("disableBypassPermissionsMode") != "disable":
        return "disableBypassPermissionsMode が disable でない"
    return None


def check_hooks(settings: dict, gated: set[str]) -> str | None:
    files = hook_files(settings)
    removed = files & REMOVED_HOOKS
    if removed:
        return f"削除した hook が登録されている: {sorted(removed)}"
    if not {"guard-gated-write.sh", "guard-gated-delete.sh"} <= files:
        return "guard hook 2 本のどちらかが登録されていない"
    return None


CHECKS: list[tuple[str, Callable[[dict, set[str]], str | None]]] = [
    ("(s) GATED_PATHS と permissions.ask の Edit(./...) が一致", check_s),
    ("(t) allow に Bash(git ...) が無い", check_t),
    ("(j) 効かない Write|NotebookEdit|MultiEdit(path) が無い", check_j),
    ("sandbox の enabled・allowUnsandboxedCommands・failIfUnavailable", check_sandbox_flags),
    ("excludedCommands が揃っている", check_excluded),
    ("denyRead が揃っている", check_deny_read),
    ("allowedDomains が決めたとおり", check_domains),
    ("$schema と disableBypassPermissionsMode", check_meta),
    ("guard hook の登録", check_hooks),
]


def self_test(settings: dict, gated: set[str]) -> list[str]:
    """壊した設定で検査が落ちることを確かめる（緑しか出ない検査を防ぐ）。"""

    def mutate(fn: Callable[[dict], None]) -> dict:
        broken = copy.deepcopy(settings)
        fn(broken)
        return broken

    cases: list[tuple[str, Callable[[dict, set[str]], str | None], Callable[[dict], None]]] = [
        ("s", check_s, lambda s: s["permissions"]["ask"].append("Edit(./extra/**)")),
        ("t", check_t, lambda s: s["permissions"].setdefault("allow", []).append("Bash(git status)")),
        ("j", check_j, lambda s: s["permissions"]["ask"].append("Write(./x)")),
        ("flags", check_sandbox_flags, lambda s: s["sandbox"].update(allowUnsandboxedCommands=True)),
        ("excluded", check_excluded, lambda s: s["sandbox"]["excludedCommands"].remove("gh *")),
        ("denyRead", check_deny_read, lambda s: s["sandbox"]["filesystem"]["denyRead"].remove("~/.ssh")),
        ("domains", check_domains, lambda s: s["sandbox"]["network"]["allowedDomains"].append("example.com")),
        ("meta", check_meta, lambda s: s.pop("$schema")),
        ("hooks", check_hooks, lambda s: s.update(hooks={})),
    ]
    silent = [name for name, fn, broken in cases if fn(mutate(broken), gated) is None]

    good = expected_template(settings)
    template_cases: list[tuple[str, Callable[[dict], None]]] = [
        ("template-flag", lambda t: t["sandbox"].update(failIfUnavailable=True)),
        ("template-deny", lambda t: t["permissions"]["deny"].pop()),
        ("template-hook", lambda t: t["hooks"].pop("Stop")),
    ]
    for name, breaker in template_cases:
        broken = copy.deepcopy(good)
        breaker(broken)
        if check_template(settings, broken) is None:
            silent.append(name)
    return silent


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--settings", type=Path, default=ROOT / ".claude" / "settings.json")
    parser.add_argument("--hook", type=Path, default=ROOT / ".claude" / "hooks" / "guard-gated-write.sh")
    parser.add_argument("--template", type=Path, default=ROOT / "templates" / "settings.template.json")
    args = parser.parse_args()

    settings = json.loads(args.settings.read_text(encoding="utf-8"))
    marker = GATED_MARKER_RE.search(args.hook.read_text(encoding="utf-8"))
    if not marker:
        print(f"FAIL {args.hook} に '# GATED_PATHS:' 行が無い")
        return 1
    gated = set(marker.group(1).split())

    failed = 0
    for label, check in CHECKS:
        problem = check(settings, gated)
        print(f"{'FAIL' if problem else 'PASS'} {label}")
        if problem:
            print(f"  {problem}")
            failed += 1

    template = json.loads(args.template.read_text(encoding="utf-8"))
    problem = check_template(settings, template)
    print(f"{'FAIL' if problem else 'PASS'} 雛形とマスターの差が決めた 2 点だけ")
    if problem:
        print(f"  {problem}")
        failed += 1

    if failed:
        print("SKIP self-test（上の失敗を先に直す）")
    else:
        silent = self_test(settings, gated)
        print(f"{'FAIL' if silent else 'PASS'} self-test: 壊した設定で検査が落ちる")
        if silent:
            print(f"  落ちなかった検査: {silent}")
            failed += 1

    print(f"\n{'NG' if failed else 'OK'}: {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
