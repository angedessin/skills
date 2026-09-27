# AI駆動開発ワークフロー 客観評価レポート

評価日: 2026-08-29  
対象: `/Users/kentaro/Desktop/_lab/ai/skills`  
主基準: Anthropic / Claude Code 公式ドキュメント  
補助基準: OpenAI Codex、Cursor、GitHub Copilot の公式ドキュメント  
評価者: Cursor上のGPT-5.6 Sol（リポジトリ調査2系統・公式資料調査1系統を独立実行後に統合）

## 1. 結論

総合評価は **3.8 / 5.0** です。

このワークフローは、2026年8月時点のClaude Code公式推奨に**構造面ではかなり強く整合**しています。特に、短い常時指示とオンデマンドskillsの分離、成果物による長期タスク状態管理、Planと実装の分離、hooks・permissions・静的検査の多層化、subagentによる調査・レビューの隔離、証拠ベースの完了判定は、Anthropicの現行ガイダンスと一致します。

ただし「最新推奨どおり完成している」とは評価できません。主因は、中心オーケストレーターの状態遷移に実害のある矛盾が2件あり、全静的検査が成功しても検出できないことです。また、承認回数の多さ、実行回帰テストの不足、CI不在、sandbox設定不在、配置先ドリフトの常態化により、設計思想の成熟度ほど運用品質が追いついていません。

端的には、**設計思想は先進的、静的保証は強い、状態機械と継続的実行保証は未完成**です。

## 2. 評価の読み方

### 5段階尺度

- 5: 公式推奨を満たし、機械検証と運用実績まで揃う
- 4: 公式推奨に概ね整合し、軽微または限定的な不足がある
- 3: 有効な設計だが、重要な不足または未検証部分がある
- 2: 一部有効だが、主要経路に構造的な欠陥がある
- 1: 目的を安定して達成できない

### 総合点の重み

- Claude公式適合性: 20%
- ワークフロー設計: 15%
- 状態遷移の正しさ: 15%
- 検証可能性: 15%
- 安全性: 10%
- コンテキスト効率: 10%
- 保守性: 10%
- 移植性・利用体験: 5%

総合点は各軸の加重平均を小数第1位へ丸めた参考値です。重大な欠陥を平均値で隠さないため、Critical / High所見を別途優先します。

## 3. 調査対象と方法

### リポジトリ内

- `CLAUDE.md`、`README.md`
- `.claude/skills/` の全29スキル
- `.claude/hooks/` の全9スクリプト
- `.claude/settings.json`
- `templates/`、`scripts/`、`tests/`
- `docs/knowledge/`、`docs/decisions/`、`docs/archive/`
- `.steering/archived/` の過去設計・レビュー・検証記録

### 外部資料

Anthropic公式資料から評価基準を先に作り、その後でリポジトリを照合しました。他社資料は、Anthropicだけに依存しない一般性の確認と、製品差による反証に限定しました。

### 事実と評価の分離

- 事実: ファイル内容、テスト結果、公式資料に明記された仕様
- 推論: 事実から導く運用上の影響
- 提案: 本評価から分離した「改善案コラム」

### 再評価用スナップショット

- 評価対象のワークフロー本体: Git commit `b09b24718925a228faf09ac873df3cb80e525f1d`
- 最終確認時の作業ツリー: ワークフロー本体に未コミット差分なし。未追跡は本レポートと `.steering/20260829-workflow-objective-evaluation/` のみ
- 本文中のリポジトリ内パスは、特記がなければ対象リポジトリルートからの相対パス
- 行番号は探索用の補助情報であり、再評価では上記commitのファイル内容を正本として確認する
- 外部資料は2026-08-29確認時のライブページ。固定版がないため、再評価日は別途記録し、内容変更の可能性を考慮する

同じ静的状態を再検査する場合は、上記commitをcheckoutしたうえで、7節のコマンドを実行します。Critical 2件は、3節の通常経路と5.3節の証拠ファイルを照合し、状態条件を表の上から適用して再現します。総合点は2節の8軸スコアと重みから再計算でき、改善案を評価入力から除外する場合は「改善案コラム」以降を渡しません。

## 4. ワークフローの実像

