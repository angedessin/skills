# 設計: report-driven-fixes

Created: 20260730
Status: **APPROVED**
Approved: 20260730

## 目的

2026-07-30 の観察レポート（個人摩擦・docs↔実装乖離・company 凍結）に基づき、**宣言と実装の矛盾**と**生きた company 負債**を先に閉じる。説明文だけ増やす修正はせず、スキル手順・ドキュメントの現行事実・機械検査のどれかを動かす。小さくマージ可能なパッケージ単位で直す。

## スコープ

### 対象

| ID | 内容 |
|---|---|
| **P0** | `blockers.md` ↔ `knowledge-capture` 配線（入力・決定木・取捨） |
| **P1a** | master-only 正本クラスタ（員数・置き場所の stale fact） |
| **P1b** | `.codify-needed` producer 対クラスタ（二重化済みを現行形に） |
| **P1c** | jq / フェイル方針クラスタ（guard・session-start・lint の誤記） |
| **E1** | company Frozen handoff — 生きた機械の削除＋文書の現況義務解除 |

### 対象外

- **export/company への追随・防御パリティ義務の復活・持ち出し Gate を受け入れ条件にすること**
- export/company **worktree / ブランチ実体の削除**（E2。ローカル任意・別判断）
- ADR・`.steering/archived/`・一般化した規律（対配置・permissions 分離・提案還元・停止契約の硬さ）の抹消
- P1d（7軸用語 / @参照残骸）、P2（design 契約/付録分離・SPIKE レーン）
- capture 粒度の再設計、ナレッジ鮮度の機械化、配置1件実走、passthrough シナリオ拡充
- プラグイン化 / 自動同期 / allowed-tools / 統計トリガー eval / knowledge の @ 常時ロード復活
- capture を「完了時のみ」に単純化、承認ゲート全撤廃
- rm/mv ポリシー（`.steering/BACKLOG.md` 既存節のまま）

## 制約

- このリポジトリはスキル／hooks／docs のマスター。フロントエンドアプリの実装ではない
- CLAUDE.md・SKILL.md・docs/ への書き込みは承認制（実装セッションでも適用）
- **片側修正禁止** — 下表のクラスタ単位で対になる参照を同コミットで直す
- レポートと実装が食い違う場合は**実装を正**とし、レポート側の誤りは注記する（本設計時点の突合では blockers 未配線・master-only 4本・guard/session-start の jq 非依存は実装と一致）
- company 関連の受け入れ条件に「持ち出しでも通る」を入れない

## 完了条件

- [x] P0: `knowledge-capture` が `blockers.md` を入力に含め、決定木で取捨し、ドラフト提示まで到達する手順が本文にある。CLAUDE.md / README / ADR 20260612 の「取捨は knowledge-capture」宣言と矛盾しない
- [x] P1a: `docs/knowledge/skill-design-patterns.md` の master-only 記述が `MASTER_ONLY` 4本（`adr` / `skill-deploy` / `skill-harvest` / `skill-test`）かつ本体パス `.claude/skills/` と一致。ツール（`scripts/` 等）との用語混線を解消
- [x] P1b: producer が FCR + knowledge-capture の二重である旨が `skill-design-patterns` / `docs/starter-kit.md` / `README.md` で現行形として一致
- [x] P1c: jq 依存・フェイル方針の記述が、実 hook（`guard-env-read` / `session-start-check` / `post-edit-lint` は jq 未使用。jq は `stop-typecheck` / `validate-skill-edit`）と一致
- [x] E1: `scripts/check_export_stopcontract.py` 削除、`package.json` の `check:export` 削除、`check_asset_consistency.py` から契約 (g)(i)・`EXPORT_INTENTIONAL_OMISSIONS`・`--require-export` および持ち出し発見経路を除去。README から差分ガードを外し、`skill-test` の持ち出し検査節は削除
- [x] E1: `deployments.example.md` に Frozen handoff（更新しない）を明記。`claude-code-config` の「防御変更時に配布物確認」現況義務を過去形の教訓＋一般法則（次の**個人**配置先）に書き換え
- [x] `npm run validate:assets` が PASS（契約数は (g)(i) 除外後の集合）
- [x] 対象クラスタについて「説明文だけ」の差分が無い（手順または検査が動いている）

