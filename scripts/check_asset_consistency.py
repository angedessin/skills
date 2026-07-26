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
  (g) 持ち出しセットの hooks が、既知の変換規則で説明できない差分を持たない
      → master が塞いだ防御の欠陥が配布物側で開いたままになるのを検出

契約 (c)(d) が「集合比較」なのは書式非依存にするため。README のツリーを構文解析すると
書式変更で壊れる。全文から *.sh を拾って集合で比べれば、ツリーに書こうが散文に書こうが拾える。
(d) だけ包含（⊆）なのは、starter-kit の *.sh 言及が手順 6 以外にも存在するため
（節境界のパースを避ける。等価にすると節の挿入で偽 PASS を生む）。

**終了コードの優先順位**: FAIL が 1 件でもあれば 1。対象不在（持ち出し worktree が無い等）は
その契約を SKIP にして他の契約の判定を通す — 契約 1 本の対象不在で全体を 2 にすると、
**他の契約の FAIL が握りつぶされて呼び出し側（hook）が無音になる**（20260726 のレビューで
検出した欠陥）。2 を返すのは走査の前提そのものが崩れている場合だけ。

使い方:
  python3 scripts/check_asset_consistency.py            # 全契約を検査
  python3 scripts/check_asset_consistency.py --verbose  # PASS の内訳も表示
  python3 scripts/check_asset_consistency.py --require-export
                                                        # 持ち出しセット不在を SKIP にせず FAIL にする
終了コード: 0 = 全 PASS（SKIP と WARN を含む）/ 1 = 契約違反あり / 2 = 走査の前提が崩れている
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

# 持ち出しセットが**意図的に**同送しない hook と、その理由。
#
# なぜマスター側に置くか: 持ち出しセットは配布先の事情でセットを取捨選択する立場であり
# （セキュリティルールは配布先に依存する・20260726 決定）、master が一律に FAIL を出すのは越権。
# 一方で「意図的な除外」と「新しい防御の入れ忘れ」は**見た目が同じ**なので、分類を宣言させないと
# 20260726 に実際に起きた「guard-gated-write.sh が配布物から丸ごと欠けていた」型を
# 検出できない（レビューで、その事故を再現しても 6/6 PASS になることが実測された）。
#
# **ここに無い欠落は FAIL になる。** 持ち出しセットが新たに hook を外す判断をしたら、
# ここに理由つきで足すこと。権威ある理由は持ち出しセットの settings.example.json の _comment。
EXPORT_INTENTIONAL_OMISSIONS = {
    # Angular ではテンプレートを型チェックできず CI と重複するため、会社セットでは外している
    "stop-typecheck.sh",
}

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


def bundled_skill_names(hooks_dir: Path) -> set[str]:
    """持ち出しセットに同梱されているスキル名（hooks_dir から辿る）。"""
    skills = hooks_dir.parent.parent / "skills"
    return {p.name for p in skills.iterdir() if p.is_dir()} if skills.is_dir() else set()


HEREDOC_RE = re.compile(r"<<-?\s*['\"]?([A-Za-z_][A-Za-z0-9_]*)['\"]?")


def code_lines(path: Path) -> list[str]:
    """「実行される行」だけを返す（コメント行と空行を落とす）。

    配布加工でコメントが言い換えられるのは**想定内**（マスター固有のパス参照を外す・
    表現を一般化する）。守りたいのは判定ロジックなので、比較対象をコードに絞る。

    **ただし heredoc の中身では '#' 落としを行わない。** hook は heredoc で JSON を出力する
    （guard-env-read.sh / guard-gated-write.sh に実在）。中身を「コメント」として落とすと、
    配布物側の heredoc に '#' 始まりの行が混入しても差分として検出できず、
    **配置先で hook の標準出力が JSON として解釈されなくなる欠陥を見逃す**。
    同じ理由で **shebang（1 行目）は常に比較対象に含める**（`#!/bin/bash` → `#!/bin/zsh` の
    書き換えを見逃さない）。
    """
    out: list[str] = []
    terminator: str | None = None
    for i, ln in enumerate(path.read_text(encoding="utf-8").splitlines()):
        if terminator is not None:
            out.append(ln)
            if ln.strip() == terminator:
                terminator = None
            continue
        s = ln.strip()
        if i == 0 and s.startswith("#!"):
            out.append(ln)
            continue
        if not s or s.startswith("#"):
            continue
        out.append(ln)
        m = HEREDOC_RE.search(ln)
        if m:
            terminator = m.group(1)
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


