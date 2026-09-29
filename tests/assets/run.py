#!/usr/bin/env python3
"""check_asset_consistency.py の検査器そのものの回帰テスト（壊した入力で FAIL すること）。

検出ツールの欠陥は「検出漏れ」として現れ、使う側からは成功と区別がつかない。実際に
(n) は抽出 0 件どうしの一致を PASS にし、(p) は黒名簿方式で `"Edit"` や `Agent` を素通りさせた。
手で壊して確かめただけでは次の変更で同じ穴が戻るため、壊した入力を固定してここで回す。

方式: 契約が読むパス定数を一時ディレクトリのコピーへ差し替え、コピーだけを壊して契約関数を呼ぶ。
対照として、壊していないコピーで PASS することも確認する（常に FAIL する検査を見逃さないため）。

Usage: python3 tests/assets/run.py
Exit 0 = all pass. Exit 1 = failure (prints details).
"""
from __future__ import annotations

import re
import shutil
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Callable, Iterator

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import check_asset_consistency as cac  # noqa: E402

Mutation = Callable[[str], str]


@contextmanager
def patched(**files: Path) -> Iterator[dict[str, Path]]:
    """cac のパス定数（ファイル or ディレクトリ）を一時コピーへ差し替える。"""
    tmp = Path(tempfile.mkdtemp(prefix="asset-check-"))
    originals = {name: getattr(cac, name) for name in files}
    copies: dict[str, Path] = {}
    try:
        for name, src in files.items():
            dst = tmp / name
            if src.is_dir():
                shutil.copytree(src, dst)
            else:
                shutil.copy(src, dst)
            copies[name] = dst
            setattr(cac, name, dst)
        yield copies
    finally:
        for name, value in originals.items():
            setattr(cac, name, value)
        shutil.rmtree(tmp, ignore_errors=True)


def mutate(path: Path, fn: Mutation) -> None:
    before = path.read_text(encoding="utf-8")
    after = fn(before)
    if after == before:
        raise AssertionError(f"変異が効いていない（入力の書式が変わった可能性）: {path.name}")
    path.write_text(after, encoding="utf-8")


def drop_lines(pattern: str) -> Mutation:
    return lambda s: re.sub(pattern, "", s, flags=re.M)


# --- (n) tasklist テンプレの写し -------------------------------------------------

N_CASES: list[tuple[str, Mutation]] = [
    ("デプロイ節のキーを正本・写しの両方から消す（0 件どうしの一致）", drop_lines(r"^- (PR|CI|Feedback):.*\n")),
    ("チェックボックス項目を両方から消す（0 件どうしの一致）", drop_lines(r"^- \[ \] .*\n")),
    ("テンプレのコードブロック見出しを両方で崩す", lambda s: s.replace("# タスクリスト:", "# Tasklist:")),
]

# --- (p) agent 定義の読み取り専用 -------------------------------------------------

TOOLS_BLOCK_RE = re.compile(r"^tools:\n(?:  - .*\n)+", re.M)


def with_tools(block: str) -> Mutation:
    return lambda s: TOOLS_BLOCK_RE.sub(block, s, count=1)


P_TARGET = "review-impl.md"
P_CASES: list[tuple[str, Mutation]] = [
    ("引用符付きの \"Edit\"", with_tools('tools:\n  - Read\n  - "Edit"\n')),
    ("インライン配列 [Read, Write]", with_tools("tools: [Read, Write]\n")),
    ("カンマ区切りに Edit", with_tools("tools: Read, Grep, Edit\n")),
    ("Agent", with_tools("tools:\n  - Read\n  - Agent\n")),
    ("mcp__*", with_tools("tools:\n  - Read\n  - mcp__x__y\n")),
    ("WebFetch", with_tools("tools:\n  - Read\n  - WebFetch\n")),
    ("素の Bash", with_tools("tools:\n  - Read\n  - Bash\n")),
    ("Bash(git diff *)（--output で書ける）", with_tools("tools:\n  - Read\n  - Bash(git diff *)\n")),
]

# --- (m) 判定表 ↔ pipeline_state.py -------------------------------------------------


def swap_first_two_rows(s: str) -> str:
    lines = s.split("\n")
    idx = [i for i, line in enumerate(lines) if cac.PHASE_ROW_RE.match(line)]
    lines[idx[0]], lines[idx[1]] = lines[idx[1]], lines[idx[0]]
    return "\n".join(lines)


def drop_first_row(s: str) -> str:
    lines = s.split("\n")
    first = next(i for i, line in enumerate(lines) if cac.PHASE_ROW_RE.match(line))
    return "\n".join(lines[:first] + lines[first + 1:])


M_CASES: list[tuple[str, Mutation]] = [
    ("表の行を 1 つ消す", drop_first_row),
    ("表の先頭 2 行を入れ替える（到達不能の原因）", swap_first_two_rows),
    ("行 ID の書式を崩す（0 行）", lambda s: re.sub(r"^\|\s*`([A-Z][0-9A-Za-z]*)`", r"| \1", s, flags=re.M)),
]

# --- (r) capture フラグの producer ------------------------------------------------

R_CASES: list[tuple[str, Mutation]] = [
    ("producer から pr_capture_done の touch を消す", drop_lines(r"^.*touch \.steering/\[task\]/pr_capture_done.*\n")),
    ("producer から capture_done の touch を消す", drop_lines(r"^touch \.steering/\[task\]/capture_done.*\n")),
]


