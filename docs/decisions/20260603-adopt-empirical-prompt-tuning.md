# Decision: プロンプト品質改善に empirical-prompt-tuning を採用

Date: 20260603
Status: Accepted

## Context

スキル作成後の品質検証手法として、このリポジトリ専用の `skill-tuner` を
自作する案を設計・実装した。しかし設計・議論の中で、汎用的な
`empirical-prompt-tuning` スキルが存在し、より完成度が高いことが判明した。

## Decision

`skill-tuner` の自作を中止し、`empirical-prompt-tuning` を採用する。
セキュリティチェックと欠落ステップ（1〜4）の補完を行って導入した。

## Rationale

- **評価軸**: skill-tuner は要件充足率1軸、empirical は7軸（定量+定性）
- **収束判定**: skill-tuner はスコア閾値、empirical は不明瞭点ゼロ+過適合チェック
- **汎用性**: skill-tuner はこのリポジトリ専用、empirical は任意のプロンプト対象
- **オーケストレーション対応**: フレッシュな subagent で評価するため、実際の自動化パイプラインでの挙動を正確に検証できる

## Consequences

- Good: 評価の精度が高く、孤立エージェント視点の問題も検出できる
- Good: 汎用的なので他プロジェクトにも持ち出せる
- Bad: サードパーティ製のためセキュリティチェックと欠落ステップ補完が必要だった

## Alternatives considered

| Alternative | Reason rejected |
|-------------|-----------------|
| skill-tuner を自作 | 評価軸・収束判定が不十分、汎用性がない |
| 評価なしでスキルをリリース | 品質の担保ができない |
