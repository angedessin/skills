# タスクリスト: 引き継ぎ文書の一元化とバックログの可視化

design.md: `.steering/20260727-handover-consolidation/design.md`
一次情報: `.tmp/master-feedback-20260726.md`（FB 指摘 2〜5）/ `.steering/BACKLOG.md` の 2 節

## 0. 変更対象の確定（実装の最初に行う）

- [x] 虚偽記述の洗い出し → `.tmp/20260726-handover-prompt.md:9` のみ（**削除すれば自動的に解消**）
- [x] スモークテストの洗い出し → HANDOVER 3 項目 / MANIFEST 4 項目（`.claude/hooks/` 編集 → ask を含む）/ MIGRATION-GUIDE 3 項目。**矛盾した「install が拒否されない」項目は 3 文書のどこにも無い**（バグは `.tmp` 版だけだった）
- [x] 対配置警告 → MIGRATION-GUIDE のつまずきどころに 1 件のみ。HANDOVER / MANIFEST は 0 件
- [x] worktree → main `5b9b9eb` + export/company `f46954a` の 2 つ
- [x] design.md を先に更新 → **1 件追加**: `MIGRATION-GUIDE.md:125` に前日自分が混入させたマスター固有語（`deploy_skills.py`）があり、配置先の読み手には解読できない

## 1. Phase 1 — `HANDOVER.md` への一元化（**export ブランチの作業**）

> **順序を守る**: `.tmp` を削除する前に `HANDOVER.md` へ移し終える。消してから移すと 20260726 に
> 直した指摘 1 の内容が失われる。

- [x] 手順 2 に **session-start / session-stop の対配置警告**を追加（`:56-58`）
- [x] 手順 3 に **`ask` を外さない**（1/4 の頻度で再現した実測を根拠として明記）を追加
- [x] 手順 3 に **ask と `guard-gated-write.sh` は対で維持** / **install deny を緩めない**を追加
- [x] 手順 9 に **開発フロー確認**を追加（install 拒否は仕様・不具合として報告しない・deny を外さない）
- [x] 手順 9 に **`.claude/hooks/` 編集 → ask** を追加 + **ask の判定は人間に委ねる**も追加
- [x] 手順一覧の前に **「保証していないこと」節**を新設（4 項目）+ 進め方の規律に「手順 8 の停止を省略しない」を追加
- [x] **マスター固有語の混入を 9 語で grep → `HANDOVER.md` は 0 件**
  - [x] 洗い出しで見つけた `MIGRATION-GUIDE.md:125` の `deploy_skills.py`（前日自分が混入）を「別の配布経路」に一般化
  - [x] `MANIFEST.md` の 2 件（`passthrough_check.py` / `validate_skills.py`）は**対象外と判断** — マスター側の運用節・非同梱の理由説明であり、今回の混入ではない（`decisions.md` に記録）
- [x] 虚偽記述の残存なしを確認（`.tmp` 版の削除で解消）
- [x] `.tmp/20260726-handover-spec.md` を削除（scratchpad にバックアップを退避）
- [x] `.tmp/20260726-handover-prompt.md` を削除（同上）
- [x] `HANDOVER.md` が単独で完結していることを確認（6248 → **9879 bytes**。design の見積「9KB 程度」の範囲内）
- [x] 静的検査 → export 10/10 PASS・停止契約 7/1/2 不変・settings.example.json 妥当

## 2. Phase 2 — 契約 (i) の追加（**main の作業**）

- [x] `contract_i(require_export)` を追加（契約 (g) と同型・SKIP を返せる）。あわせて `main()` を `export_contracts` リスト形式にリファクタして重複を削減
- [x] (i-2) 同梱スキルが 3 文書のどこかに名前で登場する（**⊆ ではなく「実体の全スキルが記載されている」向き** — 文書は非同梱スキルにも言及するため等価にできない）
- [x] (i-3) 文書が参照する `*.sh` が配布物かマスターに実在する（**マスターにあれば「意図的に同送しない理由の説明」として正当**なので実体との等価にはしない）
- [x] (i-1) 員数を **「実体の数が各文書に少なくとも 1 回現れる」**に変更 — **設計の未解決の論点 1 が実測で顕在化**（`MANIFEST` の「スキル数の主張」に履歴節由来の `8` `9` が混ざり、`hook 数` には番号リスト由来の `1`〜`4` が混ざった）。この向きなら誤検知ゼロで「増減して直し忘れ」を検出できる
- [x] 対象不在は **SKIP**（`--require-export` で FAIL に昇格）→ 実測で確認
- [x] `export_contracts` リストから呼ぶ（(g) と共通化）
- [x] docstring の契約一覧に (i) を追記（員数の判定方向とその理由も明記）
- [x] 実測 (1) 3 文書から `rule-audit` の記載を消す → **FAIL**
- [x] 実測 (2) `session-stopped.sh`（実在しない）を書く → **FAIL**
- [x] 実測 (3) `HANDOVER` の 10 スキル → 9 → **FAIL** / (4) `MIGRATION-GUIDE` の 5 本 → 4 → **FAIL** / (5) 無改変は **PASS**
- [x] 実測 (6) worktree 不在のみ → **SKIP・exit 0** / (7) worktree 不在 + 別契約違反 → **exit 1**（握りつぶさない）
- [x] `README.md` のインフラ節を「9 契約」に更新し (h)(i) を追加（員数の判定方向の理由も）
- [x] **9/9 PASS**。既定の呼び出し経路 3 つ（直接 / `npm run validate:assets` / hook 経由）でも確認

