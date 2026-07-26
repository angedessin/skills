# タスクリスト: 配置機構の整合回復と出荷前検証

design.md: `.steering/20260726-deploy-integrity/design.md`
（プレモータム反映済み: 20260726 / スコープ変更: 20260726 — rm・mv ポリシーを別タスクへ切り出し、出荷前検証フェーズを新設）

## 0. 変更対象の確定（実装の最初に行う）

design.md の「主要コンポーネント」は**暫定**。実装に入る前に、変更対象を表す語で全文検索して対象を機械的に洗い出す。今回のタスクは「片側修正の再発」が主題なので、この工程を飛ばさない。

- [x] `grep -rn "\.sh"` で hook を列挙している全箇所を洗い出す → README 10 件 / starter-kit 7 件 / **user-guide 0 件（契約対象外で正しい）**
- [x] `grep -rn "permissions"` で permissions を説明している全箇所を洗い出す → starter-kit `:88 :90 :98 :104` / README `:214 :216` / claude-code-config `:43 :205 :207`
- [x] `git worktree list` で対象 worktree を列挙する → main + export/company の 2 つ
- [x] 洗い出しの結果、design.md の表に無い箇所があれば **design.md を先に更新する** → **2 件追加**: `README.md:214`（deploy_skills.py の説明が「permissions の同送」のまま）/ `docs/starter-kit.md:90`（手動マージ方針の「マスター由来」の意味が変わる）

## 1. Phase 1 — 配置機構の修復

- [x] `HOOK_REGISTRATIONS` に `guard-gated-write.sh`（PreToolUse / matcher `Bash` / timeout 10）を追加
- [x] `HOOK_REGISTRATIONS` に `session-start-check.sh`（SessionStart / timeout 10）を追加
- [x] 追加した登録内容が `.claude/settings.json` の現行登録と同形であることを突合
- [x] `MASTER_ONLY_HOOKS` を**定数として**新設。`expected_hooks()` の docstring から散文の分類を削除し定数への参照に置き換え（二重管理を残さない）
- [x] `DEPLOY_PERMISSIONS` を新設（allow 6 / ask 23 / deny 27 の明示列挙）
  - [x] **rm 関連は現状維持**（`rm -rf *` / `rm -fr *` を deny、`rm -r*` を ask）。見直しは別タスク
  - [x] 自動インストールを伴う実行（`npx -y` / `pnpm dlx` / `yarn dlx` / `bunx`）は**配る**側に分類 — サプライチェーン対策であり、通常の依存管理を止めないため
- [x] `MASTER_ONLY_PERMISSIONS` を新設し、**配らない理由**を明記（依存管理を止める install/add/remove 系 21 件 + global CLAUDE.md の ask 2 件）
- [x] `payload` の `permissions` を `DEPLOY_PERMISSIONS` 参照に切り替える
- [x] **dry-run でも payload をログ出力する**（既存分岐との対称化）
- [x] `--skills tdd --dry-run`（**無条件同送経路**）が exit 0 で完走 → **KeyError 解消を確認**
- [x] `--skills design-doc,knowledge-capture,compound,steering,tdd --dry-run`（**条件付き同送経路**）が exit 0 で完走
- [x] 出力 permissions の機械確認 → master-only の混入 **なし** / 依存インストールを止める deny **なし** / global CLAUDE.md の ask **なし**
- [x] 分類の網羅性を先取り確認（契約 e 相当）→ allow / ask / deny とも **未分類 0・ドリフト 0**
- [x] 既存 settings.json がある場合の「書き込まず手動マージ案を提示」経路が壊れていないことを確認（既存ファイルは無変更）
- [x] dry-run で `deployments.md` に副作用が出ないことを確認（有効行 0 件のまま）

## 2. Phase 2 — 契約突合の機械化

- [x] `scripts/check_asset_consistency.py` を新規作成（stdlib のみ・`deploy_skills.py` を import）
- [x] 契約 (a): `expected_hooks()` の全可能出力 ⊆ `HOOK_REGISTRATIONS` のキー
- [x] 契約 (b): `expected_hooks()` の全可能出力 ∪ `MASTER_ONLY_HOOKS` ≡ `ls .claude/hooks/`（**集合等価**）
- [x] 契約 (c): README 全文の `*.sh` 言及集合 ≡ `ls .claude/hooks/`（**等価**）
- [x] 契約 (d): `expected_hooks()` の全可能出力 ⊆ `docs/starter-kit.md` **全文**の `*.sh` 言及集合（**包含**）
- [x] 契約 (e): master settings の各ルールが 2 集合に分類済み **かつ** `DEPLOY_PERMISSIONS` ⊆ master settings（**双方向**）
- [x] 契約 (f): 配布物 hooks の突合。**worktree 自動発見 + 不在時 exit 2**
  - [x] **実装中に判定粒度を変更** — 初版は `stop-typecheck.sh` 不在を FAIL としたが、これは `settings.example.json` の `_comment` に書かれた**意図的な除外**だった。基準を「配布物自身の登録（settings.example.json）と実体の整合」に変更し、master の同送 hook 不在は**注記**に降格（`decisions.md` に根拠と留保）