# --- (s) 書き込み hook の対象パス ≡ permissions.ask の Edit(./...) -------------------
S_CASES: list[tuple[str, str, Mutation]] = [
    ("hook", "マーカー行から .claude/hooks/ を消す", lambda t: t.replace(" .claude/hooks/", "", 1)),
    ("hook", "マーカー行そのものを消す", drop_lines(r"^# GATED_PATHS:.*\n")),
    ("settings", "ask から Edit(./docs/decisions/...) の 3 形式を消す", lambda t: re.sub(r',\s*"Edit\(\./docs/decisions/[^"]*\)"', "", t)),
    ("settings", "ask に Edit(./README.md) を足す（hook 側に無い）", lambda t: t.replace('"Edit(./CLAUDE.md)",', '"Edit(./CLAUDE.md)",\n      "Edit(./README.md)",', 1)),
]

# --- (t) allow に git を書かない --------------------------------------------------
T_CASES: list[tuple[str, Mutation]] = [
    ("allow に Bash(git diff *) を足す", lambda t: t.replace('"Bash(ls *)"', '"Bash(git diff *)",\n      "Bash(ls *)"', 1)),
    ("allow に Bash(git log*) を足す", lambda t: t.replace('"Bash(ls *)"', '"Bash(git log*)",\n      "Bash(ls *)"', 1)),
    ("allow に Bash( git show*) を足す（括弧直後の空白）", lambda t: t.replace('"Bash(ls *)"', '"Bash( git show*)",\n      "Bash(ls *)"', 1)),
]


def deploy_git_allow_case() -> tuple[str, list[str]]:
    """(t) の DEPLOY_PERMISSIONS 側。import 済みの dict なのでファイルではなくモジュール変数を差し替える。"""
    label = "(t) DEPLOY_PERMISSIONS の allow に Bash(git diff*) を足す → FAIL"
    original = cac.DEPLOY_PERMISSIONS
    mutated = dict(original, allow=[*original.get("allow", []), "Bash(git diff*)"])
    cac.DEPLOY_PERMISSIONS = mutated
    try:
        status, _ = cac.contract_t()
    finally:
        cac.DEPLOY_PERMISSIONS = original
    return label, [] if status == cac.FAIL else [f"DEPLOY_PERMISSIONS: {status} を返した（偽の緑）"]


def run_contract(
    letter: str,
    contract: Callable[[], tuple[str, list[str]]],
    files: dict[str, Path],
    target: str,
    cases: list[tuple[str, Mutation]],
    target_files: Callable[[dict[str, Path]], list[Path]],
) -> list[tuple[str, list[str]]]:
    results: list[tuple[str, list[str]]] = []
    with patched(**files):
        status, details = contract()
        results.append((f"({letter}) 対照: 壊していない入力は PASS", [] if status == cac.PASS else details))
    for label, fn in cases:
        with patched(**files) as copies:
            try:
                for path in target_files(copies):
                    mutate(path, fn)
            except AssertionError as e:
                results.append((f"({letter}) {label}", [str(e)]))
                continue
            status, _ = contract()
            results.append((f"({letter}) {label} → FAIL", [] if status == cac.FAIL else [f"{target}: {status} を返した（偽の緑）"]))
    return results


def all_results() -> list[tuple[str, list[str]]]:
    results: list[tuple[str, list[str]]] = []
    results += run_contract(
        "n", cac.contract_n,
        {"TASKLIST_TEMPLATE": cac.TASKLIST_TEMPLATE, "STEERING_SPEC": cac.STEERING_SPEC},
        "templates.md + spec.md", N_CASES,
        lambda c: [c["TASKLIST_TEMPLATE"], c["STEERING_SPEC"]],
    )
    results += run_contract(
        "p", cac.contract_p, {"AGENTS_DIR": cac.AGENTS_DIR}, P_TARGET, P_CASES,
        lambda c: [c["AGENTS_DIR"] / P_TARGET],
    )
    results += run_contract(
        "m", cac.contract_m, {"FEATURE_PIPELINE": cac.FEATURE_PIPELINE}, "feature-pipeline/SKILL.md", M_CASES,
        lambda c: [c["FEATURE_PIPELINE"]],
    )
    results += run_contract(
        "r", cac.contract_r, {"FLAG_PRODUCER": cac.FLAG_PRODUCER}, "knowledge-capture/SKILL.md", R_CASES,
        lambda c: [c["FLAG_PRODUCER"]],
    )
    for side, label, fn in S_CASES:
        results += run_contract(
            "s", cac.contract_s, {"HOOKS_DIR": cac.HOOKS_DIR, "SETTINGS": cac.SETTINGS},
            "guard-gated-write.sh + settings.json", [(label, fn)],
            (lambda c: [c["HOOKS_DIR"] / "guard-gated-write.sh"]) if side == "hook" else (lambda c: [c["SETTINGS"]]),
        )
    results += run_contract(
        "t", cac.contract_t, {"SETTINGS": cac.SETTINGS}, "settings.json", T_CASES,
        lambda c: [c["SETTINGS"]],
    )
    results.append(deploy_git_allow_case())
    return results


def main() -> int:
    results = all_results()
    passed = 0
    for label, details in results:
        if details:
            print(f"FAIL {label}")
            for line in details:
                print(f"  {line}")
        else:
            print(f"PASS {label}")
            passed += 1
    print(f"\n{passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
