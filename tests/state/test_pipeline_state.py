#!/usr/bin/env python3
"""feature-pipeline 判定表の table-driven test（pytest 非依存）。

Usage: python3 tests/state/run.py
Exit 0 = all pass. Exit 1 = failure（`run.py` が終了コードを返す）。

検査するもの（ID は出力の `PASS T1` / `PASS C1` と同じ）:
  T*  各ケースが期待どおりの行 ID で確定する（未知 Status の fail-closed が下位行に負けないこと・
      P37 / P4a / P35 の優先順位を含む）
  C1  行 ID の網羅 — ROW_ORDER の全行がいずれかのケースの期待値に現れる
  C2  到達可能性 — 入力の全直積（数千状態）を列挙し、ROW_ORDER の全行が実際に確定する
      （= 上の行に完全に隠れた行が無い。Critical 1 の回帰。手書きケースに依存しない）
  C3  全域 — 同じ直積で、どの行にも当たらない状態（NO_MATCH）が無い
  C4  PR 前 capture の後に最終 capture が飛ばされない（Critical 2 の回帰）
  C5  tasklist の書式から入力への写像（parse_tasklist）が期待どおり
"""
from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from pipeline_state import (  # noqa: E402
    NO_MATCH,
    ROW_ORDER,
    PipelineState,
    apply_capture,
    parse_tasklist,
    resolve_phase,
)

# 実装が全部終わりレビューも通った状態（デプロイ以降の分岐を書くための土台）。
REVIEWED = PipelineState(design_status="APPROVED", review_status="RESOLVED")
# PR 差分に属する知見の保存まで終えた状態。tasklist 正本の工程順では
# 知見保存(PR 分) がデプロイより先なので、PR 作成以降はこちらが土台になる。
AFTER_PR_CAPTURE = replace(REVIEWED, pr_capture_done=True)

# 現実に起こりうる状態だけを列挙する。**架空の組み合わせを入れない** —
# 到達可能性 (c) の意味が「机上で作れる状態」に薄まると、実運用で
# 到達不能な行を見逃す（Critical 1 がまさにそれだった）。
CASES: list[dict] = [
    {
        "id": "T1",
        "label": "design.md が無い → 計画から",
        "state": PipelineState(design_exists=False, design_status=None),
        "expect": "P1",
    },
    {
        "id": "T2",
        "label": "DRAFT は実装に入らない",
        "state": PipelineState(design_status="DRAFT", impl_unchecked=True),
        "expect": "G1",
    },
    {
        "id": "T3",
        "label": "SPIKE はパイプライン外",
        "state": PipelineState(design_status="SPIKE", impl_unchecked=True),
        "expect": "S1",
    },
    {
        "id": "T4",
        "label": "未知の Status 語彙は即停止",
        "state": PipelineState(design_status="PENDING"),
        "expect": "H1",
    },
    {
        "id": "T5",
        "label": "Status 行の欠落は即停止",
        "state": PipelineState(design_status=None),
        "expect": "H1",
    },
    {
        "id": "T6",
        "label": "APPROVED で実装に未チェックあり",
        "state": PipelineState(design_status="APPROVED", impl_unchecked=True),
        "expect": "P2",
    },
    {
        "id": "T7",
        "label": "実装完了・review-result.md がまだ無い",
        "state": PipelineState(design_status="APPROVED", review_status=None),
        "expect": "P3",
    },
    {
        "id": "T8",
        "label": "指摘が OPEN のまま前進しない",
        "state": replace(REVIEWED, review_status="OPEN"),
        "expect": "G3",
    },
    {
        "id": "T9",
        "label": "レビュー通過直後 → まず PR 差分の知見保存",
        "state": replace(REVIEWED, deploy_unchecked=True),
        "expect": "P4a",
    },
    {
        "id": "T9b",
        "label": "PR 前 capture 済み・PR まだ無し → PR 作成へ",
        "state": replace(AFTER_PR_CAPTURE, deploy_unchecked=True),
        "expect": "P35",
    },
    {
        "id": "T10",
        "label": "PR 済みでフィードバックが返っている → 往復対応へ",
        # PR は出したが CI が落ちている / レビューコメントが返っている状態。
        # このとき「CI グリーン確認」は当然まだチェックできないので
        # deploy_unchecked は True のまま。現行表はこの状態で P35 を返し、
        # 「もう作った PR をもう一度作れ」と案内してしまう（Critical 1）。
        "state": replace(
            AFTER_PR_CAPTURE,
            deploy_unchecked=True,
            pr_url="https://github.com/example/repo/pull/1",
            pr_feedback=True,
        ),
        "expect": "P37",
    },
    {
        "id": "T11",
        "label": "マージ済み・最終 capture がまだ",
        "state": replace(AFTER_PR_CAPTURE, deploy_unchecked=False),
        "expect": "P4b",
    },
    {
        "id": "T12",
        "label": "最終 capture 済み → クローズ",
        "state": replace(AFTER_PR_CAPTURE, capture_done=True),
        "expect": "P5",
    },
    {
        "id": "T13",
        "label": "未知 Status は capture_done があっても下位行に落ちない",
        "state": PipelineState(design_status="PENDING", capture_done=True),
        "expect": "H1",
    },
    {
        "id": "T14",
        "label": "PR 工程を省略し最終 capture だけで capture_done → クローズ",
        # Phase 3.5 は「スキップ可」。PR 前 capture を経ずに capture_done だけが
        # 立つタスクは実在する。P4a が capture_done を見ないと、ここで永久に留まる。
        "state": replace(REVIEWED, capture_done=True),
        "expect": "P5",
    },
    {
        "id": "T15",
        "label": "PR 済みだがフィードバック無し → 往復に入らずデプロイ続行",
        # `Feedback: no`（pr-feedback 対応後に戻した状態を含む）は P37 に入らない。
        "state": replace(
            AFTER_PR_CAPTURE,
            deploy_unchecked=True,
            pr_url="https://github.com/example/repo/pull/1",
            pr_feedback=False,
        ),
        "expect": "P35",
    },
    {
        "id": "T16",
        "label": "review-result.md の Status が未知語彙 → 即停止",
        "state": replace(REVIEWED, review_status="BOGUS"),
        "expect": "H2",
    },
    {
        "id": "T17",
        "label": "review-result.md があるが Status 行が無い → 即停止（P3 に落として上書きしない）",
        "state": replace(REVIEWED, review_status=""),
        "expect": "H2",
    },
    {
        "id": "T18",
        "label": "`PR: none` は PR 無し扱い → 往復に入らない",
        # tasklist の値をそのまま文字列で渡しても、`none` を PR ありと誤読しない。
        "state": replace(AFTER_PR_CAPTURE, deploy_unchecked=True, pr_url="none", pr_feedback=True),
        "expect": "P35",
    },
    {
        "id": "T19",
        "label": "マージ済み（デプロイ全チェック）なら古い Feedback: yes でも往復に居座らない",
        "state": replace(
            AFTER_PR_CAPTURE,
            capture_done=True,
            deploy_unchecked=False,
            pr_url="https://github.com/example/repo/pull/1",
            pr_feedback=True,
        ),
        "expect": "P5",
    },
    {
        "id": "T20",
        "label": "PR あり・フィードバックあり・PR 前 capture 無し → 往復が先（P37 は P4a より上）",
        "state": replace(
            REVIEWED,
            deploy_unchecked=True,
            pr_url="https://github.com/example/repo/pull/1",
            pr_feedback=True,
        ),
        "expect": "P37",
    },
]


