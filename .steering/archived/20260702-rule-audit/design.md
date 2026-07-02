# Design: rule-audit

Created: 20260702
Status: **APPROVED**
Approved: 20260703

> 設計素材: [new-skills.md の rule-audit 節](../../docs/skillset-improvement/new-skills.md)（監査基準・手順案・未決事項）/ [ai-driven-frontend-workflow-plan.md](../../docs/ai-driven-frontend-workflow-plan.md) 課題D（剪定機構の不在）

## Goal

CLAUDE.md・ルールファイルを定期監査し、肥大化・陳腐化・曖昧・重複・効果のないルールを検出して剪定する `rule-audit` スキルを新設する。compound（追加・昇格）と対をなす剪定の輪を閉じることで、「AI が読めるドキュメントの維持コストは単調増加しない」ことを構造で保証し、社内懐疑派への説明責任の片輪を埋める（改善計画 課題D）。

## Scope

### In scope

- `rule-audit` スキル新設（`.claude/skills/rule-audit/SKILL.md` 単一ファイル）
  - 監査基準 5 項目: 削除テスト / 症状ベース診断 / 含める・除外する判定 / 昇格先の振り分け（フック・スキル・docs） / 構造制約
  - 手順 7 ステップ（入力収集 → 判定 → 行数・重複 → frontmatter 機械検証 → レポート → 承認分のみ適用 → effectiveness 案内）
  - compound との棲み分けを本文に明記（方向・入力・出力の対比表）
  - 自己完結フォールバック: CLAUDE.md が無い / `.steering/` が無い / skills-ref CLI が無いプロジェクトでの縮退動作
- `compound` の Related skills に rule-audit を追記（両輪の相互参照）
- README 更新: スキル一覧（ナレッジ管理・自己改善 節）への行追加 + 自己改善ループ節に剪定の一文
- 受け入れ試行: このリポジトリ自身の CLAUDE.md に対して 1 回実行し、妥当な監査レポートが出ることを確認（セッション内実行・dispatch なし・追加コストなし）

### Out of scope

- README ワークフロー図の全面改訂（PR/統合フェーズ・入口分岐・feature-pipeline 同期は別タスク — 計画チェックリスト「ワークフローの穴埋め」の別項目）
- `/schedule` による定期実行の自動セットアップ（スキル本文には案内のみ。課金を伴う自動ループは組み込まない）
- skills-ref CLI のインストール・CI 整備（4-C は持ち運び機構タスクで扱う）
- CLAUDE.md への発動ポリシー追記（監査で CLAUDE.md 自体を触るため、ポリシー追記は初回実行の結果を見てから判断）

## Constraints

- Stack: 非依存（監査対象は Markdown ルールファイル。フロントエンドスタックと無関係に動く）
- スキルは自己完結に書く（skill-design-patterns.md）: 対象ファイルが無い場合のフォールバックを該当ステップに直接書く
- 絵文字なし / 本文 <500 行 / description ≤1024 文字 / name=ディレクトリ名
- 行数上限などの構造制約はプロジェクト側の値を使う（このリポジトリは CLAUDE.md ≤200 行）。**本文にはリポジトリ固有値をハードコードせず**「配置先の運用ルールに従う。無ければ『読まれる長さに保つ』を目安とする」と書く（エンジン＋カートリッジ契約）
- 適用は承認制（CLAUDE.md・SKILL.md・docs/ への書き込み承認ルールと整合）。レポート提示までは承認不要

## Acceptance criteria

- [x] `rule-audit/SKILL.md` が存在し、監査基準 5 項目と手順 7 ステップ、compound との棲み分け表を含む
- [x] CLAUDE.md が無いプロジェクト・skills-ref CLI が無い環境での縮退動作が該当ステップに明記されている
- [x] `compound/SKILL.md` の Related skills に rule-audit が追記されている（逆参照も rule-audit 側に）
- [x] README のスキル一覧・自己改善ループに剪定が反映されている
- [x] このリポジトリの CLAUDE.md への試行で「各ルールに保持/削除/統合/移動/明確化 + 理由」のレポートが出力される（20260703: 参照切れ・find の穴など実所見 6 件を検出、5 件適用）
- [x] 構造検証パス（166 行・desc 176 字・絵文字なし・name 一致）

## Approach

