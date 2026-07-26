#!/usr/bin/env python3
"""配置先スキルのドリフト検出（マスター専用ツール・依存ゼロ）。

配置先プロジェクト（.claude/skills/ を持つ別リポジトリ）の各スキルを、
frontmatter の metadata.source-commit（配置時に記録されるマスターの HEAD）と
突き合わせ、3 分類のドリフトを報告する:

  (a) 直接編集    — 配置先 SKILL.md が source-commit 時点のマスターと不一致
                    （配置先で本文を直接いじった。改善はマスターに還元する規約に違反）
  (b) マスター先行 — source-commit..HEAD にそのスキルへのコミットがある
                    （マスター側に配置後の改善が入っている。再コピーで還元すべき）
  (c) 記録なし    — metadata.source-commit が無い（追跡不能。配置手順の記録漏れ）

比較は SKILL.md 本文のみを対象とする。references/ は配置時にスタック別へ
再生成される（starter-kit 手順4）ため意図的に差分が出る。比較に含めると誤検出になる。
source-commit 行自体は配置時に付与されるため比較前に除去する。

hooks も検査する（SKILL.md だけを見ていると「配るべき hook が配置先に無い」状態を誰も
検出できない。20260723 に session-start-check.sh の配り忘れが敵対レビューで初めて見つかった）:

  (d) hook 未配置  — 配置スキル一式に対して同送すべき hook が配置先に無い
  (e) hook 内容差分 — 配置先の hook がマスター HEAD と不一致（配置先で編集 or マスター先行）

同送すべき hook の判定は deploy_skills.expected_hooks() を import して使う（単一情報源。
両者に同じリストを書くと片側修正で腐るため）。

加えて、配置先に溜まった skill-issues.md を回収対象として報告する（読み取り専用）:
回収済みマーカー <!-- harvested: YYYYMMDD --> より後に追記された項目だけを「新規」として
報告する。マーカーの書き込みは行わない（承認後に skill-harvest スキルが行う）。

使い方:
  python3 scripts/check_deploy_drift.py                    # deployments.md の全配置先をループ
  python3 scripts/check_deploy_drift.py <配置先パス>       # 単一配置先（既存互換）
終了コード: 0 = ドリフトなし / 1 = ドリフトあり / 2 = 実行エラー
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

MASTER_ROOT = Path(__file__).resolve().parent.parent
HARVEST_MARKER = re.compile(r"<!--\s*harvested:\s*\d{8}\s*-->")

sys.path.insert(0, str(Path(__file__).resolve().parent))
# REGISTRY もここから取る。以前は `MASTER_ROOT / "deployments.md"` を独立に定義していたが、
# **レジストリのファイル名という値の契約を 2 箇所に持つ形**で、片方だけ変えても
# どちらも自分の中では整合するため grep でも静的検査でも検出されない。
# 同送リストで同じ理由の import をしているので、ここも producer 側から取る。
from deploy_skills import REGISTRY, expected_hooks  # noqa: E402 — 値の契約の単一情報源


def git(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(MASTER_ROOT), *args],
        capture_output=True,
        text=True,
    )


def parse_source_commit(text: str) -> str | None:
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    fm = m.group(1) if m else text
    sc = re.search(r"^\s*source-commit:\s*(\S+)\s*$", fm, re.M)
    return sc.group(1) if sc else None


def strip_source_commit_line(text: str) -> str:
    """比較のため source-commit 行を除去する（マスター側には無い行のため）。"""
    return "\n".join(
        ln for ln in text.splitlines() if not re.match(r"^\s*source-commit:\s*\S+\s*$", ln)
    )


def check_skill(name: str, deployed_skill_md: Path) -> list[str]:
    """1 スキルのドリフト分類を返す（空リスト = ドリフトなし）。"""
    flags: list[str] = []
    deployed = deployed_skill_md.read_text(encoding="utf-8")

    commit = parse_source_commit(deployed)
    if commit is None:
        return ["(c) 記録なし — metadata.source-commit が無い"]

    # コミットがマスターに存在するか
    if git(["cat-file", "-e", f"{commit}^{{commit}}"]).returncode != 0:
        return [f"(!) source-commit {commit} がマスターに存在しない（無効なハッシュ）"]

    master_path = f".claude/skills/{name}/SKILL.md"

    # (a) 直接編集: source-commit 時点のマスター SKILL.md と比較
    show = git(["show", f"{commit}:{master_path}"])
    if show.returncode != 0:
        flags.append(f"(!) {master_path} が source-commit {commit[:8]} 時点のマスターに存在しない")
    else:
        if strip_source_commit_line(deployed).rstrip("\n") != show.stdout.rstrip("\n"):
            flags.append(f"(a) 直接編集 — 配置先 SKILL.md が source-commit {commit[:8]} 時点と不一致")

    # (b) マスター先行: source-commit..HEAD にこのスキルへのコミットがあるか
    log = git(["log", "--oneline", f"{commit}..HEAD", "--", f".claude/skills/{name}/"])
    if log.returncode == 0 and log.stdout.strip():
        n = len(log.stdout.strip().splitlines())
        flags.append(f"(b) マスター先行 — source-commit {commit[:8]}..HEAD にこのスキルへのコミット {n} 件")

    return flags


def check_hooks(deploy_root: Path, skill_names: list[str]) -> list[str]:
    """配置スキル一式に対して同送すべき hooks が、配置先に正しく在るかを検査する。

    hook は SKILL.md と違い source-commit を持てない（シェルスクリプト）ため、
    比較対象はマスターの現在の内容。差分は「配置先で編集」と「マスター先行」を
    区別できないので、両方の可能性として 1 分類で報告する。
    """
    flags: list[str] = []
    hooks_src = MASTER_ROOT / ".claude" / "hooks"
    hooks_dst = deploy_root / ".claude" / "hooks"
    for name in expected_hooks(skill_names):
        src = hooks_src / name
        if not src.exists():
            flags.append(f"(!) {name} がマスターに無い（同送リストと実体の不一致）")
            continue
        dst = hooks_dst / name
        if not dst.exists():
            flags.append(f"(d) hook 未配置 — {name}（同送対象だが配置先に無い）")
        elif dst.read_bytes() != src.read_bytes():
            flags.append(f"(e) hook 内容差分 — {name}（配置先で編集 or マスター先行）")
    return flags


def new_issues_after_marker(text: str) -> str:
    """skill-issues.md 本文のうち、最後の回収済みマーカーより後の部分を返す。

    マーカーが無ければ全文が新規。マーカー以降が空白のみなら空文字（新規なし）。
    このスクリプトは読み取り専用 — マーカーの書き込みはしない。
    """
    matches = list(HARVEST_MARKER.finditer(text))
    tail = text[matches[-1].end():] if matches else text
    return tail.strip()


def collect_issues(deploy_root: Path) -> list[tuple[Path, str]]:
    """配置先の .steering/**/skill-issues.md（archived 含む）から新規項目を集める。"""
    steering = deploy_root / ".steering"
    if not steering.is_dir():
        return []
    found: list[tuple[Path, str]] = []
    for p in sorted(steering.rglob("skill-issues.md")):
        new = new_issues_after_marker(p.read_text(encoding="utf-8"))
        if new:
            found.append((p, new))
    return found


def report_deploy(deploy_root: Path) -> int:
    """1 配置先のドリフト + issues 回収を報告し、ドリフト件数を返す（-1 = 実行不能）。"""
    skills_dir = deploy_root / ".claude" / "skills"
    if not skills_dir.is_dir():
        print(f"エラー: 配置先にスキルディレクトリが無い: {skills_dir}")
        return -1

    skill_dirs = sorted(d for d in skills_dir.iterdir() if d.is_dir())
    if not skill_dirs:
        print(f"エラー: スキルが 1 つも無い: {skills_dir}")
        return -1

    print(f"# 配置先: {deploy_root}")
    drifted = 0
    for d in skill_dirs:
        skill_md = d / "SKILL.md"
        if not skill_md.exists():
            print(f"SKIP  {d.name} — SKILL.md 不在")
            continue
        flags = check_skill(d.name, skill_md)
        if flags:
            drifted += 1
            print(f"DRIFT {d.name}")
            for f in flags:
                print(f"      - {f}")
        else:
            print(f"OK    {d.name}")

    # hooks はスキル数の分母に入れない（スキルのドリフト率とは別軸のため）。
    # 終了コードにだけ効かせる。
    hook_flags = check_hooks(deploy_root, [d.name for d in skill_dirs])
    if hook_flags:
        print("DRIFT hooks")
        for f in hook_flags:
            print(f"      - {f}")
    else:
        print("OK    hooks")

    issues = collect_issues(deploy_root)
    if issues:
        print(f"\nISSUES 未回収の skill-issues.md（マーカー以降の新規項目）: {len(issues)} ファイル")
        for path, _ in issues:
            print(f"      - {path}")
    else:
        print("\nISSUES 新規の未回収項目なし")

    print(f"{len(skill_dirs) - drifted}/{len(skill_dirs)} ドリフトなし（スキル）"
          f" / hooks: {'DRIFT' if hook_flags else 'OK'}\n")
    return drifted + (1 if hook_flags else 0)


def read_registry() -> list[Path]:
    """deployments.md を読み、配置先パスの一覧を返す（# コメント・空行を無視）。"""
    paths: list[Path] = []
    for ln in REGISTRY.read_text(encoding="utf-8").splitlines():
        s = ln.split("#", 1)[0].strip()
        if s:
            paths.append(Path(s).expanduser())
    return paths


