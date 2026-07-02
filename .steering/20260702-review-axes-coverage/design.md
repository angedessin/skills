# Design: review-axes-coverage

Created: 20260702
Status: **APPROVED**
Approved: 20260702

> 経緯: 2026-06-22 に同名タスクが着手されたが成果物が残っておらず（`.steering/20260622-review-axes-coverage/` は空）、design-doc から再起動した。旧ディレクトリは整理済み。設計素材は [issues-and-plan.md 課題3](../../docs/skillset-improvement/issues-and-plan.md) と [ai-driven-frontend-workflow-plan.md](../../docs/ai-driven-frontend-workflow-plan.md) 課題A。

## Goal

レビュースキル群（現行 5 スキル 21 軸）に欠けている 3 観点 — correctness（ロジックバグ）・UI/ビジュアル/レスポンシブ・UX 状態網羅 — を補い、frontend-code-review オーケストレーターに統合する。correctness はレビューの根幹なのに専任軸がなく（最大の盲点）、フロントエンドのスキルセットなのにビジュアル観点がゼロという歪みを解消する。

## Scope

### In scope

- `review-correctness` サブスキル新設（境界条件 / null・undefined / 非同期レース・stale closure / 状態遷移の矛盾 / エラー握りつぶし）
- `review-ui` サブスキル新設（レイアウト・レスポンシブ / デザイン整合 / UX 状態網羅 loading・error・empty・disabled）
- `frontend-code-review` の改訂: フルモードのディスパッチに 2 エージェント追加、重複統合ルール・スコープ表の更新、軽量モードへの review-ui 条件付き追加
- `design-doc/references/templates.md` の review-result.md テンプレートに Correctness / UI セクション追加
- README のレビュー節・「5エージェント並列」表記・スキル間関係図の更新、frontend-code-review の description 更新

### Out of scope

- i18n / l10n レビュー軸（オプトイン設計として保留 — issues-and-plan.md 3-D）
- スクリーンショット・実レンダリングによるビジュアル検証（静的コードレビューの範囲外。ビルトイン verify / Playwright の領域）
- e2e / debug / rule-audit スキル新設（別タスク。new-skills.md 参照）
- impl-review の既存 5 軸の変更（重複統合ルールでの調整のみ）

## Constraints

- Stack: React / TypeScript / Vitest / React Testing Library / MSW / Playwright
- エンジン＋カートリッジ契約に準拠する: SKILL.md 本文はスタック非依存の判断軸、スタック固有の具体例（デザイントークンの実体等）は references/ へ。references は役割名で参照する
- スキルは自己完結に書く（.steering/・CLAUDE.md が無いプロジェクトでも動くフォールバックを該当ステップに書く）
- スキルファイルに絵文字を使わない（アストラル面絵文字は 400 エラーの原因）
- 本文 <500 行 / description ≤1024 文字 / `compatibility` frontmatter を付与
- フルモードのディスパッチ数が 5 → 7 に増える（コスト増。Open questions 参照）

## Acceptance criteria

- [ ] `review-correctness/SKILL.md` が存在し、単独実行で軸ごとの表形式レポートを返す
- [ ] `review-ui/SKILL.md` が存在し、トークン定義が無いプロジェクトでは「一般的一貫性のみ確認」に縮退する
- [ ] `frontend-code-review` フルモードが 7 エージェントをディスパッチし、新 2 軸が review-result.md に記録される
- [ ] 重複統合ルールに新軸の帰属（impl-review TypeScript × correctness、impl-review React × correctness、a11y × ui 等）が明記されている
- [ ] 軽量モード（スタイル/設定のみ）で CSS 変更を含む場合に review-ui が直列実行される
- [ ] README・frontend-code-review description の「5エージェント」表記が更新されている
- [ ] 両新スキルを empirical-prompt-tuning のフレッシュ subagent 実行で検証し、重大な不明瞭点が解消されている

## Approach

correctness と UI/UX 状態を、既存 review-* と同じ「サブスキル + オーケストレーターからの並列ディスパッチ」パターンで追加する。ビルトイン `/code-review` への委譲（issues-and-plan.md 3-A の選択肢）は採らない — review-result.md への統合・指摘軸単位の差分再レビュー・横展開先での挙動制御がオーケストレーターの外に出てしまうため。ビルトインはユーザーが任意で回す補完的な深掘りレビューとして共存させる。UX 状態網羅（3-C）とエラー表示は review-ui の 1 軸に、エラー握りつぶし検知は review-correctness の 1 軸に分担させる（エラーハンドリングを単独スキール化しない — workflow-plan 4-2 の判断）。

## Key components

| Component | Location | Responsibility |
|-----------|----------|----------------|
| review-correctness（新設） | `.claude/skills/review-correctness/SKILL.md` | 4軸: 境界条件・off-by-one / null・undefined 取りこぼし / 非同期レース・stale closure / 状態遷移矛盾・エラー握りつぶし。スコープ: `.ts`/`.tsx`（テスト除く） |
| review-ui（新設） | `.claude/skills/review-ui/SKILL.md` | 3軸: レイアウト・レスポンシブ破綻 / デザイン整合（トークン定義があれば遵守確認、無ければ一般的一貫性のみ） / UX 状態網羅（loading・error・empty・disabled）。スコープ: `.tsx` + `.css`/`.scss`（テスト除く） |
| review-ui references（任意） | `.claude/skills/review-ui/references/tokens.md` | カートリッジ: デザイントークン・spacing スケールの実体。マスターには「example — 配置先で再生成」の雛形を同梱 |
| frontend-code-review 改訂 | `.claude/skills/frontend-code-review/SKILL.md` | Phase 2A に correctness-agent / ui-agent 追加、Phase 2B に review-ui 条件追加、Phase 3 重複統合ルール拡張、description 更新 |
| review-result.md テンプレート | `.claude/skills/design-doc/references/templates.md` | Correctness / UI セクションの追加 |
| README | `README.md` | レビュー節のスキル表・「5エージェント並列」→「7エージェント並列」・関係図の更新 |

