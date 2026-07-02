# Design: e2e-skill

Created: 20260703
Status: **APPROVED**
Approved: 20260703

> 設計素材: [new-skills.md の e2e 節](../../docs/skillset-improvement/new-skills.md)（判断軸の叩き台あり）/ [issues-and-plan.md 課題 1-A](../../docs/skillset-improvement/issues-and-plan.md)（最優先の穴）

## Goal

Playwright E2E テストの作成・レビューを担う `e2e` スキルを新設する。スタックに Playwright が明記されているのに E2E を主役にしたスキルが存在せず（tdd は Vitest+RTL+MSW 専用、test-review は Playwright 監査を対象外と宣言）、いつ・どの粒度で E2E を書くか、どの軸でレビューするかをワークフロー上で誰も担っていない。認証・決済等のクリティカルパス品質がワークフローの外にこぼれる状態を解消する。

## Scope

### In scope

- `e2e` スキル新設（`.claude/skills/e2e/SKILL.md` + `references/patterns.md`）
  - **本文 = ツール中立の判断軸**（エンジン＋カートリッジ契約を新規作成時から適用 — tdd/test-review が後から改修で苦労した教訓の逆張り）:
    - 対象選定: クリティカルパス（認証・決済・主要導線）に絞る。ユニット/インテグレーションで足りるものを E2E にしない（テストピラミッド）
    - 粒度: ページ横断のユーザーシナリオ単位。1 テスト 1 シナリオ
    - 安定性: ユーザー可視の意味でロケートする（役割・ラベル > テスト専用属性 > CSS）、待機は明示的な条件で（固定 sleep 禁止）、テスト間独立（順序依存・共有状態の禁止）
    - レビュー軸: flaky の温床（暗黙待機・順序依存・共有状態）、実ユーザー視点の検証か
  - **references/patterns.md = Playwright 具体例**（ロケータ API・auto-wait・fixture・認証状態の再利用）。「example — 配置先のスタックに合わせて再生成」と明記。references が無い場合は判断軸のみで縮退動作
- `test-review` / `tdd` の Related skills に e2e への相互参照を 1 行ずつ追記（E2E は e2e スキル担当という境界の明記 — skill-design-patterns の「境界の相互明記」パターン適用）
- README 更新: 実装カテゴリのテーブルに e2e 行を追加

### Out of scope

- frontend-code-review オーケストレーターへの e2e-agent 統合（Open questions 参照 — 配置先で E2E が実際に書かれてから判断）
- README ワークフロー図の改訂（「[3] クリティカルパスは e2e」の図への組み込みは PR フェーズ・入口分岐・feature-pipeline 同期とまとめて別タスク）
- Playwright の設定・CI 整備の手順（テスト設計の判断軸に絞る。インフラ監査は test-review 同様対象外）

## Constraints

- Stack: 本文はツール中立（テストピラミッド・シナリオ設計・安定性原則はツール横断で真）。Playwright 語彙は references に集約し、本文からは役割名で参照する
- `compatibility` frontmatter: "Playwright 前提（判断軸はツール中立。API 例は references を配置先で再生成）"
- スキルは自己完結: references が無い場合の縮退（判断軸のみで動作）を該当ステップに明記
- 絵文字なし / 本文 <500 行 / description ≤1024 文字 / 引用符付き description / name=ディレクトリ名
- **エンジン純度の定量確認**: 本文（frontmatter 除く）のツール固有 API 出現数を実測し、ほぼゼロに保つ（課題2 の実測手法を新規作成の受け入れに転用）

## Acceptance criteria

- [ ] `e2e/SKILL.md` が存在し、対象選定・粒度・安定性・レビュー軸の 4 判断軸と、作成/レビュー両方の手順を含む
- [ ] 本文のツール固有 API 出現がほぼゼロ（ロケータ・待機の Playwright API 名は references のみ）
- [ ] `references/patterns.md` が存在し、「example — 配置先で再生成」と冒頭に明記されている
- [ ] references 不在時の縮退動作が本文の該当ステップに明記されている
- [ ] test-review / tdd との境界が三者の本文に相互明記されている（ユニット/インテグレーション = tdd、そのレビュー = test-review、E2E の作成とレビュー = e2e）
- [ ] README の実装カテゴリに e2e が掲載されている
- [ ] 構造検証パス（行数・description 長・絵文字・name 一致）

