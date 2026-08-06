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
  (a) expected_hooks() の全可能出力 ⊆ HOOK_REGISTRATIONS のキー、かつ
      HOOK_REGISTRATIONS に実ファイルの無い死んだ登録が無い（双方向）
  (b) expected_hooks() の全可能出力 ∪ MASTER_ONLY_HOOKS ≡ .claude/hooks/ の実ファイル
      → hook を 1 本足してどちらにも分類しなければ落ちる（分類漏れの検出）
  (c) README 全文の *.sh 言及集合 ≡ .claude/hooks/ の実ファイル
  (d) expected_hooks() の全可能出力 ⊆ docs/starter-kit.md 全文の *.sh 言及集合
  (e) マスター settings.json の各 permission ルールが DEPLOY_PERMISSIONS か
      MASTER_ONLY_PERMISSIONS に分類済み。逆方向（配布側にあってマスターに無い / マスターから
      消えたのに分類に残る）と 2 集合の重複も検査する
  (f) **マスター settings.json の hooks 登録 ≡ .claude/hooks/ の実ファイル**
      → hooks/ に置いて expected_hooks() にも README にも入れたが、settings.json への
        登録を忘れる = マスターで一度も発火しない、という片側修正を検出する
  (h) deploy_skills.MASTER_ONLY ≡ validate_skills.MASTER_ONLY
      → 配布分類が 2 ファイルに独立定義されている。片方への足し忘れは
        「配布してはいけないスキルが配布可能になる」に直結する
  (j) マスター settings / DEPLOY / MASTER_ONLY に Write|NotebookEdit|MultiEdit の
      **パス付き**規則が無い（Claude Code は Edit(path)/Read(path) のみ参照。死んだ規則は
      起動時警告になる。ツール名のみの Write は対象外）

  会社向け持ち出しセット用の契約 (g)(i) は 20260730 Frozen handoff で除去済み。

契約 (c)(d) が「集合比較」なのは書式非依存にするため。README のツリーを構文解析すると
書式変更で壊れる。全文から *.sh を拾って集合で比べれば、ツリーに書こうが散文に書こうが拾える。
(d) だけ包含（⊆）なのは、starter-kit の *.sh 言及が手順 6 以外にも存在するため
（節境界のパースを避ける。等価にすると節の挿入で偽 PASS を生む）。

**終了コードの優先順位**: FAIL が 1 件でもあれば 1。2 を返すのは走査の前提そのものが崩れている場合だけ。

使い方:
  python3 scripts/check_asset_consistency.py            # 全契約を検査
  python3 scripts/check_asset_consistency.py --verbose  # PASS の内訳も表示
