---
name: knowledge-capture
description: "セッション終了時のプロジェクト知識保存に使うメタスキル。「ナレッジを保存して」「学んだことを記録して」「この決定をドキュメント化して」「セッション終了」「ドキュメントを更新して」と明示的に言われた場合のみ起動。セッション開始時に .capture-needed ファイルがあれば起動。session-log.md を読んで各知見を docs/knowledge/・docs/decisions/・.steering/decisions.md・CLAUDE.md に分類する。タスク完了のたびに自動起動しない。lint ルール・スキルを作成する retrospective-codify とは別物。"
---

# Knowledge Capture

Claude の外部記憶を構築・更新する。
セッションで得た知見を適切なメモリ層に振り分けて保存する。

## When NOT to use

- lint ルール・スキル・CLAUDE.md 行動ルールとして固めたい → `retrospective-codify`（`.tmp/skills`）
- 知識がすでにコードのコメント・型・テストとして表現されている → 追加ドキュメント不要
- タスク固有の一回限りの事象 → コミットメッセージで十分

---

## retrospective-codify との役割分担

| concern | knowledge-capture | retrospective-codify |
|---------|------------------|----------------------|
| ADR・設計判断ドキュメント | **担当** | 対象外 |
| 経験・パターン・アンチパターン集 | **担当** | 対象外 |
| CLAUDE.md 行動ルール化 | 委譲 | **担当** |
| ast-grep lint ルール | 対象外 | **担当** |
| 語彙・用語集 | **担当** | 対象外 |

---

## Step 1 — session-log.md を読む

`.steering/` のアクティブタスクから `session-log.md` を読む:

```bash
find .steering -maxdepth 2 -name "session-log.md" ! -path "*/archived/*"
```

Stop hook が自動追記したセッション記録（git diff --stat）を確認する。
`decisions.md` があれば合わせて読む。

`.capture-needed` フラグが存在する場合は、それがトリガーになっている旨をユーザーに伝える。

`.codify-needed` フラグが存在する場合: `compound` スキルがまだ実行されていない。
「compound スキルも未実行です。先に compound を実行しますか？」と確認する。
（compound = ルール・スキルへの昇格、knowledge-capture = ドキュメント保存、両方を順に実施推奨）

---

## Step 2 — 保存先を決定する

以下の決定木で各知見の保存先を分類する:

```
一回限りの設計・アーキテクチャ判断（なぜこの設計にしたか）?
  YES → docs/decisions/[YYYYMMDD]-[slug].md（ADR形式）

現在タスク固有の決定（再利用性が低い）?
  YES → .steering/[task]/decisions.md（追記）

複数回再利用できるパターン・アンチパターン・ハマりどころ?
  YES → docs/knowledge/[topic].md（トピックごとに集積）
        + CLAUDE.md に @docs/knowledge/[topic].md を追記（参照ルールとして）

Claude Code の短い常時ルール（1行の命令形）?
  YES → CLAUDE.md（project）or ~/.claude/CLAUDE.md（global）
       ※ 行動ルールの詳細化は retrospective-codify に委譲
       ※ CLAUDE.md は ≤200行 厳守

語彙・用語?
  YES → docs/glossary.md（upsert）

一回限りのタスク固有の事象?
  NO → コミットメッセージで十分
```

---

## Step 3 — 重複チェック

書く前に既存の内容と重複がないか確認する:

```bash
# docs/knowledge/ の確認
grep -r "[キーワード]" docs/knowledge/ 2>/dev/null

# docs/decisions/ の確認
grep -r "[キーワード]" docs/decisions/ 2>/dev/null

# CLAUDE.md の確認
grep "[キーワード]" CLAUDE.md ~/.claude/CLAUDE.md 2>/dev/null
```

重複・近似する内容がある場合:
- **既存に追記**: 関連する既存ファイルを更新
- **重複**: 追加不要（ユーザーに報告）

---

## Step 4 — ドラフトを作成して確認を得る

保存内容をドラフトとして提示し、ユーザーの承認を得てから書き込む。
**承認なしに自動書き込みしない。**

提示形式:
```
## Knowledge Capture ドラフト

### [知見1のラベル]
保存先: docs/knowledge/testing-patterns.md
内容:
---
## MSW vs vi.mock の使い分け
[内容]
---

### [知見2のラベル]
保存先: docs/decisions/20260528-use-msw-boundary.md
内容:
---
[ADR形式]
---

採用するものを番号または名前で教えてください。
```

---

## Step 5 — 書き込み

ユーザーが承認した内容のみを書き込む。

### docs/knowledge/[topic].md（トピック別・追記形式）

```markdown
# [Topic]: [プロジェクト名] での実践知識

## [サブトピック]

[パターン・アンチパターン・注意点を記述]

```typescript
// ✅ Good
[例]

// ❌ Bad
[例]
```

### docs/decisions/[YYYYMMDD]-[slug].md（ADR形式）

```markdown
# Decision: [タイトル]

Date: [YYYYMMDD]
Status: Accepted

## Context
[なぜこの決定が必要だったか]

## Decision
[何を決めたか（1文で明確に）]

## Rationale
[なぜこの選択をしたか]

## Consequences
- Good: [利点]
- Bad: [トレードオフ]

## Alternatives considered
| Alternative | Reason rejected |
|-------------|-----------------|
| [代替案] | [却下理由] |
```

### docs/glossary.md（語彙・用語集）

既存のファイルがあれば追記、なければ新規作成。

### CLAUDE.md への追記

短い命令形のルールのみ。行動ルールの詳細は `docs/knowledge/` に書いて `@` 参照にする:

```markdown
## ドキュメント参照（必要なトピック作業時のみ）
テスト実装時: @docs/knowledge/testing-patterns.md
```

---

## Step 6 — フラグを更新して tasklist を更新する

保存完了後:

```bash
# .capture-needed フラグを削除
rm -f .steering/[task]/.capture-needed

# knowledge-capture 完了フラグを作成
touch .steering/[task]/capture_done
```

`tasklist.md` の knowledge-capture チェックボックスをチェック済みにする。

---

## Related skills

- `steering` — フラグ更新後はアーカイブへ（steering archive モード）
- `retrospective-codify` — lint ルール・スキル・行動ルールとして固めたい場合
- `frontend-code-review` — レビューで発見したパターンをここで保存