new-skills.md の設計案（監査基準・手順案・棲み分け表）をほぼそのまま SKILL.md に落とす — 設計判断の大半は 2026-06-17 時点で済んでおり、本タスクの新規判断は「定期実行を組み込まない」「skills-ref はあれば使う」の 2 点に絞られる。監査ロジックは全てセッション内で完結させ（subagent ディスパッチなし）、実行コストを構造的にゼロ近くに保つ。references/ は作らない: 監査基準そのものが判断エンジンでありスタック語彙を含まないため、分離するカートリッジが存在しない。

## Key components

| Component | Location | Responsibility |
|-----------|----------|----------------|
| rule-audit（新設） | `.claude/skills/rule-audit/SKILL.md` | 監査本体。入力収集 → 5 基準判定 → レポート → 承認分のみ適用 |
| compound 改訂（1行） | `.claude/skills/compound/SKILL.md` | Related skills に「rule-audit — 対をなす剪定スキル」を追記 |
| README | `README.md` | スキル一覧に行追加・自己改善ループ節に「compound が増やし rule-audit が刈る」の一文 |

## Data flow

```
入力収集: CLAUDE.md（project / ~/.claude）+ docs/knowledge/ + .claude/skills/*/SKILL.md frontmatter
          + .steering/**/codify-log.md（あれば: 昇格履歴 → 由来の分かるルール）
  → 各ルールを 5 基準で判定（削除テスト / 症状診断 / 含める・除外 / 昇格先振り分け / 構造制約）
  → 監査レポート提示: ルールごとに 保持 / 削除 / 統合 / 移動（フック・スキル・docs） / 明確化 + 理由
  → ユーザー承認（項目単位）
  → 承認分のみ適用（移動先が必要ならフック・スキルの骨組みも生成）
  → 変更履歴は git が持つ（専用ログファイルは作らない）
```

## Test strategy

- 構造検証: 行数 / description 文字数 / アストラル面絵文字 / name 一致（無料・機械的）
- 受け入れ試行: このリポジトリの CLAUDE.md（約 40 行・ルール数十数件）に対して実行し、判定の妥当性を人間が確認する（セッション内・dispatch なし）
- empirical-prompt-tuning: 任意（ユーザー実施判断。前タスクの方針を踏襲し設計には組み込まない）

## Open questions

new-skills.md の未決 4 件。20260703 の承認時に推奨案で確定:

- [x] **スキル名**: `rule-audit` で確定
- [x] **監査対象スコープ**: フルスコープで確定 — CLAUDE.md（project + `~/.claude/`）+ docs/knowledge/ の参照整合（@参照切れ・重複）+ スキル frontmatter の構造検証
- [x] **定期実行**: `/schedule` セットアップは組み込まない。末尾に「定期 GC は /loop・/schedule と相性が良い」の案内のみ
- [x] **skills-ref validate**: CLI 導入を前提にしない。「あれば `skills-ref validate` を使い、無ければ手動同等チェック（name 一致 / description ≤1024 / 本文 ≤500 行）」を該当ステップに書く

## Alternatives considered

## Research

### 既存パターン調査（20260703）
- メタスキルの構造: compound / knowledge-capture は「When NOT to use → 棲み分け表 → Step 順の手順 → Related skills」構成。フラグ更新等の決定論的処理は bash ブロックで明示 → rule-audit も踏襲
- メタスキルは compatibility frontmatter を持たない（スタック非依存のため）→ rule-audit も付けない
- 注意点: 「レポート提示までは承認不要・適用は承認制」の線引きを本文冒頭に明記する（compound の「昇格は承認なしに適用しない」と同じ規律）

## Alternatives considered

| Alternative | Why rejected |
|-------------|--------------|
| compound に剪定モードを追加 | 方向（追加 vs 剪定）・入力（steering メモ vs ルールファイル自体）・出力が全て異なる（new-skills.md の棲み分け表）。1 スキルに同居させるとトリガーも手順も濁る |
| 手動レビューのみ（スキル化しない） | 「定期的に実施される」保証がなく属人化する。剪定の不在こそが課題D の本体 |
| lint / CI による自動剪定 | 削除テスト（このルールを消すと間違えるか？）は判断を要し機械化できない。機械化できる構造検証（行数等）は手順の 1 ステップとして内包する |
| references/ にベストプラクティス抜粋を分離 | 監査基準は判断エンジンそのものでスタック語彙を含まず、分離すると本文が空洞化する。単一ファイルの方が孤立 subagent にも安全 |