このリポジトリは「プロンプト集」ではなく、`.steering/[task]/` の成果物を状態ストアにした、半自動の開発ハーネスです。

通常経路は次のとおりです。

1. `design-doc`: 要求整理、決定インタビュー、設計承認
2. `impl-from-design`: APPROVED確認、実装、TDDまたは非コード検証
3. `frontend-code-review`: 最大7軸の専門レビュー
4. `knowledge-capture`: PR差分に属する知見の保存
5. `pr-create` / `pr-feedback`: PR作成、CI、レビュー往復
6. 人間によるマージ判断
7. `knowledge-capture` / `compound`: 残りの知見保存とルール昇格
8. `steering archive`: タスクの永続化

保証は4層に分かれます。

- 自然言語契約: 各`SKILL.md`の前提、停止条件、委譲先
- 状態契約: `design.md`、`tasklist.md`、`review-result.md`、フラグ
- 操作ガード: permissions、PreToolUse / PostToolUse / Stop hooks
- 検査: validator、資産整合検査、hook fixtures、任意のpassthrough実走

この分離自体は優れています。LLMの「理解した」という自己申告を保証として扱わず、可能な範囲をファイル状態と機械検査へ移しているためです。

## 5. 観点別評価

### 5.1 Claude公式適合性 — 4.4 / 5

確信度: 高  
重大度: 適合性は高いが、未充足項目は運用へ影響

強く整合している点:

- `CLAUDE.md`を常時必要な行動規則に限定し、詳細をskillsとknowledgeへ逃がしている
- skillsを単一目的、明確なdescription、必要時だけ読むreferencesで構成している
- 複雑な作業で計画と実装を分離し、設計承認前の編集を禁止している
- 長期タスクの進捗と判断を会話外の構造化成果物へ保存している
- 大規模調査と多軸レビューをsubagentへ隔離している
- lint、typecheck、fixtures、差分、SHA1など実行可能な合否信号を重視している
- 人間のレビューとマージ判断をAIレビューで置き換えていない

部分適合:

- AnthropicとCursorは複雑な変更にPlanを推奨する一方、小さく既知の変更では直接実装を認めています。本ワークフローにも小バグ・設定作業・1セッション縮退の例外はありますが、新タスクでは決定インタビューを1問ずつ2〜3回行うため、公式推奨より重い運用です
- permissionsとhooksはあるものの、OSレベルのsandbox設定はありません
- subagentを専門化していますが、レビューagentのツール権限を読み取り専用へ限定していません

判定: **最新のClaude推奨に概ね沿っているが、安全性と利用摩擦に未完成部分がある**。

### 5.2 ワークフロー設計 — 4.4 / 5

確信度: 高  
重大度: 強み

評価:

- 設計、実装、レビュー、統合、知見保存の責務境界が明確
- DRAFT / SPIKE / APPROVEDとOPEN / RESOLVED / DEFERREDを契約値にしている
- 設計変更時にDRAFTへ戻す経路があり、承認済み設計と実装の乖離を隠さない
- knowledge-capture、compound、rule-auditを「保存・昇格・剪定」に分けている
- 配布と回収をskill-deploy / skill-harvestへ分離している
- 過去の失敗をADR、knowledge、testsへ還元する学習ループがある

減点理由:

- オーケストレーターと個別skillの双方がゲートを持ち、実利用時の停止回数が全体図から予測しにくい
- READMEがいう「主要ゲート4点」と、利用者が体験する確認回数が一致しない

### 5.3 状態遷移の正しさ — 2.7 / 5

確信度: 高  
重大度: Critical

Critical 1: `feature-pipeline`のPR往復フェーズが通常状態で到達不能です。

`feature-pipeline/SKILL.md`は判定表を上から評価します。`review-result.md`が解決済みで「デプロイ」に未チェックがあればPhase 3.5へ確定し、その後の「PR URLがありフィードバックあり」というPhase 3.7条件を評価しません。PRが作成済みでもマージ前は通常「デプロイ」に未チェックが残るため、resume時にPR往復へ到達できません。

証拠:

- `.claude/skills/feature-pipeline/SKILL.md:70-89`
- `scripts/check_asset_consistency.py:50-56`はフェーズ順序を意図的に検査対象外としている

