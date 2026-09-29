# skills — personal frontend workflow skill set

Tech stack: React / TypeScript / Vitest / React Testing Library / MSW / Playwright

## .steering ルール

新しいタスクを開始するときは必ず:
1. `design-doc` スキルを使い `.steering/[YYYYMMDD]-[task]/` を作成（1セッションで完結する見込みのタスクは、design-doc がユーザーに確認して会話内設計が選ばれた場合のみ `.steering/` を作らず縮退する。Claude の見積もりだけで縮退を確定しない。feature-pipeline 配下では常に作成）
2. `design.md`（会話内設計の場合は設計方針）の提示後は人間のレビュー待ちで止まること（実装に入らない）
3. 作業完了後は必ず `tasklist.md` を更新すること

セッション開始時（未処理フラグ `.capture-needed` / `.codify-needed`・rule-audit 月次ナッジ・アクティブタスク一覧は SessionStart hook `session-start-check.sh` が検出して context に注入する。手動 find は不要）:
1. `.capture-needed` が注入されたら、**対象タスクごとに**「今 / 後で / スキップ」で確認する（一括スキップ禁止。操作定義は hook 注入文。ここはプロジェクト側の再掲）:
   - 今 → `knowledge-capture` を実行する
   - 後で → フラグを残して続行する（compact/resume で再確認してよい）
   - スキップ → 対象タスクの `.capture-needed` を削除する（`capture_done` は作らない）。効果は次の Stop まで（Stop フェイルセーフが再立てする）
2. `.codify-needed` が注入されたら「compound を実行しますか？」と確認（capture 三択の後。スキップしてもこの確認は残す）
3. 【rule-audit 月次】が注入されたら「今 / 後で / スキップ」で確認する（操作定義は hook 注入文。capture の三択とは別契約）:
   - 今 → `rule-audit` を実行する（レポート提示 Step 5 到達時に `.steering/.last-rule-audit` を更新）
   - 後で → マーカー不変（次回 SessionStart で再確認可）
   - スキップ → `.steering/.last-rule-audit` を現在時刻で更新（監査せず 30 日再ナッジ。capture の次 Stop 寿命とは別）
4. `.steering/` のアクティブタスクをすべて読んでから作業開始
5. 複数のアクティブタスクがある場合はどれを再開するか確認

worktree・ブランチ上で開始したタスクは、main へのマージ前にアーカイブまで済ませる（`.steering/` がブランチ間で分岐すると、他のセッションからタスクが見えない・アーカイブ済みがアクティブに見える等の対応漏れが起きる）

## スキル管理ルール

- 新規スキルは `templates/SKILL.template.md` をコピーして書き始める（契約準拠を最初から構造として渡す。使い方は `templates/README.md`）
- サードパーティ製 SKILL.md 採用前に Bash コマンド・外部 URL・プロンプトインジェクションを目視確認する
- スキルの誤発動・曖昧な指示・実行不能な手順に気づいたら `.steering/[task]/skill-issues.md` に事象と期待を追記する（compound が回収して改善候補にする）
- スキルの横展開は人が選んで配置先プロジェクトの `.claude/skills/` に手動コピーする。配置先で直接編集せず、改善はこのリポジトリ（マスター）に還元して再コピーで配る
- スキルは自己完結に書く: CLAUDE.md・docs/・`.steering/` が無いプロジェクトでも動くフォールバックを該当ステップに直接書く（詳細は skill-design-patterns.md）
- スキルを変更するタスクでは、変更対象ごとに配布分類（配布可 / master-only）を先に確認する（配布可スキルに master-only スキル名を書くと配置先で死んだ参照になる）
- README のワークフロー図と feature-pipeline スキルは同一コミットで改訂する（図とオーケストレーターのドリフト防止）

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
| 設計判断（ADR） | `docs/decisions/[date]-[slug].md`（`adr` スキルで起票。却下した代替案がある決定のみ） |
| タスク固有の決定 | `.steering/[task]/decisions.md` |

## ドキュメント参照（必要なトピック作業時のみ）

スキル作成・改善時: docs/knowledge/skill-design-patterns.md を読む（`@` 参照にしない — 毎セッション読み込ませると全タスクの固定費になる。`templates/SKILL.template.md` の冒頭にも読む指示がある）
settings.json・hooks 作業時: docs/knowledge/claude-code-config.md を読む（@参照にしない — 毎セッション読み込ませない）
環境構築・ツール導入時: docs/knowledge/environment-setup-patterns.md を読む（mise 下で bare pnpm/node を呼ばない・$schema をバージョン推測で先に書かない）