## Approach

new-skills.md の叩き台（判断軸 4 つ + references 分離）を、最初からエンジン＋カートリッジ契約で書き下ろす。スキルは「作成」と「レビュー」の両モードを持つ — 入口で diff / 依頼内容から判定し、作成時は対象選定 → シナリオ分解 → 安定性原則の順、レビュー時は 4 軸（対象妥当性・粒度・安定性・実ユーザー視点）で審査する。test-review が明示的に対象外としてきた領域を引き受けるため、三者（tdd / test-review / e2e）の境界を各本文に相互明記して並列実行時の越境・漏れを防ぐ（skill-design-patterns の確立済みパターン）。

## Key components

| Component | Location | Responsibility |
|-----------|----------|----------------|
| e2e（新設） | `.claude/skills/e2e/SKILL.md` | 判断エンジン: 対象選定 / シナリオ粒度 / 安定性原則 / レビュー 4 軸。作成・レビュー両モード |
| e2e references（新設） | `.claude/skills/e2e/references/patterns.md` | カートリッジ: Playwright のロケータ・待機・fixture・認証状態の具体例（example 明記・配置先所有） |
| test-review 改訂（1〜2行） | `.claude/skills/test-review/SKILL.md` | 「E2E テストのレビューは e2e スキル担当」の境界明記（Related skills + 対象外宣言の行き先） |
| tdd 改訂（1〜2行） | `.claude/skills/tdd/SKILL.md` | 「E2E の作成は e2e スキル担当」の境界明記 |
| README | `README.md` | 実装カテゴリに e2e 行を追加 |

## Data flow

```
「E2E テストを書いて / レビューして」
  → モード判定（作成 or レビュー）
  作成: 対象選定（クリティカルパスか？ ユニットで足りないか？ → 足りるなら tdd に案内）
        → シナリオ分解（1 テスト 1 シナリオ・ページ横断のユーザー行動）
        → 実装（安定性原則。具体 API は references/patterns.md §該当節 — 無ければ判断軸のみで縮退）
  レビュー: 4 軸で審査（対象妥当性 / 粒度 / 安定性 = flaky 温床 / 実ユーザー視点）
        → 軸ごとの表形式レポート（提案のみ・自動修正しない）
  .steering/[task]/ があれば tasklist.md の E2E 項目を更新（無ければ会話内で完結）
```

## Test strategy

- 構造検証: 行数 / description / 絵文字 / name 一致 + **本文ツール名カウント**（grep で Playwright API 出現数を実測 — エンジン純度の受け入れ基準）
- 受け入れ試行: Playwright プロジェクトが必要なため配置先での初回利用に繰り越し（debug と同じ扱い）
- empirical-prompt-tuning: 任意（ユーザー実施判断）

## Open questions

すべて 20260703 の承認時に推奨案で確定:

- [x] **単独スキルで確定**（tdd/test-review 拡張はスリム化済み本文への逆行のため却下）
- [x] **frontend-code-review への統合は今回しない**。配置先で E2E が書かれ始めたら e2e-agent 追加を判断（YAGNI）。test-agent スコープに Playwright spec が紛れた場合は「対象外」報告の縮退で許容
- [x] **references は patterns.md 1 ファイル**（ロケータ / 待機 / fixture / 認証の 4 節構成）

## Alternatives considered

| Alternative | Why rejected |
|-------------|--------------|
| tdd / test-review への E2E 軸拡張 | 両者は課題2 でユニット/インテグレーション用エンジンとしてスリム化済み。別ツールの関心を混ぜ直すのは改修の逆行。トリガーも濁る |
| frontend-code-review に e2e-agent を同時追加 | E2E テストが存在しないリポジトリでは空振りディスパッチが増えるだけ。実需が出てから統合を判断（YAGNI） |
| 本文に Playwright API を直書きし後で分離 | tdd（206→117行）/ test-review（198→103行）の改修コストを既に払った教訓。新規は最初から契約準拠で書く方が安い |
| E2E インフラ監査（設定・CI）も担当に含める | test-review がテストインフラ監査を対象外とした判断と整合させる。設計の判断軸とインフラ運用は別の関心 |
