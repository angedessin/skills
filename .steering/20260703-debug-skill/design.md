# Design: debug-skill

Created: 20260703
Status: **APPROVED**
Approved: 20260703

> 設計素材: [new-skills.md の debug 節](../../docs/skillset-improvement/new-skills.md)（決定方針あり）/ [ai-driven-frontend-workflow-plan.md](../../docs/ai-driven-frontend-workflow-plan.md) 5-2 の入口分岐

## Goal

障害調査の専用スキル `debug` を新設する。現状は design-doc が description で「障害調査」を謳いながら実体は設計ドキュメント作成スキルで、調査手順（再現→切り分け→根本原因→修正方針）を持たない — 看板と中身の乖離。バグ修正は新機能とフローが逆（設計より先に原因特定が要る）なのに専用手順がなく、バグが新機能と同じ入口を通る歪みを解消する。あわせて design-doc の description から「障害調査」を除去し、ワークフローの入口分岐（新機能 → design-doc / バグ・障害 → debug）を成立させる。

## Scope

### In scope

- `debug` スキル新設（`.claude/skills/debug/SKILL.md` 単一ファイル・references なし）
  - フロー 5 ステップ: 再現確認 → 仮説立案 → 切り分け（二分探索的） → 根本原因特定 → 修正方針
  - 出口分岐: 修正が小さい（影響がファイル数件に閉じ・巻き戻し容易）→ 承認を得て即修正 / 構造に触る → design-doc に接続
  - 記録先: `.steering/[task]/investigation.md`（タスクディレクトリがあれば。無ければ会話内で完結 — 自己完結フォールバック）
  - 再現できないバグの縮退動作: ログ・コードリーディングベースの仮説検証ループに切り替え、確度をレポートに明記
- `design-doc` の description 修正: 「障害調査」を除去し、「バグ・障害の調査は debug を使う」のリダイレクトを追記
- README 更新: スキル一覧（設計・コンテキスト管理の隣に新カテゴリ or 既存カテゴリへ行追加）+ メインワークフロー図直下に入口分岐の一文

### Out of scope

- README ワークフロー図の全面改訂（[0] 入口分岐・[6] PR/統合フェーズの図への組み込みは feature-pipeline 同期と同一コミットで行う別タスク — 計画 5-2 の 5）
- feature-pipeline への debug フェーズ組み込み（同上）
- スタック固有のデバッグ手技（React DevTools・ブラウザプロファイラ等）の references 化（調査フローは完全にスタック非依存。必要になった配置先が足す）
- `explore` スキル（コード探索は別の関心 — new-skills.md の分離判断どおり）

## Constraints

- Stack: 非依存（調査フロー自体はフロントエンドにも限定されない）
- スキルは自己完結に書く: `.steering/` が無いプロジェクトでも動く（investigation.md は任意出力）
- 絵文字なし / 本文 <500 行 / description ≤1024 文字 / name=ディレクトリ名 / description は引用符付き
- 誤発動防止: 「テストが失敗した」だけ（原因が自明）や新機能の設計では起動しない旨を description と When NOT to use に明記
- 修正の適用は承認制（原因特定・修正方針の提示までは調査行為として承認不要）

## Acceptance criteria

- [ ] `debug/SKILL.md` が存在し、5 ステップのフロー・出口分岐（即修正 / design-doc 接続）・再現不能時の縮退動作を含む
- [ ] `.steering/` が無いプロジェクトでの動作（会話内完結）が該当ステップに明記されている
- [ ] `design-doc` の description から「障害調査」が除去され、debug へのリダイレクトが When NOT to use にある
- [ ] README のスキル一覧に debug が掲載され、入口分岐の一文がある
- [ ] 構造検証パス（行数・description 長・絵文字・name 一致・引用符）

## Approach