## アプローチ

パッケージは依存の薄い順にマージ可能な単位で進める: **P0 → P1a/b/c（docs クラスタはまとめても可）→ E1（機械削除が最後でも可だが、docs の export 現況義務は E1 と同梱）**。E1 でスクリプトを消すときは参照側（README・skill-test・asset 契約・npm script）を同コミットで落とす。knowledge の「持ち出しから得た一般法則」節は削除せず、固有名詞の現況義務だけを過去形化する。

## 主要コンポーネント

| コンポーネント | 場所 | 変更後の記述・契約（原本なしで判定できる粒度） |
|---------------|------|------|
| knowledge-capture | `.claude/skills/knowledge-capture/SKILL.md` | Step 1 の find / 入力源に `blockers.md` を追加。Step 2 決定木に「未解決 blockers → 取捨（BACKLOG 移設案 / 知見化 / 破棄案）」分岐。空ファイルはスキップ。出力は他知見と同様ドラフト承認制 |
| skill-design-patterns | `docs/knowledge/skill-design-patterns.md` | master-only = 4 スキル名・置き場 `.claude/skills/`。ルート直下は**ツール**用と明記。codify producer 節は「二重化済み（現行）」の過去形＋現行要約。`check_export_stopcontract` 言及は歴史例として残し「削除済み・現行義務ではない」を添えるか、ツール名を一般化 |
| starter-kit | `docs/starter-kit.md` | compound 自動起動の書く側 = FCR **および** knowledge-capture。session-start の「jq 不在フェイルオープン」を削除（jq 非依存） |
| README | `README.md` | `check_export_stopcontract` / `check:export` をツリーとインフラ節から削除。契約突合の員数を (g)(i) 除外後に更新。codify producer 二重化に言及。guard の「jq 未導入でフェイルクローズ」を実挙動（jq 非依存・ask）に修正。session-start の jq 記述を削除 |
| claude-code-config | `docs/knowledge/claude-code-config.md` | L240 付近: lint/guard の jq・フェイル方針を実装に合わせる。「配布物にも同じ防御」節は 20260726 判例の過去形とし、**現行義務は deployments 登録の個人配置先**（あれば）への一般確認に限定。company 名の現況 Gate は書かない |
| deployments | `deployments.md`（gitignore・ローカル）/ `deployments.example.md`（追跡） | Frozen handoff 注記。example が正本の文言 |
| check_asset_consistency | `scripts/check_asset_consistency.py` | 契約 (g)(i)・`EXPORT_*`・`--require-export`・export worktree 発見を削除。残契約 (a)(b)(c)(d)(e)(f)(h) が緑 |
| check_export_stopcontract | `scripts/check_export_stopcontract.py` | **ファイル削除** |
| package.json | `package.json` | `check:export` スクリプト削除。`validate:assets` は維持 |
| skill-test | `.claude/skills/skill-test/SKILL.md` | 「持ち出しセットの検査」節を削除または「Frozen・対象外」に置換。`check_export_stopcontract` への依存を除去 |

### 実装前の対象洗い出し（tasklist 先頭で実行）

変更対象語で全文検索し、表の漏れを潰す: `blockers` / `check_export_stopcontract` / `check:export` / `EXPORT_INTENTIONAL` / `require-export` / `契約 (g)` / `契約 (i)` / `master-only` / `.codify-needed` / `フェイルクローズ` / `guard-env-read` / `持ち出し` / `export/company`。

## データフロー

