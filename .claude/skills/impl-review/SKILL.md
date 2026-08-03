---
name: impl-review
description: "実装コードの品質レビューに使う — 「実装をレビューして」「コードが設計に合っているか確認して」「TypeScript の問題」「React パターンのレビュー」などのフレーズが対象。確認内容: design.md との整合性・docs/knowledge/ のプロジェクト規約・TypeScript 品質・React パターン。アクセシビリティは対象外（review-a11y の担当）。単独または frontend-code-review のサブスキルとして動作。テストコードのレビュー（test-review を使う）やテストインフラの監査には起動しない。"
compatibility: "React / TypeScript"
metadata:
  version: "1.5"
---

# Impl Review

実装コードの品質審査。テストコードは対象外（`test-review` が担当）。
`.steering/design.md` との整合性チェックがこのスキル固有の最重要軸。

## When NOT to use

- テストコードのレビュー → `test-review`
- アクセシビリティのレビュー → `review-a11y`（基本セマンティクス・aria-label 等を含む。単独利用時もこのスキルでは見ない）
- テストインフラ（vitest 設定・カバレッジ設定）の監査 → 本スキルの対象外
- 深いレビューが必要 → `/code-review high` または `/code-review ultra` を追加で使う

---

## スコープの決定

デフォルト: 未コミット + コミット済み（ベースブランチとの分岐点から）を合算した diff の `.ts`・`.tsx`（テストファイルを除く）。未コミットだけを見ると、タスクごとにコミットする実装フローで対象を取りこぼす。

```bash
BASE=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's|^origin/||'); BASE=${BASE:-main}
DIFF_FILES=$({ git diff --name-only "$(git merge-base "$BASE" HEAD)..HEAD" 2>/dev/null; git diff --name-only HEAD; } | sort -u)
echo "$DIFF_FILES" | grep -E '\.(ts|tsx)$' | grep -v '\.(test|spec)\.'
```

**契約成果物の Axis 1 例外（空 TS でも終了しない）**: アクティブな `.steering/*/design.md` があり、かつ diff に `.claude/skills/**/SKILL.md`（または呼び出し元が明示した契約成果物パス）を含む場合は、`.ts`/`.tsx` が空でも **Axis 1 を実行する**。対象パスにそれらの `SKILL.md`（必要なら関連する `scripts/*.py` 等）を含める。Axis 3（TypeScript）・Axis 4（React）は対象が無ければ「対象なし」と書いてスキップしてよい。Axis 2 は設計・規約に関わる範囲で実施する。

**早期終了してよい場合**: 上記例外に当たらず、かつ `.ts`/`.tsx` スコープも空のときだけ「レビュー対象の実装ファイルがありません（変更はテストのみまたは非 TS ファイルです）」と出力して終了する。

---

## 4つのレビュー軸

### Axis 1 — 設計整合性（最重要・このスキル固有）

`.steering/[task]/design.md` が存在する場合、実装との整合性を確認する。複数のアクティブタスクがある場合は変更ファイルのパスと最も関連するタスクを選択する（判断できない場合はユーザーに確認する）。
**読み契約**: 設計整合は**契約コア全見出し**（境界マーカーより前。目的・スコープ・制約・完了条件・アプローチ・主要コンポーネント・未解決の論点）で足りる。部分集合を別定義しない。マーカーが無い旧ファイルは全文。

**Status ガード**:
- `Status` が **APPROVED** のときのみ、契約コア不一致をゲート級 **High** とする（重要度尺度の「設計契約コア不一致」）
- `DRAFT` / `SPIKE` のときは Info とするか、この軸をスキップする（未承認設計とのノイズ防止）
- design.md が無い場合: このチェックをスキップして次の軸へ

**確認項目**（APPROVED 時）:

1. **「主要コンポーネント」テーブルと実際のファイル構成**
2. **「アプローチ」「スコープ」「制約」「完了条件」** と実装方針の一致
3. **「目的」** からの逸脱がないか
4. **「未解決の論点」** が未解決のまま実装で先走りしていないか

不一致は **High**（設計契約コア不一致）。勝手に設計を直さない — 報告し、呼び出し元またはユーザーに `design-doc` 方針転換 / APPROVED 追認を案内する。

---

### Axis 2 — プロジェクト規約

