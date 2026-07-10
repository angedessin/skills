# Tasklist: workflow-companion-skills

design.md 承認後に着手。実装は別モデルが行う前提 — 各タスクは design.md の該当節を一次情報として参照すること。
共通規律: templates/SKILL.template.md から書き始める / 絵文字禁止 / validator 全 PASS / 片側修正の禁止（閉じる前に grep）。

実装ログ: 20260711 実装完了（26/26 validator PASS）。詳細は decisions.md 参照。

## 1. pr-feedback（最優先）

- [x] `.claude/skills/pr-feedback/SKILL.md` 作成（STOP x2: 対応計画承認・外向き操作承認）
- [x] `references/commands.md` 作成（GitHub CLI カートリッジ・別ホスト差し替え注記）
- [x] pr-create 側に境界相互明記を追記（同一コミット）
- [x] README ワークフロー図 [6.5] 挿入 + スキル一覧 + 関係図 + feature-pipeline 改訂（同一コミット）
- [x] validate_skills.py PASS 確認

## 2a. validator 拡張（静的層）

- [x] 項目 6: `## When NOT to use` 存在チェック追加（見出しに "When NOT to use" を含めば可）
- [x] 項目 7: 停止契約の構造検査追加（承認語彙 → ハードストップ表現。`<!-- validator: no-stop-needed -->` エスケープ・否定形除外）
- [x] 項目 8: `--purity` ツール純度レポートモード追加（FAIL にしない）
- [x] 既存 20 スキルの落ち分を修正（rule-audit/feature-pipeline は真の停止点にハードストップ追記、impl-review/test-review/steering はエスケープ、review-* 7件+empirical+fcr に When NOT to use 追加）
- [x] README「インフラ・設定」の検証スクリプト説明を 5 項目 → 7 項目 + purity に更新

## 3. design-premortem

- [x] `.claude/skills/design-premortem/SKILL.md` 作成（敵対チェックリスト 6 観点・subagent 不可時フォールバック・承認しない役割制約）
- [x] design-doc の Phase 2→3 間（Phase 2.5）に任意提案の 1 文追加（相互明記・同一コミット）
- [x] README スキル一覧 + 図注記
- [x] validate_skills.py PASS 確認

## 4. session-retrospective

- [x] `.claude/skills/session-retrospective/SKILL.md` 作成（5 分類採掘・ゼロ件時は起票しない・アクティブタスク無し時フォールバック）
- [x] compound に原料供給元として 1 行追記（同一コミット）
- [x] README スキル一覧 + 自己改善ループ図に追記
- [x] validate_skills.py PASS 確認

## 5. skill-harvest（マスター専用）

- [x] `deployments.md` レジストリ作成（ルート直下・パスのみ・コメントテンプレート）
- [x] `scripts/check_deploy_drift.py` を拡張（レジストリモード + issues 回収/マーカー切り分け。単一パスモード互換維持・読み取り専用維持）
- [x] scratchpad にダミー配置先を作って拡張分を確認 + 既存3分類の回帰確認
- [x] `.claude/skills/skill-harvest/SKILL.md` 作成（STOP: 再コピー承認・ドリフト差分の事前提示）
- [x] starter-kit.md: 配置手順に deployments.md 登録を追加 + 選定表にマスター専用の明記 + session-retrospective 併配推奨の注記（同一コミット）
- [x] validate_skills.py PASS 確認

## 6. impl-tournament

- [x] `.claude/skills/impl-tournament/SKILL.md` 作成（STOP x2: コスト承認〔無料代替併記必須〕・勝者選定。Step 0 は APPROVED 成果物チェック）
- [x] `references/commands.md` 作成（worktree カートリッジ + モデル振り分けの具体指定）
- [x] README スキル一覧 + 関係図に追記
- [x] validate_skills.py PASS 確認

## 7. skill-test 実行層（最後・任意）

- [x] `scripts/passthrough_check.py` 作成（サンドボックス → SHA1 前後差分 → 2 run 判定・--dry-run 追加）
- [x] `tests/passthrough/design-doc/scenario.md` を先行 1 本作成（エンドツーエンド確認用・--dry-run で構造検証済み）
- [x] `.claude/skills/skill-test/SKILL.md` 作成（Step 2 に課金明示 + 無料代替 + STOP。hooks 接続禁止の明記）
- [ ] 残りシナリオ整備（impl-from-design / debug / pr-create / 新設 4 スキル）— 実行は任意・デフォルトで回さない（未着手・任意）
- [x] validate_skills.py PASS 確認

## 仕上げ

- [x] 変更した契約・語彙をリポジトリ全体で grep（片側修正の禁止の最終確認 — 6スキルREADME反映・3対の相互明記確認済み）
- [x] `python3 scripts/validate_skills.py` 全体 PASS（26/26 + template）
- [x] test-review / tdd 実行チェック（対象外 — スキルリポジトリのため validator が代替）
- [x] knowledge-capture 実行（skill-design-patterns.md に「配布分類 + producer/consumer 対」「課金前置承認 + hooks禁止」を追記。静的検査機械化の洞察はハードストップ節に1文折込。#3のメカニクスはコード側に既存のため doc 化見送り）
- [ ] steering archive — 別ステップ（ユーザー判断）
