<!-- results-knowledge-b-1.json / k1-price-filter-capture / with / 0.24 USD / 71s -->

price-filter の知見をまとめた書き込み案です。**まだどのファイルにも書き込んでいません。**

**判定:** tasklist.md に「デプロイ」節がなく、項目はすべてチェック済みです。なので最後の保存として扱い、完了時に `capture_done` を立てます。`.capture-needed` と `.codify-needed` はどちらもありませんでした。

## 知見保存ドラフト（案・未書き込み）

### 1. MSW の差し替えが次のテストに残る（blockers の 1 件目、解決済み）
保存先（案）: `docs/knowledge/testing-patterns.md` の「モックの境界」節に追記
書き込む内容（案）:
---
- `server.use` による差し替えは、`src/test/setup.ts` の `afterEach(() => server.resetHandlers())` で毎回元に戻す。これが無いと、エラー用のハンドラが次のテストにも残る。単独では通るのにまとめて流すと落ちる、あるいはテストの順番で結果が変わるときは、まずこれを疑う
---
※ 今の setup.ts には `resetHandlers()` が入っていることを確認しました。

### 2. 数値の入力欄の扱い（新しいトピック）
保存先（案）: `docs/knowledge/form-input-patterns.md`（新規作成）
書き込む内容（案）:
---
# フォーム入力のパターン

## 数値の入力欄

- `type="number"` は使わず、`type="text"` に `inputMode="numeric"` を付ける。`type="number"` だと、ブラウザによっては「10,000」のようなカンマ入りの入力が空になる
- 文字列を数値にするときは、先にカンマを取り除く。`Number("10,000")` は NaN になり、`price <= NaN` はどの商品でも false になるため全件が消える
- NaN になったら絞り込まない（全件を出す）。空欄と 0 は区別する（0 は「0 円以下」の意味）

```typescript
// Good
const n = Number(input.replace(/,/g, ""));
if (input.trim() === "" || Number.isNaN(n)) return products;

// Bad
const n = Number(input); // "10,000" → NaN → 全件消える
```
---

### 3. blockers の 2 件目「`pnpm test` が node を見つけられない」
保存先（案）: blockers.md から削除（破棄）
理由: CLAUDE.md の「環境」節にある「Bash からは `mise exec --` で呼ぶ」と同じ内容です。

### 4. 記録不要なもの（参考）
- decisions.md の 5 件は、すでに決定と理由が書かれています。追記はしません。
- レビュー指摘の 2〜6（ラベル、typo、テストの追加、引数名、下限の将来案）はこのタスクだけの話なので、コミットメッセージで足ります。

---

decisions.md の「絞り込みはクライアント側で行う」には、却下した代替案（API に `maxPrice` を足す）があります。チームの決定記録に上げるか検討してください。

**補足:** tasklist に書かれている `src/features/products/filterByMaxPrice.ts` がリポジトリに見つかりませんでした。案 2 のコード例は review-result.md の内容から書いています。

採用するものを番号で教えてください（例:「1, 2, 3」）。`docs/` への書き込みには承認が必要なので、返事をもらうまで何も書き込みません。
