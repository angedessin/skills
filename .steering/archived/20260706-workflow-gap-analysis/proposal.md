# AI 駆動ワークフロー ギャップ分析 — hooks / skills / rules / agents 追加候補

Status: DRAFT（人間レビュー待ち。採用する項目ごとに design-doc または直接実装で着手）
Date: 2026-07-06

## 1. 現状マップ

| レイヤ | 現状 |
|---|---|
| ワークフロー | 入口分岐（新機能→design-doc / バグ→debug）→ 設計 → 人間承認 → 実装（impl-from-design / tdd / e2e）→ frontend-code-review（7軸）→ 修正・差分再レビュー → pr-create → compound → knowledge-capture → archive |
| Hooks（4本） | guard-env-read（PreToolUse/Bash）・post-edit-lint（PostToolUse/Edit\|Write）・stop-typecheck（Stop）・session-stop（Stop, .capture-needed フラグ） |
| Skills（19本） | 設計2・コンテキスト1・実装3・レビュー8・ナレッジ/自己改善4・オーケストレーター1 |
| Rules | CLAUDE.md 4節 + docs/knowledge 4本 + ADR 5本。compound（追加）と rule-audit（剪定）の両輪 |
| Agents | カスタム定義なし（review-* は汎用 subagent にディスパッチ） |

**強み（維持すべき点）**: lint/typecheck の機械差し戻しによる検証ループ、ハードストップの手順化（説明文では守られないという実証済み知見）、追加と剪定の両輪、配置先自己完結のポータビリティ設計。

**ギャップの構造**: 以下の 5 系統に集約される。

- (a) 「説明文では守られない」と自ら結論した箇所が、まだ説明文のまま残っている（セッション開始チェック）
- (b) マスターリポジトリ自身の品質ゲートが手動（validate_skills.py）
- (c) レビュー subagent の権限・モデル制御がない（全ツール・デフォルトモデルで 7 並列）
- (d) ライフサイクルの入口に穴（リファクタリング・依存更新の駆動スキルがない）
- (e) README / feature-pipeline が参照する pr-create がマスター外（ユーザーレベルスキル）

---

## 2. 提案 — Hooks

### H1. SessionStart hook `session-start-check.sh` 【優先度: 高】

- **現状**: CLAUDE.md「セッション開始時: 必ず find … を実行」は行動ルール（説明文）であり、モデルの遵守に依存している。skill-design-patterns.md の実証済み結論「停止・前提条件の契約は説明文では守られない」がそのまま当てはまる構造。
- **提案**: SessionStart hook（matcher: startup / resume / compact）で `.capture-needed` / `.codify-needed` の検出とアクティブタスク一覧を実行し、結果を additionalContext として注入する。compact 後の `.steering` 再読リマインドも同じ hook で担える。
- **効果**: チェックの実行が機械保証になる。導入後は CLAUDE.md「セッション開始時」節の 1〜3 項を rule-audit で削除でき、毎セッションのコンテキスト消費も減る（→ R1 とセット）。
- **コスト**: ローカル実行のみ、数十 ms。課金なし。

### H2. PostToolUse hook `validate-skill-edit.sh` 【優先度: 高・マスター専用】

- **現状**: validate_skills.py は「スキル改訂時と配置前に実行する」という手動運用。アストラル面絵文字（lone surrogate で API 400 クラッシュの実績あり）は書いた瞬間に検出できるのが理想。
- **提案**: `.claude/skills/**/SKILL.md` への Edit/Write 後に validate_skills.py を該当スキルのみに実行し、違反を exit 2 + stderr で差し戻す。post-edit-lint と同型の「検証ループ」パターンの横展開。
- **注意**: 配置先には同送しない（scripts/ に依存するマスター専用である旨をスクリプト冒頭に明記）。
- **コスト**: ローカル実行のみ。python3 不在時はフェイルオープン。

### H3. Stop hook での関連テスト実行 【優先度: 低・任意】

- stop-typecheck と同型で `vitest related`（変更ファイルの関連テストのみ）を回す案。セッション終了のたびに実行時間がかかるため、デフォルトでは提案しない。無料代替: 既存の stop-typecheck + 配置先の CI で足りるなら不要。CI の無い配置先でのみ検討。

### H4. PreCompact hook 【優先度: 低・任意】

- compact 前に「アクティブタスクあり。compact 後は .steering/ を再読すること」を注入する軽量 hook。H1 の SessionStart（matcher: compact）で代替できる可能性が高く、H1 導入後に不足を感じた場合のみ検討。

---

## 3. 提案 — Skills

### S1. pr-create のマスター取り込み（または外部依存の明記） 【優先度: 高】

- **現状**: README メインワークフロー [6] と feature-pipeline が pr-create を参照するが、マスター `.claude/skills/` に存在しない（ユーザーレベルスキル）。starter-kit で配置した先では欠落し、feature-pipeline の「依存スキル存在確認 → スキップして報告」に常に落ちる。
- **提案**: 二択。(A) pr-create をマスターに取り込み配布対象にする（自己完結原則に沿う・推奨）。(B) README と feature-pipeline に「外部依存・配置先では各自用意」と明記する。
- **根拠**: 「同じ情報を持つ全箇所を直してから閉じる」規律の対象。図とオーケストレーターが参照するものはマスターにあるべき。

### S2. refactor スキル 【優先度: 中】

