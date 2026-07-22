# Frontend A11y Patterns — フロントエンド実装のアクセシビリティ実践知識

配置先プロジェクトでの実装レビュー（`review-a11y`）で繰り返し検出される、
React コンポーネント実装時のアクセシビリティの基本パターン集。
消費者は review-a11y のみ（impl-review はアクセシビリティを見ない — 20260705 に境界を修正済み）。

---

## テキスト入力には可視ラベルか aria-label を必ず付ける

`placeholder` は代替にならない（フォーカス時・入力後に消える、スクリーンリーダーでの扱いが不安定）。
可視の `<label>` が UI 上不要な場合は `aria-label` で用途を明示する。

```tsx
// Bad — 用途がスクリーンリーダーで読み上げられない
<input type="text" value={text} onChange={...} />

// Good
<input type="text" aria-label="新しいTODOを入力" value={text} onChange={...} />
```

検出元: 20260703 todolist タスクの review-a11y / impl-review（重複統合済み）。

---

## checkbox とラベルテキストが隣接しているだけでは関連付けにならない

`<span>` 等でテキストを隣に置いても、視覚的な近接とプログラム的な関連付け（アクセシブルネーム）は別物。
`<label>` で両方を囲むか、`htmlFor`/`id` で明示的に紐付ける。

```tsx
// Bad — 見た目は隣接しているが checkbox のアクセシブルネームは空
<input type="checkbox" checked={done} onChange={...} />
<span>{text}</span>

// Good — <label> でラップして暗黙の関連付けを作る
<label>
  <input type="checkbox" checked={done} onChange={...} />
  <span>{text}</span>
</label>
```

検出元: 20260703 todolist タスクの review-a11y / impl-review（重複統合済み）。

---

## リスト項目を丸ごと削除する操作は、削除後のフォーカス行き先を明示する

削除された要素にフォーカスがあった場合、何も指定しないとフォーカスが `<body>` に落ち、
キーボード・スクリーンリーダー利用者が現在地を見失う。削除操作の起点（入力欄・リストコンテナ等）に
`ref` で明示的にフォーカスを戻す。

```tsx
const inputRef = useRef<HTMLInputElement>(null);

const deleteTodo = (id: string) => {
  setTodos((prev) => prev.filter((todo) => todo.id !== id));
  inputRef.current?.focus();
};
```

検出元: 20260703 todolist タスクの review-a11y（フォーカス管理軸、Low）。

---

## 長さ無制限のユーザー入力を表示するテキスト要素には折り返し指定を

URL の貼り付けなど空白のない長い文字列は、`overflow-wrap`/`word-break` の指定がないと
狭い画面幅で横スクロールを引き起こす。ユーザー入力をそのまま表示する要素には
`overflow-wrap: anywhere` 等を基本セットにする。

```tsx
<span style={{ overflowWrap: "anywhere" }}>{userInput}</span>
```

検出元: 20260703 todolist タスクの review-ui（レイアウト・レスポンシブ軸、Medium）。

---

※ このファイルは knowledge-capture / compound スキルによって継続的に更新される。
