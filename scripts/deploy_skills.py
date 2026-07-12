#!/usr/bin/env python3
"""スキルの新規配置（マスター専用ツール・依存ゼロ）。

starter-kit.md「配置手順」の機械的な部分（手順 2・3・6 の一部・7）を確定的に実行する。
一次情報は starter-kit.md の手順 — このスクリプトと starter-kit の配置手順は
同一コミットで改訂する（片側修正の禁止）。判断と承認は skill-deploy スキルが担当し、
このスクリプトは指示された内容を書くだけ。

実行すること:
  1. スキル一式のコピー（.claude/skills/<name> → 配置先）
  2. frontmatter metadata への source-commit 打刻（マスター HEAD を自動取得）
  3. ガードレール同送: guard-env-read.sh（常に）・session-stop.sh（knowledge-capture 配置時のみ）
     - 配置先に settings.json が無い → permissions + 同送 hooks の登録を持つ settings.json を新規作成
     - 配置先に settings.json が有る → 何も書かず、手動マージ案（JSON 断片）を表示するだけ
  4. 配置先 .gitignore に .steering ランタイムフラグ 3 行を追記（無い場合のみ）
  5. マスターの deployments.md へ配置先を登録（未登録の場合のみ）

しないこと（skill-deploy が案内する残タスク）:
  - references の再生成 / 配置先 CLAUDE.md の発動ポリシー / 信頼ダイアログ / スモークテスト
  - 既存 settings.json への書き込み（マージは人間の判断）
  - 既存スキルの上書き（--overwrite 指定時のみ許可 — 再コピーは通常 skill-harvest の担当）

使い方:
  python3 scripts/deploy_skills.py <配置先パス> --skills name1,name2 [--dry-run] [--overwrite]
終了コード: 0 = 成功 / 2 = 実行エラー
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

MASTER_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = MASTER_ROOT / ".claude" / "skills"
REGISTRY = MASTER_ROOT / "deployments.md"

# 配布分類の一次情報は starter-kit.md の選定表。ここは誤配置を機械的に弾く安全弁のみ
MASTER_ONLY = {"skill-test", "skill-harvest", "skill-deploy"}

GITIGNORE_LINES = [
    "# .steering ランタイムフラグ（セッション状態。知識は md が持つ）",
    ".steering/**/.capture-needed",
    ".steering/**/.codify-needed",
    ".steering/**/capture_done",
]

HOOK_REGISTRATIONS = {
    "guard-env-read.sh": (
        "PreToolUse",
        {
            "matcher": "Bash",
            "hooks": [
                {
                    "type": "command",
                    "command": 'bash "$CLAUDE_PROJECT_DIR"/.claude/hooks/guard-env-read.sh',
                    "timeout": 10,
                }
            ],
        },
    ),
    "session-stop.sh": (
        "Stop",
        {
            "hooks": [
                {
                    "type": "command",
                    "command": 'bash "$CLAUDE_PROJECT_DIR"/.claude/hooks/session-stop.sh',
                }
            ]
        },
    ),
}


def die(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(2)


def master_head() -> str:
    r = subprocess.run(
        ["git", "-C", str(MASTER_ROOT), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        die(f"マスターの HEAD を取得できない: {r.stderr.strip()}")
    return r.stdout.strip()


def stamp_source_commit(skill_md: Path, head: str) -> None:
    """frontmatter の metadata: 配下に source-commit を追記/更新する。version は保持。"""
    text = skill_md.read_text(encoding="utf-8")
    if re.search(r"^\s*source-commit:", text, re.M):
        text = re.sub(r"^(\s*source-commit:\s*)\S+", rf"\g<1>{head}", text, count=1, flags=re.M)
    elif re.search(r"^metadata:\s*$", text, re.M):
        text = re.sub(r"^(metadata:\s*)$", rf"\1\n  source-commit: {head}", text, count=1, flags=re.M)
    else:
        # metadata ブロックが無い場合は frontmatter 末尾に足す
        text = re.sub(r"\n---\n", f"\nmetadata:\n  source-commit: {head}\n---\n", text, count=1)
    skill_md.write_text(text, encoding="utf-8")


def ensure_gitignore(target: Path, dry: bool, log: list[str]) -> None:
    gi = target / ".gitignore"
    existing = gi.read_text(encoding="utf-8") if gi.exists() else ""
    missing = [ln for ln in GITIGNORE_LINES[1:] if ln not in existing]
    if not missing:
        log.append(".gitignore: フラグ 3 行は登録済み（変更なし）")
        return
    log.append(f".gitignore: {len(missing)} 行追記 → {gi}")
    if not dry:
        block = "\n".join([GITIGNORE_LINES[0], *missing])
        gi.write_text(existing.rstrip("\n") + ("\n\n" if existing else "") + block + "\n", encoding="utf-8")


def deploy_guardrails(target: Path, skills: list[str], dry: bool, log: list[str]) -> None:
    hooks_src = MASTER_ROOT / ".claude" / "hooks"
    hooks_dst = target / ".claude" / "hooks"
    send = ["guard-env-read.sh"]
    if "knowledge-capture" in skills:
        send.append("session-stop.sh")  # .capture-needed を立てる hook。スキル無しで送ると実行不能指示になる

    for name in send:
        src = hooks_src / name
        if not src.exists():
            log.append(f"hooks: {name} がマスターに無い — スキップ（要確認）")
            continue
        log.append(f"hooks: {name} → {hooks_dst / name}")
        if not dry:
            hooks_dst.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, hooks_dst / name)

    master_settings = json.loads((MASTER_ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
    hooks_cfg: dict = {}
    for name in send:
        event, entry = HOOK_REGISTRATIONS[name]
        hooks_cfg.setdefault(event, []).append(entry)
    payload = {"permissions": master_settings["permissions"], "hooks": hooks_cfg}

    target_settings = target / ".claude" / "settings.json"
    if target_settings.exists():
        # 既存 settings には書き込まない — マージは人間の判断（deny は削らない・衝突は deny 優先）
        log.append("settings.json: 配置先に既存あり — 書き込まず、以下を手動マージすること:")
        log.append(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        log.append(f"settings.json: 新規作成 → {target_settings}")
        if not dry:
            target_settings.parent.mkdir(parents=True, exist_ok=True)
            target_settings.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )


def register_deployment(target: Path, dry: bool, log: list[str]) -> None:
    lines = REGISTRY.read_text(encoding="utf-8").splitlines() if REGISTRY.exists() else []
    if str(target) in [ln.strip() for ln in lines]:
        log.append(f"deployments.md: {target} は登録済み（変更なし）")
        return
    log.append(f"deployments.md: {target} を登録")
    if not dry:
        REGISTRY.write_text("\n".join([*lines, str(target)]) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description="スキルの新規配置（マスター専用）")
    ap.add_argument("target", help="配置先プロジェクトのルート（絶対パス推奨）")
    ap.add_argument("--skills", required=True, help="配置するスキル名（カンマ区切り）")
    ap.add_argument("--dry-run", action="store_true", help="書き込まず計画のみ表示")
    ap.add_argument("--overwrite", action="store_true", help="配置先に既存の同名スキルがあっても上書きする")
    args = ap.parse_args()

    target = Path(args.target).expanduser().resolve()
    skills = [s.strip() for s in args.skills.split(",") if s.strip()]

    if not target.is_dir():
        die(f"配置先が存在しない: {target}")
    if target == MASTER_ROOT:
        die("配置先がマスター自身。配置は別プロジェクトに対して行う")
    if not skills:
        die("--skills が空")
    for s in skills:
        if s in MASTER_ONLY:
            die(f"{s} はマスター専用（配布しない）。starter-kit の選定表を参照")
        if not (SKILLS_DIR / s / "SKILL.md").exists():
            die(f"マスターにスキルが無い: {s}")

    head = master_head()
    dry = args.dry_run
    log: list[str] = [f"{'[DRY-RUN] ' if dry else ''}配置先: {target}", f"source-commit: {head}"]

    dst_skills = target / ".claude" / "skills"
    for s in skills:
        dst = dst_skills / s
        if dst.exists() and not args.overwrite:
            die(f"配置先に {s} が既に存在する。再コピー（還元）は skill-harvest の担当。"
                f"意図的な上書きなら --overwrite を付ける")
        log.append(f"copy: {s} → {dst}")
        if not dry:
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(SKILLS_DIR / s, dst)
            stamp_source_commit(dst / "SKILL.md", head)

    deploy_guardrails(target, skills, dry, log)
    ensure_gitignore(target, dry, log)
    register_deployment(target, dry, log)

    print("\n".join(log))
    print()
    print("=== 残タスク（手動 — starter-kit.md 配置手順を参照） ===")
    regen = [s for s in skills if s in {"tdd", "test-review", "e2e", "review-ui"}]
    if regen:
        print(f"- references 再生成（配置先スタックに合わせる）: {', '.join(regen)}")
    print("- 配置先 CLAUDE.md に発動ポリシー節を作る（starter-kit の雛形から）")
    if (target / ".claude" / "settings.json").exists() and dry:
        pass  # dry-run では判定しない（上のログに出ている）
    print("- 配置先で対話セッションを起動して信頼ダイアログを承認する")
    print("- スモークテスト（starter-kit 手順 8）")
    sys.exit(0)


if __name__ == "__main__":
    main()
