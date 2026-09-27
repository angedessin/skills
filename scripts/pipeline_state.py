#!/usr/bin/env python3
"""feature-pipeline の現在地判定表を純粋関数として写したもの（master-only）。

正本は `.claude/skills/feature-pipeline/SKILL.md` の「現在地の判定表」。
このモジュールはその表の**意味**を実行可能な形に写し、table-driven test で
到達可能性・優先順位・fail-closed を機械検査するためにある。
表と関数の同期は `scripts/check_asset_consistency.py` が行 ID 集合で突合する。

Usage: python3 tests/state/run.py
"""
from __future__ import annotations

import re
from dataclasses import dataclass, replace
from typing import Optional

# 判定表の行 ID と現在地。**SKILL.md の表の並び順と一致させる**（上が優先）。
# 行 ID は表 ↔ 関数の突合キーなので、行を消すとき以外は再利用しない。
ROWS: list[tuple[str, str]] = [
    ("P1", "Phase 1（計画）"),
    ("G1", "Gate 1 で停止（設計レビュー待ち）"),
    ("S1", "即停止（SPIKE はパイプライン外）"),
    ("H1", "即停止（fail-closed・未知 Status）"),
    ("P2", "Phase 2（実装）"),
    ("P3", "Phase 3（レビュー）"),
    ("G3", "Gate 3 で停止（指摘の修正対応待ち）"),
    ("H2", "即停止（fail-closed・未知の review Status）"),
    ("P37", "Phase 3.7（PR 往復 = pr-feedback）"),
    ("P4a", "Phase 4（知見蓄積・PR 前 = この差分に属する知見）"),
    ("P35", "Phase 3.5（PR / 統合）"),
    ("P4b", "Phase 4（知見蓄積・最終 = 会話由来・横断の残り）"),
    ("P5", "Phase 5（クローズ）"),
]

ROW_ORDER: list[str] = [row_id for row_id, _ in ROWS]
PHASE_BY_ROW: dict[str, str] = dict(ROWS)

# どの行にも当たらなかったことを表す番兵。表が全域を覆っていれば現れない。
NO_MATCH = "HALT_NO_MATCH"

DESIGN_STATUSES = ("DRAFT", "SPIKE", "APPROVED")
REVIEW_STATUSES = ("OPEN", "RESOLVED", "DEFERRED")


@dataclass(frozen=True)
class PipelineState:
    """判定表の入力。成果物から観測できる値だけを持つ。"""

    design_exists: bool = True
    # design.md の Status。None は Status 行の欠落。未知語彙はそのまま入れる。
    design_status: Optional[str] = "APPROVED"
    impl_unchecked: bool = False
    # review-result.md が無い場合は None。ファイルはあるが Status 行が無い場合は ""（未知と同じ扱い）。
    review_status: Optional[str] = None
    deploy_unchecked: bool = False
    # tasklist の `PR:` の値をそのまま入れてよい（`none`・空は PR 無しとして扱う）。
    pr_url: str = ""
    pr_feedback: bool = False
    pr_capture_done: bool = False
    capture_done: bool = False


def has_pr(pr_url: str) -> bool:
    """`PR:` の値が実在する PR を指すか。`none`・空は PR 無し（文字列 "none" を真と誤読しない）。"""
    return pr_url.strip().lower() not in ("", "none")