def check_cases() -> list[tuple[str, str, list[str]]]:
    """(a) 各ケースの確定行。"""
    results = []
    for case in CASES:
        actual = resolve_phase(case["state"])
        details = []
        if actual != case["expect"]:
            details.append(f"expected={case['expect']}  actual={actual}")
            details.append(f"state={case['state']}")
        results.append((case["id"], case["label"], details))
    return results


def check_coverage() -> list[str]:
    """(b) 全行がいずれかのケースの期待値に現れる。"""
    expected = {case["expect"] for case in CASES}
    missing = [row for row in ROW_ORDER if row not in expected]
    if missing:
        return [
            f"期待値に一度も現れない行 ID: {', '.join(missing)}",
            "→ 直し方: 判定表に行を足したら CASES にもその行を期待するケースを足す",
        ]
    return []


def all_states():
    """入力の全直積。手書きケースに依存せず、到達可能性と全域性を検査するための列挙。

    値の候補は各入力の境界（欠落・未知語彙・空文字・`none`）を含む。約 5,800 状態で一瞬で回る。
    """
    urls = ("", "none", "https://github.com/example/repo/pull/1")
    review_statuses = (None, "OPEN", "RESOLVED", "DEFERRED", "", "BOGUS")
    design_statuses = (None, "DRAFT", "SPIKE", "APPROVED", "PENDING")
    for exists in (True, False):
        for ds in design_statuses:
            for impl in (False, True):
                for rs in review_statuses:
                    for deploy in (False, True):
                        for url in urls:
                            for fb in (False, True):
                                for pc in (False, True):
                                    for cd in (False, True):
                                        yield PipelineState(
                                            design_exists=exists,
                                            design_status=ds,
                                            impl_unchecked=impl,
                                            review_status=rs,
                                            deploy_unchecked=deploy,
                                            pr_url=url,
                                            pr_feedback=fb,
                                            pr_capture_done=pc,
                                            capture_done=cd,
                                        )


def check_reachability() -> list[str]:
    """C2: 全行が、入力の全直積のどこかで実際に確定する（上の行に隠れていない）。"""
    reached = {resolve_phase(state) for state in all_states()}
    unreachable = [row for row in ROW_ORDER if row not in reached]
    if unreachable:
        return [
            f"どの状態からも確定しない行 ID: {', '.join(unreachable)}",
            "上の行の条件に完全に隠れている（到達不能）。表の行順を見直す",
            "→ 直し方: より限定的な条件の行を、それを含む広い条件の行より上に置く",
        ]
    return []


