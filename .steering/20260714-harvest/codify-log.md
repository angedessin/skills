# Codify Log — 20260714 harvest

## [20260714] — compound 実行

### 昇格したパターン
- 環境構築タスクへの半フィット発動 + 初期質問の誤前提（issues #1・#2）→ design-doc v1.3（When NOT to use の環境構築分岐 + Phase 1 前置の切り分け + description）— コミット 2515de3
- 「単発は会話内・複数セッションは .steering」の境界が初見で不明瞭（issue #6）→ starter-kit.md の CLAUDE.md 雛形（同コミット）+ webgl-boilerplate CLAUDE.md の発動ポリシー行（配置先・承認済み）
- mise プロジェクトで bare pnpm/node が exit 127（issue #4）→ webgl-boilerplate CLAUDE.md 行動ルール
- rm -rf deny による手戻り（issue #5）→ webgl-boilerplate CLAUDE.md 行動ルール

### 見送ったパターン
- biome.json $schema の推測書きで手戻り（issue #3）→ 1 回限りに近くツール固有のため見送り。再発したら「設定ファイルは導入後に実バージョンで生成する」を webgl-boilerplate CLAUDE.md に昇格する

### 検証
- 静的層: validate_skills.py 28/28 PASS + template PASS
- 実行層: passthrough_check.py（design-doc シナリオ・2 run）を v1.3 に対して実行 → **PASS 2/2**（run 2 は「小さい作業」申告を縮退確認の回答の代用にせず、headless では安全側の .steering 作成を選択 — v1.2 の材料代用禁止句が実地で機能）

### 変更したファイル
- .claude/skills/design-doc/SKILL.md（v1.2→v1.3）
- docs/starter-kit.md（CLAUDE.md 雛形）
- /Users/kentaro/Desktop/_lab/ai/webgl-boilerplate/CLAUDE.md（発動ポリシー行 + 行動ルール 2 行）
