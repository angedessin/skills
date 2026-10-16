#!/bin/bash
set -euo pipefail
cp -cR /Users/kentaro/Desktop/_lab/ai/skills-eval-app/. .
mkdir -p "$(dirname '.steering/20261014-category-filter/design.md')"
cat > '.steering/20261014-category-filter/design.md' <<'EOF_FIXTURE'
# 設計: category-filter

Created: 20261014
Status: DRAFT

## 目的

商品検索の結果をカテゴリで絞り込めるようにする。

## スコープ

- 対象: 検索フォームの下にカテゴリの select を置き、取得済みの検索結果をクライアント側で絞り込む
- 対象外: API の変更・URL への状態の保存・複数カテゴリの同時選択

## 設計

- 選択肢は、その時点の検索結果に含まれるカテゴリ（重複を除く）と、先頭の「すべて」
- 初期値は「すべて」。選択を変えたら、取得済みの結果をその場で絞り込む（再検索しない）
- 新しく検索したら、選択を「すべて」に戻す
- 絞り込みの結果が 0 件なら「該当する商品はありません」を出す。API のエラー時は select を出さない
- 絞り込みは純粋な関数 `filterByCategory(products, category)` に切り出す

## 完了条件

- [ ] カテゴリを選ぶと、そのカテゴリの商品だけが表示される（RTL のテスト）
- [ ] 新しく検索すると、選択が「すべて」に戻る（RTL のテスト）
- [ ] `filterByCategory` の単体テストが通る
- [ ] 既存のテスト 3 件が通る

## 未解決の論点

なし
EOF_FIXTURE
mkdir -p "$(dirname '.steering/20261014-category-filter/tasklist.md')"
cat > '.steering/20261014-category-filter/tasklist.md' <<'EOF_FIXTURE'
# タスクリスト: category-filter

Last updated: 20261014

- [ ] `filterByCategory` を作り、単体テストを書く
- [ ] カテゴリの select を追加する
- [ ] 新しい検索で選択を戻す
- [ ] RTL のテストを書く
EOF_FIXTURE
git add -A >/dev/null
git -c user.name=eval -c user.email=eval@example.invalid commit -q -m "fixture" --allow-empty
