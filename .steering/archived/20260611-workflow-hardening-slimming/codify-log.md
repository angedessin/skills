
## 20260611 — compound 実行

### 昇格したパターン
- deny ルールのツール間パリティ（Bash/Read 対・glob 両形列挙） → docs/knowledge/claude-code-config.md（新規）
- hook スクリプトの堅牢化（$CLAUDE_PROJECT_DIR 絶対参照・成功メッセージの && 連結） → docs/knowledge/claude-code-config.md
- 不採用: 評価系スキルの実行/採点分離パターン（ユーザー判断で見送り）
- 効果検証: 20260603 昇格ルール 2 件の再発なし。skill-issues.md の EPT 指摘 5 件はコミット 7bc20ee で適用済みを確認

### 変更したファイル
- docs/knowledge/claude-code-config.md（新規作成）
- CLAUDE.md への @参照追加はユーザー判断でスキップ