Critical 2: PR前後の2段階knowledge-captureを単一`capture_done`で表現しています。

tasklistとREADMEは「PR前の差分固有知見」と「マージ後の残り」を分けています。しかしknowledge-captureはどちらでも同じ`capture_done`を作り、pipelineはこのフラグがあればPhase 5へ進みます。PR前captureを正しく実施すると、マージ後captureを飛ばせます。またpipeline本文にはPR前captureの具体的フェーズがありません。

証拠:

- `.claude/skills/design-doc/references/templates.md:134-161`
- `.claude/skills/knowledge-capture/SKILL.md:243-264`
- `.claude/skills/feature-pipeline/SKILL.md:84-89, 223-284`

High: steering仕様と現行tasklistテンプレートの工程順がドリフトしています。

- 現行テンプレート: レビュー → PR前知見保存 → デプロイ → 福利化 → クローズ
- steering仕様: レビュー → デプロイ → 福利化 → 知見保存

証拠:

- `.claude/skills/design-doc/references/templates.md:119-161`
- `.claude/skills/steering/references/spec.md:90-123`

### 5.4 検証可能性 — 3.5 / 5

確信度: 高  
重大度: High

強み:

- 29スキルの構造と停止語彙を検査
- 10種類の資産間契約を双方向に突合
- hookの正常・誤検知境界をfixtures化
- passthroughは自己申告でなく変更前後SHA1で停止契約を判定
- 静的検査の限界をソースコメントで明記

弱み:

- validatorの意味整合検査はキーワード共存であり、「空文でも通る」と自認している
- 21 passthroughシナリオのうちfeature-pipelineはGate 1のみで、Phase 3.5 / 3.7 / 4を検証しない
- 今回は課金を伴うpassthrough実走をしておらず、dry-runはシナリオ構造しか保証しない
- hook fixturesは主にdelete / write guardへ偏り、残りのhook経路を十分に固定していない
- `.github/workflows/`がなく、検査はローカルhookまたは手動実行に依存する
- Critical 2件と仕様ドリフトが、静的検査全成功のまま存在する

### 5.5 安全性・権限境界 — 3.7 / 5

確信度: 高  
重大度: High

強み:

- 依存追加、秘密情報、破壊的git操作、force pushをdeny
- 外向き操作と保護文書編集をaskへ分類
- Bash経由の承認迂回をPreToolUse hooksで補完
- サードパーティskillを敵対入力として扱うsecurity-auditを持つ
- 課金検査を自動hookへ接続しない

限界:

- write guardは`>`, `>>`, `tee`中心で、任意インタプリタや`sed -i`を完全には防げない
- delete guardは`bash -c`、`git rm`、`/bin/rm`、複合コマンド等を意図的に対象外とする
- 品質hooksは依存不足時にフェイルオープンする
- sandbox設定がなく、Bashと子プロセスのOSレベル境界を明示していない
- MCP、ブラウザ、外部APIは各ツール固有のガードレールに依存する
- レビューsubagentに最小権限を付与する仕組みがない

結論: 多層防御は優秀ですが、**アクセス制御の完全性ではなく、事故確率を下げる実用的ガード**として評価すべきです。

### 5.6 コンテキスト効率 — 4.0 / 5

確信度: 中〜高  
重大度: Medium

強み:

- `CLAUDE.md`を行動規則へ限定
- knowledgeを常時`@`展開せず必要時に読む
- skillsとreferencesによる段階的開示
- design.mdを契約コアと付録に分割
- subagentで大量調査を隔離
- SessionStartはバックログ本文でなく存在と節数だけを注入

懸念:

- 29件の長いskill descriptionは発動判定時の固定費になる
- アクティブタスクをすべて読む規則はタスク数に比例して開始コストが増える
- 失敗履歴がSKILL、scriptコメント、knowledge、archived steeringへ重複する
- `remind-config-docs.sh`の注入要約とknowledge正本の意味的ドリフトは未検査

### 5.7 保守性 — 3.6 / 5

確信度: 高  
重大度: High

強み:

- producer / consumer、配布分類、hook登録を機械的に突合
- READMEとfeature-pipelineを同一コミットで更新する規則
- 新skillテンプレートが停止条件とフォールバックを構造として要求
- ADR、knowledge、タスク固有decisionを分離
- rule-auditによる削除・統合経路がある