```
P0: blockers.md（任意・追記承認不要）
      → knowledge-capture Step1 入力
      → Step2 取捨（BACKLOG案 / knowledge案 / 破棄案）
      → Step4 ドラフト承認 → 書き込み

P1: 実装（scripts定数・hooks）を正
      → knowledge / starter-kit / README を現行形に同期

E1: Frozen 決定
      → 生きた検査・npm・README・skill-test から除去
      → deployments / knowledge は過去形・一般法則のみ残す
      → export/company worktree は未タッチ（参照しない）
```

## 影響範囲

- システム / 外部連携: なし（リモート・会社フォークへ操作しない）
- データ: `.steering/` メモと docs / scripts のみ
- 他チーム / 利用者: 個人マスター利用者。配置先への再コピーは今回の必須ではない（knowledge-capture は配布可のため、配布時に効く）
- リグレッション懸念:
  - `npm run check:export` を手動運用している場合は消える（意図的）
  - `validate:assets` の契約数・出力ラベルが変わる
  - skill-test の持ち出し経路が使えなくなる（E1 の意図）
  - knowledge の歴史節を消しすぎると一般法則まで失う → **過去形化に留め削除しすぎない**

## テスト方針

- Unit / スクリプト: `npm run validate:assets`（必須）。E1 後に `check_export_stopcontract.py` が無いこと、`package.json` に `check:export` が無いことを確認
- 静的: 必要なら `npm run validate`（スキル本文変更時）
- 手順の人手確認（一回限りと明記しない — 可能な範囲で grep ベースの受け入れチェックを tasklist に書く）:
  - `rg blockers .claude/skills/knowledge-capture/SKILL.md` がヒット
  - `rg check_export_stopcontract` が scripts 実体を指さない（archived のみ可）
- E2E / passthrough: 今回対象外

## 未解決の論点

- [x] E1 の `check_export_stopcontract.py` 固有名 — **固有名＋削除済み注記**（実装時確定）
- [x] P0 の blockers 自動移設はしない（ドラフトのみ）— Phase 1.5 確定
- [x] ブランチ戦略 — git-flow `feature/20260730-report-driven-fixes` 1本・クラスタ単位コミット・PR 1本（ユーザー指示 20260730）

## 検討した代替案

| 代替案 | 却下理由 |
|--------|----------|
| company を設計入力から外すだけで機械は残す（文書凍結のみ） | 生きた SKIP 契約・npm・README 第一級記載が認知税と片側修正温床のまま残る（ユーザー判断: 負債） |
| export worktree も削除（E2） | ローカル環境操作が混ざる。マスターの生きた義務除去とは別判断 |
| P2（design 分離 / SPIKE）を同梱 | ワークフロー契約変更が混ざりレビュー軸が広がる（Phase 1.5 で G 採択） |
| P1d（7軸 / @残骸）を同梱 | 被害が小さく後続で足りる |
| capture「完了時のみ」化 | 偽陰性増。レポート明示のやらなくてよい縮退 |
| 説明文だけの「Frozen です」追記 | 契約・手順・機械が動かない。固定制約違反 |

## 調査結果

一次情報: `.tmp/20260730-reports-INDEX.md` および同日 4 レポート。実装突合（20260730）:

- `knowledge-capture` に `blockers` 文字列なし（穴確認）
- `deploy_skills.MASTER_ONLY` = `{adr, skill-deploy, skill-harvest, skill-test}`（4本）
- `guard-env-read.sh` / `session-start-check.sh` / `post-edit-lint.sh` に jq なし。jq 使用は `stop-typecheck.sh` / `validate-skill-edit.sh`
- `git worktree`: main + `skills-export-company`（export/company）。E1 では触らない
- `package.json`: `check:export` → `check_export_stopcontract.py`
- アクティブ `.steering/` タスクは本タスク作成時点で無し（archived + BACKLOG のみ）

## Phase 1.5 で確定した決定

| # | 決定 | 選択 |
|---|---|---|
| 1 | 今回スコープ | P0 + P1a/b/c + E1。P1d/P2/後続はバックログ |
| 2 | company 削除境界 | **E1**（機械削除＋文書凍結。履歴・一般法則・worktree は残す） |
| 3 | 残候補 | **G**（上記のみ） |
