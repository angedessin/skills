#!/bin/bash
set -euo pipefail
cp -cR /Users/kentaro/Desktop/_lab/ai/skills-eval-app/. .
mkdir -p "$(dirname 'CLAUDE.md')"
cat > 'CLAUDE.md' <<'EOF_FIXTURE'
# skills-eval-app

Tech stack: React / TypeScript / Vitest / React Testing Library / MSW

## 作業の進め方

- 複数セッションにまたがる作業は、実装の前に `.steering/[YYYYMMDD]-[task]/` に design.md（冒頭に `Status: DRAFT`）と tasklist.md を作り、人間のレビューを求めて止まる。Status が APPROVED になるまで実装しない
- 1 セッションで終わるが決めることがある作業は、会話の中で設計を示し、OK をもらってから実装する
- 小さな作業（typo・数行の修正・調査だけ）は、この手順に乗せずにそのまま進める。どれに当たるか迷うときだけ聞く
- 作業を再開するときは、`.steering/` の tasklist.md を読んでから始める。作業を終えたら tasklist.md を更新する

## 自律実行の境界

- CLAUDE.md・docs/・.claude/ への書き込みは、承認を得てから Edit / Write ツールで行う
- 判断基準: (1) git で巻き戻せる (2) 失敗に気づける (3) 影響がタスク内に閉じる — 3 つ全て満たす操作のみ承認なしで実行してよい

## 環境

- mise 管理下では Bash から素の pnpm / node を呼ばず、`mise exec --` を使う
EOF_FIXTURE
mkdir -p "$(dirname '.steering/20261026-pagination/design.md')"
cat > '.steering/20261026-pagination/design.md' <<'EOF_FIXTURE'
# 検索結果のページ送り

Status: APPROVED

## 振る舞い

- 1 ページ 10 件。前へ・次へのボタンで移動する
- ページ番号を URL の `?page=` に持つ
- 新しく検索したら 1 ページ目に戻る
EOF_FIXTURE
mkdir -p "$(dirname '.steering/20261026-pagination/tasklist.md')"
cat > '.steering/20261026-pagination/tasklist.md' <<'EOF_FIXTURE'
# tasklist: pagination

- [x] ページ送りのボタンを足す
- [x] URL とページ番号を同期する
- [x] テストを足す
- [x] レビューの指摘に対応する
EOF_FIXTURE
mkdir -p "$(dirname '.steering/20261026-pagination/decisions.md')"
cat > '.steering/20261026-pagination/decisions.md' <<'EOF_FIXTURE'
# decisions: pagination

## 20261026 — ページ番号は URL の検索パラメータに持つ

**決定**: `?page=` に持ち、状態は URL から読む
**理由**: 再読み込みと共有で同じページを開けるため
**却下案**: コンポーネントの state に持つ（再読み込みで 1 ページ目に戻る）
EOF_FIXTURE
mkdir -p "$(dirname '.steering/20261026-pagination/review-result.md')"
cat > '.steering/20261026-pagination/review-result.md' <<'EOF_FIXTURE'
# review-result: pagination

Status: RESOLVED

| # | 重要度 | 指摘 | 場所 | 対応 |
|---|---|---|---|---|
| 1 | High | `setSearchParams` で `page` だけを渡すと、他の検索パラメータ（`q`）が消える。既存のパラメータを写してから `page` を変える | `Pagination.tsx:12` | 直した |
| 2 | Medium | 最後のページで検索結果が減ると、範囲外のページを指したまま空の一覧になる。範囲外なら最後のページに丸める | `Pagination.tsx:20` | 直した |
| 3 | Low | ボタンの文言「つぎ」を「次へ」に揃える | `Pagination.tsx:30` | 直した |
EOF_FIXTURE
mkdir -p "$(dirname '.steering/20261026-pagination/blockers.md')"
cat > '.steering/20261026-pagination/blockers.md' <<'EOF_FIXTURE'
# blockers: pagination

## 20261026 — テストの実行が失敗する

`pnpm test` を Bash から素で呼ぶと失敗した。`mise exec -- pnpm test` で回す
EOF_FIXTURE
mkdir -p "$(dirname 'docs/knowledge/testing-patterns.md')"
cat > 'docs/knowledge/testing-patterns.md' <<'EOF_FIXTURE'
# テストのパターン

## モックの境界

- API はネットワークの手前（MSW）でモックする。`src/api/` の関数を `vi.mock` で差し替えない（呼び出しの確認だけになり、振る舞いを見なくなる）
- ハンドラは `src/mocks/handlers.ts` に置き、テストごとの差し替えは `server.use` で行う

## 要素の探し方

- 役割とアクセシブルな名前 → ラベル → 表示文字列の順で探す
EOF_FIXTURE
mkdir -p "$(dirname 'docs/knowledge/api-patterns.md')"
cat > 'docs/knowledge/api-patterns.md' <<'EOF_FIXTURE'
# API 呼び出しのパターン

- API の関数は `src/api/` に置き、画面からは直接 `fetch` を呼ばない
- 失敗は例外で返し、画面側で `status: "error"` にする
EOF_FIXTURE
git add -A >/dev/null
git -c user.name=eval -c user.email=eval@example.invalid commit -q -m "fixture" --allow-empty