def check_no_match() -> list[str]:
    """C3: 全直積のどの状態も、いずれかの行に当たる（表が全域を覆う）。"""
    orphans = [state for state in all_states() if resolve_phase(state) == NO_MATCH]
    if orphans:
        return [
            f"どの行にも当たらない状態が {len(orphans)} 件ある。例: {orphans[0]}",
            "→ 直し方: 判定表に fail-closed の行を足す（未知語彙は下位行へ落とさず止める）",
        ]
    return []


def check_capture_two_stage() -> list[str]:
    """(e) PR 前 capture の後に最終 capture が飛ばされない（Critical 2）。"""
    # PR を出した直後、この PR の差分に属する知見を保存する（PR 前 capture）。
    before_pr = replace(
        REVIEWED,
        deploy_unchecked=True,
        pr_url="https://github.com/example/repo/pull/1",
    )
    after_capture = apply_capture(before_pr, is_pre_pr=True)
    # PR がマージされ、デプロイ節が全部チェックされた後の状態。
    after_merge = replace(after_capture, deploy_unchecked=False)
    actual = resolve_phase(after_merge)
    if actual != "P4b":
        return [
            f"PR 前 capture の後にマージすると {actual} へ進んでしまう（期待: P4b）",
            "PR 前の capture が最終 capture のフラグを消費し、会話由来・横断の知見を保存する機会が消える",
            "→ 直し方: PR 前と最終で別のフラグを立て、判定表の Phase 4 行を 2 段に分ける",
        ]
    return []


TASKLIST_UNDONE = """# タスクリスト: x

## 実装
- [ ] a
- [x] b

## デプロイ
- [ ] PR 作成
- [ ] CI グリーン確認
- [ ] マージ
- PR: none
- CI: none
- Feedback: no
"""

TASKLIST_MERGED = """# タスクリスト: x

## 実装
- [x] a

## デプロイ
- [x] PR 作成
- [x] マージ
- PR: https://github.com/example/repo/pull/1
- CI: green
- Feedback: yes
"""

TASKLIST_NO_DEPLOY = """# タスクリスト: x

## 実装
- [x] a
"""


def check_parse_tasklist() -> list[str]:
    """C5: tasklist の書式（チェックボックスと固定キー）から入力への写像。"""
    problems = []
    undone = parse_tasklist(TASKLIST_UNDONE)
    expect_undone = {"impl_unchecked": True, "deploy_unchecked": True, "pr_url": "", "pr_feedback": False}
    if undone != expect_undone:
        problems.append(f"未着手の tasklist: 期待 {expect_undone} / 実際 {undone}")
    merged = parse_tasklist(TASKLIST_MERGED)
    expect_merged = {
        "impl_unchecked": False,
        "deploy_unchecked": False,
        "pr_url": "https://github.com/example/repo/pull/1",
        "pr_feedback": True,
    }
    if merged != expect_merged:
        problems.append(f"マージ済みの tasklist: 期待 {expect_merged} / 実際 {merged}")
    no_deploy = parse_tasklist(TASKLIST_NO_DEPLOY)
    if no_deploy.get("deploy_unchecked", True) or no_deploy.get("pr_url", "x") or no_deploy.get("pr_feedback", True):
        problems.append(f"デプロイ節が無い tasklist は未チェック無し・PR 無しのはず: {no_deploy}")
    # 固定キー行（`- PR: none` 等）はチェックボックスではないので、未チェック扱いにしない
    keys_only = parse_tasklist("## デプロイ\n- [x] マージ\n- PR: none\n- CI: none\n- Feedback: no\n")
    if keys_only.get("deploy_unchecked", True):
        problems.append("固定キー行（チェックボックスでない）を未チェックと数えている")
    if problems:
        problems.append("→ 直し方: 正本は design-doc/references/templates.md の tasklist テンプレート")
    return problems


# ID は行 ID（P1/S1/...）と混ざらないよう C 系で振る。
STRUCTURAL_CHECKS = [
    ("C1", "行 ID の網羅（表に足したらケースも足す）", check_coverage),
    ("C2", "到達可能性（全直積で、上の行に隠れた行が無い）", check_reachability),
    ("C3", "表が全域を覆う（全直積で、どの行にも当たらない状態が無い）", check_no_match),
    ("C4", "capture 2 段（PR 前の後に最終が飛ばない）", check_capture_two_stage),
    ("C5", "tasklist の書式から入力への写像", check_parse_tasklist),
]


def all_results() -> list[tuple[str, str, list[str]]]:
    """(id, label, details) のリスト。details が空なら PASS。"""
    results = check_cases()
    for check_id, label, fn in STRUCTURAL_CHECKS:
        results.append((check_id, label, fn()))
    return results
