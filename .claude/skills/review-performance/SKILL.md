---
name: review-performance
description: "フロントエンドのパフォーマンスレビューに使うサブスキル。Bundle サイズ・不要な再レンダリング・CWV（Core Web Vitals）の観点で確認する。frontend-code-review オーケストレーターからの並列呼び出しを想定。単独でも使用可。"
compatibility: "React / TypeScript（SSR・コード分割・CWV 観点はフレームワーク中立。フレームワーク固有の最適化 API があればそれを使う）"
---

# Review — Performance

フロントエンドのパフォーマンス観点からコードを審査する。
`frontend-code-review` のフルモードで並列実行されるサブスキル。

## スコープ

デフォルト: `git diff --name-only HEAD` の `.ts`・`.tsx`（テストファイルを除く）。

```bash
git diff --name-only HEAD | grep -E '\.(ts|tsx)$' | grep -v '\.(test|spec)\.'
```

上記の結果が **空の場合**: `.ts/.tsx` の変更がなくても `package.json` が変更されている場合は **Axis 1（Bundle サイズ）のみ** を実施する。`package.json` も変更がなければ「パフォーマンスレビューの対象ファイルがありません」とユーザーに伝えて終了する。

---

## 3つのチェック軸

### Axis 1 — Bundle サイズ

```typescript
// ❌ Bad: ライブラリ全体をインポート
import _ from 'lodash'
import * as dateFns from 'date-fns'

// ✅ Good: 必要な関数だけインポート（tree-shaking が効く）
import { debounce } from 'lodash-es'
import { format } from 'date-fns'
```

**チェック項目**:
- `import * as` や デフォルトインポートで大きなライブラリを全量取り込んでいないか
- `package.json` への新規依存追加がある場合、代替の軽量ライブラリがないか
- 重いコンポーネント（チャート・エディタなど）が動的 import（`React.lazy` + `Suspense` 等）で分割されず初期バンドルに含まれていないか

### Axis 2 — 不要な再レンダリング

```typescript
// ❌ Bad: 毎レンダリングで新しいオブジェクト/関数を生成
function Parent() {
  return <Child config={{ key: 'value' }} /> // 毎回新しい参照
}

// ✅ Good: useMemo / useCallback で安定した参照を渡す
const config = useMemo(() => ({ key: 'value' }), [])
return <Child config={config} />
```

**チェック項目**:
- インラインオブジェクト・配列・関数を props に渡していないか（`React.memo` の無効化）
- `useEffect` の deps が広すぎて不要な再実行が発生していないか
- リスト描画で `key` が index だけになっていないか（並び替え時に再マウント）
- 大きなコンテキスト（Provider）が頻繁に更新されていないか

### Axis 3 — Core Web Vitals（フレームワーク中立）

CWV は特定フレームワーク非依存の観点。フレームワーク固有の最適化 API（画像コンポーネント・フォントローダ等）があればそれを使い、無ければ素の手段で同じ目的を満たす。

**チェック項目**:
- **LCP**: above the fold の画像が最適化されているか（適切なサイズ・フォーマット・優先読み込み）。遅延読み込み（`loading="lazy"`）を above the fold 画像に誤用していないか
- **ウォーターフォール**: サーバー側で取得できるデータをクライアントで fetch して直列化していないか（SSR/RSC でもクライアントフェッチでも同じ落とし穴）
- **コード分割 / INP**: 動的 import と `Suspense` 境界が適切に設定されているか
- **CLS**: フォント読み込み・画像の寸法未指定でレイアウトシフトが出ていないか

---

## 出力形式

```
## Performance Review: [スコープ]

### Axis 1 — Bundle サイズ
- [utils.ts:L3] `import _ from 'lodash'` → `import { debounce } from 'lodash-es'` に変更

### Axis 2 — 再レンダリング
- [Card.tsx:L12] インラインオブジェクト `{ size: 'lg' }` を props に渡している

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
- `impl-review` — 実装品質（設計整合性・TypeScript・React パターン）のレビュー
