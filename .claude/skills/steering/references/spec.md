# .steering/ 仕様詳細

## 作成基準

**`.steering/` は複数セッションにまたがる見込みのタスクのみ作成する。**
1セッションで完了する見込みのタスクは、ユーザーに「会話内設計で進めるか、`.steering/` を作るか」を確認し、会話内設計が選ばれた場合のみ会話内で設計方針を確認して進める（Claude の見積もりだけで省略を確定しない。次セッションの自分が読まないファイルは作らない、が縮退の趣旨）。
途中で複数セッションにまたがると判明したら、その時点で作成して会話内の設計内容を design.md に転記する。
例外: `feature-pipeline` 等のオーケストレーター配下では、タスク規模によらず常に作成する（現在地検出・ゲート・フラグが成果物に依存するため。design-doc 側にも同じ例外を明記済み）。

## ディレクトリ構造

```
.steering/
├── [YYYYMMDD]-[task-name]/    ← 進行中タスク
│   ├── design.md              ← 必須: 要求 + 実装アプローチ（DRAFT / SPIKE / APPROVED）
│   ├── tasklist.md            ← 必須: チェックボックス形式のタスクリスト
│   ├── decisions.md           ← 任意: タスク固有の決定事項ログ
│   ├── blockers.md            ← 任意: 未解決の問題・依存待ち
│   ├── skill-issues.md        ← 任意: スキル自体の不具合記録（compound が読む）
│   ├── investigation.md       ← 任意: debug が生成（障害調査ログ: 仮説・検証・棄却理由）
│   ├── review-result.md       ← frontend-code-review が生成: 指摘と修正追跡
│   ├── codify-log.md          ← compound が生成: パターン昇格の履歴
│   ├── .capture-needed        ← フラグ: knowledge-capture 未実行を示す
│   ├── .codify-needed         ← フラグ: compound スキル未実行を示す
│   ├── pr_capture_done        ← フラグ: PR 差分に属する知見の保存済みを示す（PR 前 capture）
│   └── capture_done           ← フラグ: 最終 knowledge-capture 完了済みを示す（アーカイブのハードストップ）
└── archived/
    └── [YYYYMMDD]-[task-name]/  ← 完了タスク（git で永続管理）
```

**旧構造との互換**: 2026-06 以前のタスクには `requirements.md`（要求を分離したファイル）と `session-log.md`（Stop hook の自動ログ）が存在する。読み取り時はあれば読む。新規タスクでは作らない。

## 各ファイルの役割

### design.md（必須）

要求の整理（目的 / スコープ / 完了条件）と実装アプローチを1ファイルにまとめる。
**実装可否の正本**: DRAFT のみ実装禁止。SPIKE / APPROVED は実装可（SPIKE は外向き不可 — push / remote / PR をしない）。
**Status 読み取り規則**: `Status:` 行の最初の語彙トークン（`**` を除く）∈ {DRAFT,SPIKE,APPROVED}。以外・欠落は停止。
人間の承認後に DRAFT → APPROVED に変更する。探索はユーザー明示で SPIKE。SPIKE → APPROVED 直昇格は禁止（一度 DRAFT に戻す）。

```markdown
# 設計: [task-name]

Created: [YYYYMMDD]
Status: **DRAFT — awaiting review**

## 目的
[一段落: このタスクが達成することと理由]

## スコープ
### 対象
- [項目]

### 対象外
- [項目]

## 制約
- Stack: React / TypeScript / Vitest / React Testing Library / MSW / Playwright
- [その他の制約]

## 完了条件
- [ ] [基準1]
- [ ] [基準2]

## アプローチ
[2〜4文: 核となる技術的な判断]

## 主要コンポーネント
| コンポーネント | 場所 | 責務 |
|---------------|------|------|
| [name] | `src/...` | [役割] |

## 未解決の論点
- [ ] [人間のレビューが必要な質問]
```

（付録境界・付録節は `design-doc/references/templates.md` に従う。）

承認後:
```markdown
Status: **APPROVED**
Approved: [YYYYMMDD]
```

SPIKE（探索）:
```markdown
Status: **SPIKE**
```

### tasklist.md（必須）

セッションのたびに更新する。チェックボックスが Claude の「現在地」を示す。

