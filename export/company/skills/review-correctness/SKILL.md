---
name: review-correctness
description: "フロントエンドのロジック正当性レビューに使うサブスキル。境界条件・null/undefined の取りこぼし・非同期レースと stale closure・状態遷移の矛盾とエラー握りつぶしを確認する。frontend-code-review オーケストレーターからの並列呼び出しを想定。単独でも使用可。"
compatibility: "Angular / TypeScript（境界条件・null 安全・非同期の観点は言語・フレームワーク中立）"
metadata:
  version: "1.1"
  source-commit: 1dfa5081509eda8173e713c54ff6d390563352cd
---

# Review — Correctness

コードが「設計どおりか」ではなく「正しく動くか」を審査する。
`frontend-code-review` のフルモードで並列実行されるサブスキル。

**impl-review との境界**: 型注釈の品質（`any`・アサーション・`@ts-ignore`）は impl-review の TypeScript 軸が担当。本スキルはロジックがランタイムで壊れる箇所（null 参照・境界値・レース）を見る。同一行に両方の指摘が出た場合の統合はオーケストレーターが行う。

## When NOT to use

- レイアウト・デザイン整合・エラーの**ユーザー向け表示の有無** → `review-ui` の担当。ここではエラーの握りつぶし（ロジック上の取りこぼし）を見る。
- 変更検知・パフォーマンス劣化 → `review-performance` の担当。
- テストコードの品質・アサーション → `test-review` の担当。
- テストランナー・カバレッジ設定などインフラの監査には使わない。

## スコープ

デフォルト: 未コミット + コミット済み（ベースブランチとの分岐点から）を合算した diff の `.ts`・`.html`（テストファイルを除く）。未コミットだけを見ると、タスクごとにコミットする実装フローで対象を取りこぼす。

```bash
BASE=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's|^origin/||'); BASE=${BASE:-main}
{ git diff --name-only "$(git merge-base "$BASE" HEAD)..HEAD" 2>/dev/null; git diff --name-only HEAD; } | sort -u | grep -E '\.(ts|html)$' | grep -v '\.(test|spec)\.'
```

上記の結果が **空の場合** → 「correctness レビューの対象ファイルがありません（.ts/.html の実装変更なし）」とユーザーに伝えて終了する。スコープを拡張する場合はユーザーが明示的にファイルパスを指定する。

---

## 4つのチェック軸

### Axis 1 — 境界条件・off-by-one

```typescript
// Bad: 空配列で reduce が throw する
const total = items.reduce((sum, item) => sum + item.price)

// Good: 初期値を渡す
const total = items.reduce((sum, item) => sum + item.price, 0)
```

**チェック項目**:
- 空配列・空文字列・0・負数を入力したとき分岐やループが壊れないか
- `<` と `<=` の取り違え、`slice`/`substring` の端点などの off-by-one
- ページネーション・カーソルの端（最初/最後のページ、残り 0 件）の扱い
- 除算・剰余のゼロ除算、`parseInt`/`Number` の NaN 伝播

### Axis 2 — null・undefined の取りこぼし

```typescript
// Bad: find の結果を無検証で参照する
const user = users.find(u => u.id === id)
return user.name // user は undefined になりうる

// Good: ガードして早期リターン
const user = users.find(u => u.id === id)
if (!user) return null
return user.name
```

**チェック項目**:
- `find`・`match`・`Map.get` 系の戻り値を無検証で参照していないか
- optional chaining（`?.`）の結果が後段の算術・比較・テンプレート文字列に undefined のまま流れていないか
- API レスポンスの optional フィールドの分岐漏れ
- `!`（非 null アサーション）でガードを省略している箇所が本当に非 null か

### Axis 3 — 非同期レース・stale closure

```typescript
// Bad: 古いリクエストの結果が後から新しい結果を上書きする
this.searchTerm$.subscribe(term => {
  this.api.search(term).subscribe(results => this.results = results)
})

// Good: switchMap で古いリクエストを破棄する
this.results$ = this.searchTerm$.pipe(
  switchMap(term => this.api.search(term))
)
```

**チェック項目**:
- 連続発火しうる非同期処理（検索入力・タブ切替等）で古い結果が新しい結果を上書きしないか
- タイマー・イベントハンドラ・サブスクリプション内のクロージャが古い state/props を掴んでいないか（stale closure）
- 送信ボタン連打・二重送信のガード（in-flight フラグ・disabled）があるか
- `await` 漏れ（floating promise）で完了前に後続処理が走らないか

### Axis 4 — 状態遷移の矛盾・エラー握りつぶし

```typescript
// Bad: catch で握りつぶし、呼び出し側は失敗を検知できない
try { await save() } catch {}

// Good: 失敗を状態に反映するか再スローする
try { await save() } catch (e) { setError(toErrorMessage(e)) }
```

**チェック項目**:
- `catch {}`・`catch (e) { console.log(e) }` で失敗が呼び出し側・UI に伝わらない箇所（エラーの**ユーザー向け表示の有無**は review-ui の担当。ここでは**握りつぶし**を見る）
- 矛盾する状態の組み合わせが表現できてしまう設計（`isLoading && isSuccess` が同時に真になりうる等）
- 早期リターン漏れで後続処理が不正な前提のまま実行される箇所
- 到達しない分岐・常に真/偽になる条件

---

## 出力形式

```
## Correctness Review: [スコープ]

### Axis 1 — 境界条件
- [utils/paginate.ts:L14] 残り 0 件のとき totalPages が 0 になり最終ページ計算が壊れる

### Axis 2 — null・undefined
- [services/user.service.ts:L22] find の戻り値を無検証で user.name 参照

### Axis 3 — 非同期レース・stale closure
（問題なし）

### Axis 4 — 状態遷移・エラー握りつぶし
- [api/save.ts:L31] catch {} で失敗が呼び出し側に伝わらない

### サマリー
- 確認したファイル: N件
- 重要な問題: X件
```

**提案のみ。自動修正しない。**

より深い correctness レビューが必要な場合はビルトイン `/code-review high` または `/code-review ultra` を追加で使うことを提案する。

---

## Related skills

- `frontend-code-review` — このスキルを並列エージェントとして実行するオーケストレーター
- `impl-review` — 型注釈の品質・Angular パターン・設計整合性のレビュー
- `review-ui` — エラーの表示・UX 状態網羅（loading/error/empty/disabled）のレビュー
