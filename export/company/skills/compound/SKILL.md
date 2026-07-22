---
name: compound
description: "レビューや実装で得た学びをルール・知識・スキルに昇格させる汎用スキル（福利化）。「福利化して」「codify して」「ルール化して」「パターンを抽出して」などのフレーズが対象。セッション開始時に .codify-needed フラグがあれば起動を促す。knowledge-capture（ドキュメント保存）とは別物で、こちらは CLAUDE.md ルール・スキル・lint ルール・hook への昇格が主眼。"
metadata:
  version: "1.4"
  source-commit: e90165507d319933f2c07f9538b0a0040e67842e
---

# Compound（福利化）

レビュー・実装・テストで発見したパターンを、次のサイクルで自動的に防止できる
**ルール・知識・スキル** に変換する汎用スキル。

「同じ指摘を二度しない」ためのフェーズ。

## When NOT to use

- ドキュメントに保存したい（新規トピックのパターン集・設計判断の記録） → `knowledge-capture`
- lint ルール・ast-grep ルール・hook として固めたい場合は、このスキルがその起点になれる
- 1回限りの事象 → コミットメッセージで十分

**knowledge-capture との境界**: 昇格フローの中で見つけた落とし穴を docs/knowledge/ の**既存トピックへ短く追記**するのは本スキルの担当。**新規トピックの立ち上げ・まとまった集積・設計判断の記録**は knowledge-capture の担当（同スキル側にも同じ境界を明記済み）。

---

## Step 1 — 入力を収集する

以下のコマンドで対象ファイルを探す:

```bash
find .steering -maxdepth 2 \( -name "review-result.md" -o -name "decisions.md" -o -name "skill-issues.md" -o -name "codify-log.md" \) ! -path "*/archived/*" 2>/dev/null
```

**ファイルが見つかった場合** — 下記テーブルの通り読む:

| ファイル | 読む内容 |
|---|---|
| `.steering/[task]/review-result.md` | レビュー指摘のパターン（繰り返し出現するものを重視） |
| `.steering/[task]/decisions.md` | 技術的判断とその理由 |
| `.steering/[task]/skill-issues.md` | スキル自体の不具合（誤発動・曖昧な指示・裁量補完）。Step 2 でスキル改善候補にする。`session-retrospective` がセッション終盤に採掘・起票する主要な供給元 |
| `.steering/[task]/codify-log.md` | 過去に昇格したルールの履歴。Step 2 の効果検証（突合）に使う |
| `docs/knowledge/` | 既存の知識（重複確認のため） |
| `CLAUDE.md` | 既存ルールとの重複確認（同一ルールへの追記を防ぐ） |

**ファイルが 1 件も見つからなかった場合（`.steering/` が存在しない等）** — ここで止まってユーザーに確認する:

```
.steering/ にファイルが見つかりませんでした。
パターン抽出の対象ファイルのパスを教えてください。
（例: ~/project/review-result.md）
```

ユーザーが提示したファイルを読んで Step 2 に進む。Step 5 のフラグ更新（`.codify-needed` 削除・`codify-log.md`・`tasklist.md`）は `.steering/` がなければスキップし、その旨を Step 3 のドラフトに明記する。

---

## Step 2 — パターン抽出と効果検証

以下の観点で「再利用可能な学び」を識別する:

**昇格候補の優先順位:**
1. **繰り返し出現する指摘**（複数ファイルで同じ問題）→ CLAUDE.md ルール or lint ルール
2. **繰り返す操作ミス・実行時の失敗**（危険コマンドの実行未遂・「できました（できてない）」・書式崩れなど、スキルの内容と無関係なミスパターン）→ **hook 化**（PreToolUse でブロック / PostToolUse で自動検証・差し戻し / Stop で差し戻し）。実装パターンと配布手順は docs/knowledge/claude-code-config.md を参照（無い場合は既存 hook の流儀に合わせて提案する）
3. **知らなかった仕様・落とし穴**（一度詰まったもの）→ `docs/knowledge/` の**既存トピックへ短く追記**（新規トピックを立ち上げる分量なら `knowledge-capture` に委譲）
4. **技術的判断の理由**（なぜその設計か）→ `knowledge-capture` に委譲（決定の記録は同スキルの担当）
5. **再利用可能な実装パターン**（汎用的な解法）→ 新スキルの骨組み（ドキュメント集積として残す場合は `knowledge-capture` に委譲）
6. **スキル自体の不具合**（skill-issues.md 由来）→ 該当スキルの修正（修正後、同じ状況を再現させて挙動が直ったかを実地で確認する）

**昇格しないもの:**
- 1回限りのバグ修正 → コミットメッセージで十分
- プロジェクト固有すぎて横展開できないもの

**昇格済みルールの効果検証（codify-log.md がある場合は必ず行う）:**

1. `codify-log.md`（アクティブタスクと `archived/` 直近数件）から過去に昇格したルールの一覧を得る
   ```bash
   find .steering -name "codify-log.md" 2>/dev/null
   ```
