---
name: compound
description: "レビューや実装で得た学びをルール・知識・スキルに昇格させる汎用スキル（福利化）。「福利化して」「codify して」「ルール化して」「パターンを抽出して」などのフレーズが対象。セッション開始時に .codify-needed フラグがあれば起動を促す。frontend-code-review 完了後に自動的に提案される。knowledge-capture（ドキュメント保存）とは別物で、こちらは CLAUDE.md ルール・スキル・lint ルールへの昇格が主眼。"
---

# Compound（福利化）

レビュー・実装・テストで発見したパターンを、次のサイクルで自動的に防止できる
**ルール・知識・スキル** に変換する汎用スキル。

「同じ指摘を二度しない」ためのフェーズ。

## When NOT to use

- ドキュメントに保存したい（ADR・パターン集） → `knowledge-capture`
- lint ルールや ast-grep ルールとして固めたい場合は、このスキルがその起点になれる
- 1回限りの事象 → コミットメッセージで十分

---

## Step 1 — 入力を収集する

以下のファイルを読んでパターンを探す（存在するものだけ）:

```bash
# .steering/ のアクティブタスクを確認
find .steering -maxdepth 2 \( -name "review-result.md" -o -name "session-log.md" -o -name "decisions.md" \) ! -path "*/archived/*" 2>/dev/null
```

| ファイル | 読む内容 |
|---|---|
| `.steering/[task]/review-result.md` | レビュー指摘のパターン（繰り返し出現するものを重視） |
| `.steering/[task]/session-log.md` | 実装中の判断・詰まりどころ |
| `.steering/[task]/decisions.md` | 技術的判断とその理由 |
| `docs/knowledge/` | 既存の知識（重複確認のため） |

---

## Step 2 — パターン抽出

以下の観点で「再利用可能な学び」を識別する:

**昇格候補の優先順位:**
1. **繰り返し出現する指摘**（複数ファイルで同じ問題）→ CLAUDE.md ルール or lint ルール
2. **知らなかった仕様・落とし穴**（一度詰まったもの）→ `docs/knowledge/`
3. **技術的判断の理由**（なぜその設計か）→ `docs/decisions/` (ADR)
4. **再利用可能な実装パターン**（汎用的な解法）→ `docs/knowledge/` or 新スキルの骨組み

**昇格しないもの:**
- 1回限りのバグ修正 → コミットメッセージで十分
- プロジェクト固有すぎて横展開できないもの

---

## Step 3 — 昇格先の提案

抽出したパターンを分類してドラフトを提示する:

```
## Compound ドラフト

### [パターン1のラベル]
昇格先: CLAUDE.md ルール
理由: review-result.md に3箇所で同じ指摘
内容:
───
- `<div onClick>` は `<button>` に置き換える
───

### [パターン2のラベル]
昇格先: docs/knowledge/testing-patterns.md への追記
理由: MSW vs vi.mock の使い分けで詰まった
内容:
───
## [サブトピック]
[パターン説明]
───

### [パターン3のラベル]
昇格先: 新スキルの骨組み生成
理由: 毎回同じ手順でセットアップしている
内容: [スキルの骨組み概要]
───

採用するものを番号または名前で教えてください。
```

**承認なしに自動適用しない。**

---

## Step 4 — 実行

ユーザーが承認した項目のみを実行する。

### CLAUDE.md ルール追記

```markdown
## スタック制約（行動ルール）
- [新しい1行ルール]
```

**制約**: CLAUDE.md は ≤200行 厳守。詳細な説明は `docs/knowledge/` に書いて `@参照` にする。

### docs/knowledge/[topic].md への追記

既存ファイルがあれば追記、なければ新規作成。

```markdown
## [サブトピック]

[パターン・アンチパターン・注意点]

```typescript
// ✅ Good
// ❌ Bad
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

`tasklist.md` の Compound チェックボックスをチェック済みにする。

---

## 汎用性について

このスキルはプロジェクト固有の前提を持たない。
異なるプロジェクトで使う場合:
- `.steering/` が存在しなければ `review-result.md` のみを入力として使う
- `docs/knowledge/` が存在しなければ、出力先をユーザーに確認する
- CLAUDE.md が存在しなければ、適切な設定ファイルをユーザーに確認する

---

## Related skills

- `knowledge-capture` — ドキュメント保存（ADR・パターン集・語彙）が主眼
- `frontend-code-review` — このスキルの入力（review-result.md）を生成する
- `steering` — compound 完了後はアーカイブへ（steering archive モード）
