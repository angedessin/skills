---
name: knowledge-capture
description: "セッション終了時のプロジェクト知識保存に使うメタスキル。「ナレッジを保存して」「学んだことを記録して」「この決定をドキュメント化して」「セッション終了」「ドキュメントを更新して」と明示的に言われた場合のみ起動。セッション開始時に .capture-needed ファイルがあれば起動。decisions.md・review-result.md・会話コンテキストから知見を抽出し docs/knowledge/・docs/decisions/・.steering/decisions.md・CLAUDE.md に分類する。タスク完了のたびに自動起動しない。lint ルール・スキルを作成する compound とは別物。"
metadata:
  version: "1.3"
  source-commit: 496a050cfde484237439c1899294042fecc06732
---

# Knowledge Capture

Claude の外部記憶を構築・更新する。
セッションで得た知見を適切なメモリ層に振り分けて保存する。

## When NOT to use

- lint ルール・スキル・CLAUDE.md 行動ルールとして固めたい → `compound`
- 知識がすでにコードのコメント・型・テストとして表現されている → 追加ドキュメント不要
- タスク固有の一回限りの事象 → コミットメッセージで十分

---

## compound との役割分担

| concern | knowledge-capture | compound |
|---------|------------------|----------------------|
| ADR・設計判断ドキュメント | **担当** | 対象外 |
| 経験・パターン・アンチパターン集（新規トピック・まとまった集積） | **担当** | 既存トピックへの短い落とし穴追記のみ担当 |
| CLAUDE.md 行動ルール化 | 委譲 | **担当** |
| ast-grep lint ルール | 対象外 | **担当** |
| 語彙・用語集 | **担当** | 対象外 |

---

## Step 1 — 知見の入力を集める

`.steering/` のアクティブタスクのフラグと入力ファイルを一括確認する:

```bash
find .steering -maxdepth 2 \( -name "decisions.md" -o -name "review-result.md" -o -name ".capture-needed" -o -name ".codify-needed" \) ! -path "*/archived/*"
```

**フラグ確認（入力ファイルの有無に関係なく独立して処理する。上から順に実行する）:**

- `.capture-needed` が存在する → それがトリガーになっている旨をユーザーに伝える
- `.codify-needed` が存在する → **入力ファイルの有無に関わらずここで確認する**:
  「compound スキルも未実行です。先に compound を実行しますか？」
  （compound = ルール・スキルへの昇格、knowledge-capture = ドキュメント保存、両方を順に実施推奨）
  - ユーザーが **Yes** → knowledge-capture をここで中断し、compound スキルを先に実行するよう案内する。compound 完了後にもう一度 knowledge-capture を呼び出してもらう。
  - ユーザーが **No** → そのまま続行する（入力の確認へ進む）。
- `capture_done` が既に存在する → このタスクの knowledge-capture は完了済み。再実行の必要はない旨を伝え、追加の知見保存が目的かをユーザーに確認する（目的が無ければここで終了する）

**知見の入力（フラグ確認の後で行う）。入力源は3つで、あるものをすべて使う:**

1. `.steering/[task]/decisions.md` — 実装中の技術的判断とその理由
2. `.steering/[task]/review-result.md` — レビューで発見されたパターン
3. **現在の会話コンテキスト** — このセッションで得た学び・ハマりどころ（同一セッション内で起動された場合）

3つとも**得られない場合**（ファイルなし・別セッションからの再開で会話に文脈もない）→ ここで止まる:
```
知見の入力が見つかりませんでした（decisions.md / review-result.md なし）。
保存したい知見の内容を直接教えてください。
```
ユーザーが内容を提示したらその内容を「知見」として Step 2 に進む。

git の変更履歴を確認したい場合は `git log --oneline -20` と `git diff [範囲] --stat` を使う（旧構造の session-log.md は廃止済み。古いタスクに残っていれば参考として読んでよい）。

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
        + 常時参照させたい知識のみ CLAUDE.md に @参照を追記
          （@ は毎セッション展開される固定費。必要時に読む導線ならプレーンなパス表記 — Step 5 と同基準）

Claude Code の短い常時ルール（1行の命令形）?
  YES → CLAUDE.md（project）or ~/.claude/CLAUDE.md（global）
       ※ 行動ルールの詳細化は compound に委譲
       ※ CLAUDE.md は ≤200行 厳守

語彙・用語?
  YES → docs/glossary.md（upsert）

上記のどれにも該当しない一回限りのタスク固有の事象?
  YES → コミットメッセージで十分。ドキュメント保存は不要。
```

**複数の分岐に同時命中する場合**: 命中した分岐すべてのドラフトを作成してユーザーに提示する（例: 「なぜこの設計にしたか」と「再利用できるパターン」の両方に命中 → ADR と knowledge の両方をドラフトに含める）。ユーザーがどれを採用するか選ぶ。

**`docs/` ディレクトリが存在しないプロジェクトの場合**: 決定木の保存先はそのまま使い、Step 4 のドラフト提示時に「ディレクトリを新規作成するか・別の置き場にするか」をあわせて確認する。

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
保存先: docs/knowledge/[topic].md
内容:
---
## [保存する知見の見出し]
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
// Good
[例]

// Bad
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

**既存 ADR の決定を変更・進化させる場合**: 新規 ADR を書くだけで終えず、旧 ADR の Status を
`Superseded by [新ADRファイル名]`（決定を置き換えた）または `Accepted (Amended [YYYYMMDD])` +
末尾に `## Amendments` 節追記（核は不変で運用が進化した）に更新し、新旧を相互リンクする。
ADR は行動には配線されず pull でのみ読まれるため、この印が無いと後から読んだ人（AI 含む）が
古い決定を現行と誤読する。Step 3 の重複チェックで近縁 ADR が見つかったら、この更新が要るかを確認する。

### docs/glossary.md（語彙・用語集）

既存のファイルがあれば追記、なければ新規作成。

### CLAUDE.md への追記

短い命令形のルールのみ。行動ルールの詳細は `docs/knowledge/` に書いて参照にする。
**`@` 参照は毎セッション中身が展開される**（コンテキスト固定費）— 常時読ませたい場合のみ `@` を付け、必要時に読む導線ならプレーンなパス表記にする:

```markdown
## ドキュメント参照（必要なトピック作業時のみ）
[トピック]作業時: @docs/knowledge/[topic].md
```

---

## Step 6 — フラグを更新して tasklist を更新する

`.steering/` のタスクディレクトリが存在しない場合（会話から直接知見を保存した場合）はこの Step をスキップして完了報告する。

保存完了後:

```bash
# .capture-needed フラグを削除
rm -f .steering/[task]/.capture-needed

# knowledge-capture 完了フラグを作成
touch .steering/[task]/capture_done
```

`tasklist.md` の knowledge-capture チェックボックスをチェック済みにする（tasklist.md が無ければスキップ）。

---

## Related skills

- `steering` — フラグ更新後はアーカイブへ（steering archive モード）
- `compound` — lint ルール・スキル・行動ルールとして固めたい場合
- `frontend-code-review` — レビューで発見したパターンをここで保存
