#!/bin/bash
set -euo pipefail
cp -cR /Users/kentaro/Desktop/_lab/ai/skills-eval-app/. .
mkdir -p "$(dirname '.steering/20261022-search-refine/design.md')"
cat > '.steering/20261022-search-refine/design.md' <<'EOF_FIXTURE'
# 設計: search-refine

Created: 20261022
Status: **APPROVED**（20261022）

## 目的

検索結果を、カテゴリ・価格帯・並び順で絞り込み、並べ替えられるようにする。

## スコープ

- 対象: 取得済みの検索結果に対する、クライアント側の絞り込みと並び替え
- 対象外: API と MSW のハンドラの変更・URL への状態の保存

## 振る舞い

- **カテゴリ:** select。選択肢は「すべて」と、検索結果に含まれるカテゴリ（重複なし・出てきた順）
- **価格帯:** 下限と上限の数値入力。空欄はその側を制限しない。下限が上限を超えたら「下限が上限を超えています」と出し、価格帯の絞り込みはかけない（カテゴリと並び順は効く）
- **並び順:** select。「安い順」「高い順」。既定は「安い順」。同じ価格の商品は id の昇順
- 絞り込みと並び順は、取得済みの結果にその場でかける（再検索しない）
- 新しく検索したら、カテゴリと並び順を初期値に戻す。価格帯は残す
- 絞り込んだ結果が 0 件なら「該当する商品はありません」を出す
- 検索前・読み込み中・エラーのときは、絞り込みと並び順の入力を出さない

## 構成

- `src/features/products/searchFilters.ts`（新規）: カテゴリの一覧・カテゴリの絞り込み・価格帯の絞り込み・並び替えの純粋な関数
- `src/features/products/searchFilters.test.ts`（新規）: 上の関数の単体テスト
- `src/features/products/ProductSearch.tsx`: 入力の state と UI
- `src/features/products/ProductSearch.test.tsx`: 画面の操作で確かめるテストを足す

## 完了条件

- [ ] カテゴリ・価格帯・並び順を組み合わせて、画面の結果が変わる
- [ ] 下限が上限を超えたとき、メッセージが出て価格帯の絞り込みがかからない
- [ ] 新しく検索すると、カテゴリと並び順が初期値に戻り、価格帯は残る
- [ ] 既存のテストと足したテストが通る
EOF_FIXTURE
mkdir -p "$(dirname '.steering/20261022-search-refine/tasklist.md')"
cat > '.steering/20261022-search-refine/tasklist.md' <<'EOF_FIXTURE'
# タスクリスト: search-refine

Last updated: 20261022

- [ ] `searchFilters.ts` にカテゴリの一覧とカテゴリの絞り込みを書く（単体テストつき）
- [ ] `searchFilters.ts` に価格帯の絞り込みを書く（空欄・下限が上限を超える場合を含む。単体テストつき）
- [ ] `searchFilters.ts` に並び替えを書く（同じ価格は id の昇順。単体テストつき）
- [ ] ProductSearch に入力の state と UI を足す（検索前・読み込み中・エラーでは出さない）
- [ ] 新しく検索したらカテゴリと並び順を戻す（価格帯は残す）
- [ ] 画面のテストを足し、全テストを流して tasklist を更新する
EOF_FIXTURE
mkdir -p "$(dirname '.steering/20261022-search-refine/decisions.md')"
cat > '.steering/20261022-search-refine/decisions.md' <<'EOF_FIXTURE'
# 決定事項: search-refine

## 20261023 — 並び順の既定を「おすすめ順」にする

**決定**: 並び順の選択肢に「おすすめ順」（API が返した順のまま）を足し、既定にする。「安い順」「高い順」は選択肢として残す。新しく検索したら「おすすめ順」に戻す
**理由**: API の返す順は人気順で、既定で価格順にすると上位の商品が埋もれるため
**影響**: design.md の「並び順」と完了条件は、まだ「既定は安い順」のまま（実装のときに直す）
EOF_FIXTURE
git add -A >/dev/null
git -c user.name=eval -c user.email=eval@example.invalid commit -q -m "fixture" --allow-empty
