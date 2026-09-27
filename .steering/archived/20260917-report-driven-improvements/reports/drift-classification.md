# 配置先ドリフトの分類（20260921・読み取り専用で調査。配置先には一切書き込んでいない）

`python3 scripts/check_deploy_drift.py` の 14 件（配置先 2 件）を、実差分を読んで分類した。
**本タスクの完了条件は分類と提示まで。再コピー・取り込みは承認後に別途行う。**

凡例: **意図** = 意図的なローカル適応 / **先行** = マスター先行（再コピーで解消）/ **還流** = 配置先のほうが良く、マスターへ取り込む候補 / **記録なし** = source-commit が無い

## 配置先 1: `skill-test`（マスター自身の検証用）— 2 件

| # | 対象 | 検出 | 分類 | 根拠 |
|---|---|---|---|---|
| 1 | frontend-code-review | (b) マスター先行 | **先行** | 直接編集は無く、マスター側の 2 コミット（`71a8071` PR #13 must-fix・`b09b247` diff トリアージ漏れ）だけが未反映（+24/-5 行）。安全に再コピーできる |
| 2 | hooks | (e) guard-gated-write.sh の差分 13 行 / (d) guard-gated-delete.sh 未配置 | **先行** | 配置後にマスターで増えた hook・改訂された hook。同送対象なのに欠けている（配置漏れ）。同送を再実行すれば解消 |

## 配置先 2: `hospital-search-mock`（Next.js の実プロジェクト）— 12 件

このプロジェクトは version `2.0` 系でスキルを**大きく自前で作り替えている**。全面再コピーすると適応が消える。

| # | 対象 | 検出 | 分類 | 根拠（差分の要点） |
|---|---|---|---|---|
| 3 | debug | (a) 直接編集 | **意図** | 配置していない `tdd` / `pr-feedback` への参照を外し、「テスト基盤が無ければ再現手順の明文化に留める」へ縮退 |
| 4 | design-doc | (a) 直接編集 | **意図** | 会話内設計への縮退分岐を廃止し「常に `.steering/` を作る」へ。マスターとは逆の設計判断（v2.0） |
| 5 | design-premortem | (c) 記録なし | **意図（縮退）+ 先行** | 手コピー。配置していない `rule-audit` / `impl-tournament` への参照を外しただけの旧版。マスター側の `premortem-attacker` 参照は未反映 |
| 6 | frontend-code-review | (a) 直接編集 + (b) 先行 | **意図** + 先行 | v2.0 で「固定モードを廃止し diff 分類で必要なレビューだけを選ぶ」へ大改訂。マスターの `b09b247` 1 件は**再コピーではなく手動マージ**が要る |
| 7 | impl-from-design | (a) 直接編集 | **意図** + **還流** | モード選択を廃した単一フロー。`UNKNOWN` の明示化と、`guard-spike-outbound` hook による SPIKE 外向き操作の機械的 deny の記述は還流の材料 |
| 8 | impl-review | (a) 直接編集 | **意図** + **還流** | Next.js 向けに軸を書き換え。「存在しないスキルへ委譲しない」の縮退記述はマスターにも有益 |
| 9 | next-dev-loop | (c) 記録なし | **配置先固有スキル** | 下の「還流可否の判断材料」参照 |
| 10 | review-a11y | (a) 直接編集 | **意図** | `next-dev-loop` での実ブラウザ確認を組み込み、担当先を `impl-review` に付け替え（配置していない `review-ui` / `review-correctness` の代替） |
| 11 | review-performance | (a) 直接編集 | **還流** | 「High / Medium の指摘には実測または具体的な実行経路を要求する」「`useMemo` の不使用を一律に問題視しない」は、根拠のない性能推測を減らす汎用的な改善 |
| 12 | review-security | (a) 直接編集 | **還流** | lockfile から audit コマンドを判別する表（bare の `pnpm` を呼ばない規律と整合）、null / 型注釈の境界の明確化（外部入力が危険な処理へ到達する経路があるときだけ指摘）。マスターは `pnpm audit` を直書き |
| 13 | steering | (a) 直接編集 | **意図** | フラグ類を持たない「小さな作業台」へ簡素化（v2.0） |
| 14 | hooks | (e) 内容差分 4 件（guard-gated-write / guard-gated-delete / post-edit-lint / session-start-check） | **還流（要精査）** | 配置先のほうが新しい設計に見える: `lib/gated-paths.sh` にパス正本を一本化、`tool_input.command` の構造抽出、lint → format 順。加えて**マスターに無い hook が 2 本**（`guard-draft-implementation.sh`・`guard-spike-outbound.sh`）。承認ゲート（DRAFT 実装禁止・SPIKE 外向き禁止）を機械で強制する内容 |

注意: hooks の差分の向きは、コード精読と git 履歴で確かめてから取り込むこと（マスター側 README は `guard-gated-delete` を python3 の構造抽出と記載しており、どちらが新しいかを差分だけでは断定できない）。

## `next-dev-loop` の還流可否（判断材料）

- 183 行の単一ファイル（references なし）。Next.js の実行時挙動を確認するスキルで、`/_next/mcp`（Next.js 側の視点）と `agent-browser`（ブラウザ側の視点）を併用する。前提は `next dev` の起動
- description は英語。プロジェクト固有語（病院・患者・社名）は 0 件ヒット — 汎用的に書かれている
- 論点: マスターは React / TypeScript 汎用で、Next.js 前提のスキルは配布可否の分類（`docs/starter-kit.md` の選定表）が要る。取り込むなら「Next.js 利用プロジェクト向けの任意スキル」としての新分類になる。外部依存（`agent-browser`・`/_next/mcp`）は `security-audit` の採用前チェック対象
- 還流するなら `review-a11y` の `next-dev-loop` 連携（#10）も同時に扱う必要がある（連携先が無い環境で死んだ参照になる）

## 提示する方針（実行は承認後）

1. **skill-test**: 再コピー + hooks 同送の再実行で解消できる（#1・#2）。`skill-harvest` → 承認 → 実行の通常手順
2. **hospital-search-mock**: **全面再コピーはしない**（v2.0 の適応が消える）。次の 3 つに分ける
   - 「意図的なローカル適応」（#3・#4・#6・#10・#13）は `deployments.md` に理由つきで記録し、以後のドリフト報告から区別できるようにする
   - **還流**（#7・#8・#11・#12・#14）はマスターへ個別に取り込む。優先度: hooks の 2 本（機械強制はスキル本文の改善より効きが確実）> review-security の lockfile 表 > review-performance の実測要求
   - #6 の `b09b247` は手動マージ、#5 は次回の再配置時に整理
3. `next-dev-loop` は還流するかをまず決める（上の論点）。決まるまで #10 の連携は据え置き