## Data flow

```
frontend-code-review Phase 1（diff トリアージ）
  → フルモード: 7 エージェント並列ディスパッチ
      test / impl / security / perf / a11y / correctness（新） / ui（新）
  → 軽量モード: test → impl →（CSS/スタイル変更を含む場合のみ）ui
  → Phase 3: 重複統合（同一 file:line・同趣旨は最専門の軸に帰属）
      impl-review TypeScript 軸 × correctness の null 指摘 → correctness に帰属
      impl-review React 軸 × correctness の stale closure 指摘 → correctness に帰属
      review-a11y セマンティクス × ui のレイアウト指摘 → 趣旨が異なるため統合しない
  → review-result.md（Correctness / UI セクション追加）→ .codify-needed
```

## Test strategy

スキル（Markdown）が成果物のためコードテストは無い。代替の検証:

- 構造検証: name=ディレクトリ名一致 / description ≤1024 文字 / 本文 <500 行 / 絵文字なし を目視 + grep で確認
- 挙動検証: empirical-prompt-tuning でフレッシュ subagent に両新スキルを単独実行させ、不明瞭点・裁量補完を検出（無料相当・dispatch 数本）
- 統合検証: サンプル diff（本リポジトリ or 手元の React プロジェクト）で frontend-code-review フルモードを 1 回実行し、7 エージェントのディスパッチと review-result.md への記録を確認
- skill-creator による baseline 比較は任意（コスト高。実施するならコスト記録を残す — workflow-plan 課題E の運用ルール）

## Open questions

すべて 20260702 の承認時に推奨案で確定:

- [x] **フルモード 7 エージェント並列のコスト増を許容するか** → **許容（7 並列で確定）**。各軸の専門性を維持し、差分再レビューが軸単位で効くため増分は限定的
- [x] **correctness の担い先** → **自前サブスキル `review-correctness` 新設で確定**。ビルトイン `/code-review` は補完的な深掘りレビューとして共存
- [x] **review-ui の軽量モード追加** → **追加する**。スタイル/設定のみの変更で CSS 変更を含む場合、test-review + impl-review の後に review-ui を直列実行
- [x] **review-ui の CSS ファイルスコープ** → **トリアージ分類は現行維持、フルモード時の ui-agent スコープに `.css`/`.scss` を含める**

## Alternatives considered

| Alternative | Why rejected |
|-------------|--------------|
| correctness をビルトイン `/code-review` に委譲 | review-result.md への統合・軸単位の差分再レビュー・横展開先での可用性がオーケストレーターの制御外になる。補完として共存させる方が筋が良い |
| impl-review に correctness 軸を追加 | impl-review は既に 5 軸で、correctness は「最大の盲点」として専任を置く方針（issues-and-plan.md 3-A）と合わない。肥大化はエンジン＋カートリッジ契約の劣化要因 |
| UX 状態網羅を correctness 側に置く | 状態の「実装漏れ」は視覚・体感品質の関心で UI 側が自然。エラーの「握りつぶし」（ロジック）と「表示漏れ」（UI）で分担する方が軸が濁らない |
| エラーハンドリング単独スキル新設 | correctness / review-ui / 既存 impl-review への分担で足りる（workflow-plan 4-2）。スキル数の増加はトリガー精度を下げる |
| スクリーンショットベースのビジュアルレビュー | 静的レビューの範囲外。実行環境依存が強く自己完結原則に反する。ビルトイン verify の領域として棲み分ける |

## Research

### 既存パターン調査（20260702）

既存 review-* サブスキル（review-a11y / review-security / review-performance）の共通構造を実測。新設 2 スキルはこれに合わせる:

- frontmatter: `name` / `description`（「フロントエンドの◯◯レビューに使うサブスキル。…オーケストレーターからの並列呼び出しを想定。単独でも使用可。」の定型）/ `compatibility`（中立な観点はその旨を括弧書き）
- 本文構成: タイトル「Review — X」→ スコープ（`git diff --name-only HEAD` + grep、**空の場合のフォールバックを必ず明記**）→ N つのチェック軸（Bad/Good コード例 + チェック項目リスト）→ 出力形式（軸ごとの箇条書き + サマリー）→「**提案のみ。自動修正しない。**」定型 → Related skills
- impl-review は深掘りが必要な場合にビルトイン `/code-review high` を案内するパターンを持つ → review-correctness にも踏襲（Approach の「ビルトインと共存」の実装形）
- 注意点: 絵文字なし・本文は判断軸中心・スタック固有の実体は references へ（エンジン＋カートリッジ契約）

### ビルトイン /code-review の correctness カバレッジ（20260702）

- ビルトイン `/code-review` は「current diff の correctness バグ」を明示的に対象とする（effort レベル可変・PR コメント連携あり）。correctness 観点の存在自体はビルトインで担保できるが、(1) review-result.md の軸別記録、(2) 指摘があった軸のみの差分再レビュー、(3) 配置先プロジェクトでの挙動の一貫性、の 3 点がオーケストレーター統合の決め手となり自前サブスキルを推奨する
- 現行トリアージ分類（frontend-code-review Phase 1）は `*.css` を「スタイル/設定のみ」= 軽量モードに送る。review-ui を軽量モードに条件追加しない場合、CSS 破綻の検知機会がフルモード時（他のロジック変更に相乗りした場合）に限られる点に注意
