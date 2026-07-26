# レビュー結果: 配置機構の整合回復と出荷前検証

Status: **RESOLVED**
Date: 20260726
範囲: `git diff 04b912c..HEAD`（main の実装 2 コミット）
方式: 汎用 subagent 1 体（`frontend-code-review` は React/TS 前提の 7 軸なので、Python / bash / Markdown の今回の差分には噛み合わないためユーザー判断で代替）

## 結果: High 3 / Medium 3 / Low 3 — **High と Medium を全て解消**

レビュアーは全指摘を**実行して再現**したうえで報告し、こちらでも 3 件の High を独立に裏取りした。

## High（すべて「検査が偽グリーンを出す」型 = このスクリプトの存在理由に反する欠陥）

### H1: `contract_f` の exit 2 が他の契約の FAIL を握りつぶし、hook が恒久的に無音になる

- **裏取り**: 持ち出し worktree を不在にし未分類 hook を 1 本足した状態で実行 → `FAIL (b)` `FAIL (c)` を印字したうえで **exit 2**。`validate-skill-edit.sh` は `rc≠1` を exit 0 に変換するため差し戻しが起きない
- **失敗シナリオ**: 別マシンにクローンした環境（worktree 無し）では常に exit 2。assets hook は恒久的に無音、`npm run validate:assets` も緑を出せない。その環境で hook を足して分類を忘れても誰も止めない
- **修正**: 対象不在を `die()` から **SKIP** に降格し、終了コードは「FAIL が 1 件でもあれば 1」を優先。exit 2 は走査の前提が崩れた場合だけに限定。必須にしたい場面用に `--require-export` を追加。hook 側も rc=2 を無言で捨てず差し戻す
- **実測（修正後）**: worktree 不在 + 違反あり → **exit 1**（FAIL が見える）／ worktree 不在のみ → **exit 0・SKIP 1 件**／ `permissions` 欠落状態の README 編集 → **hook が exit 2 で差し戻す**

### H2: 「必ず列挙する」と宣言した警告が既定出力に出ず、過去の実害が 7/7 PASS で通る

- **裏取り**: 既定実行での警告件数 **0**。`package.json` の `validate:assets` に `--verbose` が無い。本文コメントは「人が確認できるよう必ず列挙する」と書いてあり、**コメントが嘘になっていた**
- **失敗シナリオ**: レビュアーが 20260726 の実害（配布物から `guard-gated-write.sh` と登録を削除）を再現 → 出力は「6/6 PASS」のみ、警告ゼロ。**契約 (g) が存在する理由そのものが既定経路で検出されない**
- **修正**: WARN を `--verbose` の有無に関わらず無条件に印字。さらに `EXPORT_INTENTIONAL_OMISSIONS` を定数として新設し、**宣言の無い欠落は FAIL** にした（`MASTER_ONLY_HOOKS` と同じ「分類を強制する」型に揃えた）
- **実測（修正後）**: 20260726 の実害の再現 → **FAIL「master の同送 hook が配布物に無い: guard-gated-write.sh」**／通常実行で `WARN company: stop-typecheck.sh は意図的に同送しない（宣言あり）` が毎回出る

### H3: マスター自身の `settings.json` の hooks 登録が突合対象外

- **裏取り**: `registered_hooks()` という helper があるのに、export の `settings.example.json` にしか適用されていなかった（281 行目のみ）。マスターの登録を削っても全契約 PASS
- **失敗シナリオ**: hook を `hooks/` に置き、`expected_hooks()` にも README にも入れたが `settings.json` への登録を忘れる → **マスターで一度も発火しない**のに全契約 PASS。まさにこのスクリプトが狙っている型
- **自省**: この確認は Phase 4 で**手作業で 1 回やって「なし ✓」と報告していた**。契約として encode しなかったため、次回以降は誰も見ない状態だった。「手で確認した」を「機械化した」と混同していた
- **修正**: 契約 (f) として追加（双方向）。既存の (f) は (g) にリネーム
- **実測（修正後）**: `guard-gated-write` の PreToolUse 登録だけ削除 → **FAIL「ファイルがあるのに settings.json に登録が無い」**

## Medium（すべて解消）

### M1: `.claude/settings.json` の編集が assets モードに乗らない

