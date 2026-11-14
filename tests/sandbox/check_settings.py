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
#   gh: Seatbelt の下で TLS の検証に失敗しうる。使う形だけに絞る（gh gist などで秘密を外へ送らないため）
REQUIRED_EXCLUDED = {
    "git checkout *", "git switch *", "git merge *", "git rebase *", "git stash *",
    "git restore *", "git rm *", "git mv *", "git cherry-pick *", "git revert *",
    "git fetch *", "git pull *", "git push *", "gh pr *", "gh api *", "gh repo view *",
}
REQUIRED_ASK = {
    "Bash(git push*)", "Bash(npx *)", "Bash(rm -r*)",
    "Edit(./CLAUDE.md)", "Edit(~/.claude/CLAUDE.md)", "Edit(./docs/**)", "Edit(./.claude/**)",
}
REQUIRED_DENY = {
    "Bash(pnpm add *)", "Bash(pnpm remove *)", "Bash(pnpm install)", "Bash(pnpm install *)", "Bash(pnpm i)", "Bash(pnpm i *)", "Bash(pnpm dlx *)",
    "Bash(npm install)", "Bash(npm install *)", "Bash(npm i)", "Bash(npm i *)", "Bash(npm ci)", "Bash(npm ci *)",
    "Bash(npx -y *)", "Bash(npx --yes *)",
    "Bash(yarn add *)", "Bash(yarn install)", "Bash(yarn install *)", "Bash(yarn dlx *)",
    "Bash(bun add *)", "Bash(bun install)", "Bash(bun install *)", "Bash(bunx *)",
    "Bash(pip install *)", "Bash(pip3 install *)", "Bash(brew install *)",
    "Bash(printenv)", "Bash(printenv *)", "Bash(env)",
    "Read(./.env*)", "Read(./**/.env*)", "Read(./*.env)", "Read(./**/*.env)", "Read(./**/*.pem)", "Read(./**/*.key)",
    "Read(~/.ssh/**)", "Read(~/.aws/**)", "Read(~/.claude/.credentials.json)",
    "Bash(rm -rf *)", "Bash(rm -fr *)",
    "Bash(git push --force*)", "Bash(git push -f*)", "Bash(git push * +*)", "Bash(git reset --hard*)", "Bash(git clean -f*)",
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
    """マスターの settings から、配置先の雛形にあるべき形を作る（違いはマスター専用の hook の登録だけ）。"""
    want = copy.deepcopy(settings)
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
    return f"雛形がマスターと {sorted(MASTER_ONLY_HOOKS)} の除外以外でも違う: {keys}"


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
    want = {
        "enabled": True,
        "autoAllowBashIfSandboxed": False,
        "allowUnsandboxedCommands": False,
        "failIfUnavailable": True,
    }
    bad = {k: sb.get(k) for k, v in want.items() if sb.get(k) is not v}
    return f"sandbox の値が違う: {bad}" if bad else None


def check_excluded(settings: dict, gated: set[str]) -> str | None:
    got = set(settings.get("sandbox", {}).get("excludedCommands", []))
    if got == REQUIRED_EXCLUDED:
        return None
    return f"excludedCommands が違う（無い: {sorted(REQUIRED_EXCLUDED - got)}・余分: {sorted(got - REQUIRED_EXCLUDED)}）"


def check_deny_read(settings: dict, gated: set[str]) -> str | None:
    fs = settings.get("sandbox", {}).get("filesystem", {})
    missing = REQUIRED_DENY_READ - set(fs.get("denyRead", []))
    return f"denyRead に無い: {sorted(missing)}" if missing else None


def check_domains(settings: dict, gated: set[str]) -> str | None:
    net = settings.get("sandbox", {}).get("network", {})
    got = set(net.get("allowedDomains", []))
    if got != REQUIRED_DOMAINS:
        return f"allowedDomains が違う: {sorted(got)}"
    return None if net.get("allowLocalBinding") is True else "allowLocalBinding が true でない（E2E の開発サーバーが動かない）"


def check_meta(settings: dict, gated: set[str]) -> str | None:
    if "$schema" not in settings:
        return "$schema が無い"
    if settings.get("permissions", {}).get("disableBypassPermissionsMode") != "disable":
        return "disableBypassPermissionsMode が disable でない"
    return None


def check_permissions(settings: dict, gated: set[str]) -> str | None:
    perms = settings.get("permissions", {})
    missing_ask = REQUIRED_ASK - set(perms.get("ask", []))
    missing_deny = REQUIRED_DENY - set(perms.get("deny", []))
    if missing_ask or missing_deny:
        return f"必須のルールが無い（ask: {sorted(missing_ask)}・deny: {sorted(missing_deny)}）"
    return None


def check_hooks(settings: dict, gated: set[str]) -> str | None:
    files = hook_files(settings)
    removed = files & REMOVED_HOOKS
    if removed:
        return f"削除した hook が登録されている: {sorted(removed)}"
    guards = {
        name
        for group in settings.get("hooks", {}).get("PreToolUse", [])
        if group.get("matcher") == "Bash"
        for name in hook_files({"hooks": group})
    }
    missing = {"guard-gated-write.sh", "guard-gated-delete.sh"} - guards
    return f"guard hook が PreToolUse の matcher Bash に無い: {sorted(missing)}" if missing else None


STOP_HOOKS = ("stop-typecheck.sh", "stop-test-gate.sh")
GATE_HOOK = ROOT / ".claude" / "hooks" / "stop-test-gate.sh"
GATE_TIMEOUT_RE = re.compile(r'^TIMEOUT="\$\{STOP_TEST_GATE_TIMEOUT:-(\d+)\}"', re.MULTILINE)


GATE_MARGIN = 10  # 打ち切った後の後片付け（kill・sleep 2・jq）と、計測の前の git・ハッシュの処理の分


def gate_inner_timeout(text: str | None = None) -> int | None:
    if text is None:
        text = GATE_HOOK.read_text(encoding="utf-8") if GATE_HOOK.exists() else ""
    m = GATE_TIMEOUT_RE.search(text)
    return int(m.group(1)) if m else None


def check_stop_hooks(settings: dict, gated: set[str], hook_text: str | None = None) -> str | None:
    """Stop に型検査とテストのゲートがあり、ゲートの hook の timeout が中の打ち切り時間より GATE_MARGIN 秒以上長い。"""
    timeouts = {
        name: h.get("timeout")
        for group in settings.get("hooks", {}).get("Stop", [])
        for h in group.get("hooks", [])
        for name in HOOK_PATH_RE.findall(h.get("command", ""))
    }
    missing = [n for n in STOP_HOOKS if n not in timeouts]
    if missing:
        return f"Stop に無い: {missing}"
    inner = gate_inner_timeout(hook_text)
    if inner is None:
        return f"{GATE_HOOK.name} に打ち切り時間（STOP_TEST_GATE_TIMEOUT の既定）の行が無い"
    outer = timeouts["stop-test-gate.sh"]
    if not isinstance(outer, int) or outer - inner < GATE_MARGIN:
        return f"stop-test-gate.sh の timeout {outer} が中の打ち切り {inner} 秒より {GATE_MARGIN} 秒以上長くない（時間切れが差し戻さないエラーになる）"
    return None


CHECKS: list[tuple[str, Callable[[dict, set[str]], str | None]]] = [
    ("(s) GATED_PATHS と permissions.ask の Edit(./...) が一致", check_s),
    ("(t) allow に Bash(git ...) が無い", check_t),
    ("(j) 効かない Write|NotebookEdit|MultiEdit(path) が無い", check_j),
    ("sandbox の enabled・autoAllowBashIfSandboxed・allowUnsandboxedCommands・failIfUnavailable", check_sandbox_flags),
    ("excludedCommands が決めたとおり", check_excluded),
    ("denyRead が揃っている", check_deny_read),
    ("allowedDomains と allowLocalBinding が決めたとおり", check_domains),
    ("$schema と disableBypassPermissionsMode", check_meta),
    ("必須の deny・ask が揃っている", check_permissions),
    ("guard hook が PreToolUse の matcher Bash にある", check_hooks),
    ("Stop に型検査とテストのゲートがあり、ゲートの timeout が中の打ち切りより長い", check_stop_hooks),
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
        ("flags-auto-allow", check_sandbox_flags, lambda s: s["sandbox"].update(autoAllowBashIfSandboxed=True)),
        ("excluded", check_excluded, lambda s: s["sandbox"]["excludedCommands"].remove("gh pr *")),
        ("excluded-extra", check_excluded, lambda s: s["sandbox"]["excludedCommands"].append("python3 *")),
        ("denyRead", check_deny_read, lambda s: s["sandbox"]["filesystem"]["denyRead"].remove("~/.ssh")),
        ("domains", check_domains, lambda s: s["sandbox"]["network"]["allowedDomains"].append("example.com")),
        ("local-binding", check_domains, lambda s: s["sandbox"]["network"].pop("allowLocalBinding")),
        ("meta", check_meta, lambda s: s.pop("$schema")),
        ("hooks", check_hooks, lambda s: s.update(hooks={})),
        ("hooks-event", check_hooks, lambda s: s["hooks"].update(PostToolUse=s["hooks"].pop("PreToolUse"))),
        ("hooks-matcher", check_hooks, lambda s: s["hooks"]["PreToolUse"][0].update(matcher="Edit")),
        ("permissions-deny", check_permissions, lambda s: s["permissions"]["deny"].remove("Bash(git reset --hard*)")),
        ("permissions-read", check_permissions, lambda s: s["permissions"]["deny"].remove("Read(~/.ssh/**)")),
        ("permissions-ask", check_permissions, lambda s: s["permissions"]["ask"].remove("Bash(git push*)")),
        ("stop-gate-missing", check_stop_hooks, lambda s: s["hooks"]["Stop"][0]["hooks"].pop()),
        ("stop-typecheck-missing", check_stop_hooks, lambda s: s["hooks"]["Stop"][0]["hooks"].pop(0)),
        ("stop-gate-timeout", check_stop_hooks, lambda s: s["hooks"]["Stop"][0]["hooks"][-1].update(timeout=120)),
        ("stop-gate-timeout-margin", check_stop_hooks, lambda s: s["hooks"]["Stop"][0]["hooks"][-1].update(timeout=155)),
    ]
    silent = [name for name, fn, broken in cases if fn(mutate(broken), gated) is None]
    if check_stop_hooks(settings, gated, hook_text="# 打ち切りの行が無い hook\n") is None:
        silent.append("stop-gate-no-inner-timeout")

    good = expected_template(settings)
    template_cases: list[tuple[str, Callable[[dict], None]]] = [
        ("template-flag", lambda t: t["sandbox"].update(failIfUnavailable=False)),
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
    print(f"{'FAIL' if problem else 'PASS'} 雛形とマスターの差がマスター専用の hook だけ")
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
