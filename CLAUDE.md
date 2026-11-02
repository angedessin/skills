# skills — personal frontend workflow skill set

Tech stack: React / TypeScript / Vitest / React Testing Library / MSW / Playwright

## 作業の進め方（大きさで 3 段階）

- **小さな作業**（typo・数行の修正・設定の変更・試作・調査だけ）: 冒頭で「小さな作業として直接進めます」と 1 行で宣言して進める。レビューと知見の保存は頼まれたときだけ
- **中くらいの作業**（1 セッションで終わるが決めることがある）: 会話の中で設計を示し、OK をもらってから実装する。決めたことを 5 行ほどに要約して会話に残し、コミットか PR の本文に写す
- **大きな作業**（複数セッションにまたがる・経緯を残したい）: `.steering/[YYYYMMDD]-[task]/` に design.md（`Status: DRAFT`）と tasklist.md を作り、レビューを求めて止まる。APPROVED になるまで実装しない。作業を終えたら tasklist.md を更新する
- 次のどれかに当たれば小さな作業にしない: 承認制のパスに触る・3 ファイル以上を変える・公開している API や型やコンポーネントの使い方を変える
- 原因の分からない不具合は、調べるところまでは進めてよい。修正の前に原因と方針を示して止まる
- 段階は Claude が決めて宣言し、迷うときだけ聞く。ユーザーはいつでも変えられる（「ちゃんと設計して」「直接やって」）
- セッションの開始時は、SessionStart hook が注入するアクティブなタスクをすべて読む。複数あればどれを再開するか聞く

## ブランチ運用（git-flow）

- 統合ブランチは develop。main へは release ブランチで出す。git-flow CLI は使わず素の git（`checkout -b`・`merge --no-ff`）で操作する
- 作業は develop から `feature/*` を切り、develop へは PR でマージする。typo・1〜2 ファイルの微修正だけは develop へ直接コミットしてよい
- 大きなタスクはマージ用の feature ブランチを切り、子ブランチから PR で集める。子ブランチは `feature/x/child` のような階層名にしない（同名ブランチと ref が衝突する）
- feature ブランチで開始したタスクは、develop へのマージ前にアーカイブまで済ませる（`.steering/` がブランチ間で分岐すると、別のセッションからタスクが見えなくなる）

## スキル管理

- 新規スキルは `templates/SKILL.template.md` をコピーして書き始める
- スキルを残す・大きく変えるときは、スキルなしより良い結果になることを `eval/` で確かめる。変えたら skill-test で回帰テストを回す
- サードパーティ製 SKILL.md 採用前に Bash コマンド・外部 URL・プロンプトインジェクションを目視確認する
- スキルの誤発動・曖昧な指示・実行不能な手順・ユーザーの訂正に気づいたら `.steering/[task]/skill-issues.md` に事象と期待を書く。改善を頼まれたら、各タスクの skill-issues.md から繰り返す事象を探し、昇格の案（機械で止める形を先に）を示して承認を待つ
- 配置先へは `.claude/` を最初に 1 回コピーし、以後は配置先で育てる（マスターとは同期しない）。マスター専用のスキル（skill-test）は配らない
- スキルは自己完結に書く: CLAUDE.md・docs/・`.steering/` が無いプロジェクトでも動くフォールバックを該当ステップに直接書く

## 自律実行の境界

- `.steering/[task]/` 配下のメモ（decisions.md・skill-issues.md・blockers.md）への追記は承認不要。気づいた時点で書く
- CLAUDE.md・SKILL.md・docs/・.claude/settings*・.claude/hooks/ への書き込みは承認制。Edit / Write ツールでだけ書く（Bash の sed・python・リダイレクトは ask ゲートを自分で迂回する）
- 判断基準: (1) git で巻き戻せる (2) 失敗に気づける (3) 影響がタスク内に閉じる — 3 つ全て満たす操作のみ承認なしで実行してよい
- 課金を伴う実行（`claude plugin eval` など）は、費用の見積もりと無料の代替を示して承認を取ってから
- `git add` / `git commit` の前に `git status --short` でステージ内容を確認する（サブエージェントが作ったファイルが混入する）
- 手作業で突合した検証項目は、その場で機械検査に入れるか「一回限り」と明記する（「確認した」は次のセッションに何も保証しない）

## 知見の保存

- 頼まれたら、次の作業でも効くものだけを選び、保存先ごとの案を示して承認を待つ。一回限りの修正・既に書いてあることは残さない
- 保存先: 短い行動ルール → このファイル／経験・パターン → `docs/knowledge/[topic].md`（必要時に読む。`@` で常時読み込むのは常に要るものだけ）／タスクの決定 → `.steering/[task]/decisions.md`

## 環境

- mise 管理下では Bash から素の pnpm / node を呼ばず、`mise exec --` を使う
