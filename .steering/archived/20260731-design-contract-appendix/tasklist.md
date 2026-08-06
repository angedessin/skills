# タスクリスト: design-contract-appendix

Last updated: 20260731

## 実装前

- [x] 変更対象語で全文検索し、主要コンポーネント表の漏れを潰す（`design.md` を読む / `## 調査結果` / `## 未解決の論点` / `templates.md` / `プレモータム所見` / `主要コンポーネント` / `検討した代替案`）

## 実装

- [x] `design-doc/references/templates.md`: 節順入れ替え + `<!-- design-doc-boundary: appendix -->` + 付録説明
- [x] `design-doc/SKILL.md`: Phase 2 節列挙・境界必須・Phase 3 承認前必読（影響範囲・代替案）・継続時コア読み・方針転換の追記先
- [x] `impl-from-design/SKILL.md`: 既定コア・実装前に影響範囲例外・テスト方針/調査結果/データフロー都度・フォールバック
- [x] `design-premortem/SKILL.md`: 常に全文 + 所見は境界直後（マーカー無しなら EOF）
- [x] `steering/SKILL.md`: resume 要約はコアまで・構造説明の更新・フォールバック
- [x] `impl-review` / `adr` / `impl-tournament` / `feature-pipeline` / `debug` / `frontend-code-review`: 一文パッチ
- [x] `scripts/validate_skills.py`: テンプレに境界マーカー必須（`pnpm run validate`）
- [x] `docs/user-guide.md`: resume 行に契約コアまでの一文
- [x] `.steering/BACKLOG.md`: アクティブ design の境界追記は任意・強制しない、一行

## 検証

- [x] テンプレから境界を一時削除 → `pnpm run validate` FAIL → 戻す
- [x] `pnpm run validate` PASS（30/30）。回帰で `pnpm run validate:assets` PASS（7/7）
- [x] （一回限り）テンプレ節順がコア→境界→付録であること

## レビュー

- [x] frontend-code-review の実行（Markdown / スクリプト差分）
- [x] レビュー指摘の修正
- [x] 修正後の差分再レビュー（validate 30/30・操作定義追記確認）

## 知見保存（この PR / ブランチに載せる分）

- [x] knowledge-capture — **省略**（decisions / compound 済み。追加 knowledge なし）。`capture_done` 済み
- [x] compound（片側修正節に操作定義の具体例）— `codify-log.md` 記録済み
- [x] docs/ への追記をこのブランチでコミット（skill-design-patterns）

## デプロイ

- [x] base = `integration/20260730-reports` の PR 作成（[#6](https://github.com/angedessin/skills/pull/6)）
- [x] CI グリーン確認 — チェック無し（N/A）
- [x] マージ（PR #6 → integration/20260730-reports）

Archived: 20260731
