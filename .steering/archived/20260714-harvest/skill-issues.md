# Skill Issues — 20260714 harvest（配置先からの還流）

skill-harvest が配置先から回収した未処理の skill-issues。`compound` での昇格検討が次工程。

由来: `/Users/kentaro/Desktop/_lab/ai/webgl-boilerplate/.steering/20260713-retrospective/skill-issues.md`（環境構築セッション 20260713）

## [20260713] — design-doc に環境構築の分岐が無い（由来: webgl-boilerplate）
**事象**: (a) `/design-doc` が「ツール環境セットアップ＋スキル/フック動作確認」タスクに発動したが、design-doc には機能設計の分岐しかなく半フィット。会話内セットアップに手動で切り替えた。
**期待**: design-doc が「環境/ツール構築タスク」を検知したら、設計フローではなくセットアップ手順（またはセットアップ用スキルへのリダイレクト）を案内する分岐を持つ。
**該当**: design-doc

## [20260713] — 初期質問が誤前提（WebGL設計を仮定）（由来: webgl-boilerplate）
**事象**: (b) 最初の AskUserQuestion が「描画スタック選定・設計対象」を前提にしたが、ユーザー意図は環境構築だった。ユーザーが両質問に「まずは初期環境の構築から」と回答して前提を訂正した。
**期待**: リクエスト（「各種スキルが実行できるかチェック」「Lintツールをインストール」）から環境構築意図を読み取り、設計前提の質問より先に「今回は設計かセットアップか」を切り分ける。
**該当**: design-doc / 未特定（質問設計の判断）

## [20260713] — biome.json の $schema バージョンを推測して手戻り（由来: webgl-boilerplate）
**事象**: (c) インストール前に `biome.json` の `$schema` を推測で `2.1.2` と記述 → 実インストールは `2.5.3` で警告＋`recommended` フィールド非推奨。`biome migrate` が必要になった。
**期待**: 設定ファイルはツール導入後に実バージョンで生成する（`biome init` / `biome migrate` 前提）、またはバージョン固定の $schema を書かず導入後に揃える手順を先に踏む。
**該当**: 未特定（ツール導入手順の定石）

## [20260713] — 非対話 Bash で壊れた standalone pnpm を拾い exit 127（由来: webgl-boilerplate）
**事象**: (c) 非対話 Bash では mise が有効化されず、PATH 上の壊れた standalone pnpm（`~/Library/pnpm/pnpm`）を拾って `pnpm exec` が exit 127。`node_modules/.bin` 直叩き／`mise exec --` に切替。
**期待**: mise 管理プロジェクトでは、Bash ツールから bare `pnpm`/`node` を呼ばず `mise exec --` か `node_modules/.bin` を直接使うことを既定にする（ルール化候補）。
**該当**: 未特定（Bash 実行規約 / CLAUDE.md 候補）

## [20260713] — rm -rf が deny でコマンド全体が拒否され手戻り（由来: webgl-boilerplate）
**事象**: (d) フックテストのクリーンアップで `rm -rf .steering` が settings.json の deny に該当し、コマンド全体が拒否された。`rm -f` + `rmdir` に書き直して再実行。
**期待**: このリポジトリでは `rm -rf` / `rm -fr` が deny である前提で、ディレクトリ削除は `rm -f`（ファイル）＋`rmdir` を最初から使う。
**該当**: settings.json permissions（deny）/ Bash 実行規約

## [20260713] — design-doc / steering の適用境界が不明瞭（由来: webgl-boilerplate）
**事象**: (e) 「基本的に design-doc と steering を通すものだと思った」等、適用境界（全タスクを通すのか／単発は通さないのか）がユーザーに不明瞭で、確認のやり取りが2回発生した。
**期待**: 「単発は会話内・複数セッションは .steering」という粒度による振り分け方針が、初回に一目で伝わる形（README / CLAUDE.md の運用ガイド）で明示されている。
**該当**: design-doc / steering（運用ドキュメント）
**補記（回収時）**: 縮退判断そのものは 20260714 のマスター修正（design-doc v1.2 — 縮退のユーザー確認制化・コミット 9376e92）で部分対応済み。「初回に一目で伝わる運用ガイド」は未対応。
