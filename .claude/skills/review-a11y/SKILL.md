---
name: review-a11y
description: "フロントエンドのアクセシビリティレビューに使うサブスキル。セマンティクス・ARIA・フォーカス管理・キーボード操作の観点で確認する。frontend-code-review オーケストレーターからの並列呼び出しを想定。単独でも使用可。"
compatibility: "React / TypeScript（a11y 観点はフレームワーク中立）"
---

# Review — Accessibility

フロントエンドのアクセシビリティ観点からコードを審査する。
`frontend-code-review` のフルモードで並列実行されるサブスキル。

## スコープ

デフォルト: `git diff --name-only HEAD` の `.tsx`（テストファイルを除く）。

```bash
git diff --name-only HEAD | grep -E '\.tsx$' | grep -v '\.(test|spec)\.'
```

上記の結果が **空の場合**（対象ファイルなし）→ 「アクセシビリティレビューの対象ファイルがありません（.tsx の変更なし）」とユーザーに伝えて終了する。スコープを拡張する場合はユーザーが明示的にファイルパスを指定する。

---

## 4つのチェック軸

### Axis 1 — セマンティクスとインタラクティブ要素

```tsx
// ❌ Bad: クリック可能な div
<div onClick={handleSubmit} className="btn">送信</div>

// ✅ Good: セマンティックな button
<button type="button" onClick={handleSubmit}>送信</button>
```

**チェック項目**:
- `<div onClick>` / `<span onClick>` → `<button>` への置き換え候補
- `<a href="#">` の誤用（ボタン動作には `<button>` を使う）
- フォームの送信ボタンに `type="submit"` があるか

### Axis 2 — ARIA ラベルと説明

```tsx
// ❌ Bad: アイコンのみのボタンに aria-label なし
<button onClick={handleClose}><XIcon /></button>

// ✅ Good
<button onClick={handleClose} aria-label="閉じる"><XIcon /></button>

// ❌ Bad: 画像の alt なし
<img src="/logo.png" />

// ✅ Good
<img src="/logo.png" alt="サービスロゴ" />
// 装飾画像は空文字
<img src="/decoration.png" alt="" />
```

**チェック項目**:
- テキストを持たないインタラクティブ要素に `aria-label` or `aria-labelledby` があるか
- `<img>` に `alt` があるか（装飾画像は `alt=""`）
- フォーム入力に `<label>` or `aria-label` が関連付けられているか
- `aria-expanded`・`aria-selected`・`aria-checked` の状態が正しく反映されているか

### Axis 3 — フォーカス管理

```tsx
// ❌ Bad: モーダルを開いてもフォーカスが移動しない
function Modal({ isOpen }) {
  return isOpen ? <div role="dialog">...</div> : null
}

// ✅ Good: useEffect でフォーカスを移動 + Escape で閉じる
function Modal({ isOpen, onClose }) {
  const firstFocusableRef = useRef<HTMLButtonElement>(null)
  useEffect(() => {
    if (isOpen) firstFocusableRef.current?.focus()
  }, [isOpen])
  // ...
}
```

**チェック項目**:
- モーダル・ドロワー・ポップアップ開閉時にフォーカスが適切に移動するか
- `tabIndex={-1}` を適切に使っているか（フォーカス順序の管理）
- モーダルの Escape キーハンドリングがあるか

### Axis 4 — キーボード操作

```tsx
// ❌ Bad: onMouseEnter / onMouseLeave のみ（キーボード非対応）
<div onMouseEnter={showTooltip} onMouseLeave={hideTooltip}>

// ✅ Good: フォーカスイベントも併用
<div
  onMouseEnter={showTooltip}
  onMouseLeave={hideTooltip}
  onFocus={showTooltip}
  onBlur={hideTooltip}
>
```

**チェック項目**:
- マウスイベントのみの実装でキーボード操作が不可能になっていないか
- カスタムドロップダウン・メニューに矢印キー操作があるか
- `role="button"` を付けた非 button 要素に `onKeyDown` でEnter/Space 処理があるか

---

## 出力形式

```
## Accessibility Review: [スコープ]

### Axis 1 — セマンティクス
- [Button.tsx:L8] `<div onClick={onClick}>` → `<button>` に変更

### Axis 2 — ARIA
- [IconButton.tsx:L3] アイコンのみのボタンに aria-label がない

### Axis 3 — フォーカス管理
（問題なし）

### Axis 4 — キーボード操作
- [Dropdown.tsx:L22] onMouseEnter のみで onFocus がない

### サマリー
- 確認したファイル: N件
- 重要な問題: X件
```

**提案のみ。自動修正しない。**

**複数軸への重複報告**: 同一箇所が複数のチェック軸に該当する場合（例: `<div onClick>` は Axis 1・Axis 4 の両方に該当）は各軸で個別に報告する。

---

## Related skills

- `frontend-code-review` — このスキルを並列エージェントとして実行するオーケストレーター
- `impl-review` — 実装品質（設計整合性・TypeScript・React パターン）のレビュー
