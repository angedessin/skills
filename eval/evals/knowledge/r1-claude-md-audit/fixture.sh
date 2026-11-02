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

## コードの書き方

- いい感じのコードを書く
- `src/legacy/` のコンポーネントは触らない
- API のキーやトークンをコードに書かない。`.env.local` に置き、`import.meta.env` から読む
- `.steering/` の design.md が APPROVED になるまで実装しない

## テスト

- テストは振る舞いを確かめる
- 実装の詳細をテストしない

## コミット

- コミットは小さく分ける
- 1 タスク 1 コミットにする

## リリース前の確認（必ず行う）

1. `mise exec -- pnpm typecheck` を流す
2. `mise exec -- pnpm test` を流す
3. 変更した画面を開いて目で確かめる
4. 画面の幅を 375px にして崩れを確かめる
5. ダークモードで確かめる
6. キーボードだけで操作できるか確かめる
7. スクリーンリーダーで読み上げを確かめる
8. 遅い回線（Slow 3G）で確かめる
9. 確かめた結果をタスクの tasklist.md に書く
10. 上の 1〜9 を、変更のたびに必ずすべて行う
EOF_FIXTURE
git add -A >/dev/null
git -c user.name=eval -c user.email=eval@example.invalid commit -q -m "fixture" --allow-empty
