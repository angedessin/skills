# Tasklist: review-axes-coverage

Last updated: 20260702（Implementation 全完了・構造検証パス）

## Implementation

- [x] `review-correctness/SKILL.md` 新設（4軸: 境界条件 / null・undefined / 非同期レース・stale closure / 状態遷移矛盾・エラー握りつぶし）
- [x] `review-ui/SKILL.md` 新設（3軸: レイアウト・レスポンシブ / デザイン整合 / UX 状態網羅）
- [x] `review-ui/references/tokens.md` 雛形作成（example — 配置先で再生成の明記）
- [x] `frontend-code-review` 改訂: Phase 2A に correctness-agent / ui-agent 追加（スコープ表・ディスパッチ条件）
- [x] `frontend-code-review` 改訂: Phase 2B（軽量モード）に review-ui 条件追加（CSS/SCSS 変更を含む場合のみ）
- [x] `frontend-code-review` 改訂: Phase 3 重複統合ルールに新軸の帰属を追記、description の「5エージェント」→「7エージェント」更新
- [x] `design-doc/references/templates.md` の review-result.md テンプレートに Correctness / UI セクション追加
- [x] README 更新: レビュー節スキル表（2行追加）・「5エージェント並列」表記（図・テーブルとも）・スキル間関係図

## Verification

- [x] 構造検証: name 一致 / description ≤1024（150・154・191 文字）/ 本文 <500 行（135・122・268 行）/ アストラル面絵文字なし（python 走査）
- [ ] empirical-prompt-tuning: review-correctness をフレッシュ subagent で実行・両面評価 **（ユーザーが実施 — 20260702 分担決定）**
- [ ] empirical-prompt-tuning: review-ui をフレッシュ subagent で実行・両面評価（トークン無しプロジェクトでの縮退動作を含む）**（ユーザーが実施 — 同上）**
- [ ] 統合検証: フルモード 1 回実行し 7 エージェントのディスパッチと review-result.md 記録を確認 **（このリポジトリは Markdown のみで .ts/.tsx diff が作れないため、React プロジェクトへの配置後の初回利用時に実施）**

## Deploy
<!-- git push してブランチを PR にするフェーズ。CI がないリポジトリはスキップ可。 -->

- [ ] コミット（マスターへの反映）
- [ ] 配置先プロジェクトへの再コピー要否の判断（source-commit 記録）

## Compound

- [ ] compound スキルの実行（実装中に見つけたパターンをルール・知識に昇格）

## Knowledge

- [ ] knowledge-capture スキルの実行
- [ ] steering archive モードでアーカイブ
