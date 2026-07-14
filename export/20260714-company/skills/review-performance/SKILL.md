---
name: review-performance
description: "フロントエンドのパフォーマンスレビューに使うサブスキル。Bundle サイズ・不要な変更検知・CWV（Core Web Vitals）の観点で確認する。frontend-code-review オーケストレーターからの並列呼び出しを想定。単独でも使用可。"
compatibility: "Angular / TypeScript（SSR・コード分割・CWV 観点はフレームワーク中立。フレームワーク固有の最適化 API があればそれを使う）"
metadata:
  version: "1.1"
  source-commit: 496a050cfde484237439c1899294042fecc06732
---

# Review — Performance

フロントエンドのパフォーマンス観点からコードを審査する。
`frontend-code-review` のフルモードで並列実行されるサブスキル。

## When NOT to use

- ロジック正当性・状態遷移 → `review-correctness` の担当。ここでは Bundle・変更検知・CWV を見る。
- 依存関係の脆弱性 → `review-security` の担当。
- 一般的な実装品質・設計整合 → `impl-review` の担当。
- テストコード・テストインフラの監査には使わない。

## スコープ

デフォルト: 未コミット + コミット済み（ベースブランチとの分岐点から）を合算した diff の `.ts`・`.html`（テストファイルを除く）。未コミットだけを見ると、タスクごとにコミットする実装フローで対象を取りこぼす。

```bash
BASE=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's|^origin/||'); BASE=${BASE:-main}
{ git diff --name-only "$(git merge-base "$BASE" HEAD)..HEAD" 2>/dev/null; git diff --name-only HEAD; } | sort -u | grep -E '\.(ts|html)$' | grep -v '\.(test|spec)\.'
```

上記の結果が **空の場合**: `.ts/.html` の変更がなくても `package.json` が変更されている場合は **Axis 1（Bundle サイズ）のみ** を実施する。`package.json` も変更がなければ「パフォーマンスレビューの対象ファイルがありません」とユーザーに伝えて終了する。

---

## 3つのチェック軸

### Axis 1 — Bundle サイズ

```typescript
// Bad: ライブラリ全体をインポート
import _ from 'lodash'
import * as dateFns from 'date-fns'

// Good: 必要な関数だけインポート（tree-shaking が効く）
import { debounce } from 'lodash-es'
import { format } from 'date-fns'
```

**チェック項目**:
- `import * as` や デフォルトインポートで大きなライブラリを全量取り込んでいないか
- `package.json` への新規依存追加がある場合、代替の軽量ライブラリがないか
- 重いコンポーネント（チャート・エディタなど）が遅延ロード（`loadComponent` / `loadChildren`・`@defer` 等）で分割されず初期バンドルに含まれていないか

### Axis 2 — 不要な変更検知（change detection）

```typescript
// Bad: テンプレート式で毎回関数を呼ぶ（変更検知のたびに再計算される）
// template: <li *ngFor="let item of items">{{ heavyFormat(item) }}</li>

// Good: pure pipe か事前計算した値を使う
// template: <li *ngFor="let item of items">{{ item.formatted }}</li>
```

**チェック項目**:
- テンプレート式で重い関数を呼んでいないか（pure pipe・signal の computed・事前計算に置き換える）
- 大きなリスト・更新頻度の高いツリーで `ChangeDetectionStrategy.OnPush`（または signals）が検討されているか
- `*ngFor` に `trackBy`（`@for` なら `track`）が指定されているか（未指定は並び替え・更新時に再マウント）
- 高頻度イベント（scroll・mousemove 等）の処理が毎回変更検知を起動していないか（`runOutsideAngular` 等の緩和策）

### Axis 3 — Core Web Vitals（フレームワーク中立）

CWV は特定フレームワーク非依存の観点。フレームワーク固有の最適化 API（Angular の `NgOptimizedImage` 等）があればそれを使い、無ければ素の手段で同じ目的を満たす。

**チェック項目**:
- **LCP**: above the fold の画像が最適化されているか（適切なサイズ・フォーマット・優先読み込み）。遅延読み込み（`loading="lazy"`）を above the fold 画像に誤用していないか
- **ウォーターフォール**: サーバー側で取得できるデータをクライアントで fetch して直列化していないか（SSR/RSC でもクライアントフェッチでも同じ落とし穴）
- **コード分割 / INP**: 遅延ルート・`@defer` の境界が適切に設定されているか
- **CLS**: フォント読み込み・画像の寸法未指定でレイアウトシフトが出ていないか

---

## 出力形式

```
## Performance Review: [スコープ]

### Axis 1 — Bundle サイズ
- [utils.ts:L3] `import _ from 'lodash'` → `import { debounce } from 'lodash-es'` に変更

### Axis 2 — 変更検知
- [card.component.html:L12] テンプレート式で `heavyFormat(item)` を呼んでいる — pure pipe か事前計算に変更

### Axis 3 — CWV
（問題なし）

### サマリー
- 確認したファイル: N件
- 重要な問題: X件
```

**提案のみ。自動修正しない。**

---

## Related skills

- `frontend-code-review` — このスキルを並列エージェントとして実行するオーケストレーター
- `impl-review` — 実装品質（設計整合性・TypeScript・Angular パターン）のレビュー
