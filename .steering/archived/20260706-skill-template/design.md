# Design: skill-template

Created: 20260706
Status: **DRAFT — awaiting review**

## Goal

新規スキル作成時に契約準拠（validate_skills.py の機械契約 + skill-design-patterns.md の設計契約）を最初から構造として渡すための `templates/SKILL.template.md` を作成する。「後から契約準拠に改修するのは高くつく（tdd 206→117行）、最初から準拠で書けばコストほぼゼロ」という既存の学びを、作成時点の成果物として実装する。

## Scope

### In scope

- `templates/SKILL.template.md` — SKILL.md の雛形（構造 + プレースホルダのみの最小構成）
  - frontmatter 骨格: `name`（ディレクトリ名一致の注記付き）・`description`（引用符付き1行・発動条件/非発動条件を書く旨のガイド）・`metadata.version`
  - 本文セクション骨格: When NOT to use / 手順 Step（フォールバック「無い場合の代替動作」プレースホルダ付き）/ ハードストップが必要な地点の書き方例（「ここで止まる」+ 何を待つか）/ Related skills
  - 並列サブスキル用の境界相互明記プレースホルダ（該当する場合のみ使う旨のコメント付き）
  - ルール本文は複製せず `docs/knowledge/skill-design-patterns.md` へのポインタで済ませる（3箇所目の複製を作らない）
- `templates/README.md` — テンプレートの使い方（コピー → 埋める → `validate_skills.py --skill` で検証）を数行で記載
- CLAUDE.md「スキル管理ルール」に1行追加: 新規スキルは `templates/SKILL.template.md` から始める
- `docs/knowledge/skill-design-patterns.md` の「新規スキルは最初から契約準拠で書き」節にテンプレートへのポインタを1行追記（同じ情報を持つ箇所の相互リンク）

### Out of scope

- agents（`.claude/agents/*.md`）のテンプレート — このリポジトリではまだ agents を使っていない（YAGNI）
- rules（CLAUDE.md 行動ルール）のテンプレート — 書式規約1〜3行で足りる。必要になったら compound スキル改訂として別タスクで扱う
- `.steering/` 成果物のテンプレート — `design-doc/references/templates.md` に既存
- 既存スキルのテンプレート準拠への改修 — テンプレは新規作成専用
- テンプレートの他プロジェクトへの配布 — マスター専用ツール（validate_skills.py と同じ扱い）

## Constraints

- Stack: Markdown のみ（コード変更なし）。検証は `python3 scripts/validate_skills.py`
- アストラル面文字（絵文字含む）をテンプレートに含めない
- テンプレは validate_skills.py・skill-design-patterns.md と同じ情報の3箇所目になるため、最小構成（構造とプレースホルダだけ）を厳守し、ルールの説明文は書かない
- CLAUDE.md・docs/ への書き込みは承認制 — この design.md の承認をもって当該2ファイルへの追記の承認とする

## Acceptance criteria

- [ ] `templates/SKILL.template.md` が存在し、構造 + プレースホルダ + ポインタのみで構成されている（ルール本文の複製がない）
- [ ] プレースホルダを埋めたインスタンスが `validate_skills.py --skill` で PASS する（検証手順を templates/README.md に記載）
- [ ] テンプレート・README にアストラル面文字がない
- [ ] CLAUDE.md と skill-design-patterns.md の該当箇所に相互ポインタが入っている（片側修正の禁止に従い同一コミット）
- [ ] ハードストップ・前提チェックの雛形が「手順のステップ」形式になっている（説明文形式でない）

## Approach

テンプレートは「何を書くか」の骨格だけを持ち、「なぜそう書くか」は skill-design-patterns.md へのポインタに委ねる。これによりルール変更時の修正箇所を knowledge doc 1箇所に保てる。テンプレ自体は `name:` がディレクトリ名と一致しないため validator を直接は通せない — 検証はコピー先（実スキルのディレクトリ）で行う前提とし、その手順を templates/README.md に明記する。

## Key components

| Component | Location | Responsibility |
|-----------|----------|----------------|
| SKILL テンプレート | `templates/SKILL.template.md` | 新規スキルの骨格（frontmatter・セクション・ハードストップ雛形） |
| 使い方 | `templates/README.md` | コピー → 埋め → 検証の手順（3〜10行） |
| ルール追記 | `CLAUDE.md` スキル管理ルール節 | 「新規スキルはテンプレから始める」1行 |
| ポインタ追記 | `docs/knowledge/skill-design-patterns.md` | 契約準拠パターン節からテンプレへのリンク1行 |

## Data flow

```
新規スキル作成:
templates/SKILL.template.md
  → .claude/skills/[new-skill]/SKILL.md にコピー
  → プレースホルダを埋める（ルールの詳細は skill-design-patterns.md を参照）
  → python3 scripts/validate_skills.py --skill .claude/skills/[new-skill]
  → PASS で完成

契約変更時:
validate_skills.py or skill-design-patterns.md を更新
  → 相互ポインタをたどって templates/SKILL.template.md も同一コミットで更新
```

## Test strategy

- Unit: なし（コードなし）
- 検証: テンプレのプレースホルダを仮の値で埋めたインスタンスを scratchpad 上のスキルディレクトリに置き、`validate_skills.py --skill` が PASS することを実装セッションで確認する
- 回帰: 既存の `pnpm` scripts（あれば validate 系）が引き続き PASS すること

## Open questions

- [ ] テンプレートのドリフト検出を自動化するか？（案: validate_skills.py にテンプレ専用チェックを足す / しない — 相互ポインタ + 「片側修正の禁止」の運用で足りるか）。推奨: まず運用で足りるかを見る（自動化しない）
- [ ] compound スキルは学びをスキルに昇格させる際に新規スキルを作ることがある。compound の本文にもテンプレ参照を1行入れるか？（入れる場合、スキルは自己完結の原則より「テンプレが無いプロジェクトでは従来どおり」のフォールバック文が必要）。推奨: 入れる（フォールバック付き1行）
- [ ] テンプレの言語は既存スキルに合わせて日本語で良いか？推奨: 日本語

## Alternatives considered

| Alternative | Why rejected |
|-------------|--------------|
| skill-creator プラグインをそのまま使う | 汎用テンプレのため、このリポジトリ固有の契約（metadata.version・ハードストップ手順化・境界相互明記・日本語）を毎回上書きする必要がある |
| ルール本文もテンプレに複製して自己完結させる | 同じ情報の3箇所目になり「片側修正の禁止」の学びに反する。テンプレはマスター専用で配布されないため自己完結の要件が無い |
| `.claude/skills/_template/` に置く | スキルディレクトリに見え、validator の走査対象・スキル一覧の誤認の恐れ。マスター専用ツールは `scripts/` と同様にトップレベルが自然 |
| agents / rules テンプレも同時に作る | agents は未使用（YAGNI）、rules は書式規約1〜3行で足りる |
