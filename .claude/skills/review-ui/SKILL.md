---
name: review-ui
description: "フロントエンドの UI レビューに使うサブスキル。レイアウト・レスポンシブの破綻、デザイン整合（トークン遵守・一貫性）、UX 状態網羅（loading・error・empty・disabled）を確認する。frontend-code-review オーケストレーターからの並列呼び出しを想定。単独でも使用可。"
compatibility: "React / TypeScript / CSS（レスポンシブ・UX 状態の観点はフレームワーク中立。デザイントークンの実体は references/tokens.md を配置先プロジェクトで再生成する）"
metadata:
  version: "1.0"
---

# Review — UI

静的コードから検知できる UI 品質を審査する。
`frontend-code-review` のフルモードで並列実行されるサブスキル。

**対象外**: 実レンダリング・スクリーンショットによる視覚検証（ビルトイン `verify` / Playwright の領域）。本スキルはコードとスタイル定義から読み取れる範囲のみを見る。

## スコープ

デフォルト: `git diff --name-only HEAD` の `.tsx`・`.css`・`.scss`（テストファイルを除く）。

```bash
git diff --name-only HEAD | grep -E '\.(tsx|css|scss)$' | grep -v '\.(test|spec)\.'
```

上記の結果が **空の場合** → 「UI レビューの対象ファイルがありません（.tsx/.css/.scss の変更なし）」とユーザーに伝えて終了する。スコープを拡張する場合はユーザーが明示的にファイルパスを指定する。

---

## 3つのチェック軸

### Axis 1 — レイアウト・レスポンシブ

```css
/* Bad: 固定幅でコンテンツ可変・狭幅ビューポートに追従しない */
.card { width: 480px; }

/* Good: 上限のみ固定し可変にする */
.card { max-width: 480px; width: 100%; }
```

**チェック項目**:
- 固定 px 幅・高さがコンテンツの増減や狭幅ビューポートで破綻しないか（`max-width`/`min-width`・flex・grid への置き換え候補）
- 長いテキスト（ユーザー入力・翻訳で伸びる文字列）の折り返し/省略（`overflow-wrap`・`text-overflow`）が考慮されているか
- 変更した UI にモバイル幅の考慮があるか（メディアクエリ・コンテナクエリ・可変レイアウト）
- `z-index` の場当たり的な大きい値の積み増し（既存の重なり順の規約と矛盾しないか）

### Axis 2 — デザイン整合

`references/tokens.md`（このプロジェクトのデザイントークン定義）を読み、変更コードが定義済みトークンを使っているか確認する。

**tokens.md が存在しない場合は縮退動作**: トークン遵守チェックはスキップし、変更ファイル内および隣接コンポーネントとの**一般的一貫性**（spacing・色・タイポグラフィの値が周辺コードと揃っているか）のみを確認する。縮退したことをサマリーに明記する。

```tsx
// Bad: トークン定義があるのに生値をハードコード
<div style={{ padding: '13px', color: '#3b82f6' }}>

// Good: 定義済みトークン・スケール値を使う（具体名は references/tokens.md）
<div className="p-4 text-primary">
```

**チェック項目**:
- ハードコードされた色・spacing・フォントサイズに対応するトークンが既に定義されていないか
- spacing / タイポグラフィのスケールから外れた中途半端な値（13px 等）が導入されていないか
- テーマ（ダークモード等）を持つプロジェクトで片方のテーマのみ対応していないか

### Axis 3 — UX 状態網羅

データ取得・送信を行う UI で、ユーザーに見える状態が揃っているかを確認する。

```tsx
// Bad: 成功パスしか描画がない
function UserList() {
  const { data } = useUsers()
  return <ul>{data?.map(u => <li key={u.id}>{u.name}</li>)}</ul>
}

// Good: loading / error / empty を描画で区別する
function UserList() {
  const { data, isLoading, error } = useUsers()
  if (isLoading) return <Spinner />
  if (error) return <ErrorMessage error={error} />
  if (data.length === 0) return <EmptyState />
  return <ul>{data.map(u => <li key={u.id}>{u.name}</li>)}</ul>
}
```

**チェック項目**:
- loading 状態の表示があるか（スピナー・スケルトン等）
- error 状態の**ユーザー向け表示**があるか（エラーがコードで握りつぶされる問題は review-correctness の担当。ここでは表示の有無を見る）
- empty 状態（0 件）の表示があるか（空の `<ul>` だけが残っていないか）
- 送信中の disabled・進行表示があるか（多重送信の防止は review-correctness、視覚フィードバックはこちら）
- 想定される失敗ツリーにエラーバウンダリまたは同等のフォールバックがあるか

---

## 出力形式

```
## UI Review: [スコープ]

### Axis 1 — レイアウト・レスポンシブ
- [Card.module.css:L4] width: 480px 固定 — max-width への変更候補

### Axis 2 — デザイン整合
- [Button.tsx:L12] color: '#3b82f6' ハードコード — トークン定義に primary が存在
（tokens.md 不在の場合: 「トークン定義なし — 一般的一貫性のみ確認（縮退動作）」と明記）

### Axis 3 — UX 状態網羅
- [UserList.tsx] error 状態と empty 状態の描画がない

### サマリー
- 確認したファイル: N件
- 重要な問題: X件
- トークン照合: 実施 / 縮退（tokens.md なし）
```

**提案のみ。自動修正しない。**

---

## Related skills

- `frontend-code-review` — このスキルを並列エージェントとして実行するオーケストレーター
- `review-a11y` — 同じ .tsx を対象とするが観点が異なる（セマンティクス・ARIA・フォーカス・キーボード）
- `review-correctness` — エラー握りつぶし・状態遷移矛盾のレビュー（本スキルは「表示」を見る）
