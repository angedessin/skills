---
name: review-ui
description: "フロントエンドの UI レビューに使うサブスキル。レイアウト・レスポンシブの破綻、デザイン整合（トークン遵守・一貫性）、UX 状態網羅（loading・error・empty・disabled）を確認する。frontend-code-review オーケストレーターからの並列呼び出しを想定。単独でも使用可。"
compatibility: "Angular / TypeScript / CSS（レスポンシブ・UX 状態の観点はフレームワーク中立。デザイントークンの実体は references/tokens.md をこのプロジェクトのトークン定義に合わせて再生成する）"
metadata:
  version: "1.1"
  source-commit: df027219393941e5a3e80cd2a9e8a4baa26f0b19
---

# Review — UI

静的コードから検知できる UI 品質を審査する。
`frontend-code-review` のフルモードで並列実行されるサブスキル。

**対象外**: 実レンダリング・スクリーンショットによる視覚検証（実ブラウザでの視覚検証ツールの領域）。本スキルはコードとスタイル定義から読み取れる範囲のみを見る。

## When NOT to use

- ロジック正当性・エラーの握りつぶし → `review-correctness` の担当。ここではエラーの**ユーザー向け表示の有無**（loading / error / empty / disabled の網羅）を見る。
- セマンティクス・ARIA・フォーカス・キーボード操作 → `review-a11y` の担当。
- 変更検知・パフォーマンス → `review-performance` の担当。
- テストコード・テストインフラの監査には使わない。

## スコープ

デフォルト: 未コミット + コミット済み（ベースブランチとの分岐点から）を合算した diff の `.html`・`.ts`・`.css`・`.scss`（テストファイルを除く）。未コミットだけを見ると、タスクごとにコミットする実装フローで対象を取りこぼす。

```bash
BASE=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's|^origin/||'); BASE=${BASE:-main}
{ git diff --name-only "$(git merge-base "$BASE" HEAD)..HEAD" 2>/dev/null; git diff --name-only HEAD; } | sort -u | grep -E '\.(html|ts|css|scss)$' | grep -v '\.(test|spec)\.'
```

上記の結果が **空の場合** → 「UI レビューの対象ファイルがありません（.html/.ts/.css/.scss の変更なし）」とユーザーに伝えて終了する。スコープを拡張する場合はユーザーが明示的にファイルパスを指定する。

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

```html
<!-- Bad: トークン定義があるのに生値をハードコード -->
<div style="padding: 13px; color: #3b82f6">

<!-- Good: 定義済みトークン・スケール値を使う（具体名は references/tokens.md） -->
<div class="p-4 text-primary">
```

**チェック項目**:
- ハードコードされた色・spacing・フォントサイズに対応するトークンが既に定義されていないか
- spacing / タイポグラフィのスケールから外れた中途半端な値（13px 等）が導入されていないか
- テーマ（ダークモード等）を持つプロジェクトで片方のテーマのみ対応していないか

### Axis 3 — UX 状態網羅

データ取得・送信を行う UI で、ユーザーに見える状態が揃っているかを確認する。

```html
<!-- Bad: 成功パスしか描画がない -->
<ul><li *ngFor="let u of users">{{ u.name }}</li></ul>

<!-- Good: loading / error / empty を描画で区別する（@if / @for のプロジェクトでは読み替える） -->
<app-spinner *ngIf="isLoading" />
<app-error-message *ngIf="error" [error]="error" />
<app-empty-state *ngIf="!isLoading && !error && users.length === 0" />
<ul *ngIf="users.length > 0"><li *ngFor="let u of users">{{ u.name }}</li></ul>
```

**チェック項目**:
- loading 状態の表示があるか（スピナー・スケルトン等）
- error 状態の**ユーザー向け表示**があるか（エラーがコードで握りつぶされる問題は review-correctness の担当。ここでは表示の有無を見る）
- empty 状態（0 件）の表示があるか（空の `<ul>` だけが残っていないか）
- 送信中の disabled・進行表示があるか（多重送信の防止は review-correctness、視覚フィードバックはこちら）
- 想定される失敗にユーザー向けのフォールバック表示があるか（グローバル ErrorHandler 任せで白画面にしない）

---

## 出力形式

```
## UI レビュー: [スコープ]

### Axis 1 — レイアウト・レスポンシブ
- [card.component.scss:L4] width: 480px 固定 — max-width への変更候補

### Axis 2 — デザイン整合
- [button.component.scss:L12] color: #3b82f6 ハードコード — トークン定義に primary が存在
（tokens.md 不在の場合: 「トークン定義なし — 一般的一貫性のみ確認（縮退動作）」と明記）

### Axis 3 — UX 状態網羅
- [user-list.component.html] error 状態と empty 状態の描画がない

### サマリー
- 確認したファイル: N件
- 重要な問題: X件
- トークン照合: 実施 / 縮退（tokens.md なし）
```

**提案のみ。自動修正しない。**

---

## Related skills

- `frontend-code-review` — このスキルを並列エージェントとして実行するオーケストレーター
- `review-a11y` — 同じテンプレートを対象とするが観点が異なる（セマンティクス・ARIA・フォーカス・キーボード）
- `review-correctness` — エラー握りつぶし・状態遷移矛盾のレビュー（本スキルは「表示」を見る）
