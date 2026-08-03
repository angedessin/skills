# Decisions: design-impl-sync

## 20260803 — 設計承認（未解決は推奨一括）

**決定**: design.md を APPROVED。プレモータム由来の未解決 6 件はすべて推奨案で確定する
**理由**: ユーザーが「未解決は推奨案で approve」と明示。Phase 1.5 の骨格（コア→DRAFT 戻し / APPROVED 追認）はそのまま
**影響**:
- High 尺度に設計契約コア不一致を追加。Gate 3 の設計整合 DEFERRED に必須警告
- design あり＋契約成果物変更では軽量でも Axis 1 必須
- 機械検査は validate キーワード共存が主（passthrough 必須にしない）
- DRAFT 戻し時は review-result 破棄・作業ツリー残置前提
- Axis 1 ゲート級は APPROVED のみ。design 無しはスキップ維持

## 20260803 — レビュー High: 空 TS でも Axis 1

**決定**: impl-review に「契約成果物の Axis 1 例外」を追加し、FCR は空 TS でも impl-agent をディスパッチする。design 変更（DRAFT 戻し）は不要 — 承認済み完了条件の実装追完
**理由**: レビューで設計整合 High（ゲート不発）。分類は APPROVED 設計に対する実装不足
**影響**: impl-review v1.5 / frontend-code-review v1.6 / validate キーに「契約成果物の Axis 1 例外」追加