def resolve_phase(state: PipelineState) -> str:
    """判定表を上から評価し、最初にマッチした行の ID を返す。

    戻り値は行 ID（`PHASE_BY_ROW` で現在地の表示名に変換できる）。
    """
    if not state.design_exists:
        return "P1"
    if state.design_status == "DRAFT":
        return "G1"
    if state.design_status == "SPIKE":
        return "S1"
    if state.design_status != "APPROVED":
        # 未知・欠落は下位行へ落とさない（fail-closed）。
        return "H1"
    if state.impl_unchecked:
        return "P2"
    if state.review_status is None:
        return "P3"
    if state.review_status == "OPEN":
        return "G3"
    if state.review_status not in ("RESOLVED", "DEFERRED"):
        # 未知語彙・Status 行の欠落は下位行へ落とさない（fail-closed。H1 の review 側）。
        # P3 に落とすと、既にある review-result.md をやり直しで上書きしかねない。
        return "H2"
    if state.review_status in ("RESOLVED", "DEFERRED"):
        # 未対応のフィードバックが返っている PR が最優先。P35 より**上**に置く —
        # 下に置くと「デプロイ節に未チェックあり」が先に成立し、往復対応の行に
        # 永久に到達しない（Critical 1）。pr-feedback が対応を終えたら
        # tasklist の `Feedback:` を `no` に戻すことでこの行を抜ける。
        # デプロイ節が全チェック済み（= マージ済み）なら、`Feedback:` が古いまま残っていても
        # 往復に居座らない。
        if has_pr(state.pr_url) and state.pr_feedback and state.deploy_unchecked:
            return "P37"
        # PR 差分に属する知見の保存。tasklist 正本の工程順（知見保存 → デプロイ）に
        # 合わせて P35 より上に置く。`capture_done`（最終）が既にあれば PR 前の分は
        # 包含済みなので P4a に入らない — PR 工程を省略したタスクが、
        # `pr_capture_done` を立てる機会の無いまま P4a に永久に留まるのを防ぐ。
        if not state.pr_capture_done and not state.capture_done:
            return "P4a"
        if state.deploy_unchecked:
            return "P35"
        if not state.capture_done:
            return "P4b"
        return "P5"
    return NO_MATCH


def capture_flag(is_pre_pr: bool) -> str:
    """knowledge-capture が完了時に立てるフラグ名を返す。

    `knowledge-capture/SKILL.md` の契約を写したもの。PR 前と最終で別のフラグを
    立てることで、PR 前の capture が最終 capture の機会を消さないようにする
    （両者を 1 つの `capture_done` にまとめると、マージ後に Phase 5 へ飛ぶ）。
    """
    return "pr_capture_done" if is_pre_pr else "capture_done"


def apply_capture(state: PipelineState, is_pre_pr: bool) -> PipelineState:
    """knowledge-capture を 1 回実行した後の状態を返す（フラグ書き込みの反映）。"""
    flag = capture_flag(is_pre_pr)
    if flag == "pr_capture_done":
        return replace(state, pr_capture_done=True)
    return replace(state, capture_done=True)


def _section(text: str, heading: str) -> str:
    """`## <heading>...` から次の `## ` 直前までの本文。節が無ければ空文字。"""
    m = re.search(rf"^## {re.escape(heading)}.*?(?=^## |\Z)", text, re.M | re.S)
    return m.group(0) if m else ""


def parse_tasklist(text: str) -> dict:
    """tasklist.md から判定入力（PipelineState のうち tasklist 由来の 4 項目）を読む。

    正本は `design-doc/references/templates.md` の tasklist テンプレート:
    - 未チェック = 「実装」「デプロイ」節の `- [ ]`。固定キー行（`- PR:` 等）はチェックボックスではないので数えない
    - `- PR:` の値は URL か `none`（`none`・空は PR 無し → 空文字に正規化）
    - `- Feedback:` は `yes` のときだけ真
    節が無い tasklist は未チェック無し・PR 無し・フィードバック無し（旧形式）。
    戻り値は `replace(PipelineState(...), **parse_tasklist(text))` にそのまま渡せる。
    """
    unchecked = re.compile(r"^\s*- \[ \]", re.M)
    deploy = _section(text, "デプロイ")
    pr = re.search(r"^- PR:[ \t]*(.*)$", deploy, re.M)
    pr_url = pr.group(1).strip() if pr else ""
    feedback = re.search(r"^- Feedback:[ \t]*(\S+)", deploy, re.M)
    return {
        "impl_unchecked": bool(unchecked.search(_section(text, "実装"))),
        "deploy_unchecked": bool(unchecked.search(deploy)),
        "pr_url": pr_url if has_pr(pr_url) else "",
        "pr_feedback": bool(feedback and feedback.group(1).lower() == "yes"),
    }
