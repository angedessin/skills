# 決定事項: p1d-terminology-at-refs

## 20260730 — 新規タスクとして切り出す

**決定**: P1d は既存 `20260730-report-driven-fixes` に追記せず、`.steering/20260730-p1d-terminology-at-refs/` を新規作成する。
**理由**: 既存 design は P1d を対象外にし親へマージ済み。完了条件を汚さない。
**影響**: 既存タスクの compound/archive は別クローズのまま。

## 20260730 — 用語正本は「7エージェント」

**決定**: 「7軸」を廃止。フルモード = 7エージェント（review-* 5 + impl-review + test-review）。review-* = 5 サブスキル。
**理由**: 実装（frontend-code-review）の語彙に合わせ、用語混線を消す。別名残しは再発する。
**影響**: starter-kit / user-guide の該当行を置換。

## 20260730 — @残骸は Context 置換 + Amendment + rule-audit

**決定**: ADR 20260715 の Decision / Consequences は触らず、Context 該当文を過去形／現行運用に置換し Amendments に 20260730 を追記。rule-audit L41・L56 を同梱修正。CLAUDE と template のサイズ誤記も対で直す。
**理由**: Decision 核は有効。Amendment だけだと Context 現在形が残る（プレモータム）。
**影響**: 参照切れ検出（consumer）は残す。

## 20260730 — 用語対象に関連 SKILL.md を含める

**決定**: starter-kit / user-guide に加え、フルモードを「7軸」と呼ぶ impl-from-design / impl-review / test-review / skill-deploy も同 PR で直す。
**理由**: プレモータムで docs 限定だと禁止語ゼロの完了条件と矛盾し、片側修正になることが判明。
**影響**: 配布可スキルの文言も変わる（挙動は不変）。

## 20260730 — 用語ドリフト永続ゲートは作らない

**決定**: 今回は手動 rg の完了条件のみ。CI / validate への用語ゲート追加はしない。
**理由**: 説明文修正パッケージにゲート新設は肥大。再発したら BACKLOG に積む。
**影響**: 3ヶ月後の再流入は検知されない（受け入れ済み）。