弱み:

- 多数の契約が特定文字列と見出しに依存し、意味を保った言い換えに弱い
- checker自体の単体テスト・故障注入回帰が不足
- 正本が複数あり、現にsteering specがドリフト
- `biome.json`は次期majorで削除予定の`recommended`設定を使用
- 状態機械の遷移表を実行可能仕様としてテストしていない

### 5.8 移植性・利用体験 — 3.0 / 5

確信度: 高  
重大度: High

移植性の強み:

- Pythonは標準ライブラリ中心
- skill本体とスタック固有referencesを分離
- 配置時に既存settingsを上書きしない
- master-only資産を分類し、source-commitを記録

移植性の弱み:

- portability検査が2件を報告するがreport-onlyで成功終了
- references、settings、CLAUDE.mdの配置後ドリフトを十分に追跡しない
- 登録済み2配置先の双方で実際にドリフトを検出
- 公式のplugin配布形式に比べ、独自deploy / harvestの保守負担が大きい

利用体験の弱み:

- design-docの決定インタビューは1問ごとに停止し、通常2〜3問＋設計承認を要求する
- 個別skillにも承認があり、「不可逆・外向き・価値判断だけを主要ゲートにする」という全体方針より実停止が多い
- 承認済みの元依頼に対し、さらに「実装開始」を求めるような過剰ゲートを誘発しやすい。これは本評価セッションでも発生した

公式資料は複雑な作業でPlanを推奨しますが、quick changeでは直接Agent modeへ進むことも妥当としています。本ワークフローは安全寄りですが、摩擦コストを定量評価していません。

## 6. 重要所見

### Critical

1. PR往復フェーズの状態判定が通常経路で到達不能
2. 2段階captureを単一フラグで表し、マージ後captureを飛ばせる

### High

1. steering仕様とtasklistテンプレートの工程順ドリフト
2. 状態機械の意味的欠陥を全静的検査が見逃す
3. 現行モデルでのpassthrough実走証跡がない
4. CIがなく、検査実行がローカル運用依存
5. 安全hooksの適用範囲が限定的でsandbox設定がない
6. 登録済み配置先が両方ドリフト
7. 承認ゲートの累積が利用者の流れを阻害する

### Medium

1. 29 skill descriptionsと複数アクティブタスクによる固定コンテキスト負荷
2. referencesの配置後ドリフトが検出対象外
3. テストインフラ、設定ロジック、shell / Pythonコードの専門レビュー範囲が曖昧
4. Biome設定にdeprecated警告
5. portability警告が非ブロッキング

## 7. 今回の機械検査結果

実行日: 2026-08-30  
実行環境: ローカル、課金エージェント実走なし

- `mise exec -- pnpm run validate`: 34 / 34 PASS
- `mise exec -- pnpm run validate:assets`: 10 / 10 PASS
- `mise exec -- pnpm run test:hooks`: 35 / 35 PASS
- `mise exec -- pnpm run validate:portability`: 成功終了、警告2件
- `mise exec -- pnpm run lint`: エラーなし、Biome deprecated情報1件
- `python3 scripts/passthrough_check.py --all --dry-run`: 21 / 21シナリオの構造生成成功
- `python3 scripts/check_deploy_drift.py`: exit 1、配置先2件、ドリフト合計14

重要な解釈:

- 34 / 34と10 / 10の成功は構造・集合整合を示します
- Critical 2件はこの成功状態で存在するため、意味的な正しさの証明ではありません
- passthrough dry-runはエージェントが停止契約を守ることを検証しません
- driftのexit 1は検査機構が機能している証拠である一方、配布状態が収束していない証拠でもあります

## 8. 最新Claude推奨との照合

### 明確に適合

- 短く具体的な`CLAUDE.md`
- オンデマンドskillsとreferences
- 複雑な変更でのPlanとレビュー
- subagentによる調査隔離と並列レビュー
- hooks / permissionsによる機械的補強
- 長期作業の構造化進捗ファイル
- テスト・lint・差分を使う証拠ベースの完了判定
- AIレビューを人間のマージ責任の代替にしない
- worktreeによる並列実装の隔離

### 部分適合