```markdown
# タスクリスト: [task-name]

Last updated: [YYYYMMDD]

## 実装

- [ ] [design.md の主要コンポーネントから導出したタスク]
- [ ] [タスク2]
- [ ] テスト作成（TDD Red フェーズ）
- [ ] 実装（TDD Green フェーズ）
- [ ] リファクタリング（TDD Refactor フェーズ）

## レビュー

- [ ] frontend-code-review の実行
- [ ] レビュー指摘の修正（review-result.md を参照）
- [ ] 修正後の差分再レビュー

## 知見保存（この PR / ブランチに載せる分）
<!-- この変更の説明・落とし穴として残す knowledge は、マージ前に同じブランチへ含める。 -->
<!-- 「デプロイのあと」に回すと、後続 PR や別差分に混ざる。 -->

- [ ] knowledge-capture スキルの実行（PR 差分に属する知見）
- [ ] 必要なら docs/ への追記をこのブランチでコミット

## デプロイ
<!-- git push してブランチを PR にするフェーズ。CI がないリポジトリはスキップ可。 -->
<!-- GitHub Actions 等があれば CI グリーンを確認してからマージする。 -->
<!-- 末尾の `PR:` / `CI:` / `Feedback:` の 3 行はチェックボックスにしない（状態の記録）。feature-pipeline の現在地判定が読む。 -->
<!-- `PR:` は URL か none / `CI:` は green・failing・none / `Feedback:` は yes（返信待ちの指摘あり）か no。pr-feedback の対応後は no に戻す。 -->

- [ ] PR 作成（`pr-create` スキルまたは `gh pr create`）
- [ ] CI グリーン確認
- [ ] マージ
- PR: none
- CI: none
- Feedback: no

## 福利化
<!-- レビュー・実装で発見したパターンをルール・知識・スキルに昇格するフェーズ。 -->
<!-- frontend-code-review 完了後に .codify-needed フラグが作成される。 -->
<!-- マージ後でもよい（昇格は別ゲート）。PR に載せる knowledge 本文とは分ける。 -->

- [ ] compound スキルの実行（パターンをルール・知識に昇格）

## クローズ
<!-- マージ後の横断知見・アーカイブ。PR 差分に属する知見は上の「知見保存」で済ませる。 -->

- [ ] knowledge-capture（会話由来・横断の残りがあれば）
- [ ] steering archive モードでアーカイブ
```

### review-result.md（frontend-code-review が生成）

`frontend-code-review` スキルがレビュー完了後に書き込む。
修正状況のチェックボックスで「何が直ったか」を追跡する。
`compound` スキルはこのファイルを入力として使う。

### codify-log.md（compound が生成）

compound 実行のたびに「何をどこへ昇格したか」を追記する履歴。
次回の compound がこれを読み、**昇格済みルールに反する指摘が再発していないか**を突合する（ルールの効果検証）。

### decisions.md（任意）

タスク固有の決定事項。決定・理由・却下した代替案を残す。

```markdown
## [YYYYMMDD] — [短いラベル]

**決定**: [決定内容]
**理由**: [なぜ]
**影響**: [今後に影響すること]
```

### skill-issues.md（任意）

セッション中に気づいたスキル自体の不具合（誤発動・指示の曖昧さ・実行不能な手順・裁量補完が必要だった箇所）を記録する。
`compound` が読んで `empirical-prompt-tuning` の起動候補にする。

```markdown
## [YYYYMMDD] — [skill-name]

**事象**: [何が起きたか]
**期待**: [本来どう動くべきだったか]
```

### investigation.md（任意）

`debug` スキルが生成する障害調査ログ。仮説・検証結果・棄却理由を残す（同じ道を二度調べないため）。
調査が design-doc に接続された場合、結論は design.md の「調査結果」セクションに引き継がれる。

```markdown
## [YYYYMMDD] — [症状の要約]

**再現**: 確認済み（最小再現: ...）/ 未確認
**仮説と検証**: [仮説] → [裏付け / 棄却理由]
**根本原因**: [file:line] — [機序]
```

### blockers.md（任意）

解決待ちの問題。次のセッションで見逃さないように記録する。

```markdown
## [YYYYMMDD] — [ブロッカーの内容]

**Status**: OPEN / RESOLVED
**待ち先**: [誰・何を待っているか]
**解決**: [解決したら記入]
```

## セッション開始コントラクト

毎セッション:
1. 未処理フラグ（`.capture-needed` / `.codify-needed`）とアクティブタスク一覧は **SessionStart hook `session-start-check.sh` が検出して context に注入する**（手動の find は不要）
2. `.capture-needed` が注入されたら、対象タスクごとに「今 / 後で / スキップ」で確認する（一括スキップ禁止。操作定義は `session-start-check.sh` の注入文。CLAUDE.md 再掲は任意）。スキップは `.capture-needed` のみ削除（`capture_done` 非作成・効果は次の Stop まで）
3. `.codify-needed` が注入されたら compound スキルを促す（capture 三択の後。スキップしても残す）
4. アクティブタスクの context を読む
5. 複数タスクがあれば優先度を確認

**hook が配置されていないプロジェクト**（SessionStart hook を同送していない場合）は、1 を次のコマンドで代替する:
```bash
find .steering \( -name '.capture-needed' -o -name '.codify-needed' \) -not -path '*/archived/*' 2>/dev/null
```

## アーカイブポリシー

**完了後も削除しない。git で永続管理を推奨。**

理由:
- 意思決定ログとして残る
- 類似タスクのたたき台になる
- 障害時に当時の設計意図を遡れる

`tasklist.md` が全チェック済みになったら `archived/` へ移動。
直近3件は `steering status` で表示される。

**knowledge-capture ハードストップ**（`steering` archive モードと同一）: アーカイブ前に `capture_done` または「知見なしでアーカイブ」が必要。汎用「省略してアーカイブ」および tasklist `[x]` 単独では非充足。