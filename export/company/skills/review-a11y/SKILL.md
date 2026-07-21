---
name: review-a11y
description: "フロントエンドのアクセシビリティレビューに使うサブスキル。セマンティクス・ARIA・フォーカス管理・キーボード操作の観点で確認する。frontend-code-review オーケストレーターからの並列呼び出しを想定。単独でも使用可。"
compatibility: "Angular / TypeScript（a11y 観点はフレームワーク中立）"
metadata:
  version: "1.2"
  source-commit: e90165507d319933f2c07f9538b0a0040e67842e
---

# Review — Accessibility

フロントエンドのアクセシビリティ観点からコードを審査する。
`frontend-code-review` のフルモードで並列実行されるサブスキル。

アクセシビリティは**このスキルの単独担当**（`<div (click)>` のセマンティクス・aria-label・alt などの基本項目を含む）。impl-review はアクセシビリティを見ない（20260705 に境界を修正 — 以前は「基本 a11y」が重複していた）。逆に、TypeScript 品質・Angular パターン・設計整合性は impl-review の担当で、このスキルでは見ない。

## When NOT to use

- 見た目の崩れ・レスポンシブ・デザイン整合 → `review-ui` の担当。ここではセマンティクス・ARIA・フォーカス・キーボード操作を見る。
- ロジック正当性・状態遷移 → `review-correctness` の担当。
- パフォーマンス → `review-performance` の担当。
- テストコードのレビューには使わない（`test-review`）。

## スコープ

デフォルト: 未コミット + コミット済み（ベースブランチとの分岐点から）を合算した diff の `.html`・`.ts`（テストファイルを除く）。未コミットだけを見ると、タスクごとにコミットする実装フローで対象を取りこぼす。

```bash
BASE=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's|^origin/||'); BASE=${BASE:-main}
{ git diff --name-only "$(git merge-base "$BASE" HEAD)..HEAD" 2>/dev/null; git diff --name-only HEAD; } | sort -u | grep -E '\.(html|ts)$' | grep -v '\.(test|spec)\.'
```

上記の結果が **空の場合**（対象ファイルなし）→ 「アクセシビリティレビューの対象ファイルがありません（.html/.ts の変更なし）」とユーザーに伝えて終了する。スコープを拡張する場合はユーザーが明示的にファイルパスを指定する。

---

## 4つのチェック軸

### Axis 1 — セマンティクスとインタラクティブ要素

```html
<!-- Bad: クリック可能な div -->
<div (click)="handleSubmit()" class="btn">送信</div>

<!-- Good: セマンティックな button -->
<button type="button" (click)="handleSubmit()">送信</button>
```

**チェック項目**:
- `<div (click)>` / `<span (click)>` → `<button>` への置き換え候補
- `<a href="#">` の誤用（ボタン動作には `<button>` を使う）
- フォームの送信ボタンに `type="submit"` があるか

### Axis 2 — ARIA ラベルと説明

```html
<!-- Bad: アイコンのみのボタンに aria-label なし -->
<button (click)="handleClose()"><app-x-icon /></button>

<!-- Good -->
<button (click)="handleClose()" aria-label="閉じる"><app-x-icon /></button>

<!-- Bad: 画像の alt なし -->
<img src="/logo.png" />

<!-- Good -->
<img src="/logo.png" alt="サービスロゴ" />
<!-- 装飾画像は空文字 -->
<img src="/decoration.png" alt="" />
```

**チェック項目**:
- テキストを持たないインタラクティブ要素に `aria-label` or `aria-labelledby` があるか
- `<img>` に `alt` があるか（装飾画像は `alt=""`）
- フォーム入力に `<label>` or `aria-label` が関連付けられているか
- `aria-expanded`・`aria-selected`・`aria-checked` の状態が正しく反映されているか

### Axis 3 — フォーカス管理

```typescript
// Bad: モーダルを開いてもフォーカスが移動しない
@Component({ selector: 'app-modal', template: `<div role="dialog">...</div>` })
export class ModalComponent {}

// Good: 開いたら最初のフォーカス可能要素へ移動 + Escape で閉じる
@Component({ /* ... */ })
export class ModalComponent {
  @ViewChild('firstFocusable') firstFocusable?: ElementRef<HTMLButtonElement>
  @Input() isOpen = false
  @Output() closed = new EventEmitter<void>()

  ngOnChanges() { if (this.isOpen) this.firstFocusable?.nativeElement.focus() }
  @HostListener('keydown.escape') onEscape() { this.closed.emit() }
}
```

**チェック項目**:
- モーダル・ドロワー・ポップアップ開閉時にフォーカスが適切に移動するか
- `tabindex="-1"` を適切に使っているか（フォーカス順序の管理）
- モーダルの Escape キーハンドリングがあるか

### Axis 4 — キーボード操作

```html
<!-- Bad: mouseenter / mouseleave のみ（キーボード非対応） -->
<div (mouseenter)="showTooltip()" (mouseleave)="hideTooltip()">

<!-- Good: フォーカスイベントも併用 -->
<div
  (mouseenter)="showTooltip()"
  (mouseleave)="hideTooltip()"
  (focus)="showTooltip()"
  (blur)="hideTooltip()"
>
```

**チェック項目**:
- マウスイベントのみの実装でキーボード操作が不可能になっていないか
- カスタムドロップダウン・メニューに矢印キー操作があるか
- `role="button"` を付けた非 button 要素に `(keydown)` で Enter/Space 処理があるか

---

## 出力形式

```
## アクセシビリティレビュー: [スコープ]

### Axis 1 — セマンティクス
- [button.component.html:L8] `<div (click)="onClick()">` → `<button>` に変更

### Axis 2 — ARIA
- [icon-button.component.html:L3] アイコンのみのボタンに aria-label がない

### Axis 3 — フォーカス管理
（問題なし）

### Axis 4 — キーボード操作
- [dropdown.component.html:L22] (mouseenter) のみで (focus) がない

### サマリー
- 確認したファイル: N件
- 重要な問題: X件
```

**提案のみ。自動修正しない。**

**複数軸への重複報告**: 同一箇所が複数のチェック軸に該当する場合（例: `<div (click)>` は Axis 1・Axis 4 の両方に該当）は各軸で個別に報告する。

---

## Related skills

- `frontend-code-review` — このスキルを並列エージェントとして実行するオーケストレーター
- `impl-review` — 実装品質（設計整合性・TypeScript・Angular パターン）のレビュー
