#!/usr/bin/env python3
"""セットアップ資産どうしの契約突合（マスター専用ツール・依存ゼロ）。

このリポジトリは「同じ情報が複数箇所にある」構造を繰り返し壊してきた。実例:

  20260723 `27c19ab` 「契約ズレ・片側修正 13 件を修正」というコミットが、
           session-start-check.sh を expected_hooks() に足しながら
           HOOK_REGISTRATIONS への登録を忘れ、配置を KeyError で全滅させた
  20260726 `b9b6a91` 「同送 hook の漏れ」をルールとして昇格させたコミットが、
           guard-gated-write.sh で **同じ漏れを 1 階層下で再発**させた

どちらも注意力の問題ではない。expected_hooks() は「単一情報源」として作られたのに、
実際には expected_hooks() の返り値と HOOK_REGISTRATIONS のキーという **2 つのリスト**が
あり、両者を突合するものが存在しなかった。ドキュメント（README・starter-kit）に至っては
実体との機械的な繋がりが一切なかった。

このスクリプトはその突合を機械化する。**人が「直したつもり」でも、片側だけ直したら落ちる。**

検査する契約:
  (a) expected_hooks() の全可能出力 ⊆ HOOK_REGISTRATIONS のキー
      → 同送するのに登録が無い = 配置が KeyError で落ちる
  (b) expected_hooks() の全可能出力 ∪ MASTER_ONLY_HOOKS ≡ .claude/hooks/ の実ファイル
      → hook を 1 本足してどちらにも分類しなければ落ちる（分類漏れの検出）
  (c) README 全文の *.sh 言及集合 ≡ .claude/hooks/ の実ファイル
      → ドキュメントに載っていない hook / 実在しない hook の記述を検出
  (d) expected_hooks() の全可能出力 ⊆ docs/starter-kit.md 全文の *.sh 言及集合
      → 配置手順に載っていない同送 hook を検出
  (e) マスター settings.json の各ルールが DEPLOY_PERMISSIONS か
      MASTER_ONLY_PERMISSIONS に分類済み **かつ** DEPLOY_PERMISSIONS ⊆ マスター
      → 分類漏れ（新ルールが無断で配られる/配られない）と静かなドリフトの両方向を検出
  (f) 持ち出しセットの hooks が、既知の変換規則で説明できない差分を持たない
      → master が塞いだ防御の欠陥が配布物側で開いたままになるのを検出
      （20260726 に guard-gated-write.sh が配布物から丸ごと欠けていた実例がある）

契約 (c)(d) が「集合比較」なのは書式非依存にするため。README のツリーを構文解析すると
書式変更で壊れる。全文から *.sh を拾って集合で比べれば、ツリーに書こうが散文に書こうが拾える。
(d) だけ包含（⊆）なのは、starter-kit の *.sh 言及が手順 6 以外にも存在するため
（節境界のパースを避ける。等価にすると節の挿入で偽 PASS を生む）。

使い方:
  python3 scripts/check_asset_consistency.py            # 全契約を検査
  python3 scripts/check_asset_consistency.py --verbose  # PASS の内訳も表示
終了コード: 0 = 全 PASS / 1 = 契約違反あり / 2 = 対象不在などの実行エラー
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

MASTER_ROOT = Path(__file__).resolve().parent.parent
HOOKS_DIR = MASTER_ROOT / ".claude" / "hooks"
SETTINGS = MASTER_ROOT / ".claude" / "settings.json"
README = MASTER_ROOT / "README.md"
STARTER_KIT = MASTER_ROOT / "docs" / "starter-kit.md"

sys.path.insert(0, str(MASTER_ROOT / "scripts"))
try:
    from deploy_skills import (  # noqa: E402
        DEPLOY_PERMISSIONS,
        HOOK_REGISTRATIONS,
        MASTER_ONLY_HOOKS,
        MASTER_ONLY_PERMISSIONS,
        expected_hooks,
    )
except ImportError as e:  # pragma: no cover - 実行環境の異常のみ
    print(f"ERROR: deploy_skills.py を読み込めない: {e}", file=sys.stderr)
    sys.exit(2)

SH_RE = re.compile(r"[A-Za-z0-9_-]+\.sh")


def die(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(2)


def all_possible_sends() -> set[str]:
    """expected_hooks() が返しうる hook の**全体**。

    条件分岐（knowledge-capture の有無・.steering 系スキルの有無）を素通りせず、
    全スキルを渡した場合の最大集合を取る。ここを「代表的なセット 1 つ」で代用すると、
    条件分岐の片方だけ壊れたときに検出できない。
    """
    skills_dir = MASTER_ROOT / ".claude" / "skills"
    all_skills = [p.name for p in skills_dir.iterdir() if p.is_dir()] if skills_dir.is_dir() else []
    return set(expected_hooks(all_skills))


def actual_hooks() -> set[str]:
    return {p.name for p in HOOKS_DIR.glob("*.sh")}


def sh_mentions(path: Path) -> set[str]:
    return set(SH_RE.findall(path.read_text(encoding="utf-8")))


def discover_export_hook_dirs() -> list[Path]:
    """git worktree を走査して `export/*/claude-config/hooks` を探す。

    持ち出しセットは別ブランチ（worktree）にしか存在せず、置き場所は環境ごとに違う。
    パスを固定で書くと環境依存になるため git に聞く（check_export_stopcontract.py と同じ方式）。
    """
    try:
        out = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            cwd=str(MASTER_ROOT), capture_output=True, text=True, check=False,
        ).stdout
    except OSError:
        return []
    dirs: list[Path] = []
    for ln in out.splitlines():
        if not ln.startswith("worktree "):
            continue
        wt = Path(ln[len("worktree "):].strip())
        for hooks in sorted(wt.glob("export/*/claude-config/hooks")):
            if hooks.is_dir():
                dirs.append(hooks)
    return dirs


def registered_hooks(hooks_dir: Path) -> set[str]:
    """持ち出しセットの settings.example.json が登録している hook 名。

    配布物が**自分で何を配ると宣言しているか**の機械可読な一次情報。
    「master の同送リスト」と比べると意図的な取捨選択まで差分になってしまうため、
    登録と実体の整合はこちらを基準にする。
    """
    example = hooks_dir.parent / "settings.example.json"
    if not example.is_file():
        return set()
    try:
        cfg = json.loads(example.read_text(encoding="utf-8")).get("hooks", {})
    except json.JSONDecodeError:
        return set()
    names: set[str] = set()
    for entries in cfg.values():
        for entry in entries:
            for h in entry.get("hooks", []):
                names.update(SH_RE.findall(h.get("command", "")))
    return names


def bundled_skill_names(hooks_dir: Path) -> set[str]:
    """持ち出しセットに同梱されているスキル名（hooks_dir から辿る）。"""
    skills = hooks_dir.parent.parent / "skills"
    return {p.name for p in skills.iterdir() if p.is_dir()} if skills.is_dir() else set()


def code_lines(path: Path) -> list[str]:
    """コメント行と空行を落とした「実行される行」だけを返す。

    配布加工でコメントが言い換えられるのは**想定内**（マスター固有のパス参照を外す・
    表現を一般化する）。守りたいのは判定ロジックそのものなので、比較対象をコードに絞る。
    """
    out = []
    for ln in path.read_text(encoding="utf-8").splitlines():
        s = ln.strip()
        if not s or s.startswith("#"):
            continue
        out.append(ln)
    return out


def strip_nonbundled(line: str, nonbundled: set[str]) -> str:
    """非同梱スキル名を、隣接する区切り（ ` / ` ）ごと除去する。

    配布版はセットに無いスキル名を理由文から外す（例: master の
    「knowledge-capture / compound / adr が」→ 配布版「knowledge-capture / compound が」）。
    これは既知の変換規則なので差分として数えない。語境界を見るので `adrenaline` は巻き込まない。
    """
    for name in sorted(nonbundled, key=len, reverse=True):
        esc = re.escape(name)
        line = re.sub(rf"\s*/\s*(?<![A-Za-z0-9-]){esc}(?![A-Za-z0-9-])", "", line)
        line = re.sub(rf"(?<![A-Za-z0-9-]){esc}(?![A-Za-z0-9-])\s*/\s*", "", line)
        line = re.sub(rf"(?<![A-Za-z0-9-]){esc}(?![A-Za-z0-9-])", "", line)
    return re.sub(r"\s+", " ", line).strip()


# ---- 契約 ----------------------------------------------------------------


def contract_a() -> tuple[bool, list[str]]:
    missing = sorted(all_possible_sends() - set(HOOK_REGISTRATIONS))
    if missing:
        return False, [
            f"同送するのに HOOK_REGISTRATIONS に登録が無い: {', '.join(missing)}",
            "→ deploy_guardrails() が KeyError で落ちる（配置が全滅する）",
        ]
    return True, [f"同送 {len(all_possible_sends())} 本すべて登録済み"]


def contract_b() -> tuple[bool, list[str]]:
    classified = all_possible_sends() | set(MASTER_ONLY_HOOKS)
    actual = actual_hooks()
    unclassified = sorted(actual - classified)
    phantom = sorted(classified - actual)
    details = []
    if unclassified:
        details.append(f"分類されていない hook: {', '.join(unclassified)}")
        details.append("→ expected_hooks() に足すか MASTER_ONLY_HOOKS に入れるかを決める")
    if phantom:
        details.append(f"分類にあるが実ファイルが無い: {', '.join(phantom)}")
    if details:
        return False, details
    return True, [f"実ファイル {len(actual)} 本すべて分類済み（同送 {len(all_possible_sends())} / master-only {len(MASTER_ONLY_HOOKS)}）"]


def contract_c() -> tuple[bool, list[str]]:
    if not README.exists():
        die(f"README が無い: {README}")
    mentioned = sh_mentions(README)
    actual = actual_hooks()
    details = []
    if actual - mentioned:
        details.append(f"README に載っていない hook: {', '.join(sorted(actual - mentioned))}")
    if mentioned - actual:
        details.append(f"README にあるが実在しない hook: {', '.join(sorted(mentioned - actual))}")
    if details:
        return False, details
    return True, [f"README の記述 {len(mentioned)} 件が実ファイルと一致"]


def contract_d() -> tuple[bool, list[str]]:
    if not STARTER_KIT.exists():
        die(f"starter-kit が無い: {STARTER_KIT}")
    mentioned = sh_mentions(STARTER_KIT)
    missing = sorted(all_possible_sends() - mentioned)
    if missing:
        return False, [
            f"配置手順に載っていない同送 hook: {', '.join(missing)}",
            "→ 手動配置する人がこの hook を配らない（deploy_skills.py は配るので手順とズレる）",
        ]
    return True, [f"同送 {len(all_possible_sends())} 本すべて配置手順に記載あり"]


def contract_e() -> tuple[bool, list[str]]:
    if not SETTINGS.exists():
        die(f"settings.json が無い: {SETTINGS}")
    master = json.loads(SETTINGS.read_text(encoding="utf-8"))["permissions"]
    details = []
    for key in ("allow", "ask", "deny"):
        m = set(master.get(key, []))
        dep = set(DEPLOY_PERMISSIONS.get(key, []))
        mo = set(MASTER_ONLY_PERMISSIONS.get(key, []))
        unclassified = sorted(m - dep - mo)
        drift = sorted(dep - m)
        if unclassified:
            details.append(f"[{key}] マスターにあるが未分類: {', '.join(unclassified)}")
            details.append("  → DEPLOY_PERMISSIONS か MASTER_ONLY_PERMISSIONS に入れる")
        if drift:
            details.append(f"[{key}] 配布側にあるがマスターに無い（ドリフト）: {', '.join(drift)}")
    if details:
        return False, details
    total = sum(len(master.get(k, [])) for k in ("allow", "ask", "deny"))
    return True, [f"マスターの {total} ルールすべて分類済み・配布側のドリフトなし"]


def contract_f() -> tuple[bool, list[str]]:
    dirs = discover_export_hook_dirs()
    if not dirs:
        die(
            "持ち出しセットの hooks が見つからない（export/*/claude-config/hooks）。\n"
            "  持ち出しセットは別ブランチの worktree にしかない。走査 0 件を「差分なし」と\n"
            "  報告すると偽グリーンになるためフェイルクローズする。\n"
            "  worktree が無い環境で本契約を飛ばしたい場合は、その旨を明示して別途実行すること。"
        )
    details: list[str] = []
    notes: list[str] = []
    checked = 0
    for hooks_dir in dirs:
        nonbundled = {p.name for p in (MASTER_ROOT / ".claude" / "skills").iterdir() if p.is_dir()}
        nonbundled -= bundled_skill_names(hooks_dir)
        export_names = {p.name for p in hooks_dir.glob("*.sh")}

        # 配布物が**自分で登録した** hook のファイルが存在するか。登録と実体の食い違いは
        # 配布物側の欠陥であり、意図的な取捨選択ではない（配置先で登録だけあって動かない）
        registered = registered_hooks(hooks_dir)
        for name in sorted(registered - export_names):
            details.append(f"{hooks_dir.name}: settings.example.json に登録があるのにファイルが無い: {name}")
        for name in sorted(export_names - registered):
            details.append(f"{hooks_dir.name}: ファイルがあるのに settings.example.json に登録が無い: {name}")

        # master の同送 hook で配布物に無いもの。**FAIL にはしない** — 持ち出しセットは
        # 配布先の事情でセットを取捨選択する（例: stop-typecheck.sh は Angular では
        # テンプレートを型チェックできず CI と重複するため意図的に外している）。
        # ただし「意図的な除外」と「新しい防御の入れ忘れ」は見た目が同じなので、
        # 人が確認できるよう必ず列挙する（20260726 に guard-gated-write.sh が
        # 丸ごと欠けていた実例がある — master が High として塞いだ迂回路が配布物では開いたまま）。
        for name in sorted(all_possible_sends() - export_names):
            notes.append(f"{name} は master の同送対象だが配布物に無い（意図的な除外か要確認）")

        for name in sorted(export_names):
            master_hook = HOOKS_DIR / name
            if not master_hook.exists():
                details.append(f"{name}: 配布物にあるがマスターに無い")
                continue
            checked += 1
            a = [strip_nonbundled(x, nonbundled) for x in code_lines(master_hook)]
            b = [strip_nonbundled(x, nonbundled) for x in code_lines(hooks_dir / name)]
            if a != b:
                details.append(f"{name}: 既知の変換規則で説明できないコード差分")
                for i, (x, y) in enumerate(zip(a, b)):
                    if x != y:
                        details.append(f"    master: {x[:100]}")
                        details.append(f"    export: {y[:100]}")
                        break
                if len(a) != len(b):
                    details.append(f"    行数が違う（master {len(a)} / export {len(b)}）")
    if details:
        return False, details + notes
    return True, [f"配布物 {checked} 本のコードがマスターと一致（コメントの配布加工は許容）"] + notes


CONTRACTS = [
    ("(a) 同送 hook が HOOK_REGISTRATIONS に登録済み", contract_a),
    ("(b) .claude/hooks/ の全ファイルが分類済み", contract_b),
    ("(c) README の hook 記述が実体と一致", contract_c),
    ("(d) 同送 hook が配置手順に記載済み", contract_d),
    ("(e) permissions が配布/マスター専用に分類済み", contract_e),
    ("(f) 配布物 hooks に未説明の差分が無い", contract_f),
]


def main() -> None:
    ap = argparse.ArgumentParser(
        description="セットアップ資産どうしの契約突合（マスター専用）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="終了コード: 0 = 全 PASS / 1 = 契約違反あり / 2 = 対象不在などの実行エラー",
    )
    ap.add_argument("--verbose", action="store_true", help="PASS の契約も内訳を表示する")
    args = ap.parse_args()

    if not HOOKS_DIR.is_dir():
        die(f"hooks ディレクトリが無い: {HOOKS_DIR}")

    failed = 0
    for label, fn in CONTRACTS:
        ok, details = fn()
        print(f"{'PASS' if ok else 'FAIL'}  {label}")
        if not ok:
            failed += 1
            for d in details:
                print(f"      {d}")
        elif args.verbose:
            for d in details:
                print(f"      {d}")

    print()
    if failed:
        print(f"{len(CONTRACTS) - failed}/{len(CONTRACTS)} PASS — {failed} 件の契約違反")
        sys.exit(1)
    print(f"{len(CONTRACTS)}/{len(CONTRACTS)} PASS")


if __name__ == "__main__":
    main()
