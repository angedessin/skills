# 決定ログ: design-contract-appendix

## 2026-07-31 — Phase 1.5

**決定**: 分離の形は同一ファイル内の契約コア / 付録境界 + 読み契約（案 A）
**理由**: ADR 20260611 の 1 ファイル承認を維持しつつ、テンプレと読み手順を動かして context 税を減らす
**却下**: 物理分割（B）、説明のみの節選択（C）

**決定**: 契約コア = Status / 目的 / スコープ / 制約 / 完了条件 / アプローチ / 主要コンポーネント / 未解決の論点（案 A）
**理由**: impl-from-design の実装スコープ表をコアに残す。テスト方針は例外読み
**却下**: 主要コンポーネントを付録へ（B）、テスト方針をコアへ（C）

## 2026-07-31 — 承認（未解決論点の確定）

**決定**: Phase 3 承認前必読 = 契約コア + 付録の `影響範囲` + `検討した代替案`（コアへは戻さない）
**決定**: impl-from-design は実装開始前に `影響範囲` を例外追加。データフローは都度
**決定**: 追加読み手は一文パッチ（impl-review=コア / adr・impl-tournament=付録開く / feature-pipeline・debug・frontend-code-review=スキップ明記）
**決定**: 境界無し live design は全文フォールバック維持。BACKLOG に任意移行一行。強制移行しない
**決定**: コア行数上限は YAGNI
**決定**: 機械検査は `validate_skills.py`（`pnpm run validate`）
**決定**: user-guide は resume 一行同梱
**決定**: 読み打切りのフィクスチャ/passthrough 検証は対象外
**決定**: 検証コマンド表記は `pnpm run`（mise で pnpm 復帰済み）
