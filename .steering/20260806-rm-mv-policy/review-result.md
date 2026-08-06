# レビュー結果: rm-mv-policy

Date: 20260806
PR: https://github.com/angedessin/skills/pull/15
Mode: フル（スコープ読み替え: .sh/.py。a11y / UI / perf は対象なし）
Range: `integration/20260730-reports...HEAD`（57be75a）

## テスト（test-review）

重要な問題: 0件

| Axis | 問題 | ファイル | 分類 |
|------|------|----------|------|
| 全軸 | 問題なし（permissionDecision 観察・リスト 1:1・20/20） | `tests/hooks/run_fixtures.py` | — |

## 実装（impl-review）

重要な問題: 1件

| Axis | 問題 | ファイル | 分類 |
|------|------|----------|------|
| 設計整合 | 主要コンポーネント表は `tests/hooks/guard-gated-delete/` だが実装は `run_fixtures.py` インライン | `design.md` / `run_fixtures.py` | Medium |
| 設計整合（他） | 契約コア整合・permissions 不変・片側修正 — 問題なし | — | — |

## セキュリティ（review-security）

重要な問題: 5件（High 2 + Medium 3）

| Axis | 問題 | ファイル | 分類 |
|------|------|----------|------|
| 抽出 | JSON 内の二重引用パス（`rm "docs/knowledge/x.md"`）が `[^"]*` で切れ沈黙（実測） | `guard-gated-delete.sh:23` | High |
| パス | 末尾 `/` 無しディレクトリ（`rm -rf docs/knowledge`）が沈黙（実測） | `guard-gated-delete.sh:37` | High |
| パス | command 全文 grep のため `rm /tmp/a && ls docs/knowledge/` が誤 deny（実測） | `guard-gated-delete.sh:38` | Medium |
| パス | `CLAUDE.md` 部分一致で `CLAUDE.md.bak` 等も deny | `guard-gated-delete.sh:37` | Medium |
| 文書 | deploy コメントが deny ヒットを「フェイルオープン」と並記し過小評価 | `deploy_skills.py` | Medium |

## ロジック正当性（review-correctness）

重要な問題: 4件（High 2 は security と重複 → 統合）

| Axis | 問題 | ファイル | 分類 |
|------|------|----------|------|
| 境界 | 二重引用パス沈黙 | 同上 | High（→ security に帰属） |
| 境界 | 裸ディレクトリ沈黙 | 同上 | High（→ security に帰属） |
| 境界 | `\t`/`\n` JSON エスケープ未デコードで沈黙しうる | `guard-gated-delete.sh:26` | Medium |
| 境界 | `CLAUDE.md` 部分一致誤 deny | 同上 | Medium（→ security に帰属） |

## パフォーマンス / a11y / UI

対象なし

## 全体サマリー

- 重要な問題（統合後）: **High 2 / Medium 4**（重複統合: High 2 + Medium 1）
- モード: フル（読み替え）
- Low/Info: フィクスチャ置き場表記、アンエスケープ順序、など

### 推奨トリアージ（人間判断待ち）

| ID | 指摘 | 推奨 | 対応 |
|---|---|---|---|
| H1 | 二重引用パス沈黙 | **must-fix** | **済** — python3 JSON 抽出 + A9 |
| H2 | 裸ディレクトリ沈黙 | **must-fix** | **済** — 境界付き targets + A10/A11 |
| M1 | `&&` / コメント後の誤 deny | 修正推奨 | **済** — simple 切り出し + B19 |
| M2 | `CLAUDE.md` 部分一致 | 修正推奨 | **済** — トークン境界 + B20 |
| M3 | deploy コメント過小評価 | 文言修正 | **済** |
| M4 | design 表と runner パスずれ | APPROVED 追認 | **済** |
| M5 | `\t`/`\n` | H1 と同時 | **済**（JSON パーサ） |