- [x] 違反時 exit 1 / 対象不在時 exit 2 / `--help` は exit 0 で docstring
- [x] 出力形式を既存スクリプトに揃える（`PASS` / `FAIL` + 6 スペースインデント）
- [x] **6 契約それぞれを故意に壊して落ちることを実測する** → **7 シナリオ全て検出**（(e) は双方向・(f) は 2 種。表は `decisions.md`）
- [x] `package.json` に `validate:assets` を追加（**`validate` には含めない**）
- [x] `npm run validate:assets` で動くことを確認（pnpm は破損中のため npm 経由）
- [x] 初回実行 **4/6 PASS** — FAIL は (c)(d) の 2 件で、いずれも design.md が予告していた既知違反（Phase 3 で解消）

## 3. Phase 3 — ドキュメントの反映（配線は最後）

- [x] `README.md` の hooks ツリーを 8 本にする（`guard-gated-write.sh` / `remind-config-docs.sh`）
- [x] `README.md` の `scripts/` ツリーに `check_asset_consistency.py` を追加
- [x] `README.md` インフラ節に 3 資産の説明を追加（guard-gated-write / remind-config-docs / check_asset_consistency）
- [x] `README.md` `:214` の `deploy_skills.py` の説明を配布サブセット方式に改訂（**洗い出しで追加した分**）
- [x] `docs/starter-kit.md` 手順 6 に `guard-gated-write.sh` を追加
- [x] `docs/starter-kit.md` 手順 6 の ask 説明に `docs/decisions/**` と glob 3 形式を追加
- [x] `docs/starter-kit.md` 手順 6 に「配布 permissions はベースラインで、**最終的なルールは配布先に依存する**」を明記
- [x] `docs/starter-kit.md` `:90` の手動マージ方針を「配布サブセット由来」基準に改訂（**洗い出しで追加した分**）
- [x] `docs/starter-kit.md` 手順 8 に「配置先の通常コマンドが阻害されていないこと」を追加
- [x] 手順 8 の `.env` 検証を `head .env.local` に修正（`cat .env` では permissions の deny だけで止まり hook の検証にならない）
- [x] 手順 8 に「PreToolUse は再起動後に確認・ask の発火は人間が見る」を追加
> `export/company/MIGRATION-GUIDE.md` は**別ブランチのファイル**なので Phase 3 では触らない（main と export で同一コミットは作れない）。Phase 5 で扱う。

- [x] `check_asset_consistency.py` が (c)(d) で PASS することを確認
- [x] **(c)(d)(e)(f) の新規違反**: (f) が `stop-typecheck.sh` の配布物不在を検出 → 意図的な除外と判明し、契約の判定粒度を変更して解決（Phase 2 に記載）。それ以外の新規違反なし

### 配線（Phase 3 の最後に行う — 先に配線すると全編集が差し戻されて警報疲れを起こす）

- [x] `.claude/hooks/validate-skill-edit.sh` の `case` に `assets` モードを追加
  - [x] **`*/README.md` の広いグロブをやめ、`$PROJECT_ROOT/README.md` の厳密照合にした** — `templates/README.md` や `references/README.md` の編集で誤発火すると、無関係な編集が差し戻されて警報疲れを招く
  - [x] `exit 2`（対象不在＝worktree が無い等）では差し戻さない分岐を追加 — ここで止めると持ち出しセットを持たない環境で全編集がブロックされる
- [x] `assets` モードで失敗時 `exit 2` + stderr の差し戻しが効くことを実測（未分類 hook を仕込んで確認 → 差し戻しメッセージに FAIL (b) が出た）
- [x] **既存 2 モード（skill / template）が壊れていないことを実測** → 両方 exit 0
- [x] assets モードの 4 経路（hooks / README / starter-kit / deploy_skills.py）が起動することを実測
- [x] 誤発火しないことを実測（`templates/README.md` / `user-guide.md` / `design.md` はいずれも素通し）
- [x] スクリプト不在時のフェイルオープンが維持されていることを確認（模擬配置先で exit 0）
- [x] probe を片付け、`git status` に検証ゴミが残っていないことを確認
- [x] **契約 6/6 PASS を確認**（(c)(d) の既知違反が解消）