def contract_g(require_export: bool) -> tuple[str, list[str], list[str]]:
    """持ち出しセットの hooks 突合。(status, details, warns) を返す。"""
    dirs = discover_export_hook_dirs()
    if not dirs:
        msg = (
            "持ち出しセットの hooks が見つからない（export/*/claude-config/hooks）。"
            " 別ブランチの worktree にしか存在しないため、この環境では検査できない"
        )
        if require_export:
            return FAIL, [msg + "（--require-export 指定のため FAIL）"], []
        # **SKIP にして他の契約の判定を通す。** 以前はここで exit 2 していたが、
        # それだと他の契約が FAIL していても終了コードが 2 になり、呼び出し側の hook が
        # 「1 以外は差し戻さない」ため**恒久的に無音**になっていた（20260726 のレビューで検出）。
        return SKIP, [msg, "→ 必須にしたい場合は --require-export を付ける"], []

    details: list[str] = []
    warns: list[str] = []
    checked = 0
    master_skills = {p.name for p in (MASTER_ROOT / ".claude" / "skills").iterdir() if p.is_dir()}
    for hooks_dir in dirs:
        nonbundled = master_skills - bundled_skill_names(hooks_dir)
        export_names = {p.name for p in hooks_dir.glob("*.sh")}
        label = hooks_dir.parent.parent.name

        # 配布物が**自分で登録した** hook のファイルが存在するか（登録と実体の食い違いは
        # 配布物側の明確な欠陥で、意図的な取捨選択ではない）
        registered = registered_hooks(hooks_dir.parent / "settings.example.json")
        for name in sorted(registered - export_names):
            details.append(f"{label}: settings.example.json に登録があるのにファイルが無い: {name}")
        for name in sorted(export_names - registered):
            details.append(f"{label}: ファイルがあるのに settings.example.json に登録が無い: {name}")

        # master の同送 hook が配布物に無い場合、**EXPORT_INTENTIONAL_OMISSIONS に
        # 宣言が無ければ FAIL**。宣言があれば WARN として毎回可視化する。
        # 「意図的な除外」と「新しい防御の入れ忘れ」は見た目が同じなので分類を強制する。
        for name in sorted(all_possible_sends() - export_names):
            if name in EXPORT_INTENTIONAL_OMISSIONS:
                warns.append(f"{label}: {name} は意図的に同送しない（宣言あり）")
            else:
                details.append(f"{label}: master の同送 hook が配布物に無い: {name}")
                details.append("→ 意図的な除外なら EXPORT_INTENTIONAL_OMISSIONS に理由つきで宣言する")

        for name in sorted(export_names):
            master_hook = HOOKS_DIR / name
            if not master_hook.exists():
                details.append(f"{label}: 配布物にあるがマスターに無い: {name}")
                continue
            checked += 1
            a = [strip_nonbundled(x, nonbundled) for x in code_lines(master_hook)]
            b = [strip_nonbundled(x, nonbundled) for x in code_lines(hooks_dir / name)]
            if a != b:
                details.append(f"{label}/{name}: 既知の変換規則で説明できないコード差分")
                for x, y in zip(a, b):
                    if x != y:
                        details.append(f"    master: {x[:100]}")
                        details.append(f"    export: {y[:100]}")
                        break
                if len(a) != len(b):
                    details.append(f"    行数が違う（master {len(a)} / export {len(b)}）")
    if details:
        return FAIL, details, warns
    return PASS, [f"配布物 {checked} 本のコードがマスターと一致（コメントの配布加工は許容）"], warns


def main() -> None:
    ap = argparse.ArgumentParser(
        description="セットアップ資産どうしの契約突合（マスター専用）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="終了コード: 0 = 全 PASS / 1 = 契約違反あり / 2 = 走査の前提が崩れている",
    )
    ap.add_argument("--verbose", action="store_true", help="PASS の契約も内訳を表示する")
    ap.add_argument(
        "--require-export", action="store_true",
        help="持ち出しセットが見つからない場合を SKIP ではなく FAIL にする",
    )
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
    ]

    failed = skipped = 0
    warns: list[str] = []
    for label, fn in contracts:
        status, details = fn()
        print(f"{status}  {label}")
        if status == FAIL:
            failed += 1
        if status == FAIL or args.verbose:
            for d in details:
                print(f"      {d}")

    status, details, w = contract_g(args.require_export)
    warns.extend(w)
    print(f"{status}  (g) 配布物 hooks に未説明の差分が無い")
    if status == FAIL:
        failed += 1
    if status == SKIP:
        skipped += 1
    if status in (FAIL, SKIP) or args.verbose:
        for d in details:
            print(f"      {d}")

    # WARN は **--verbose の有無に関わらず必ず出す。** 以前は PASS 時に隠れており、
    # 「配布物から防御 hook が丸ごと欠けても既定実行が完全な緑を返す」状態だった。
    for w_ in warns:
        print(f"WARN  {w_}")

    total = len(contracts) + 1
    print()
    if failed:
        print(f"{total - failed}/{total} PASS — {failed} 件の契約違反")
        sys.exit(1)
    tail = f"（SKIP {skipped} 件）" if skipped else ""
    print(f"{total}/{total} PASS{tail}")


if __name__ == "__main__":
    main()
