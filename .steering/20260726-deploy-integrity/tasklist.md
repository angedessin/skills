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
- [ ] **素通り検査を回すかユーザーに確認する** — 課金する（承認ゲート系 5 本 × `--runs 4` = 20 run 相当）。無料の代替は上の静的検査とフィクスチャ検証。**既定では回さない**

## 5. Phase 5 — 持ち出しセットへの最小反映と引き継ぎ

> 実行ディレクトリに注意: スクリプトの `MASTER_ROOT` は実行ファイルの位置から決まる。export の作業は worktree 側（`/Users/kentaro/Desktop/_lab/ai/skills-export-company/`）で行う。
>
> **スキル本文の突合はしない**（ユーザー判断 20260726 — export はプロジェクト用に意図的に改変したフォーク）。行うのは merge・hooks の突合・引き継ぎ文書の正確性のみ。

- [ ] main 側をコミットしてから export worktree へ merge する（順序を守る）
- [ ] merge で `export/company/` 側の改変が潰れていないことを確認（**内容の一致は検証しない**）
- [ ] **契約 (f) が PASS することを確認** — hooks に既知の変換規則で説明できない差分が無いこと。**防御の欠陥が配布物側で開いていないか**の一点のみ
- [ ] 配布物の hooks 5 本にフィクスチャ検証を回す（master と同じケースで発火数・誤検知数を記録。「master で動く」は export で動く証拠にならない）
- [ ] `export/company/MIGRATION-GUIDE.md` `:119-120` の permissions 要約と hooks 登録の列挙を実体に合わせる（**引き継ぎ文書の正確性**。会社側 AI が読む一次情報のため、配布直前に誤記を残さない）
- [ ] 同ファイルに**会社向けのパッケージインストール deny は配布先依存の正しい差異**である旨を 1 行添える（論点 5 の回答。「master と揃っていないのは漏れではない」と次に読む人に伝わる形にする）
- [ ] `export/company/MANIFEST.md` / `HANDOVER.md` の記述と実体の一致を確認（hook 5 本・スキル 10 本。齟齬が無ければ変更しない）
- [ ] `validate_skills.py <worktree>/export/company/skills` が 10/10 PASS（無回帰確認のみ）
- [ ] `check_export_stopcontract.py` のサマリが 7/1/2 で不変（既存ツール・無回帰確認のみ）
- [ ] **引き継ぎ内容をユーザーに提示する**（会社側の作業要否を明示。未配布のため、持ち出し前に整合させれば会社側の作業は発生しない）

## 6. レビュー

- [ ] 静的検査を全て回す（無回帰条件の 6 項目）
- [ ] `frontend-code-review` でレビューする（前回はセッション上限で 3 エージェントとも中断した実績があるため、範囲を絞って起動する）
- [ ] 指摘をトリアージし、`review-result.md` に記録
- [ ] must-fix に対応
- [ ] **Phase 4 で新たな不具合が見つかった場合**は「配布をブロックするか」で切り分ける（ブロックするなら本タスク内で直す / しないなら起票して配布を進める）

## 7. デプロイ・知見保存

- [ ] main へコミット（Phase 単位で分ける）
- [ ] `git status --short` でステージ内容を確認してからコミットする（検証ゴミの混入防止）
- [ ] export ブランチへ merge してコミット
- [ ] **push**（main / export/company の両方）
- [ ] **rm / mv ポリシーの後続タスクを起票する** — design.md の「対象外」節がそのまま設計材料。既に確定していること: ユーザー決定は `deny` を使う／`mv` も塞ぐ／公式 docs で確定した技術的制約 4 点（hook は permissions の deny を救済できない・`Bash(rm -rf /*)` は使えない・全文検査でパス判定はできない・非対話では ask が deny に落ちる）
- [ ] `knowledge-capture` で知見を保存する
- [ ] `compound` でルール・スキルへの昇格を検討する（特に「単一情報源が実は 2 つある」型の検出方法）
- [ ] `steering` の archive モードでこのタスクをアーカイブする