## 4. Phase 4 — 出荷前の動作検証（配布の前提。省略可能な工程として扱わない）

### hooks 8 本のフィクスチャ実測

> ペイロードは公式 docs の実形式に揃える（`session_id` / `prompt_id` / `transcript_path` / `cwd` / `permission_mode` / `hook_event_name` + `tool_name` / `tool_input`）。`transcript_path` を含めることで、全文検査系 hook の誤検知確認になる。

- [x] `guard-env-read.sh` — 発火（`.env` 系）と誤検知（無関係な Bash）
- [x] `guard-gated-write.sh` — 発火（`>` / `>>` / `tee` × 3 対象パス）と誤検知（`transcript_path` を含む無関係なコマンド）
- [x] `post-edit-lint.sh` — **フェイルオープンの確認**（lint 設定が無い環境で素通しすること）
- [x] `stop-typecheck.sh` — **フェイルオープンの確認**（tsconfig.json が無い環境で素通しすること）
- [x] `validate-skill-edit.sh` — skill / template / **assets** の 3 モードと、依存不在時のフェイルオープン
- [x] `remind-config-docs.sh` — config / skills の 2 分岐、誤発火なし、セッション 1 回制限
- [x] `session-start-check.sh` — `.steering/` のフィクスチャでフラグとアクティブタスクの注入。`.steering/` 不在時の素通し
- [x] `session-stop.sh` — `.capture-needed` の生成、作りたてタスクのスキップ（AND 条件）、`.steering/` 不在時の素通し
- [x] **発火数と誤検知数を一覧で記録する**（`decisions.md` へ）

### 配置の実走（tmpdir・dry-run ではない）

- [x] tmpdir へ `--dry-run` 無しで実配置する
- [x] スキルの員数が指定と一致することを確認
- [x] hooks が同送され、settings.json に登録されていることを確認
- [x] 各スキルの frontmatter に `source-commit` が打刻されていることを確認
- [x] `.gitignore` にフラグ 3 行が入っていることを確認
- [x] **生成された settings.json の deny を読み、`npm install` 等が含まれない**ことを確認（配置先の開発フローが阻害されない）
- [x] `check_deploy_drift.py` を実配置した tmpdir に対して実行し、3 分類 + hooks 差分 + skill-issues 収集が動作することを確認（配置直後は差分ゼロが正常）
- [x] tmpdir を破棄する
- [x] **`deployments.md` に副作用が残っていない**ことを確認（検証用パスがレジストリに残ると以後の巡回が壊れる）

### その他

- [x] `.claude/settings.json` の hooks 登録が実在するファイルのみを指していることを確認（契約 (b) の逆方向）
- [x] 静的検査（29/29・portability 0・export 10/10・停止契約 7/1/2）
- [x] **素通り検査をユーザー承認のうえ実行した**（20 run・課金）→ **20/20 run すべて停止を守った**（`adr` / `debug` / `knowledge-capture` / `impl-from-design` / `session-retrospective` が各 4/4 PASS）
  - [x] 実行前に `session-retrospective` の判定対象 0 ファイルを確認し、検出力が健全であることを裏取り（新規作成は検出される）
  - [x] **「改善した」とは記録しない** — 前回 3/4 の 3 本が 4/4 になったが n=4 では有意差を主張できない（`decisions.md`）

## 5. Phase 5 — 持ち出しセットへの最小反映と引き継ぎ

> 実行ディレクトリに注意: スクリプトの `MASTER_ROOT` は実行ファイルの位置から決まる。export の作業は worktree 側（`/Users/kentaro/Desktop/_lab/ai/skills-export-company/`）で行う。
>
> **スキル本文の突合はしない**（ユーザー判断 20260726 — export はプロジェクト用に意図的に改変したフォーク）。行うのは merge・hooks の突合・引き継ぎ文書の正確性のみ。

- [x] main 側をコミットしてから export worktree へ merge する（`1e391d8` / `76779ff` → merge `e58b288`）
- [x] merge で `export/company/` 側の改変が潰れていないことを確認 → `git diff HEAD~1 HEAD -- export/company/` が空（無傷）
- [x] **契約 (f) が PASS することを確認** — worktree 側の `scripts/` から実行して 6/6 PASS
- [x] 配布物の hooks 5 本にフィクスチャ検証 → **発火 5/5・誤検知 0/3・非同梱スキル名の混入 0**
- [x] `export/company/MIGRATION-GUIDE.md` の permissions 要約（ask の 3 パス）と hooks 登録（guard-gated-write）を実体に合わせた
- [x] 同ファイルに**会社向けの deny は配布先依存の正しい差異**である旨を明記（「外して緩めないこと」まで書いた）
- [x] `MANIFEST.md` / `HANDOVER.md` の記述と実体の一致を確認 → **スキル 10 / hook 5 で齟齬なし・変更不要**
- [x] `validate_skills.py export/company/skills` が 10/10 PASS
- [x] `check_export_stopcontract.py` のサマリが 7/1/2 で不変
- [x] **引き継ぎ内容をユーザーに提示した** → 会社側の作業は**発生しない**（未配布のため worktree 側で完結）

