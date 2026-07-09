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

使い方:
  python3 scripts/check_deploy_drift.py <配置先プロジェクトのパス>
終了コード: 0 = ドリフトなし / 1 = ドリフトあり / 2 = 実行エラー
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

MASTER_ROOT = Path(__file__).resolve().parent.parent


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


def main() -> None:
    args = sys.argv[1:]
    if len(args) != 1:
        print(__doc__)
        sys.exit(2)

    if git(["rev-parse", "--git-dir"]).returncode != 0:
        print(f"エラー: マスター {MASTER_ROOT} が git リポジトリではない")
        sys.exit(2)

    deploy_root = Path(args[0]).expanduser()
    skills_dir = deploy_root / ".claude" / "skills"
    if not skills_dir.is_dir():
        print(f"エラー: 配置先にスキルディレクトリが無い: {skills_dir}")
        sys.exit(2)

    skill_dirs = sorted(d for d in skills_dir.iterdir() if d.is_dir())
    if not skill_dirs:
        print(f"エラー: スキルが 1 つも無い: {skills_dir}")
        sys.exit(2)

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

    print(f"\n{len(skill_dirs) - drifted}/{len(skill_dirs)} ドリフトなし")
    sys.exit(1 if drifted else 0)


if __name__ == "__main__":
    main()