- 最小権限: settingsは強いがsubagent単位の権限制限が弱い
- sandbox: 概念上の配慮はあるがプロジェクト設定がない
- memory: 保存・剪定経路はあるが、鮮度や再検証を全知識へ機械適用していない
- CI: PRフローはあるが検査をCIで自動実行していない
- Plan適用範囲: 小タスク例外はあるが、通常の質問・承認回数は公式推奨より重い

### 不適合または未証明

- 現行モデルで主要ハードストップが守られること
- 状態機械の全遷移が到達可能で矛盾しないこと
- 配置済み環境がmasterと整合していること
- hooksで保護対象への全迂回を遮断すること

## 9. 評価限界

- 公式ページはライブ更新され、固定版や最終更新日がないものがあります。URLと確認日による再現に留まります
- 課金を伴うフレッシュエージェントのpassthrough実走は行っていません
- IDE上のpermission prompt、workspace trust、hook再読み込みをE2E検証していません
- 実PR、実CI、実レビューコメントを使った一気通貫試験をしていません
- 自然言語トリガーの誤発動率・不発動率を統計測定していません
- 配置先ドリフトが意図的なローカル適応か事故かは判定していません
- archived資産は設計意図と失敗履歴の抽出に使い、現行契約の正本とは扱っていません
- 本レポートの重要主張は一回限りで手作業照合しており、継続的保証ではありません

## 10. 公式資料

公式資料と主要な評価基準の対応は次のとおりです。

- 常時指示を短く保ち、詳細を必要時に読む構成: `How Claude remembers your project`、`Extend Claude Code`
- 独立作業のcontext隔離とsubagent活用: `Create custom subagents`、`Effective context engineering for AI agents`
- permissionsとhooksによる操作境界: `Configure permissions`、`Hooks reference`
- 計画、検証可能な合否信号、人間による確認: `Best practices for Claude Code`
- 長期作業での状態外部化と段階的進行: `Effective harnesses for long-running agents`

上記は各資料の機能説明・推奨から作った評価基準であり、本リポジトリ固有のフェーズ数や承認回数を公式が直接推奨している、という意味ではありません。

### Anthropic / Claude Code

