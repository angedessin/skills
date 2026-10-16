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

- 対象: 検索フォームの下にカテゴリの select を置き、選んだカテゴリで API を再検索する
- 対象外: API 側の変更（既存の `/api/products` に `category` のクエリを足す前提で、MSW のハンドラだけ直す）

## 設計

- 選択肢は、その時点の検索結果に含まれるカテゴリと、先頭の「すべて」
- カテゴリを選んだら、キーワードと選んだカテゴリで `/api/products?q=...&category=...` を呼び、結果を差し替える
- キーワードを変えて検索したら、キーワードと選択中のカテゴリで検索する
- 状態は ProductSearch の `useState` に、`query`・`category`・検索の状態を持つ

## 完了条件

- [ ] カテゴリを選ぶと、そのカテゴリの商品だけが表示される
- [ ] 選んだカテゴリが URL に残り、再読み込みしても選択が保たれる
- [ ] 使いやすいこと

## 未解決の論点

なし
EOF_FIXTURE
git add -A >/dev/null
git -c user.name=eval -c user.email=eval@example.invalid commit -q -m "fixture" --allow-empty
