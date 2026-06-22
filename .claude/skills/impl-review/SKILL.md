---
name: impl-review
description: "実装コードの品質レビューに使う — 「実装をレビューして」「コードが設計に合っているか確認して」「TypeScript の問題」「React パターンのレビュー」などのフレーズが対象。確認内容: design.md との整合性・docs/knowledge/ のプロジェクト規約・TypeScript 品質・React パターン・基本アクセシビリティ。単独または frontend-code-review の Step 2 として動作。テストコードのレビュー（test-review を使う）やテストインフラの監査には起動しない。"
compatibility: "React / TypeScript"
---

# Impl Review

実装コードの品質審査。テストコードは対象外（`test-review` が担当）。
`.steering/design.md` との整合性チェックがこのスキル固有の最重要軸。

## When NOT to use

- テストコードのレビュー → `test-review`
- テストインフラ（vitest 設定・カバレッジ設定）の監査 → 本スキルの対象外
- 深いレビューが必要 → `/code-review high` または `/code-review ultra` を追加で使う

---

## スコープの決定

デフォルト: `git diff --name-only HEAD` の `.ts`・`.tsx`（テストファイルを除く）。

```bash
git diff --name-only HEAD | grep -E '\.(ts|tsx)$' | grep -v '\.(test|spec)\.'
```

スコープが空の場合は「レビュー対象の実装ファイルがありません（変更はテストのみまたは非 TS ファイルです）」と出力して終了する。

---

## 5つのレビュー軸

### Axis 1 — 設計整合性（最重要・このスキル固有）

`.steering/[task]/design.md` が存在する場合、実装との整合性を確認する。複数のアクティブタスクがある場合は変更ファイルのパスと最も関連するタスクを選択する（判断できない場合はユーザーに確認する）。

**確認項目**:

1. **Key components テーブルと実際のファイル構成**
   - テーブルに記載されたコンポーネントが実際に作成されているか
   - 責務が分割されているか

2. **Approach セクションの実装方針**
   - 設計で決めたアプローチが守られているか
   - 勝手に設計変更されていないか

3. **Open questions の解決状況**
   - レビュー待ちの質問が未解決のまま実装が進んでいないか

**設計がない場合**: このチェックをスキップして次の軸へ。

---

### Axis 2 — プロジェクト規約

`docs/knowledge/` の antipatterns.md が存在すれば読んで照合する。
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

**Server / Client Component の境界**:

```typescript
// Bad: Server Component で useEffect を使用
// app/users/page.tsx
'use server' // または宣言なし
export default function Page() {
  const [data, setData] = useState([]) // エラー: Server Component で state 不可
}

// Good: Client Component に分離
'use client'
export function UserList({ users }: { users: User[] }) {
  const [selected, setSelected] = useState<string | null>(null)
}
```

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

### Axis 5 — アクセシビリティ（基本）

```tsx
// Bad: インタラクティブな div
<div onClick={handleSubmit} className="btn">送信</div>

// Good: セマンティックな要素
<button type="button" onClick={handleSubmit}>送信</button>

// Bad: aria-label なしのアイコンボタン
<button onClick={handleClose}><XIcon /></button>

// Good
<button onClick={handleClose} aria-label="閉じる"><XIcon /></button>
```

**チェック項目**:
- `<div onClick>` → `<button>` への置き換え候補
- インタラクティブ要素に `aria-label` or `aria-labelledby` があるか
- `<img>` に `alt` があるか

---

## 出力形式

```
## Implementation Review: [スコープ]

### Axis 1 — 設計整合性
- [file.ts] design.md の Key components に `AuthService` があるが `src/services/auth.ts` が存在しない
- Open question "リフレッシュトークンの保存場所" が未解決のまま実装が進んでいる

### Axis 2 — プロジェクト規約
（問題なし）

### Axis 3 — TypeScript
- [api/user.ts:L12] `as any` → 型を定義して明示 (`UserResponse`)

### Axis 4 — React
- [components/Form.tsx:L34] useEffect の deps に `userId` が抜けている

### Axis 5 — アクセシビリティ
- [components/Modal.tsx:L8] `<div onClick={close}>` → `<button>` に変更

### サマリー
- 確認したファイル: N件
- 重要な問題: X件
- 設計整合性: OK / 要確認
```

**提案のみ。自動修正しない。** 承認後に修正を実施する。

深いレビューが必要な場合: `/code-review high` または `/code-review ultra` を追加で使うことを提案する。

---

## Related skills

- `test-review` — テストコードのレビュー（こちらは実装コードのみ）
- `frontend-code-review` — test-review + impl-review を順番に実行するオーケストレーター
- `knowledge-capture` — レビューで発見したパターンを `docs/knowledge/` に保存
