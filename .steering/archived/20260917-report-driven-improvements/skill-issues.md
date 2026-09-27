# スキル課題: report-driven-improvements

## [20260921] — frontend-code-review（および agent 定義を参照する全ディスパッチ箇所）

**事象**: `.claude/agents/review-impl.md` などの定義ファイルは存在するのに、作成直後で subagent 種別として未登録だったため（数ターン後に登録された。再起動は不要）、
`Agent type 'review-impl' not found` でディスパッチが失敗した（利用可能な種別に含まれない）。本文の 2 段フォールバックは
「定義ファイルが**存在するか**」で分岐する書き方のため、存在するのに使えないケースを扱えていない。
**期待**: 「定義があれば使う。指定して種別が見つからず失敗したら、汎用エージェントへ落とす」まで書く。導入直後（セッション再起動前）でも止まらない。
**影響範囲**: `frontend-code-review` / `impl-from-design`（codebase-explorer）/ `design-premortem`（premortem-attacker）/ `impl-tournament` / `compound`（knowledge-scanner）の 5 か所。
**対応**: 20260921 に本文へ 1 文ずつ足した（5 か所）。

## [20260921] — frontend-code-review のスコープ節

**事象**: 対象が Python・Markdown・YAML 中心の差分だと、各エージェントのスコープ（`.ts` / `.tsx`）に合致するファイルが 0 件になる。
本文は「ゼロのエージェントはディスパッチしない」（例外は impl-agent の契約成果物のみ）と書くため、correctness / security は本文どおりでは起動しない。
今回は「スコープの読み替え」をディスパッチプロンプトに明記して起動した（本文の「どのエージェントのスコープにも合致しないファイル」の規定に近い運用）。
**期待**: スクリプト・設定・CI 中心の差分（マスターリポジトリの日常）でどう扱うかを明示する。読み替えの書き方のテンプレートがあると毎回の裁量補完が減る。

**対応（20260927・compound）**: スコープ外ファイルは観点が当たるエージェントすべて（impl / correctness / security）に割り当てる形に本文を変更した。
