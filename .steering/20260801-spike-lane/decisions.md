# 決定事項: spike-lane

## 20260801 — Phase 1.5

**決定**: SPIKE は (1) `design.md` の `Status: SPIKE` で表す (2) ローカル実装のみ可・PR/push/マージ禁止・学びは `decisions.md` (3) 出口は破棄 or 契約コア更新のうえ DRAFT 戻し→通常承認。SPIKE→APPROVED 直昇格は禁止
**理由**: personal-friction 指摘 5 に沿い、既存 Status ゲートを壊さず探索を第一級化する。専用スキルや会話フラグは経路増加・揮発の欠点がある
**影響**: design-doc / impl-from-design / pr-create / feature-pipeline / steering / README / user-guide / starter-kit / passthrough が同一タスクの変更対象

## 20260801 — 設計承認（未解決は推奨案で確定）

**決定**: design.md を APPROVED。プレモータム後の未解決は推奨案どおり確定する  
- 入口: 生成時選択と既存 DRAFT からの明示遷移の**両方**  
- 破棄: 差分提示→確認後のみ戻す（黙って hard reset しない）  
- impl-tournament: SPIKE 不可を一文追加  
- 外向き防衛: **B**（impl-from-design 等にも SPIKE 中の push/remote/PR 禁止を横断）  
- DRAFT 戻しで差分を残す場合: 追認経路を本スライスに含め、黙った残置は禁止  
- tdd 直呼び等: **対象外に明示**（全入口一本化はしない）  
- 滞在上限: **受容**し、短い探索の一文を README 等に書くだけ  
**理由**: 承認時に個別修正が無かったため、design 上の推奨を採用  
**影響**: 実装は上記を前提に進める
