#!/bin/bash
set -euo pipefail
cp -cR /Users/kentaro/Desktop/_lab/ai/skills-eval-app/. .
mkdir -p "$(dirname '.steering/20261020-category-filter/design.md')"
cat > '.steering/20261020-category-filter/design.md' <<'EOF_FIXTURE'
# 設計: category-filter

Created: 20261020
Status: **APPROVED**（20261021）

## 目的

商品検索の結果をカテゴリで絞り込めるようにする。

## スコープ

- 対象: 検索結果をカテゴリの select でクライアント側で絞り込む
- 対象外: API と MSW のハンドラの変更・URL への状態の保存

## 振る舞い

- select の選択肢は「すべて」と、その時点の検索結果に含まれるカテゴリ（重複なし・出てきた順）。「すべて」を先頭に置く
- 初期値は「すべて」。選択を変えたら、取得済みの結果をその場で絞り込む（再検索しない）
- 新しく検索したら、選択を「すべて」に戻す
- 絞り込んだ結果が 0 件なら「該当する商品はありません」を出す
- 検索前・読み込み中・エラーのときは select を出さない

## 構成

- `src/features/products/filter.ts`（新規）: `filterByCategory(products, category)` と、結果からカテゴリの一覧を作る関数
- `src/features/products/ProductSearch.tsx`: 選択中のカテゴリの state と select を足す
- テストは `src/features/products/ProductSearch.test.tsx` に足す

## 完了条件

- [ ] カテゴリを選ぶと、そのカテゴリの商品だけが表示される
- [ ] 新しく検索すると、選択が「すべて」に戻る
- [ ] 絞り込んだ結果が 0 件のとき「該当する商品はありません」が出る
- [ ] 既存のテスト 3 件と、足したテストが通る

## テスト方針

- MSW のハンドラはそのまま使う（data.ts に 3 カテゴリある）
- ユーザーの操作（キーワードを入れて検索 → カテゴリを選ぶ）で確かめる
EOF_FIXTURE
mkdir -p "$(dirname '.steering/20261020-category-filter/tasklist.md')"
cat > '.steering/20261020-category-filter/tasklist.md' <<'EOF_FIXTURE'
# タスクリスト: category-filter

Last updated: 20261021

- [ ] `filter.ts` に `filterByCategory` とカテゴリの一覧を作る関数を書く
- [ ] ProductSearch に選択中のカテゴリの state と select を足す
- [ ] 新しく検索したら「すべて」に戻す
- [ ] テストを足す（絞り込み・検索し直したら戻る）
- [ ] 全テストを流して tasklist を更新する
EOF_FIXTURE
git add -A >/dev/null
git -c user.name=eval -c user.email=eval@example.invalid commit -q -m "fixture" --allow-empty