契約 (e) の producer なのに hook が起動しなかった。`case` に追加（`check_asset_consistency.py` 自身も追加して自己整合を取った）。**実測**: 違反状態で settings.json を編集 → exit 2 で差し戻し。

### M2: `code_lines()` の `#` 落としが heredoc の中身にも効く

hook は heredoc で JSON を出力する（`guard-env-read.sh` / `guard-gated-write.sh` に実在）。現状の heredoc 本文は JSON なので実害は出ていなかったが、配布物の heredoc に `#` 始まりの行が混入すると **hook の標準出力が JSON として解釈されなくなる**のに契約が緑になる。shebang（`#!/bin/bash` → `#!/bin/zsh`）も同様に見逃していた。

**修正**: heredoc 終端までは `#` 落としを行わない簡易ステートマシンにし、shebang（1 行目）は常に比較対象に含める。**実測**: heredoc 内への `#` 行注入 → FAIL / shebang 書き換え → FAIL / 無改変のコピー → PASS。

### M3: `*/.claude/hooks/*.sh` が非アンカーで、別 worktree の hook 編集でも起動する

ファイル冒頭のコメントは「対象はリポジトリルート基準の厳密なパスで判定する」と宣言しているのに、hooks だけグロブのままだった（**自分のコメントと実装が矛盾していた**）。`skills` / `templates` も同じ方針に揃えた。

**実測**: 違反状態で別 worktree（`skills-export-company/.claude/hooks/foo.sh`）とリポジトリ外の hook を渡す → **exit 0**（起動しない）。自リポジトリの hook → exit 2。

## Low（対応済み 2 / 据え置き 1）

- **`contract_e` の片方向の穴**: `mo - m`（マスターから消えたのに分類に残る死んだ分類）と `dep ∩ mo`（両方に入っている）を検査していなかった → **両方追加**。`contract_a` の逆方向（実ファイルの無い死んだ登録）も追加。`["permissions"]` の KeyError も `die()` 経路に載せた
- **`contract_c` は hooks 以外の `.sh` で偽 FAIL する**: 将来 `scripts/` にシェルスクリプトを置いて README に書くと FAIL する。**据え置き** — 現状 0 件で、起きたときに気づける（偽 FAIL は偽 PASS より安全側）。起きたら許容リストを持たせる
- **`contract_d` は「全文に名前があれば PASS」なので手順 6 のコピー指示が消えても通る**: `starter-kit.md:47-48` の表にも 2 本の名前があるため。**据え置き** — 節境界のパースを避ける設計判断（偽 PASS の範囲は「名前は載っているがコピー指示が消えた」に限られ、包含判定をやめる副作用のほうが大きい）

## 「確認したが問題なし」としてレビュアーが明示した点

- `DEPLOY_PERMISSIONS` の可変辞書共有: 実際に mutation する箇所は無く、`json.dumps` されるだけ。破壊経路なし（予防的に deepcopy する提案は受けたが、現状の実装では不要と判断）
- `strip_nonbundled()` の過剰除去: 非同梱 19 名（`adr` / `e2e` の短い語を含む）で全コード行に適用しても、変化するのは意図した 1 行のみ。偽 PASS を作る過剰除去は発生していない
- `SH_RE` の集合抽出: README 8 件・starter-kit 6 件で誤検出・取りこぼしなし
- 集合演算の向き（`⊆` と `≡` の使い分け）が docstring・README の記述と一致
- 配布物への影響: dry-run で hooks 6 本が解決、permissions が配布サブセットで出力、実ファイルは書かれない
- `check_deploy_drift.py` との干渉: permissions を比較していないため偽ドリフトは出ない
- 性能: checker の実行 0.14s（hook の timeout 15s に対して十分）

## 反省として記録すること

**H3 は「手で確認した」を「機械化した」と混同した実例。** Phase 4 で `settings.json` の hooks 登録を手作業で突合し「なし ✓」と報告したが、契約として encode しなかったため次回以降は誰も見ない状態だった。このタスク自身の主題（人の注意ではなく機械で支える）を、検証工程で自分が破っていた。

**H1・H2 は「検査を書いた」ことを「検査が効いている」と混同した実例。** 6 契約それぞれを故意に壊して落ちることは実測したが、**契約の組み合わせ**（対象不在 + 別契約の違反）と**既定の呼び出し経路**（`--verbose` 無し）は測っていなかった。単体で効くことは全体で効くことを意味しない。
