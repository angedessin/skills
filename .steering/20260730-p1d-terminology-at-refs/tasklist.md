# タスクリスト: p1d-terminology-at-refs

Last updated: 20260730

## 実装前（表の漏れ潰し）

- [x] 禁止語で全文検索し、表の漏れを潰す

## 実装

### 用語正本

- [x] `docs/starter-kit.md` L46 / L61
- [x] `docs/user-guide.md` L43
- [x] `.claude/skills/impl-from-design/SKILL.md`（フルモード 7 軸 → 7 エージェント）
- [x] `.claude/skills/impl-review/SKILL.md`（同上）
- [x] `.claude/skills/test-review/SKILL.md`（Related のみ。本文「5軸」は残す）
- [x] `.claude/skills/skill-deploy/SKILL.md`（review-* 7 軸フルモード）

### @残骸

- [x] ADR 20260715: Context 該当文を置換 + Amendments 20260730。Decision 核は不変
- [x] `rule-audit/SKILL.md` L41・L56 現行化。L97 参照切れ検出は残す
- [x] `CLAUDE.md` と `templates/SKILL.template.md` のサイズ表記を同じ実測に揃える

### BACKLOG

- [x] `.steering/BACKLOG.md` 節 4 の P1d を完了印（禁止語を含まない文言に）

## 検証

- [x] 対象パスで禁止語ゼロ（archive / archived 除外）
- [x] starter-kit 依存表に「7 エージェント」固定フレーズあり
- [x] rule-audit に「@参照として配線」現在形が無い（L97 残存）
- [x] CLAUDE と template のサイズ表記が一致（約49KB・547行）
- [x] `npm run validate` 29/29 PASS

## 知見保存（この PR / ブランチに載せる分）

- [x] decisions.md に用語境界・プレモータム反映を短く残す
- [ ] knowledge-capture は差分に属する知見があれば同ブランチへ（任意）

## レビュー

- [ ] ~~frontend-code-review~~ — 省略可（docs/ADR/スキル文言。人間が PR で確認）
- [ ] PR 作成前に差分を人間確認

## デプロイ

- [ ] PR 作成（base: `integration/20260730-reports`）
- [ ] CI グリーン確認
- [ ] マージ（**人間の明示指示があるまでしない**）

## 福利化 / クローズ

- [ ] compound（任意・別ゲート）
- [ ] steering archive（親へマージ後）