終了コード: 0 = 全 PASS / 1 = 契約違反あり / 2 = 走査の前提が崩れている
"""
from __future__ import annotations

import argparse
import json
import re
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
    from deploy_skills import MASTER_ONLY as DEPLOY_MASTER_ONLY  # noqa: E402
except ImportError as e:  # pragma: no cover - 実行環境の異常のみ
    print(f"ERROR: deploy_skills.py を読み込めない: {e}", file=sys.stderr)
    sys.exit(2)

SH_RE = re.compile(r"[A-Za-z0-9_-]+\.sh")

PASS, FAIL, SKIP = "PASS", "FAIL", "SKIP"


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


def registered_hooks(settings_path: Path) -> set[str]:
    """settings.json（または settings.example.json）が登録している hook 名。

    「何を配ると宣言しているか」「何を発火させると宣言しているか」の機械可読な一次情報。
    """
    if not settings_path.is_file():
        return set()
    try:
        cfg = json.loads(settings_path.read_text(encoding="utf-8")).get("hooks", {})
    except json.JSONDecodeError:
        return set()
    names: set[str] = set()
    for entries in cfg.values():
        for entry in entries:
            for h in entry.get("hooks", []):
                names.update(SH_RE.findall(h.get("command", "")))
    return names


def master_permissions() -> dict:
    if not SETTINGS.exists():
        die(f"settings.json が無い: {SETTINGS}")
    try:
        cfg = json.loads(SETTINGS.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        die(f"settings.json が JSON として読めない: {e}")
    if "permissions" not in cfg:
        die("settings.json に permissions セクションが無い（走査の前提が崩れている）")
    return cfg["permissions"]


# ---- 契約 ----------------------------------------------------------------


def contract_a() -> tuple[str, list[str]]:
    sends = all_possible_sends()
    missing = sorted(sends - set(HOOK_REGISTRATIONS))
    dead = sorted(set(HOOK_REGISTRATIONS) - actual_hooks())
    details = []
    if missing:
        details.append(f"同送するのに HOOK_REGISTRATIONS に登録が無い: {', '.join(missing)}")
        details.append("→ deploy_guardrails() が KeyError で落ちる（配置が全滅する）")
    if dead:
        details.append(f"HOOK_REGISTRATIONS にあるが実ファイルが無い（死んだ登録）: {', '.join(dead)}")
    return (FAIL, details) if details else (PASS, [f"同送 {len(sends)} 本すべて登録済み・死んだ登録なし"])


def contract_b() -> tuple[str, list[str]]:
    classified = all_possible_sends() | set(MASTER_ONLY_HOOKS)
    actual = actual_hooks()
    details = []
    if actual - classified:
        details.append(f"分類されていない hook: {', '.join(sorted(actual - classified))}")
        details.append("→ expected_hooks() に足すか MASTER_ONLY_HOOKS に入れるかを決める")
    if classified - actual:
        details.append(f"分類にあるが実ファイルが無い: {', '.join(sorted(classified - actual))}")
    if details:
        return FAIL, details
    return PASS, [
        f"実ファイル {len(actual)} 本すべて分類済み"
        f"（同送 {len(all_possible_sends())} / master-only {len(MASTER_ONLY_HOOKS)}）"
    ]


def contract_c() -> tuple[str, list[str]]:
    if not README.exists():
        die(f"README が無い: {README}")
    mentioned = sh_mentions(README)
    actual = actual_hooks()
    details = []
    if actual - mentioned:
        details.append(f"README に載っていない hook: {', '.join(sorted(actual - mentioned))}")
    if mentioned - actual:
        details.append(f"README にあるが実在しない hook: {', '.join(sorted(mentioned - actual))}")
    return (FAIL, details) if details else (PASS, [f"README の記述 {len(mentioned)} 件が実ファイルと一致"])


def contract_d() -> tuple[str, list[str]]:
    if not STARTER_KIT.exists():
        die(f"starter-kit が無い: {STARTER_KIT}")
    missing = sorted(all_possible_sends() - sh_mentions(STARTER_KIT))
    if missing:
        return FAIL, [
            f"配置手順に載っていない同送 hook: {', '.join(missing)}",
            "→ 手動配置する人がこの hook を配らない（deploy_skills.py は配るので手順とズレる）",
        ]
    return PASS, [f"同送 {len(all_possible_sends())} 本すべて配置手順に記載あり"]


def contract_e() -> tuple[str, list[str]]:
    master = master_permissions()
    details = []
    for key in ("allow", "ask", "deny"):
        m = set(master.get(key, []))
        dep = set(DEPLOY_PERMISSIONS.get(key, []))
        mo = set(MASTER_ONLY_PERMISSIONS.get(key, []))
        if m - dep - mo:
            details.append(f"[{key}] マスターにあるが未分類: {', '.join(sorted(m - dep - mo))}")
            details.append("  → DEPLOY_PERMISSIONS か MASTER_ONLY_PERMISSIONS に入れる")
        if dep - m:
            details.append(f"[{key}] 配布側にあるがマスターに無い（ドリフト）: {', '.join(sorted(dep - m))}")
        if mo - m:
            details.append(f"[{key}] master-only 分類に残っているがマスターに無い（死んだ分類）: {', '.join(sorted(mo - m))}")
        if dep & mo:
            details.append(f"[{key}] 配布と master-only の両方に入っている: {', '.join(sorted(dep & mo))}")
    if details:
        return FAIL, details
    total = sum(len(master.get(k, [])) for k in ("allow", "ask", "deny"))
    return PASS, [f"マスターの {total} ルールすべて分類済み・ドリフト/死んだ分類/重複なし"]


def contract_f() -> tuple[str, list[str]]:
    """マスター settings.json の hooks 登録 ≡ .claude/hooks/ の実ファイル。

    hooks/ に置いて expected_hooks() にも README にも入れたが settings.json への登録を
    忘れる = マスターで一度も発火しない、という片側修正を塞ぐ。20260726 のレビューで
    「この経路が無検査だった」と指摘されて追加した（手作業で 1 回確認しただけで
    契約として encode していなかった）。
    """
    reg = registered_hooks(SETTINGS)
    actual = actual_hooks()
    details = []
    if reg - actual:
        details.append(f"settings.json に登録があるのにファイルが無い: {', '.join(sorted(reg - actual))}")
    if actual - reg:
        details.append(f"ファイルがあるのに settings.json に登録が無い: {', '.join(sorted(actual - reg))}")
        details.append("→ マスターで一度も発火しない（置いただけで効いていない）")
    return (FAIL, details) if details else (PASS, [f"hooks 登録 {len(reg)} 件が実ファイルと一致"])


def contract_h() -> tuple[str, list[str]]:
    """master-only スキルの分類が 2 ファイルで一致しているか。

    `MASTER_ONLY` は deploy_skills.py（誤配置の防止）と validate_skills.py（--portability の
    走査除外）に**独立して定義**されている。用途が違うので統合はしないが、片方に新しい
    master-only スキルを足し忘れると「配布してはいけないスキルが配布可能になる」か
    「portability 検査が誤った対象を走査する」。値の集合の片側修正は grep でも静的検査でも
    検出されないため（どちらも自分の中では整合している）、突合をここに置く。

    import による単一化はしない: validate_skills.py は PostToolUse hook が --skill で呼ぶ
    最も頻繁に走る経路で、そこに deploy_skills への import 依存を足すと片方の破損がもう片方を
    巻き込む。「スクリプトは依存ゼロ」の規約にも反する。
    """
    try:
        import validate_skills  # noqa: PLC0415 - 突合のためだけに読む
    except ImportError as e:
        return FAIL, [f"validate_skills.py を読み込めない: {e}"]
    d_only = set(DEPLOY_MASTER_ONLY)
    v_only = set(validate_skills.MASTER_ONLY)
    if d_only != v_only:
        details = []
        if d_only - v_only:
            details.append(f"deploy_skills.py にのみある: {', '.join(sorted(d_only - v_only))}")
        if v_only - d_only:
            details.append(f"validate_skills.py にのみある: {', '.join(sorted(v_only - d_only))}")
        details.append("→ 分類の一次情報は docs/starter-kit.md の選定表。両方を揃える")
        return FAIL, details
    return PASS, [f"master-only スキル {len(d_only)} 件が両ファイルで一致"]


DEAD_FILE_PATH_PERM_RE = re.compile(r"^(Write|NotebookEdit|MultiEdit)\(.+\)$")


def contract_j() -> tuple[str, list[str]]:
    """パス付き Write/NotebookEdit/MultiEdit は Claude Code が参照せず起動時警告になる。"""
    details: list[str] = []
    sources = [
        ("settings.json", master_permissions()),
        ("DEPLOY_PERMISSIONS", DEPLOY_PERMISSIONS),
        ("MASTER_ONLY_PERMISSIONS", MASTER_ONLY_PERMISSIONS),
    ]
    for label, perms in sources:
        for key in ("allow", "ask", "deny"):
            dead = sorted(r for r in perms.get(key, []) if DEAD_FILE_PATH_PERM_RE.match(r))
            if dead:
                details.append(f"[{label}/{key}] 死んだパス規則: {', '.join(dead)}")
                details.append("  → Edit(path) に置き換える（Edit が編集系ツールを覆う）")
    if details:
        return FAIL, details
    return PASS, ["settings / DEPLOY / MASTER_ONLY に死んだ Write|NotebookEdit|MultiEdit(path) なし"]


def main() -> None:
    ap = argparse.ArgumentParser(
        description="セットアップ資産どうしの契約突合（マスター専用）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="終了コード: 0 = 全 PASS / 1 = 契約違反あり / 2 = 走査の前提が崩れている",
    )
    ap.add_argument("--verbose", action="store_true", help="PASS の契約も内訳を表示する")
    args = ap.parse_args()

    if not HOOKS_DIR.is_dir():
        die(f"hooks ディレクトリが無い: {HOOKS_DIR}")

    contracts = [
        ("(a) 同送 hook が HOOK_REGISTRATIONS に登録済み", contract_a),
        ("(b) .claude/hooks/ の全ファイルが分類済み", contract_b),
        ("(c) README の hook 記述が実体と一致", contract_c),
        ("(d) 同送 hook が配置手順に記載済み", contract_d),
        ("(e) permissions が配布/マスター専用に分類済み", contract_e),
        ("(f) settings.json の hooks 登録が実体と一致", contract_f),
        ("(h) master-only スキルの分類が 2 ファイルで一致", contract_h),
        ("(j) 死んだ Write|NotebookEdit|MultiEdit(path) が無い", contract_j),
    ]

    failed = 0
    for label, fn in contracts:
        status, details = fn()
        print(f"{status}  {label}")
        if status == FAIL:
            failed += 1
        if status == FAIL or args.verbose:
            for d in details:
                print(f"      {d}")

    total = len(contracts)
    print()
    if failed:
        print(f"{total - failed}/{total} PASS — {failed} 件の契約違反")
        sys.exit(1)
    print(f"{total}/{total} PASS")


if __name__ == "__main__":
    main()