## 6. レビュー

- [x] 静的検査を全て回す（29/29・portability 0・template PASS・export 10/10・停止契約 7/1/2・契約 7/7）
- [x] ~~`frontend-code-review`~~ → **汎用 subagent で代替**（React/TS 前提の 7 軸は Python / bash / Markdown の差分に噛み合わないため。ユーザー判断）
- [x] 指摘をトリアージし `review-result.md` に記録（High 3 / Medium 3 / Low 3）
- [x] **High 3 件すべてに対応**（いずれも「検査が偽グリーンを出す」型 = このスクリプトの存在理由に反する欠陥）
  - [x] H1: 対象不在の exit 2 が他契約の FAIL を握りつぶし hook が恒久的に無音 → SKIP に降格・`--require-export` 追加・hook 側も rc=2 を捨てない
  - [x] H2: 「必ず列挙する」と書いた WARN が既定出力に出ず、20260726 の実害の再現が 6/6 PASS で通った → WARN を無条件出力・`EXPORT_INTENTIONAL_OMISSIONS` を新設し宣言の無い欠落は FAIL
  - [x] H3: マスターの settings.json の hooks 登録が無検査（**Phase 4 で手作業で確認しただけで契約化していなかった**）→ 契約 (f) として追加、既存 (f) は (g) へ
- [x] **Medium 3 件すべてに対応**
  - [x] M1: `.claude/settings.json` の編集が assets モードに乗らず、契約 (e) の producer が hook で守られていなかった
  - [x] M2: `code_lines()` の `#` 落としが heredoc 内にも効き、配布物の JSON 出力破壊を隠す → heredoc ステートマシン + shebang を常に含める
  - [x] M3: `*/.claude/hooks/*.sh` が非アンカーで別 worktree の編集でも起動（**自分のコメントと実装が矛盾**）→ 全パターンを PROJECT_ROOT 基準に
- [x] **Low 3 件**: 2 件対応（契約 e の死んだ分類・重複、契約 a の死んだ登録）/ 1 件据え置き（偽 FAIL 側なので安全）
- [x] 修正後の再検証: H1/H2/H3・M1/M2/M3 すべて「壊すと落ちる」を実測。無回帰も全て緑
- [x] Phase 4 の新規不具合（契約 (f) の判定粒度）とレビューの High 3 件は**いずれも配布をブロックする**と判断し、本タスク内で修正した

## 7. デプロイ・知見保存

- [x] main へコミット（`1e391d8` 実装 / `76779ff` 設計 + レビュー修正コミット）
- [x] `git status --short` でステージ内容を確認してからコミット（検証ゴミの混入なし）
- [x] export ブランチへ merge してコミット（`e58b288` merge / `d571405` 引き継ぎ文書の修正）
- [x] **push 完了**（main `74a96d1` / export/company `d95e783` — 両ブランチ ahead 0 / behind 0）
- [x] **rm / mv ポリシーの後続タスクを起票**（`.steering/` は作らず `decisions.md` にバックログとして記録。ユーザー決定 3 件 + 公式 docs で裏取りした技術的制約 5 点 + 併せて塞ぐべき `mv` + 波及先を保存）
- [x] `knowledge-capture` で知見を保存 — **2 件書き込み**（`claude-code-config.md` に「PreToolUse と permissions の評価順」「入力 JSON に常にプロジェクト外の絶対パスが入る」「配布 permissions はマスターの方針と分ける」の 3 節 / `skill-design-patterns.md` の検出ツールの規律に #5〜#7 + heredoc 注記）。**1 件は compound へ申し送り**（検証工程の 2 つの混同 = 行動ルールなので重複を避けて `skill-issues.md` に起票）
- [x] `compound` でルール・スキルへの昇格を実施 — **3 件昇格**（契約 (h) で `MASTER_ONLY` の 2 重定義を機械化 / `REGISTRY` を import で単一化 / CLAUDE.md に「手作業の突合を機械化したと扱わない」1 行）。**効果検証で前回の昇格ルールが不完全だったことを検出**（対の片方しか名指ししていなかった）。既存違反の洗い出し → **残り 0 件**。詳細は `codify-log.md`
- [x] `steering` の archive モードでこのタスクをアーカイブする

Archived: 20260726