def main() -> None:
    ap = argparse.ArgumentParser(
        description="配置先スキルのドリフト検出（読み取り専用）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "引数なしで deployments.md の全配置先をループする。\n"
            "終了コード: 0 = ドリフトなし / 1 = ドリフトあり / 2 = 実行エラー"
        ),
    )
    ap.add_argument(
        "target",
        nargs="?",
        help="単一配置先のパス（省略時は deployments.md の全配置先）",
    )
    args = ap.parse_args()

    if git(["rev-parse", "--git-dir"]).returncode != 0:
        print(f"エラー: マスター {MASTER_ROOT} が git リポジトリではない")
        sys.exit(2)

    # 単一配置先モード（既存互換）
    if args.target:
        deploy_root = Path(args.target).expanduser()
        drifted = report_deploy(deploy_root)
        sys.exit(2 if drifted < 0 else (1 if drifted else 0))

    # レジストリモード（引数なし）— deployments.md の全配置先をループ
    if not REGISTRY.exists():
        print(f"エラー: レジストリが無い: {REGISTRY}")
        print("`cp deployments.example.md deployments.md` してから配置先の絶対パスを 1 行 1 件で追記してください。")
        sys.exit(2)

    roots = read_registry()
    if not roots:
        print(f"エラー: {REGISTRY} に配置先が 1 件も無い")
        sys.exit(2)

    total_drift = 0
    errors = 0
    for root in roots:
        if not root.exists():
            print(f"# 配置先: {root}\nエラー: パスが存在しない\n")
            errors += 1
            continue
        d = report_deploy(root)
        if d < 0:
            errors += 1
        else:
            total_drift += d

    print(f"=== 配置先 {len(roots)} 件 / ドリフト合計 {total_drift} / 実行不能 {errors} ===")
    sys.exit(2 if errors else (1 if total_drift else 0))


if __name__ == "__main__":
    main()