- [How Claude remembers your project](https://docs.anthropic.com/en/docs/claude-code/memory)
- [Extend Claude Code](https://docs.anthropic.com/en/docs/claude-code/features-overview)
- [Create custom subagents](https://docs.anthropic.com/en/docs/claude-code/sub-agents)
- [Configure permissions](https://docs.anthropic.com/en/docs/claude-code/permissions)
- [Hooks reference](https://docs.anthropic.com/en/docs/claude-code/hooks)
- [Best practices for Claude Code](https://www.anthropic.com/engineering/claude-code-best-practices)
- [Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)

### 補助資料

- [OpenAI Codex best practices](https://developers.openai.com/codex/learn/best-practices)
- [OpenAI Codex skills](https://developers.openai.com/codex/skills)
- [OpenAI Codex subagents](https://developers.openai.com/codex/subagents)
- [Cursor Agent Skills](https://cursor.com/docs/skills)
- [Cursor Subagents](https://cursor.com/docs/subagents)
- [Cursor Plan Mode](https://cursor.com/docs/agent/plan-mode)
- [GitHub Copilot code review](https://docs.github.com/copilot/concepts/agents/code-review)
- [GitHub Copilot custom instructions](https://docs.github.com/copilot/customizing-copilot/adding-custom-instructions-for-github-copilot)

---

# 改善案コラム

この節は現状評価ではなく、評価者による変更案です。別のClaudeへ現状だけを評価させたい場合は、この節を除外できます。

## P0: 状態機械を修正する

### A. Phase 3.7をPhase 3.5より先に判定する

期待効果:

- resume時にPRコメント・CI失敗へ正しく遷移
- pr-feedbackが実際にオーケストレーターへ接続される

コスト:

- 低〜中。判定表変更と遷移テスト追加

副作用:

- 「フィードバックあり」の観測方法を成果物へ明示しないと、会話依存が残る

推奨:

- `pr-state.md`またはtasklistの明示状態として、PR URL、CI状態、レビュー状態を記録する
- 状態判定を文章の上から順ではなく、実行可能な遷移表またはテスト対象の純粋関数へ寄せる

### B. capture状態を2段階へ分ける

例:

- `pr_knowledge_captured`
- `session_knowledge_captured`

期待効果:

- PR前とマージ後の知見保存を独立して追跡
- 後続PRへの無関係なdocs混入を防止

コスト:

- 中。hooks、pipeline、knowledge-capture、templates、steering spec、testsの同期が必要

副作用:

- フラグ数が増えるため、状態名とproducer / consumerの機械突合が必要

## P1: 状態遷移を実行可能仕様にする

変更案:

- 状態判定をPythonまたはTypeScriptの純粋関数へ抽出
- 全状態組合せをtable-driven testで検証
- 到達不能フェーズ、優先順位、未知Statusのfail-closedをテスト
- README図と実装の対応は現在の集合検査を維持

期待効果:

- キーワード共存検査では拾えない意味的欠陥を検出

コスト:

- 中

副作用:

- 「ルーターはプロンプトだけ」という単純さが減る

## P1: CIへ無料検査を載せる

対象:

- validate
- validate:assets
- validate:portabilityのstrictモード
- test:hooks
- lint
- passthrough dry-run

期待効果:

- ローカルhook不発や手動実行忘れを補完
- main上の保証状態を可視化

コスト:

- 低

副作用:

- portability警告の既存2件を先に整理する必要がある

## P1: 承認ゲートを再編する

原則:

- 不可逆、外向き、課金、価値判断だけを人間ゲートにする
- 元依頼が実装まで含み、設計が承認された場合は、その承認を次フェーズ開始として扱う
- 小タスクでは決定インタビューを最大1問または会話内設計へ縮退
- 情報不足の確認と承認を分ける

期待効果:

- 安全性を保ちつつ、会話ターンと待ち時間を削減

コスト:

- 中。design-doc、impl-from-design、feature-pipeline、passthroughの見直し

副作用:

- ゲート削減を「自律実行範囲の拡大」と誤解させない明文化が必要

## P1: 安全境界を明示する

変更案:

- sandboxを有効化し、workspace・network境界を設定
- subagentの役割ごとにツール権限を最小化
- hookを完全なアクセス制御と表現せず、対象外構文を脅威モデルに明記
- MCP・ブラウザ・外部APIを個別に分類

期待効果:

- 自然言語と部分的hookに依存する範囲を縮小

コスト:

- 中〜高。実環境差とツール互換性の検証が必要

副作用:

- 開発コマンドの追加許可やユーザーpromptが増える可能性

## P2: 配布方式を再評価する

選択肢:

- 現行deploy / harvestを維持し、定期drift checkと収束SLOを設ける
- Claude Code / Cursor / OpenAIが採用するplugin形式へ寄せる

期待効果:

- 配置先2件ともdriftしている現状を改善
- 独自配布ロジックの保守負担を削減できる可能性

コスト:

- 中〜高

副作用:

- 配置先固有referencesの再生成やsettings手動マージはpluginだけでは解消しない

## P2: レビュー範囲をコード種別に合わせる

変更案:

- TypeScript / React以外のshell、Python、設定、workflow向けレビュー軸を追加
- review-uiは必要時に実レンダリングまたはスクリーンショット検証へ接続
- テストインフラ監査の明示的な担当を決める

期待効果:

- このリポジトリ自身の主要コードであるshell / Pythonが専門レビューの隙間に落ちる問題を解消

コスト:

- 中

副作用:

- review agent数とコストが増えるため、diffトリアージが必要

## P3: 小規模な衛生改善

- steering specを現行templateへ同期
- portability警告2件から内部日付依存を除去
- Biomeの`recommended`を`preset`へ移行
- `remind-config-docs.sh`の要約と正本のドリフト検査を追加

期待効果:

- 警告ノイズと文書不整合を減らす

コスト:

- 低

---

## Claudeへ再評価を依頼する際の推奨文

> このレポートの「改善案コラム」より前だけを入力として扱い、リポジトリ原文と公式URLを独立に確認してください。各Critical / High所見について、再現可能性、反証、重大度、見落としを検証し、評価者の結論へ同意する必要はありません。公式資料に明記された推奨と、評価者が機能説明から推論した基準を区別してください。
