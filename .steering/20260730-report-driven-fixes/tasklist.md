# タスクリスト: report-driven-fixes

Last updated: 20260730

## 実装前（表の漏れ潰し）

- [x] 変更対象語で全文検索し、表の漏れを潰す（実装中に実施）

## 実装

### P0 — blockers ↔ knowledge-capture

- [x] `knowledge-capture` Step 1: find / 入力源に `blockers.md` を追加
- [x] Step 2: blockers 取捨の決定木分岐を追加
- [x] 空・欠落時はスキップ。ドラフト承認制は既存と同じ
- [x] CLAUDE.md / README の宣言と矛盾しないことを確認（宣言側は既存どおり有効）

### P1a — master-only 正本

- [x] `skill-design-patterns.md`: 4本列挙・置き場 `.claude/skills/`・ツールとの用語分離

### P1b — codify producer 対

- [x] `skill-design-patterns.md`: 二重化を現行形に
- [x] `docs/starter-kit.md`: 書く側 = FCR + knowledge-capture
- [x] `README.md`: producer 二重化に言及

### P1c — jq / フェイル方針

- [x] `claude-code-config.md`: lint/guard の jq・フェイル方針を実装に合わせる
- [x] `README.md`: guard / session-start の誤記を修正
- [x] `docs/starter-kit.md`: session-start の jq 記述を修正

### E1 — company Frozen（機械＋文書）

- [x] `scripts/check_export_stopcontract.py` 削除
- [x] `package.json` から `check:export` 削除
- [x] `check_asset_consistency.py`: (g)(i) / EXPORT_* / `--require-export` / 持ち出し発見を除去
- [x] `README.md`: ツリー・インフラ節から export 差分ガードを削除。契約員数を更新
- [x] `skill-test/SKILL.md`: 持ち出し検査節を Frozen・対象外化
- [x] `deployments.md`（ローカル）/ `deployments.example.md`: Frozen handoff 明記
- [x] `claude-code-config.md`: 防御パリティ現況義務 → 過去形＋個人配置向け一般則
- [x] `skill-design-patterns.md`: `check_export_*` に削除済み注記

### 検証

- [x] `npm run validate:assets` PASS（7/7）
- [x] `npm run validate` 29/29 PASS
- [x] `npm run validate:portability` 混入なし
- [x] `rg check_export_stopcontract` — 実体パス無し（削除済み注記のみ）
- [x] `rg blockers .claude/skills/knowledge-capture` ヒット
- [x] `package.json` に `check:export` 無し

## レビュー

- [ ] frontend-code-review（PR 前後で任意）
- [ ] レビュー指摘の修正
- [ ] 修正後の差分再レビュー

## デプロイ

- [ ] PR 作成（`pr-create`）
- [ ] マージ（人間）

## 福利化 / 知見

- [ ] compound（必要なら）
- [ ] knowledge-capture
- [x] `.steering/BACKLOG.md` に P1d / P2 / 後続候補を追記
- [ ] steering archive
