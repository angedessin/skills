# skills — personal frontend workflow skill set

Tech stack: React / TypeScript / Vitest / React Testing Library / MSW / Playwright

## .steering ルール

新しいタスクを開始するときは必ず:
1. `design-doc` スキルを使い `.steering/[YYYYMMDD]-[task]/` を作成（1セッションで完結する見込みのタスクは、design-doc がユーザーに確認して会話内設計が選ばれた場合のみ `.steering/` を作らず縮退する。Claude の見積もりだけで縮退を確定しない）
2. `design.md`（会話内設計の場合は設計方針）の提示後は人間のレビュー待ちで止まること（実装に入らない）
3. 作業完了後は必ず `tasklist.md` を更新すること

セッション開始時（アクティブタスク一覧は SessionStart hook `session-start-check.sh` が context に注入する）:
1. `.steering/` のアクティブタスクをすべて読んでから作業開始
2. 複数のアクティブタスクがある場合はどれを再開するか確認

## ブランチ運用（git-flow）

- 統合ブランチは develop。main へは release ブランチで出す。git-flow CLI は使わず素の git（`checkout -b`・`merge --no-ff`）で操作する
- 作業は develop から `feature/*` を切り、develop へは PR でマージする。typo・1〜2 ファイルの微修正だけは develop へ直接コミットしてよい
- 大きなタスクはマージ用の feature ブランチを切り、子ブランチから PR で集める。子ブランチは `feature/x/child` のような階層名にしない（同名ブランチと ref が衝突する）
- feature ブランチで開始したタスクは、develop へのマージ前にアーカイブまで済ませる（`.steering/` がブランチ間で分岐すると、他のセッションからタスクが見えない・アーカイブ済みがアクティブに見える等の対応漏れが起きる）

## スキル管理ルール

- 新規スキルは `templates/SKILL.template.md` をコピーして書き始める（契約準拠を最初から構造として渡す。使い方は `templates/README.md`）
- サードパーティ製 SKILL.md 採用前に Bash コマンド・外部 URL・プロンプトインジェクションを目視確認する
- スキルの誤発動・曖昧な指示・実行不能な手順に気づいたら `.steering/[task]/skill-issues.md` に事象と期待を追記する（compound が回収して改善候補にする）
- スキルの横展開は人が選んで配置先プロジェクトの `.claude/skills/` に手動コピーする。配置先で直接編集せず、改善はこのリポジトリ（マスター）に還元して再コピーで配る
- スキルは自己完結に書く: CLAUDE.md・docs/・`.steering/` が無いプロジェクトでも動くフォールバックを該当ステップに直接書く（詳細は skill-design-patterns.md）
- スキルを変更するタスクでは、変更対象ごとに配布分類（配布可 / master-only）を先に確認する（配布可スキルに master-only スキル名を書くと配置先で死んだ参照になる）

## 自律実行の境界

- `.steering/[task]/` 配下のメモ（decisions.md・skill-issues.md・blockers.md）への追記は承認不要。気づいた時点で書く（内容の取捨選択は compound / knowledge-capture 時にまとめて行う）
- CLAUDE.md・SKILL.md・docs/・.claude/settings*・.claude/hooks/ への書き込みは承認制を維持し、Edit / Write ツールでだけ書く（Bash の sed・python・リダイレクトは ask ゲートを自分で迂回する）
- 判断基準: (1) git で巻き戻せる (2) 失敗に気づける (3) 影響がタスク内に閉じる — 3つ全て満たす操作のみ承認なしで実行してよい
- `git add -A` / `git commit` の前に `git status --short` でステージ内容を確認する（サブエージェントが「変更するな」の指示に反して作ったファイルが混入する。確認せずコミットして検証ゴミを追跡下に入れた実例がある）
- 手作業で突合した検証項目は、その場で機械検査に入れるか「一回限り」と明記する（報告書の「確認した」は次セッションに何も保証しない。手で確認して報告し契約化しなかったため、次のレビューで High として指摘された実例がある）

## ナレッジ保存先のルール

CLAUDE.md は行動ルールのみ。知識の倉庫にしない（毎回コンテキストを消費するため）。

| 種類 | 保存先 |
|---|---|
| 行動ルール（短い命令形） | このファイル or `~/.claude/CLAUDE.md` |
| 経験・パターン・アンチパターン | `docs/knowledge/[topic].md`（**必要時に読む**。`@` を付けると毎セッション全文が展開され固定費になるため、常時参照が要るものだけに限る） |
| タスク固有の決定 | `.steering/[task]/decisions.md` |

## 環境

- mise 管理下では Bash から素の pnpm / node を呼ばず、`mise exec --` を使う
