#!/usr/bin/env python3
"""持ち出しセットと master の「停止契約」差分の検出（マスター専用ツール・依存ゼロ）。

持ち出しセット（export/company/skills/）は master から手で転記・加工されるため、
転記の過程で停止契約（ハードストップ・承認ゲート）が意図せず変質しうる。
本スクリプトは両者の停止契約領域だけを比較し、**実質差分**を報告する。

実質差分と無害差分の区別:
  無害差分 — 非同梱スキル名の除去・マスター固有語の一般化・スタック語の置換だけで
             説明がつく差分（持ち出し加工として想定済み）
  実質差分 — 上記を打ち消してもなお残る差分（停止の条件・順序・強さが変わった疑い）

実質差分のあるスキルは、持ち出しセット側にも素通り検査シナリオを持つ候補になる。
実質差分が無いスキルは、master 側のシナリオで検証した停止契約がそのまま転記されている
とみなせるため、二重にシナリオを作らない。

**フェイルクローズ**: 比較対象ディレクトリが存在しない場合は exit 2 で落ちる。
持ち出しセットは export ブランチ（worktree）にしか存在しないため、main 側で
うっかり実行すると走査 0 件になる。それを「差分なし」と報告すると偽グリーンになる。

使い方:
  python3 scripts/check_export_stopcontract.py                    # git worktree から自動発見
  python3 scripts/check_export_stopcontract.py --export <skills ディレクトリ>   # 明示指定
  python3 scripts/check_export_stopcontract.py --master <master の skills ディレクトリ>
  python3 scripts/check_export_stopcontract.py --verbose          # 無害差分も行単位で表示
終了コード: 0 = 正常終了（差分の有無を問わない・report-only）/ 2 = 対象不在などの実行エラー
"""
from __future__ import annotations

import argparse
import difflib
import re
import subprocess
import sys
from pathlib import Path

MASTER_ROOT = Path(__file__).resolve().parent.parent

# 停止契約を構成する語彙。この語を含む行とその見出しを比較対象にする
STOP_VOCAB = (
    "ここで止ま",
    "ここで必ず止ま",
    "停止",
    "止まる",
    "承認",
    "APPROVED",
    "ハードストップ",
    "STOP",
    "代用にしない",
    "headless",
)

# マスター固有語 → 持ち出し側での言い換え（無害差分として打ち消す）
GENERALIZE = (
    ("このリポジトリ", ""),
    ("このプロジェクト", ""),
    ("配置先プロジェクト", ""),
    ("配置先", ""),
    ("マスター", ""),
    ("プルリクエスト", "MR"),
    ("プルリク", "MR"),
    ("PR", "MR"),
    ("パイプライン", "CI"),
)

# スタック語（Angular 変換で入れ替わる。停止契約の強さには影響しない）
STACK_WORDS = (
    "React", "Vitest", "TypeScript", "Jasmine", "Angular", "TestBed",
    "Playwright", "MSW", "RTL", "Testing Library", "pnpm", "npm", "npx",
    ".tsx", ".spec.ts", ".test.ts", ".ts", ".html", "Jotai", "Karma",
)


def read_body(skill_md: Path) -> list[str]:
    """frontmatter を除いた本文を行のリストで返す。

    frontmatter の metadata.modified には「停止をステップ境界化」等の
    停止語彙が入りうるが、それは変更履歴であって停止契約ではない。
    """
    text = skill_md.read_text(encoding="utf-8")
    m = re.match(r"^---\n.*?\n---\n", text, re.S)
    body = text[m.end():] if m else text
    offset = text[: m.end()].count("\n") if m else 0
    return [(i + offset, ln) for i, ln in enumerate(body.splitlines(), 1)]


def stop_lines(skill_md: Path) -> list[tuple[int, str]]:
    """停止契約に関わる行を (行番号, 行) で抽出する。"""
    hits = []
    for lineno, ln in read_body(skill_md):
        if any(v in ln for v in STOP_VOCAB):
            hits.append((lineno, ln))
    return hits


def normalize(line: str, nonbundled: set[str]) -> str:
    """既知の無害差分を打ち消した比較用の文字列を返す。"""
    s = line
    # 非同梱スキル名の除去（バッククォート付き → 素の順で消す）
    for n in sorted(nonbundled, key=len, reverse=True):
        s = s.replace(f"`{n}`", "").replace(n, "")
    for a, b in GENERALIZE:
        s = s.replace(a, b)
    for w in STACK_WORDS:
        s = s.replace(w, "")
    # 記号・空白・強調の揺れを吸収する（語順と語そのものだけを見る）
    s = re.sub(r"[\s、。，．「」『』（）()\[\]`*_\-—–/：:；;→←↔|]+", "", s)
    return s


