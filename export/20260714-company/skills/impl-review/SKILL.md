---
name: impl-review
description: "実装コードの品質レビューに使う — 「実装をレビューして」「コードが設計に合っているか確認して」「TypeScript の問題」「Angular パターンのレビュー」などのフレーズが対象。確認内容: design.md との整合性・docs/knowledge/ のプロジェクト規約・TypeScript 品質・Angular パターン。アクセシビリティは対象外（review-a11y の担当）。単独または frontend-code-review の Step 2 として動作。テストコードのレビュー（test-review を使う）やテストインフラの監査には起動しない。"
compatibility: "Angular / TypeScript"
metadata:
  version: "1.2"
  source-commit: 496a050cfde484237439c1899294042fecc06732
---

# Impl Review

実装コードの品質審査。テストコードは対象外（`test-review` が担当）。
`.steering/design.md` との整合性チェックがこのスキル固有の最重要軸。

## When NOT to use

- テストコードのレビュー → `test-review`
- アクセシビリティのレビュー → `review-a11y`（基本セマンティクス・aria-label 等を含む。単独利用時もこのスキルでは見ない）
- テストインフラ（Karma / Jasmine 設定・カバレッジ設定）の監査 → 本スキルの対象外
- 深いレビューが必要 → `/code-review high` または `/code-review ultra` を追加で使う

---

## スコープの決定

デフォルト: 未コミット + コミット済み（ベースブランチとの分岐点から）を合算した diff の `.ts`・`.html`（テストファイルを除く）。未コミットだけを見ると、タスクごとにコミットする実装フローで対象を取りこぼす。

```bash
BASE=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's|^origin/||'); BASE=${BASE:-main}
{ git diff --name-only "$(git merge-base "$BASE" HEAD)..HEAD" 2>/dev/null; git diff --name-only HEAD; } | sort -u | grep -E '\.(ts|html)$' | grep -v '\.(test|spec)\.'
```

スコープが空の場合は「レビュー対象の実装ファイルがありません（変更はテストのみまたは非 TS ファイルです）」と出力して終了する。

---

## 4つのレビュー軸

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
- コンポーネントが `HttpClient` を直接 subscribe してデータアクセスしていないか（サービスに分離する）
- テストが実時間待ち（`setTimeout`・`done` とタイマーの組み合わせ）でタイミングを合わせていないか（`fakeAsync` + `tick` を使う）
- `<div (click)>` になっていないか

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

### Axis 4 — Angular パターン

**Observable の subscribe 管理**:

```typescript
// Bad: subscribe の破棄漏れ（コンポーネント破棄後も購読が生き続ける）
ngOnInit() {
  this.userService.getUser(this.userId).subscribe(u => this.user = u)
}

// Good: async pipe に寄せる（テンプレート側で購読・自動破棄）
user$ = this.userService.getUser(this.userId)
// subscribe が必要な場合は破棄を紐付ける
this.userService.getUser(this.userId)
  .pipe(takeUntilDestroyed(this.destroyRef))
  .subscribe(u => this.user = u)
```

**SSR 境界（プロジェクトが SSR / hydration を使う場合のみ）**:
サーバーでも実行されるコードで `window`・`document` などのブラウザ API を直接参照していないか、参照する場合は `isPlatformBrowser` 等でガードされているかを確認する。SSR を使わないプロジェクトではこの観点をスキップする。

**@Input のローカルコピー**:

```typescript
// Bad: @Input を内部プロパティへコピーする（Input が変わっても追従しない）
@Input() title = ''
localTitle = ''
ngOnInit() { this.localTitle = this.title }

// Good: @Input を直接使う（派生値が必要なら getter / computed にする）
@Input() title = ''
```

---

### 担当外 — アクセシビリティ

アクセシビリティ（`<div (click)>` のセマンティクス・aria-label・alt などの基本項目を含む）は
**review-a11y の単独担当**。このスキルでは指摘しない — 並列実行時に同一指摘が重複し、
統合コストと越境の温床になるため（20260705 に境界を修正。実測で本スキルの a11y 指摘は
全件 review-a11y と重複していた）。単独利用でアクセシビリティも見たい場合は
review-a11y をあわせて実行する。

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

### Axis 4 — Angular
- [components/form.component.ts:L34] `ngOnInit` の subscribe が破棄されていない（async pipe か takeUntilDestroyed に変更）

### サマリー
- 確認したファイル: N件
- 重要な問題: X件
- 設計整合性: OK / 要確認
```

**提案のみ。自動修正しない。** 承認後に修正を実施する。
<!-- validator: no-stop-needed — このスキルはレビュー結果を報告して終わる。修正の適用と承認は呼び出し元（frontend-code-review / ユーザー）の担当で、このスキル自身は停止点を持たない。 -->

深いレビューが必要な場合: `/code-review high` または `/code-review ultra` を追加で使うことを提案する。

---

## Related skills

- `test-review` — テストコードのレビュー（こちらは実装コードのみ）
- `frontend-code-review` — test-review + impl-review を順番に実行するオーケストレーター
- `knowledge-capture` — レビューで発見したパターンを `docs/knowledge/` に保存