2. 今回の `review-result.md` の指摘と突合する
3. **昇格済みルールに反する指摘が再発している場合** → そのルールは効いていない。「ルールの書き方自体」を改善対象として Step 3 のドラフトに含める（例: 表現が曖昧 → 具体例を追加、CLAUDE.md では読まれない → lint ルール化を提案）

---

## Step 3 — 昇格先の提案

抽出したパターンを分類してドラフトを提示する:

**昇格候補が 1 件以上ある場合:**

```
## 福利化ドラフト

### [パターン1のラベル]
昇格先: CLAUDE.md ルール
理由: review-result.md に3箇所で同じ指摘
内容:
───
- `<div onClick>` は `<button>` に置き換える
───

### [パターン2のラベル]（skill-issues.md 由来の例）
昇格先: .claude/skills/[skill]/SKILL.md の修正
理由: skill-issues.md に「[事象]」の記録
内容:
───
[SKILL.md の修正案。適用後に同じ状況を再現させて挙動が直ったかを確認する]
───

### [パターン3のラベル]（効果検証で再発を検知した例）
昇格先: 既存ルールの改善（CLAUDE.md / lint ルール化）
理由: codify-log.md の昇格済みルール「[ルール]」に反する指摘が review-result.md に再発
内容:
───
[ルールの書き直し案 or lint ルール化の提案]
───

採用するものを番号または名前で教えてください。
```

**各候補に「実証済み / 未検証」を明記する** — 実地で動いた実績のあるパターンの記録か、動作未確認の新しいメカニズム（新しい呼び出し契約・フォールバック経路など）の提案かを区別する。未検証の新メカニズムは直接適用せず、`skill-issues.md` への提案記録に留めることを推奨案として提示する（実地かレビューで検証されてから適用する）。

**昇格先が「新規スキルの作成」になる場合** → このプロジェクトにスキルの雛形（`templates/SKILL.template.md` 等）があればコピーして書き始める（契約準拠を最初から構造として渡せる）。**雛形が無い場合は**既存スキルの書式に倣って書く。

**昇格候補がゼロの場合（すべて既存ルールと重複 / 1回限りの事象のみ）:**

承認は求めない。以下を報告し、そのまま Step 5（フラグ更新）を実行する:

```
## 福利化ドラフト

新規昇格候補はありませんでした。
（理由: [重複 / 1回限りの事象など]）

.codify-needed フラグの削除と codify-log.md への記録を行います。
```

**昇格（CLAUDE.md・docs/・スキルへの書き込み）は承認なしに適用しない。** フラグ削除・codify-log.md 追記は git で巻き戻せてタスク内に閉じる操作なので承認不要。

---

## Step 4 — 実行

ユーザーが承認した項目のみを実行する。

### CLAUDE.md ルール追記

```markdown
## スタック制約（行動ルール）
- [新しい1行ルール]
```

**制約**: CLAUDE.md は ≤200行 厳守。詳細な説明は `docs/knowledge/` に書いて `@参照` にする。
CLAUDE.md が存在しないプロジェクトでは、追記先（AGENTS.md 等の相当ファイル）をユーザーに確認する。

### docs/knowledge/[topic].md への追記（既存トピックのみ）

既存ファイルへ短い節を追記する。**新規トピックの立ち上げは `knowledge-capture` に委譲する**（When NOT to use の境界）。
`docs/knowledge/` ディレクトリ自体が無いプロジェクトでも同様に knowledge-capture 側で扱う。

```markdown
## [サブトピック]

[パターン・アンチパターン・注意点]

```typescript
// Good
// Bad
```

### 新スキルの骨組み生成

`.claude/skills/[skill-name]/SKILL.md` を以下の最小構造で生成:

```markdown
---
name: [skill-name]
description: "[起動条件の説明]"
---

# [Skill Name]

[このスキルが何をするか]

## 手順

1. [ステップ1]
2. [ステップ2]

## Related skills

- [関連スキル]
```

---

## Step 5 — フラグを更新する

**昇格候補があった場合は Step 4 の承認後に、昇格候補ゼロの場合は承認なしでそのまま実行する。昇格作業がゼロでも `.codify-needed` フラグ削除・`codify-log.md` 追記・`tasklist.md` 更新は必ず実行する。**

実行完了後:

```bash
# .codify-needed フラグを削除
rm -f .steering/[task]/.codify-needed

# 実行ログを記録
cat >> .steering/[task]/codify-log.md << 'EOF'

## [YYYYMMDD] — compound 実行

### 昇格したパターン
- [パターン] → [昇格先]

### 変更したファイル
- [ファイルパス]
EOF
```

`tasklist.md` の「福利化」セクションの compound チェックボックスをチェック済みにする（tasklist.md が無ければスキップ）。

---

## Related skills

- `knowledge-capture` — ドキュメント保存（パターン集・決定の記録）が主眼
- `session-retrospective` — このスキルの入力（skill-issues.md）を会話から採掘して供給する原料元
- `rule-audit` — 対をなす剪定スキル（既存ルールの削除・統合・GC）。compound が増やし rule-audit が刈る
- `steering` — compound 完了後はアーカイブへ（steering archive モード）