def compare(master_md: Path, export_md: Path, nonbundled: set[str]):
    """(実質差分のリスト, 無害差分の件数) を返す。

    実質差分は (種別, master 側の行, export 側の行) のタプル。
    """
    m_lines = stop_lines(master_md)
    e_lines = stop_lines(export_md)
    m_norm = [normalize(ln, nonbundled) for _, ln in m_lines]
    e_norm = [normalize(ln, nonbundled) for _, ln in e_lines]

    substantive = []
    benign = 0
    sm = difflib.SequenceMatcher(None, m_norm, e_norm, autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            # 正規化後は同じ = 無害差分。生の行が違うものだけ数える
            for k in range(i2 - i1):
                if m_lines[i1 + k][1] != e_lines[j1 + k][1]:
                    benign += 1
            continue
        if tag == "replace":
            for k in range(max(i2 - i1, j2 - j1)):
                m = m_lines[i1 + k] if i1 + k < i2 else None
                e = e_lines[j1 + k] if j1 + k < j2 else None
                substantive.append(("変更", m, e))
        elif tag == "delete":
            for k in range(i1, i2):
                substantive.append(("master のみ", m_lines[k], None))
        elif tag == "insert":
            for k in range(j1, j2):
                substantive.append(("export のみ", None, e_lines[k]))
    return substantive, benign


def discover_export_roots() -> list[Path]:
    """git worktree を走査して `export/*/skills` を持つディレクトリを探す。

    持ち出しセットは別ブランチ（worktree）にしか存在せず、その置き場所は
    環境ごとに違う。パスを package.json 等に固定で書くと環境依存の設定になるため、
    git に聞いて発見する。見つからなければ呼び出し側がフェイルクローズする。
    """
    try:
        out = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            cwd=str(MASTER_ROOT), capture_output=True, text=True, check=False,
        ).stdout
    except OSError:
        return []
    roots: list[Path] = []
    for ln in out.splitlines():
        if not ln.startswith("worktree "):
            continue
        wt = Path(ln[len("worktree "):].strip())
        for skills in sorted(wt.glob("export/*/skills")):
            if skills.is_dir():
                roots.append(skills)
    return roots


def main() -> None:
    ap = argparse.ArgumentParser(
        description="持ち出しセットと master の停止契約差分を検出する（report-only）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="終了コード: 0 = 正常終了（差分の有無を問わない）/ 2 = 対象不在などの実行エラー",
    )
    ap.add_argument(
        "--export",
        help="持ち出しセットの skills ディレクトリ（省略時は git worktree から自動発見）",
    )
    ap.add_argument(
        "--master",
        default=str(MASTER_ROOT / ".claude" / "skills"),
        help="master の skills ディレクトリ（既定: このリポジトリの .claude/skills）",
    )
    ap.add_argument("--verbose", action="store_true", help="無害差分も行単位で表示する")
    args = ap.parse_args()

    master_root = Path(args.master)

    if args.export:
        export_root = Path(args.export)
    else:
        found = discover_export_roots()
        if not found:
            print("エラー: 持ち出しセットが見つかりません（--export を指定してください）", file=sys.stderr)
            print(
                "  持ち出しセットは別ブランチの worktree にしかありません。"
                "worktree が無い環境では比較できません。",
                file=sys.stderr,
            )
            sys.exit(2)
        if len(found) > 1:
            print(f"エラー: 持ち出しセットが複数見つかりました。--export で選んでください:", file=sys.stderr)
            for f in found:
                print(f"  {f}", file=sys.stderr)
            sys.exit(2)
        export_root = found[0]

    # フェイルクローズ: 対象が無いのに「差分なし」と報告しない
    for label, root in (("--export", export_root), ("--master", master_root)):
        if not root.is_dir():
            print(f"エラー: {label} のディレクトリが存在しません: {root}", file=sys.stderr)
            print(
                "  持ち出しセットは export ブランチ（worktree）にしかありません。"
                "main 側で実行していないか確認してください。",
                file=sys.stderr,
            )
            sys.exit(2)

    export_skills = sorted(d.name for d in export_root.iterdir() if (d / "SKILL.md").exists())
    master_skills = sorted(d.name for d in master_root.iterdir() if (d / "SKILL.md").exists())
    if not export_skills:
        print(f"エラー: {export_root} に SKILL.md を持つスキルがありません", file=sys.stderr)
        sys.exit(2)

    nonbundled = set(master_skills) - set(export_skills)

    print("停止契約の差分レポート（持ち出しセット ↔ master・report-only）")
    print(f"  export: {export_root}  （{len(export_skills)} スキル）")
    print(f"  master: {master_root}  （{len(master_skills)} スキル）")
    print(f"  無害差分として打ち消す非同梱スキル名: {len(nonbundled)} 件\n")

    only_export = [n for n in export_skills if n not in master_skills]
    if only_export:
        print(f"master に対応が無いスキル（比較不能）: {', '.join(only_export)}\n")

    n_sub = n_benign_only = n_clean = 0
    for name in export_skills:
        if name not in master_skills:
            continue
        substantive, benign = compare(
            master_root / name / "SKILL.md", export_root / name / "SKILL.md", nonbundled
        )
        if substantive:
            n_sub += 1
            print(f"{name}:  実質差分 {len(substantive)} 件 / 無害差分 {benign} 件")
            for kind, m, e in substantive:
                if m:
                    print(f"      [{kind}] master {m[0]}: {m[1].strip()[:120]}")
                if e:
                    print(f"      [{kind}] export {e[0]}: {e[1].strip()[:120]}")
            print()
        elif benign:
            n_benign_only += 1
            if args.verbose:
                print(f"{name}:  無害差分のみ {benign} 件")
        else:
            n_clean += 1

    print(
        f"実質差分あり: {n_sub} スキル / 無害差分のみ: {n_benign_only} スキル / 差分なし: {n_clean} スキル"
    )
    if n_sub:
        print("→ 実質差分のあるスキルは、持ち出しセット側にも素通り検査シナリオを持つ候補")
    else:
        print("→ 停止契約は master と実質同一。持ち出し側の追加シナリオは不要")
    sys.exit(0)


if __name__ == "__main__":
    main()