`docs/knowledge/` が存在すれば**ディレクトリを走査し、実装規約に関わるファイル**（アンチパターン集・パターン集・レビュー観点など）を読んで照合する。ファイル名を決め打ちしない（プロジェクトごとに名前が違い、決め打ちすると蓄積した知識が一度も読まれない）。ディレクトリが無ければこのチェックを飛ばす。
CLAUDE.md が存在すればスタック制約も確認する。

**デフォルトチェック**（docs/knowledge/・CLAUDE.md がないプロジェクトでも実施）:
- `vi.mock` でネットワーク系をモックしていないか（MSW を使うべき）
- `waitForTimeout` が使われていないか
- `<div onClick>` になっていないか

---

### Axis 3 — TypeScript 品質

```typescript
// Bad: any の使用
const data: any = await fetch('/api/user').then(r => r.json())
function process(input: any) { ... }

// Good: 型を明示
const data: User = await fetch('/api/user').then(r => r.json())
function process(input: ProcessInput) { ... }
```

**チェック項目**:
- `any` の不用意な使用（型注釈 `: any` · キャスト `as any` · `as unknown` を問わず）
- `Record<string, any>` → 型引数の明示化
- 非 null アサーション（`!`）の過剰使用
- `@ts-ignore` の使用（理由がコメントにあるか）

---

### Axis 4 — React パターン

**useEffect の依存配列**:

```typescript
// Bad: deps が不完全
useEffect(() => {
  fetchUser(userId)
}, []) // userId が抜けている

// Good
useEffect(() => {
  fetchUser(userId)
}, [userId])
```

**Server/Client 境界（プロジェクトが RSC / SSR を使う場合のみ）**:
サーバー側で実行されるコンポーネントに state・ブラウザ API・イベントハンドラが混入していないか、境界の宣言はプロジェクトのフレームワーク規約に従っているかを確認する。RSC を使わないプロジェクトではこの観点をスキップする。

**過剰な state**:

```typescript
// Bad: props で十分なのに state を使う
const [title, setTitle] = useState(props.title) // props が変わっても追従しない

// Good: props を直接使う
function Card({ title }: { title: string }) {
  return <h2>{title}</h2>
}
```

---

### 担当外 — アクセシビリティ

アクセシビリティ（`<div onClick>` のセマンティクス・aria-label・alt などの基本項目を含む）は
**review-a11y の単独担当**。このスキルでは指摘しない — 並列実行時に同一指摘が重複し、
統合コストと越境の温床になるため（以前は「基本 a11y」の指摘が review-a11y と
全件重複していたため境界を整理した）。単独利用でアクセシビリティも見たい場合は
review-a11y をあわせて実行する。

---

## 出力形式

```
## 実装レビュー: [スコープ]

### Axis 1 — 設計整合性
- [file.ts] design.md の「主要コンポーネント」に `AuthService` があるが `src/services/auth.ts` が存在しない
- 「リフレッシュトークンの保存場所」が未解決の論点のまま実装が進んでいる

### Axis 2 — プロジェクト規約
（問題なし）

### Axis 3 — TypeScript
- [api/user.ts:L12] `as any` → 型を定義して明示 (`UserResponse`)

### Axis 4 — React
- [components/Form.tsx:L34] useEffect の deps に `userId` が抜けている

### サマリー
- 確認したファイル: N件
- 重要な問題: X件
- 設計整合性: OK / High（設計契約コア不一致） / スキップ（design 無し or DRAFT/SPIKE）

### 次のステップ（設計整合が High のとき）
- design 同期が先（OPEN のままマージ前提にしない）
- 契約コア変更なら `design-doc` 方針転換（DRAFT 戻し）。APPROVED 追認なら decisions 1 行
```

**提案のみ。自動修正しない。** 承認後に修正を実施する。
<!-- validator: no-stop-needed — このスキルはレビュー結果を報告して終わる。修正の適用と承認は呼び出し元（frontend-code-review / ユーザー）の担当で、このスキル自身は停止点を持たない。 -->

深いレビューが必要な場合: `/code-review high` または `/code-review ultra` を追加で使うことを提案する。

---

## Related skills

- `test-review` — テストコードのレビュー（こちらは実装コードのみ）
- `frontend-code-review` — レビューのオーケストレーター（フルモード: 7 エージェントを並列実行 / 軽量モード: test-review・impl-review・review-ui を直列実行）
- `knowledge-capture` — レビューで発見したパターンを `docs/knowledge/` に保存
