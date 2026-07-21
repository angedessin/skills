---
name: review-security
description: "フロントエンドのセキュリティレビューに使うサブスキル。XSS・型安全・environment/シークレット管理・依存関係の脆弱性を確認する。frontend-code-review オーケストレーターからの並列呼び出しを想定。単独でも使用可。"
compatibility: "Angular / TypeScript（XSS・シークレット・依存関係の観点はフレームワーク中立）"
metadata:
  version: "1.2"
  source-commit: 1dfa5081509eda8173e713c54ff6d390563352cd
---

# Review — Security

フロントエンドのセキュリティ観点からコードを審査する。
`frontend-code-review` のフルモードで並列実行されるサブスキル。

## When NOT to use

- 一般的なロジックバグ・状態遷移の矛盾 → `review-correctness` の担当。ここでは XSS・型安全・シークレット管理・依存脆弱性を見る。
- パフォーマンス（Bundle・変更検知）→ `review-performance` の担当。
- UI・アクセシビリティ → `review-ui` / `review-a11y` の担当。
- テストコード・テストインフラの監査には使わない。

## スコープ

デフォルト: 未コミット + コミット済み（ベースブランチとの分岐点から）を合算した diff の `.ts`・`.html`（テストファイルを除く）。未コミットだけを見ると、タスクごとにコミットする実装フローで対象を取りこぼす。

```bash
BASE=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's|^origin/||'); BASE=${BASE:-main}
{ git diff --name-only "$(git merge-base "$BASE" HEAD)..HEAD" 2>/dev/null; git diff --name-only HEAD; } | sort -u | grep -E '\.(ts|html)$' | grep -v '\.(test|spec)\.'
```

上記の結果が **空の場合**: Axis 1〜3 は「対象ファイルなし」としてスキップし、Axis 4（依存関係 audit）のみ実施する。`package.json` の変更もない場合は「セキュリティレビューの対象ファイルがありません」とユーザーに伝えて終了する。

---

## 4つのチェック軸

### Axis 1 — XSS リスク

```typescript
// Bad: サニタイズを迂回して外部入力を HTML として挿入する
html = this.sanitizer.bypassSecurityTrustHtml(userInput)
// template: <div [innerHTML]="html"></div>

// Good: テキストとして描画する（Angular が自動エスケープする）
// template: <div>{{ userInput }}</div>
```

**チェック項目**:
- `bypassSecurityTrust*`（Html / Url / ResourceUrl 等）に外部入力を渡していないか
- `[innerHTML]` の入力元（既定サニタイズはあるが、信頼できない HTML を流さない）
- `eval()`・`new Function()` の使用
- URL パラメータを直接 DOM に挿入していないか（`ElementRef.nativeElement` の直接操作を含む）

### Axis 2 — 型安全とインジェクションリスク

```typescript
// Bad: any で型を逃げるとランタイムエラーの温床
const params: any = new URLSearchParams(location.search)
fetch(`/api/user?id=${params.id}`) // SQL インジェクション相当

// Good: 型付きで検証してから使用
const id = z.string().uuid().parse(new URLSearchParams(location.search).get('id'))
```

**チェック項目**:
- `as any` / `as unknown` 経由で外部入力が型検証なしに使われていないか
- URL パラメータ・フォーム入力の検証漏れ
- `JSON.parse()` の結果に型アサーションのみで検証がない箇所

### Axis 3 — environment・シークレット管理

```typescript
// Bad: シークレットを environment ファイルに置く（ビルド成果物に埋め込まれ配布される）
export const environment = { apiSecret: 'sk-xxxx' }

// Good: クライアントに置くのは公開してよい値のみ。シークレットはサーバー側に置く
export const environment = { apiUrl: 'https://api.example.com' }
```

**チェック項目**:
- `src/environments/` やクライアントコードにシークレット・トークンが置かれていないか（environment ファイルはビルド成果物に含まれ配布される）
- シークレット・トークンがハードコードされていないか（`Bearer xxx`・API key など）
- サーバー側にのみ置くべき値が API レスポンスやビルド定数経由でクライアントに漏れていないか

### Axis 4 — 依存関係

```bash
# 既知の CVE がある依存関係を確認
pnpm audit --audit-level=high 2>/dev/null || true   # npm プロジェクトでは npm audit
```

**チェック項目**:
- `package.json` の変更に high/critical CVE のある新規依存関係がないか
- `pnpm audit`（npm プロジェクトでは `npm audit`）の high 以上の出力

**Axis 4 判定順**:
1. `package.json` に変更なし → 「（audit 対象変更なし）」と記載してスキップ
2. `package.json` に変更あり → `pnpm audit --audit-level=high` を実行:
   - 実行できた → その結果を記載
   - 実行できない（シミュレーション環境、CI 外など）→ 「audit 実行不可 — 手動での確認を推奨: `pnpm audit --audit-level=high`」と記載

---

## 出力形式

```
## Security Review: [スコープ]

### Axis 1 — XSS
- [comment.component.ts:L42] bypassSecurityTrustHtml に userComment を直接渡している

### Axis 2 — 型安全
（問題なし）

### Axis 3 — environment
- [environments/environment.ts:L8] apiSecret がクライアント配布物に含まれている

### Axis 4 — 依存関係
- （audit 実行不可またはクリーン）

### サマリー
- 確認したファイル: N件
- 重要な問題: X件
```

**提案のみ。自動修正しない。**

---

## Related skills

- `frontend-code-review` — このスキルを並列エージェントとして実行するオーケストレーター
- `impl-review` — 実装品質（設計整合性・TypeScript・Angular パターン）のレビュー