## 3. Phase 3 — バックログの注入（**main + export の両方**）

- [x] `.claude/hooks/session-start-check.sh` に BACKLOG 分岐を追加
- [x] 文言を設計どおりに実装
- [x] **「未着手 N 件」と書かない**（理由をコメントに明記）
- [x] 依存を増やさない（`grep -c`。0 件で exit 1 を返す罠は `[ -z ]` で処理）
- [x] export 側にも反映 → **実際に契約 (g) が片側修正を検出して PostToolUse hook が編集を差し戻した**（設計どおりの挙動）。非同梱スキル名を含まないため変換不要でバイト一致
- [x] `README.md` の SessionStart Hook の説明に BACKLOG 注入と理由を追記
- [x] フィクスチャ (1) BACKLOG あり → 1 行注入 ✓
- [x] フィクスチャ (2) BACKLOG なし → 注入なし（アクティブタスクは出る）✓
- [x] フィクスチャ (3) `.steering/` なし → exit 0・無出力 ✓
- [x] フィクスチャ (4) 既存 3 分岐すべて健全 ✓
- [x] フィクスチャ (5) JSON 妥当 ✓ + 境界（0 節・空ファイル）も確認
  - [x] **テスト側のバグを 1 件自己検出**: `echo "$out"` がバックスラッシュエスケープを展開して JSON を壊し、hook の欠陥に見えた。`printf '%s'` で解消。**hook は正常**（ハーネスの誤りをスクリプトの欠陥と誤認しかけた）
- [x] `bash -n` 全 hook OK（master / export 両方）
- [x] **契約 (g) PASS**（反映後にバイト一致を確認）

## 4. Phase 4 — BACKLOG の更新（**main の作業**）

- [x] 解消済みの 2 節を**削除**した（当初は「畳んで記録を残す」形にしたが、**自分がこのファイルの冒頭に書いた運用ルール「完了したら該当節を削除する」に反しており**、かつ節数が減らず注入が「着手前の候補」を過大に見せていた）。記録はアーカイブ済みタスクに残る
- [x] 残す 3 節の番号を 1 / 2 / 3 に詰め、運用節に「履歴を積まない」理由を追記
- [x] 注入が **3 節**を出すことを確認（4 → 3 に正しく追随）

## 5. レビュー

- [x] 静的検査 → 29/29・export 10/10・portability 0・template PASS・停止契約 7/1/2 不変・契約 9/9・配置 dry-run 両経路 exit 0・`validate_skills.py` の既存 6 経路すべて exit 0
- [x] ~~汎用 subagent でレビュー~~ → **ユーザー判断で省略**。前回 High 3 件の原因（契約の組み合わせ・既定の呼び出し経路の未測定）は今回明示的に測った。**残るリスクは `main()` のリファクタが未レビューであること**（(g) の 3 状態が通ることは確認済み）
- [x] ~~指摘のトリアージ~~ — レビュー省略のため該当なし
- [x] ~~must-fix~~ — 同上
- [x] **「単体で効く」を「全体で効く」と混同しない** → 組み合わせ（worktree 不在 + 別契約違反 → exit 1）と既定の呼び出し経路 3 つ（直接 / npm / hook 経由）を実測済み

## 6. デプロイ・知見保存

- [x] main へコミット `bf7a719`（Phase 2〜4 は相互依存のため 1 コミット）
- [x] `git status --short` でステージ内容を確認してからコミット（両ブランチとも）
- [x] export 側を先にコミット `24190ad` してから main を merge `326c389`（stash を使わない順序）
- [x] **push 完了**（main `bf7a719` / export/company `326c389`）
- [x] `knowledge-capture` — **2 件書き込み**（`skill-design-patterns.md` の検出ツールの規律に #8「文書と実体の突合で等価を既定にしない」+ bash 注記を 2 項目に拡張）。**2 件は見送り**: 契約 (g) の実時間検出は既存規律 #3 と重複 / 「自分の運用ルールに自分で違反」は行動パターンなので compound へ
- [x] `compound` — **1 件昇格**（契約 (i-4): 配置先が読む文書にマスター専用スクリプト名が混入しない。検出リストは動的生成）。**効果検証でルール 3 が働いたことを確認、同時に同じ型の違反を自分がまた作っていたことも検出**。1 件は昇格せず（詳細は `codify-log.md`）
- [x] `steering` の archive モードでこのタスクをアーカイブする

Archived: 20260727
