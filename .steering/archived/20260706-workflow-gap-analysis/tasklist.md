# tasklist — workflow-gap-analysis

- [x] 現状のワークフロー確認（README・CLAUDE.md・hooks 4本・settings.json・skills 19本・archived tasklist の未チェック項目）
- [x] ギャップ分析と追加候補のドキュメント作成（proposal.md）
- [x] 人間レビュー: proposal.md の採否判断（H1+R1・H2 を採用）
- [x] H1: SessionStart hook `session-start-check.sh`（フラグ＋アクティブタスクを additionalContext 注入）+ settings.json 登録
- [x] R1: CLAUDE.md「セッション開始時」節から手動 find（1〜3項）を剪定、hook 移管を明記
- [x] H2: PostToolUse hook `validate-skill-edit.sh`（SKILL.md 編集後に validate_skills.py を該当スキルのみ実行、違反を exit 2 差し戻し）+ validate_skills.py に `--skill` 単一検証モード追加 + settings.json 登録
- [x] 検証: settings.json JSON 妥当性 / `--skill` PASS・FAIL / H1 注入 / H2 ブロック・素通し・フェイルオープン
- [x] S1（選択肢 A: マスター取り込み）: `pr-create` スキルを新規作成（本文ツール中立 + references/commands.md カートリッジ、ハードストップ = プッシュ/PR 作成前の明示承認・マージ非実行の境界）。README に「統合」カテゴリと行を追加、feature-pipeline の「ビルトイン」表記を「マスタースキル/未配置なら gh 代替」に修正（全箇所 grep 済み）
- [~] A1（読み取り専用 reviewer agent）: **見送り**。安全性メリットは本物だが未観測の事故への予防に留まり、得る安全性（推測ベース）に対し失うコスト（配置先にも agent 定義が必要＝ポータビリティの穴・本文へのツール固有語彙流入＝エンジン純度の逆行）がこの設計の核の価値に具体的に刺さる。**再検討トリガー**: 「レビュー agent がコードを誤編集した」を実際に観測したら compound で最小版（読み取りツール制限のみ・agent 未定義時は汎用フォールバック）を検討
- [x] knowledge-capture: ADR `docs/decisions/20260706-no-custom-reviewer-agent.md`（A1 見送りの設計判断）を保存。ドラフト2/3（skill-design-patterns・claude-code-config への短い追記）は compound 領域として見送り
- [~] S2（refactor スキル）: **保留（見送り寄り）**。入口の穴は埋まるが、スキル数増・境界維持コスト・design-doc との重複・トリガーの曖昧さで純増分が細い。**着手トリガー**: refactor 依頼が手順なしで実際にコケる事象を 2〜3 回踏んだら compound でスキル化を検討
- [~] S3（dependency-update スキル）: **保留（将来の勝ち筋は S2 より強い）**。稀・高リスクでチェックリスト向き、deny ポリシーの案内欠落を補完、trigger（依存 drift）は確実。**着手方針**: 次に実際に依存更新が発生したら design-doc で 1 回回し、そのケースを土台にフルスキル or 軽量チェックリストを見極めて作る
- [ ] 未着手（別セッション）: レビュースリム化後半

Archived: 20260706