new-skills.md の決定方針（分離して独立スキル化・フロー 5 段階・design-doc とは逆順）をそのまま SKILL.md に落とす。調査ステップは「証拠に基づいて仮説を絞る」規律を核にする — 症状のパターンマッチで直しに行かず、根本原因を再現/コードの証拠で確認してから修正方針を出す。出口は改善計画 5-2 の入口分岐と対になる二方向: 小さい修正は承認を得てその場で完了（30 分以内のバグ修正に design-doc を要求しない既存ルールと整合）、構造に触る修正は design-doc に接続して通常フローに合流する。

## Key components

| Component | Location | Responsibility |
|-----------|----------|----------------|
| debug（新設） | `.claude/skills/debug/SKILL.md` | 調査フロー本体。再現→仮説→切り分け→根本原因→修正方針 |
| design-doc 改訂（frontmatter + When NOT to use） | `.claude/skills/design-doc/SKILL.md` | description から「障害調査」除去 + debug へのリダイレクト 1 行 |
| README | `README.md` | スキル一覧への行追加 + 入口分岐の一文 |

## Data flow

```
バグ報告・「動かない」
  → Step 1 再現確認（再現手順の確立。不能なら縮退: ログ・コードリーディングベースと明記）
  → Step 2 仮説立案（可能性順に複数列挙。1つに飛びつかない）
  → Step 3 切り分け（二分探索: git bisect / レイヤー分割 / 最小再現コード）
  → Step 4 根本原因特定（症状でなく原因。証拠 = 再現差分・コード箇所を明示）
  → Step 5 修正方針の提示
       ├─ 小さい修正（影響が閉じる・巻き戻し容易）→ 承認 → 即修正 → テストで再発防止
       └─ 構造に触る修正 → design-doc に接続（調査結果を design.md の Research に引き継ぐ）
  記録: .steering/[task]/ があれば investigation.md に調査ログ、無ければ会話内で完結
```

## Test strategy

- 構造検証: 行数 / description 文字数 / アストラル面絵文字 / name 一致（無料・機械的）
- 受け入れ試行: 実バグが必要なためこのリポジトリでは実施しない（rule-audit と異なり監査対象が手元にない）。配置先プロジェクトでの初回利用が実地検証を兼ねる
- empirical-prompt-tuning: 任意（ユーザー実施判断。これまでの方針を踏襲）

## Open questions

すべて 20260703 の承認時に推奨案で確定:

- [x] **即修正の「小さい」の線引き**: 「影響がファイル数件に閉じる・git で巻き戻し容易・テストで再発防止できる」の 3 条件で確定
- [x] **design-doc の description 修正**: 除去 + When NOT to use リダイレクト + description 本文にも「バグ・障害の調査は debug を使う」を明記（発動判定での誤発動防止）
- [x] **README の掲載位置**: 「設計・コンテキスト管理」テーブルに行追加で確定

## Research

### 既存パターン調査（20260703）
- スキル規約は本セッションで rule-audit / review-correctness 新設時に確立済みのものを踏襲（引用符付き description・When NOT to use 先頭・フォールバックを該当ステップに直書き・「承認不要の範囲」を冒頭に明記）
- design-doc の description 修正は「新機能・タスク開始・障害調査に使う」→「新機能・タスク開始に使う」+ 末尾リダイレクト文の追加（実測 L3）

## Alternatives considered

| Alternative | Why rejected |
|-------------|--------------|
| design-doc に調査モードを追加 | フローが逆順（原因特定が先）で手順を同居させると両方濁る。看板と中身の乖離の解消にならない（new-skills.md の分離判断） |
| explore（コード探索）と統合 | 「障害調査」と「コード探索」は別の関心（同上）。explore はビルトイン重複の確認が先で保留中 |
| references/ にデバッグ手技集を分離 | 調査フローは完全にスタック非依存で、分離するカートリッジが現状ない。必要になった配置先が足せばよい（YAGNI） |
| 修正まで常にスキル内で完結 | 構造に触る修正を調査の勢いで進めると承認ゲートを迂回する。design-doc 接続で通常フローに合流させる |
