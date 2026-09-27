# Decision: レビュー用のカスタム agent 定義を導入しない（読み取り専用 reviewer agent の見送り）

Date: 20260706
Status: Superseded by [20260927-subagent-roles-in-agent-definitions](20260927-subagent-roles-in-agent-definitions.md)（再検討トリガー「書き込み経路の観測」が S1 の実測で満たされた）

## Context

frontend-code-review のフルモードは 7 subagent を並列ディスパッチするが、全員が
汎用 subagent（Edit/Write 含む全ツール・デフォルトモデル）で動く。「レビューは読み取り
だけで足りるので `.claude/agents/reviewer.md` を定義し読み取り専用ツール＋安価モデルに
絞る」案（gap-analysis 提案 A1）を検討した。

## Decision

カスタム agent 定義は導入しない。レビュー subagent は現行どおり汎用ディスパッチのまま。
将来「レビュー agent がコードを誤編集した」を実際に観測したら、compound で最小版
（読み取りツール制限のみ・agent 未定義時は汎用フォールバック）を再検討する。

## Rationale

- 得られる安全性（誤編集防止）は本物だが、その事故はまだ観測されておらず予防的
  ハードニングに留まる（compound の「繰り返し出現するパターンを重視」の逆）。
- 失うコストが具体的:
  - ポータビリティの穴 — agent 定義は配置先にも別途コピーが要る隠れ依存。忘れると
    ディスパッチが壊れる/黙って汎用に落ちる（[[20260612-manual-copy-skill-distribution]]
    の自己完結原則に反する）。
  - エンジン純度の逆行 — ディスパッチ本文は現在ツール中立の散文。`subagent_type: reviewer`
    を書くと Claude Code 固有語彙が本文に入る（skill-design-patterns のツール語彙隔離に反する）。
  - haiku 化は correctness/security の微妙な指摘を取りこぼすトレードオフ。
- 天秤が見合わないのはこの設計（自己完結・単体コピー配布）に固有の理由であり、
  agent 機構自体を否定するものではない。

## Consequences

- Good: ポータビリティとエンジン純度を維持。レビュー subagent の権限モデルは 1 系統のまま。
- Bad: レビュー subagent は書き込み権限を持ち続ける（多重防御は入らない）。
  再検討トリガーを tasklist に明記して受け入れる。

## Alternatives considered

| Alternative | Reason rejected |
|---|---|
| 提案フル（読み取り制限 + haiku で1軸試験） | 精度リスク + ポータビリティ/純度コストが予防的利益に見合わない |
| 最小版（読み取り制限のみ・即実装） | 事故未観測。フォールバック分岐の複雑化に見合う根拠が現時点で無い |
