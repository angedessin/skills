#!/usr/bin/env python3
"""スキルの新規配置（マスター専用ツール・依存ゼロ）。

starter-kit.md「配置手順」の機械的な部分（手順 2・3・6 の一部・7）を確定的に実行する。
一次情報は starter-kit.md の手順 — このスクリプトと starter-kit の配置手順は
同一コミットで改訂する（片側修正の禁止）。判断と承認は skill-deploy スキルが担当し、
このスクリプトは指示された内容を書くだけ。

実行すること:
  1. スキル一式のコピー（.claude/skills/<name> → 配置先）
  2. frontmatter metadata への source-commit 打刻（マスター HEAD を自動取得）
  3. ガードレール同送: guard-env-read.sh（セキュリティ・常に）・
     post-edit-lint.sh / stop-typecheck.sh（品質ゲート・常に。両方フェイルオープン設計 —
     lint 設定や tsconfig.json が無いプロジェクトでは素通しなのでスタックを問わず配れる）・
     session-stop.sh（knowledge-capture 配置時のみ）
     - 配置先に settings.json が無い → permissions + 同送 hooks の登録を持つ settings.json を新規作成
     - 配置先に settings.json が有る → 何も書かず、手動マージ案（JSON 断片）を表示するだけ
  4. 配置先 .gitignore に .steering ランタイムフラグ 5 行を追記（無い場合のみ）
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
MASTER_ONLY = {"skill-test", "skill-harvest", "skill-deploy", "adr"}

GITIGNORE_LINES = [
    "# .steering ランタイムフラグ（セッション状態。知識は md が持つ）",
    ".steering/**/.capture-needed",
    ".steering/**/.codify-needed",
    ".steering/**/capture_done",
    ".steering/**/pr_capture_done",
    ".steering/.last-rule-audit",
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
    "guard-gated-write.sh": (
        "PreToolUse",
        {
            "matcher": "Bash",
            "hooks": [
                {
                    "type": "command",
                    "command": 'bash "$CLAUDE_PROJECT_DIR"/.claude/hooks/guard-gated-write.sh',
                    "timeout": 10,
                }
            ],
        },
    ),
    "guard-gated-delete.sh": (
        "PreToolUse",
        {
            "matcher": "Bash",
            "hooks": [
                {
                    "type": "command",
                    "command": 'bash "$CLAUDE_PROJECT_DIR"/.claude/hooks/guard-gated-delete.sh',
                    "timeout": 10,
                }
            ],
        },
    ),
    "post-edit-lint.sh": (
        "PostToolUse",
        {
            "matcher": "Edit|Write",
            "hooks": [
                {
                    "type": "command",
                    "command": 'bash "$CLAUDE_PROJECT_DIR"/.claude/hooks/post-edit-lint.sh',
                    "timeout": 30,
                }
            ],
        },
    ),
    "stop-typecheck.sh": (
        "Stop",
        {
            "hooks": [
                {
                    "type": "command",
                    "command": 'bash "$CLAUDE_PROJECT_DIR"/.claude/hooks/stop-typecheck.sh',
                    "timeout": 120,
                }
            ]
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
    "session-start-check.sh": (
        "SessionStart",
        {
            "hooks": [
                {
                    "type": "command",
                    "command": 'bash "$CLAUDE_PROJECT_DIR"/.claude/hooks/session-start-check.sh',
                    "timeout": 10,
                }
            ]
        },
    ),
}

# 同送しない hook とその理由。**expected_hooks() と対で「.claude/hooks/ の全ファイルの分類」を成す。**
# check_asset_consistency.py の契約 (b) が
#   expected_hooks() の全可能出力 ∪ MASTER_ONLY_HOOKS ≡ ls .claude/hooks/
# を検査するため、hook を 1 本足してどちらにも入れなければ検査が落ちる（分類漏れを機械が捕まえる）。
#
# 定数にしてある理由: 以前は expected_hooks() の docstring に散文で書かれていたため、
# 「配るべきなのに配られていない」と「意図的に配らない」を機械が区別できなかった。
MASTER_ONLY_HOOKS = {
    # 注入する本文がマスターの docs/knowledge/ のパスと内容に依存する。
    # 配置先には該当ファイルが無く、死んだ参照を注入することになる。
    "remind-config-docs.sh",
    # scripts/validate_skills.py に依存する。配置先にスクリプトが無いため
    # フェイルオープンで素通しし、置いても効かない。
    "validate-skill-edit.sh",
}

# 配置先に配る permissions の**ベースライン**。
#
# なぜマスターの settings.json をそのまま配らないか: マスターの permissions には
# 「このリポジトリはスキル定義の置き場で依存を増やさない」というマスター固有の方針が
# 混ざっている。それを配置先に押し付けると、配置直後から依存インストールが全部拒否される
# （配置先に settings.json が無い場合、この payload が丸ごと新規作成されるため）。
#
# なぜ「除外リスト」ではなく「配るものの列挙」か: 除外方式は新しい deny を足すたびに
# 除外判断が要り、判断し忘れると**配置先が壊れる方向**（フェイルオープン）に倒れる。
# 列挙方式なら、足し忘れは**配られない方向**（フェイルセーフ）に倒れる。
# 二重管理の腐りは check_asset_consistency.py の契約 (e) が双方向で検出する。
#
# **ベースラインであって最終形ではない。** 最終的なセキュリティルールは配布先に依存する
# （20260726 決定）。skill-deploy の dry-run 提示で配置先の事情に合わせて調整する。
DEPLOY_PERMISSIONS = {
    "allow": [
        "Bash(ls)",
        "Bash(ls *)",
        "Bash(git status*)",
        "Bash(git diff*)",
        "Bash(git log*)",
        "Bash(git show*)",
    ],
    "ask": [
        "Bash(git push*)",
        "Bash(npx *)",
        "Bash(rm -r*)",
        # ファイルパス規則は Edit(path) のみ（Write(path) は参照されず起動時警告。
        # Edit が Write / NotebookEdit 等の編集系を覆う — Claude Code permissions 正本）
        "Edit(./.claude/settings.json)",
        "Edit(./.claude/settings.local.json)",
        "Edit(./.claude/hooks/**)",
        "Edit(./CLAUDE.md)",
        # ディレクトリ配下は * / ** / **/* の 3 形式を並べる（単一形式では直下を取りこぼす）
        "Edit(./docs/knowledge/*)",
        "Edit(./docs/knowledge/**)",
        "Edit(./docs/knowledge/**/*)",
        "Edit(./docs/decisions/*)",
        "Edit(./docs/decisions/**)",
        "Edit(./docs/decisions/**/*)",
    ],
    "deny": [
        # 自動インストールを伴う実行（サプライチェーン対策）。依存管理そのものは止めない
        "Bash(pnpm dlx *)",
        "Bash(npx -y *)",
        "Bash(npx --yes *)",
        "Bash(yarn dlx *)",
        "Bash(bunx *)",
        # シークレットの読み取り（Bash / Read の両ツール分を揃える）
        "Bash(cat .env*)",
        "Bash(cat *.env)",
        "Bash(grep * .env*)",
        "Bash(grep * *.env)",
        "Bash(printenv)",
        "Bash(printenv *)",
        "Bash(env)",
        "Read(./.env*)",
        "Read(./**/.env*)",
        "Read(./*.env)",
        "Read(./**/*.env)",
        "Read(./**/*.pem)",
        "Read(./**/*.key)",
        "Read(~/.ssh/**)",
        "Read(~/.aws/**)",
        "Read(~/.claude/.credentials.json)",
        # 破壊的操作
        "Bash(rm -rf *)",
        "Bash(rm -fr *)",
        "Bash(git push --force*)",
        "Bash(git push -f*)",
        "Bash(git push * +*)",
        "Bash(git reset --hard*)",
        "Bash(git clean -f*)",
    ],
}

# マスターにしか置かない permission と、その理由。
# **DEPLOY_PERMISSIONS と対で「マスター settings.json の全ルールの分類」を成す。**
# check_asset_consistency.py の契約 (e) が双方向で検査する:
#   - マスターにあって両集合のどちらにも無いルール → 分類漏れ
#   - DEPLOY_PERMISSIONS にあってマスターに無いルール → 静かなドリフト
MASTER_ONLY_PERMISSIONS = {
    "ask": [
        # 配置先を超えたグローバルな副作用になる。配置先の settings が
        # ユーザーのホーム設定をゲートするのは越権
        "Edit(~/.claude/CLAUDE.md)",
    ],
    "deny": [
        # 配置先の**通常の依存管理**を止めてしまう。マスターは「依存を増やさない」方針だが、
        # それは配布対象ではない（配置先は普通に npm install する必要がある）
        "Bash(pnpm add *)",
        "Bash(pnpm remove *)",
        "Bash(pnpm install)",
        "Bash(pnpm install *)",
        "Bash(pnpm i)",
        "Bash(pnpm i *)",
        "Bash(npm install)",
        "Bash(npm install *)",
        "Bash(npm i)",
        "Bash(npm i *)",
        "Bash(npm ci)",
        "Bash(npm ci *)",
        "Bash(yarn add *)",
        "Bash(yarn install)",
        "Bash(yarn install *)",
        "Bash(bun add *)",
        "Bash(bun install)",
        "Bash(bun install *)",
        "Bash(pip install *)",
        "Bash(pip3 install *)",
        "Bash(brew install *)",
    ],
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
        log.append(".gitignore: フラグ 5 行は登録済み（変更なし）")
        return
    log.append(f".gitignore: {len(missing)} 行追記 → {gi}")
    if not dry:
        block = "\n".join([GITIGNORE_LINES[0], *missing])
        gi.write_text(existing.rstrip("\n") + ("\n\n" if existing else "") + block + "\n", encoding="utf-8")


def expected_hooks(skills: list[str] | set[str]) -> list[str]:
    """配置スキル一式に対して同送すべき hooks を返す。

    check_deploy_drift.py がこの関数を import して「配るべきなのに配置先に無い hook」を
    検出する。**同送リストの単一情報源** — ここを直せば配置側と検出側が同時に追随する
    （両者に同じリストを書くと片側修正で腐る。20260723 の敵対レビューで実際に起きた系統）。

    **新しい hook を .claude/hooks/ に追加したら、ここに載せるか MASTER_ONLY_HOOKS に
    入れるかをその場で決める。** どちらにも入れないと check_asset_consistency.py の
    契約 (b) が落ちる（分類漏れを機械が捕まえる）。

    master-only（意図的に同送しない）hook の一覧と理由は MASTER_ONLY_HOOKS を見る。
    以前はここに散文で書いていたが、それでは「配るべきなのに漏れた」と「意図的に配らない」を
    機械が区別できなかった（20260725 新設の guard-gated-write.sh が漏れ、20260726 まで
    気づかれなかった系統）。

    **返り値に入れた hook は HOOK_REGISTRATIONS にも登録すること。** 登録を忘れると
    deploy_guardrails() が KeyError で落ちる。契約 (a) がこれを検出する。
    """
    # 品質ゲート 2 本はフェイルオープンで常時同送。書き込み/削除ガードも常時同送だが意味が違う:
    # guard-gated-write.sh = ヒット時 ask（確認）。guard-gated-delete.sh = ヒット時 deny（硬拒否・配置先でも摩擦あり）。
    # どちらも抽出失敗・非対象形は沈黙。追加パッケージ無し（delete の JSON 抽出は python3 stdlib）。
    send = [
        "guard-env-read.sh",
        "guard-gated-write.sh",
        "guard-gated-delete.sh",
        "post-edit-lint.sh",
        "stop-typecheck.sh",
    ]
    skills = set(skills)
    if "knowledge-capture" in skills:
        send.append("session-stop.sh")  # .capture-needed を立てる hook。スキル無しで送ると実行不能指示になる
    # フラグを「読む側」。これが無いと .capture-needed / .codify-needed は立つだけで誰も拾わず、
    # knowledge-capture / compound の「セッション開始時にフラグがあれば起動」が配置先で永久に発火しない
    # （producer だけ配って consumer が欠ける片欠け）。.steering/ が無い環境では素通しするので同送して安全。
    if {"knowledge-capture", "compound", "steering", "design-doc"} & skills:
        send.append("session-start-check.sh")
    return send


def _append_or_merge_hook(hooks_cfg: dict, event: str, entry: dict) -> None:
    """同一 event+matcher の hooks を 1 エントリにマージして hooks_cfg に載せる。"""
    matcher = entry.get("matcher")
    entries = hooks_cfg.setdefault(event, [])
    for existing in entries:
        if existing.get("matcher") == matcher:
            existing.setdefault("hooks", []).extend(entry.get("hooks", []))
            return
    # 呼び出し元の entry を共有しない（後続マージで hooks を破壊しない）
    entries.append(
        {
            **{k: v for k, v in entry.items() if k != "hooks"},
            "hooks": list(entry.get("hooks", [])),
        }
    )


def deploy_guardrails(target: Path, skills: list[str], dry: bool, log: list[str]) -> None:
    hooks_src = MASTER_ROOT / ".claude" / "hooks"
    hooks_dst = target / ".claude" / "hooks"
    send = expected_hooks(skills)

    for name in send:
        src = hooks_src / name
        if not src.exists():
            log.append(f"hooks: {name} がマスターに無い — スキップ（要確認）")
            continue
        log.append(f"hooks: {name} → {hooks_dst / name}")
        if not dry:
            hooks_dst.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, hooks_dst / name)

    hooks_cfg: dict = {}
    for name in send:
        event, entry = HOOK_REGISTRATIONS[name]
        # 同一 event+matcher は 1 エントリに hooks をマージする。
        # PreToolUse の Bash を配列で分割すると、Claude Code が後段を落とす実測がある
        # （/hooks に guard-gated-delete が出ず deny が沈黙。20260807）。
        _append_or_merge_hook(hooks_cfg, event, entry)
    # マスターの settings.json をそのまま配らない（DEPLOY_PERMISSIONS の宣言を参照）
    payload = {"permissions": DEPLOY_PERMISSIONS, "hooks": hooks_cfg}

    target_settings = target / ".claude" / "settings.json"
    if target_settings.exists():
        # 既存 settings には書き込まない — マージは人間の判断（deny は削らない・衝突は deny 優先）
        log.append("settings.json: 配置先に既存あり — 書き込まず、以下を手動マージすること:")
        log.append(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        log.append(f"settings.json: 新規作成 → {target_settings}")
        # dry-run でも中身を出す。既存ありの分岐だけ payload を見せて新規作成の分岐で
        # 見せないと、**新規作成経路の内容を配置前に確認する手段が無くなる**
        # （実際、配布 permissions の検証手段が無いという欠陥として顕在化した）。
        if dry:
            log.append("settings.json: 上記パスに書き込む内容（dry-run のため未書き込み）:")
            log.append(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
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