- **現状**: 入口分岐は「新機能 → design-doc / バグ → debug」の 2 本のみ。「振る舞いを変えない構造改善」の入口がなく、design-doc（過剰）か素の依頼（手順なし）に流れる。
- **提案**: テスト存在確認（なければ tdd で特性テストを先に張る）→ 小さいステップに分割 → 各ステップで post-edit-lint / stop-typecheck の検証ループに乗せる → 完了後は frontend-code-review 軽量モード、という手順を駆動するスキル。
- **境界**: 新機能を伴う場合は design-doc へ、バグ起因なら debug へリダイレクト（既存スキルとの相互明記が必要）。

### S3. dependency-update スキル 【優先度: 中】

- **現状**: settings.json がインストール系コマンドを全 deny しており、依存更新は必ず人間の手を通る設計。ただしその「人間の手」を案内する手順が存在せず、changelog 未確認・一括更新などの抜けが起きうる。
- **提案**: `pnpm outdated` で候補確認 → breaking change / changelog の確認 → ユーザー自身にコマンド実行を案内（`! pnpm update …` の `!` プレフィックス）→ テスト・typecheck で検証 → 失敗時のロールバック手順、を駆動するスキル。deny ポリシーと矛盾しない（AI は実行せず案内する）。

### S4. design.md セルフレビュー（新スキルにせず design-doc に追加） 【優先度: 低】

- **現状**: コードにはレビュー 7 軸があるが、design.md は人間レビューのみ。Acceptance の検証可能性・Scope 漏れ・既存パターンとの整合は、人間レビュー前に自己チェックできる。
- **提案**: design-doc の STOP 直前に短いセルフチェック節を足す。新スキルは作らない（スキル数の抑制）。レビュースリム化の持ち越し作業と方向が逆（追加）なので、同時に判断する。

---

## 4. 提案 — Rules

### R1. CLAUDE.md「セッション開始時」節の削除 【優先度: 高・H1 とセット】

- H1 導入後、同節 1〜3 項は hook が担うため削除できる（4〜5 項の「アクティブタスクを読む・複数なら確認」は残す or hook の注入文言に統合）。rule-audit の削除テストで安全に実施。

### R2. スキル編集後の検証ルールは追加しない 【判断のみ】

- 「SKILL.md 編集後は validate_skills.py を実行する」という明文ルールの追加は不要。H2 の hook が機械的に担うため、ルールを増やさないことが正しい（説明文より hook、の原則の適用）。

### R3. コミット規約の明文化 【優先度: 低・見送り寄り】

- feat/fix/docs の Conventional Commits 慣行は git 履歴に既にあり、モデルは履歴から追随できている。CLAUDE.md 肥大化とのトレードオフで、現状は追加不要と判断。逸脱が観測されたら compound で 1 行ルール化する。

---

## 5. 提案 — Agents

### A1. 読み取り専用 reviewer agent 定義 【優先度: 中】

- **現状**: review-* サブスキルは汎用 subagent にディスパッチされ、Edit/Write を含む全ツールを持つ。レビューは読み取りだけで足りる。
- **提案**: `.claude/agents/reviewer.md` を 1 本定義（tools: Read / Grep / Glob / Bash の読み取り系のみ）し、frontend-code-review のディスパッチ先に指定する。レビュー agent が誤ってコードを直す事故を構造的に防止（最小権限）。
- **コスト削減の選択肢**: agent 定義でモデルを haiku 等に落とせばフルモード 7 並列のコストが下がる。精度とのトレードオフがあるため、まず機械的検出が多い軸（review-security の依存関係チェック等）1 本で試す。
- **設計上の注意**: agent 定義には権限とモデルだけを置き、手順は SKILL.md に置いたまま（二重管理・ドリフトを作らない）。レビュースリム化の持ち越し作業と同じタイミングで着手すると重複作業を避けられる。

### A2. empirical-prompt-tuning 用 fresh-executor agent 【優先度: 低】

- バイアス排除の実行者を毎回汎用 agent で立てている。ツール制限付きの定義に固定すると再現性が上がるが、empirical 検証自体が任意運用のため急がない。

---

## 6. 追加しないもの（意図的な見送り）

| 候補 | 見送り理由 |
|---|---|
| cron / schedule による自動ループ | 課金が発生する重い自動処理は避ける方針。必要時は手動起動で足りる |
| 自動コミット hook | コミット粒度・タイミングは人間の判断に残す（可逆性の担保） |
| プラグイン化・symlink 配布 | ADR 20260612 で却下済み。段階基準（配置先 >3 で再検討）が既にある |
| レビュー軸の追加（8 本目） | 既存の持ち越しは「レビュースリム化」であり方向が逆 |
| UserPromptSubmit hook | 毎プロンプトに注入すべき定常情報が現状ない |

---

## 7. 推奨着手順

1. **H1 + R1**: SessionStart hook 化と CLAUDE.md 剪定（自前の実証知見の適用。効果が最も確実）
2. **H2**: validate-skill-edit hook（既知のクラッシュ要因を機械検出に）
3. **S1**: pr-create のマスター取り込み or 外部依存明記（ドリフトの芽を摘む）
4. **A1**: reviewer agent — レビュースリム化の持ち越し作業と同時に
5. **S2 / S3**: refactor・dependency-update — 実際にそのタスクが発生したときに design-doc から

## 8. 既存バックログとの関係（この提案とは別枠）

- レビュースリム化の後半・ハードストップ再検証（20260705 時点の持ち越し）→ A1 と同時着手を推奨
- 配置先初回利用に繰り越し済みの検証: frontend-code-review フルモード統合検証・debug / e2e の受け入れ試行・starter-kit 手順の実地検証（archived tasklist に未チェックで残存）
