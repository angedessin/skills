---
name: review-security
description: "Next.js/TypeScript フロントエンドのセキュリティレビューに使うサブスキル。XSS・型安全・env var 管理・依存関係の脆弱性を確認する。frontend-code-review オーケストレーターからの並列呼び出しを想定。単独でも使用可。"
---

# Review — Security

フロントエンドのセキュリティ観点からコードを審査する。
`frontend-code-review` のフルモードで並列実行されるサブスキル。

## スコープ

デフォルト: `git diff --name-only HEAD` の `.ts`・`.tsx`（テストファイルを除く）。

```bash
git diff --name-only HEAD | grep -E '\.(ts|tsx)$' | grep -v '\.(test|spec)\.'
```

---

## 4つのチェック軸

### Axis 1 — XSS リスク

```typescript
// ❌ Bad: dangerouslySetInnerHTML に外部入力を直接渡す
<div dangerouslySetInnerHTML={{ __html: userInput }} />

// ✅ Good: サニタイズ済みか、テキストノードとして渡す
<div>{userInput}</div>
```

**チェック項目**:
- `dangerouslySetInnerHTML` の使用箇所と入力元
- `eval()`・`new Function()` の使用
- URL パラメータを直接 DOM に挿入していないか

### Axis 2 — 型安全とインジェクションリスク

```typescript
// ❌ Bad: any で型を逃げるとランタイムエラーの温床
const params: any = new URLSearchParams(location.search)
fetch(`/api/user?id=${params.id}`) // SQL インジェクション相当

// ✅ Good: 型付きで検証してから使用
const id = z.string().uuid().parse(new URLSearchParams(location.search).get('id'))
```

**チェック項目**:
- `as any` / `as unknown` 経由で外部入力が型検証なしに使われていないか
- URL パラメータ・フォーム入力の検証漏れ
- `JSON.parse()` の結果に型アサーションのみで検証がない箇所

### Axis 3 — env var・シークレット管理

```typescript
// ❌ Bad: NEXT_PUBLIC_ なしのシークレットをクライアントで参照
const secret = process.env.API_SECRET // クライアントバンドルに含まれる

// ✅ Good: クライアントには NEXT_PUBLIC_ のみ公開
const apiUrl = process.env.NEXT_PUBLIC_API_URL
```

**チェック項目**:
- `NEXT_PUBLIC_` プレフィックスなしの env var がクライアントコードで使われていないか
- シークレット・トークンがハードコードされていないか（`Bearer xxx`・API key など）
- `.env.local` に入るべき値がソースに直書きされていないか

### Axis 4 — 依存関係

```bash
# 既知の CVE がある依存関係を確認
npm audit --audit-level=high 2>/dev/null || true
```

**チェック項目**:
- `package.json` の変更に high/critical CVE のある新規依存関係がないか
- `npm audit` の high 以上の出力

---

## 出力形式

```
## Security Review: [スコープ]

### Axis 1 — XSS
- [file.tsx:L42] dangerouslySetInnerHTML に userComment を直接渡している

### Axis 2 — 型安全
（問題なし）

### Axis 3 — env var
- [config.ts:L8] API_SECRET をクライアントコードで参照している

### Axis 4 — 依存関係
- （npm audit 実行不可またはクリーン）

### サマリー
- 確認したファイル: N件
- 重要な問題: X件
```

**提案のみ。自動修正しない。**

---

## Related skills

- `frontend-code-review` — このスキルを並列エージェントとして実行するオーケストレーター
- `impl-review` — 実装品質（設計整合性・TypeScript・React パターン）のレビュー
