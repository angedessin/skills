# 設計: 配置機構の整合回復と出荷前検証

Status: **APPROVED**
Date: 20260726（プレモータム反映: 20260726 / スコープ変更: 20260726）
Approved: 20260726（契約 (f) を残す設計者推奨を採用）

## 目的

未 push の 17 コミットをレビューした結果、**配置機構が壊れたまま出荷されようとしている**ことが分かった。`deploy_skills.py` は `expected_hooks()` が返す hook のうち 2 本が `HOOK_REGISTRATIONS` に無く、`--dry-run` ですら `KeyError` で落ちる。`guard-gated-write.sh` は**無条件同送リスト**（`deploy_skills.py:170-175`）に入っているため、`--skills tdd` の最小構成を含む**全構成が落ちる**（プレモータムの実測で確認）。

これは単発のバグではなく**再発している型**である。git がそれを示している:

| 欠落 hook | 混入コミット | 日付 | 状態 |
|---|---|---|---|
| `session-start-check.sh` | `27c19ab` fix: 敵対レビューで検出した**契約ズレ・片側修正 13 件を修正** | 2026-07-23 | **push 済み（既存バグ）** |
| `guard-gated-write.sh` | `b9b6a91` feat: 福利化 — **同送 hook の漏れ**・洗い出し範囲・フラグ偽陽性を昇格 | 2026-07-26 | 未 push（今回） |

**片側修正を直すコミットが片側修正を新造し、「同送 hook の漏れ」をルール化するコミットが同じ漏れを 1 階層下で再発させている。** 同じ型が README（hooks ツリーが 6/8 本）と `docs/starter-kit.md`（同送手順に `guard-gated-write.sh` が無い）にも出ている。

原因は注意力ではなく構造にある。`expected_hooks()` は「両者に同じリストを書くと片側修正で腐る」という理由で単一情報源として作られたが、実際は **`expected_hooks()` の返り値と `HOOK_REGISTRATIONS` のキーという 2 つのリスト**があり、両者を突合するものが存在しない。ドキュメントに至っては実体との機械的な繋がりが一切ない。

**そして本タスクの直後に配布が予定されている**（20260726 のユーザー判断）。main と `export/company/` のチェックが済み次第、会社および外部プロジェクトへ配る。したがって「直した」だけでは足りず、**ワークフロー・スキル・hooks が実際に動作することを検証してから出荷する**ところまでが本タスクの責務になる。

## スコープ変更の記録（20260726）

当初の Phase 1（rm ポリシーの再設計）は**別タスクへ切り出した**。ユーザー判断「rm ポリシーの方式は一旦別で議論する。今回のことと関係ない気がしてきた」による。切り出す内容と、既に得られている決定は「対象外」節に保存する。

## レビュー前に確定した決定

| 決定 | 内容 | 経緯 |
|---|---|---|
| 契約突合の置き場 | **新スクリプト `check_asset_consistency.py` + 既存 `validate-skill-edit.sh` の拡張**で自動起動。npm script にも載せる | Phase 1.5 の決定インタビュー |
| 配布 permissions | **配布用サブセット `DEPLOY_PERMISSIONS` を明示定義**。マスターの permissions はこのリポジトリ固有の方針を含むため配布対象にしない | 同上 |
| `check_asset_consistency.py` の起動 | **`validate:assets` として別立て**にする（`npm run validate` には含めない） | 論点 2 の回答（20260726） |
| 配布先ごとのセキュリティ方針 | **`DEPLOY_PERMISSIONS` はベースラインであり、最終的なルールは配布先に依存する。** `skill-deploy` の dry-run 提示で配置先の事情に合わせて調整する。会社向け（`export/company/`）がパッケージインストール deny を維持するのは矛盾ではなく、配布先ごとの正しい差異 | 論点 5 の回答（20260726） |
| 出荷前検証 | 静的検査だけで出荷しない。**hooks 8 本のフィクスチャ実測と、配置の実走（tmpdir）まで行う** | 論点 1 の回答（20260726・配布予定あり） |
| **`export/company/` の検証範囲** | **スキル本文は対象外**（配置先プロジェクト用に意図的に改変したフォークであり、master との一致を検証する意味がない）。**hooks だけは契約 (f) で突合を残す** — hooks はフォークではなくバイト単位のコピー + 文言調整であり、「master が動けば export も動く」は**過去に成立しなかった**（下記） | ユーザー判断（20260726）+ 設計者の限定的な反論 |
| `guard-gated-write.sh` のリネーム | **行わない。** rm / mv を別タスクへ切り出した結果、この hook は書き込み専用のままとなり、名前と実態が一致する（リネームの前提が消えた）。リネームの是非は rm タスクで再検討する | 論点 6 の前提消滅（20260726） |

## スコープ

### 対象

- **Phase 1 — 配置機構の修復**: `HOOK_REGISTRATIONS` の欠落 2 件、`MASTER_ONLY_HOOKS` / `DEPLOY_PERMISSIONS` / `MASTER_ONLY_PERMISSIONS` の新設、dry-run の payload 出力
- **Phase 2 — 契約突合の機械化**: `check_asset_consistency.py`（6 契約）の新設
- **Phase 3 — ドキュメントの反映**: README・starter-kit・MIGRATION-GUIDE を実体に合わせる。**最後に `validate-skill-edit.sh` への配線を行う**
- **Phase 4 — 出荷前の動作検証**: hooks 8 本のフィクスチャ実測、配置の実走（tmpdir への実配置とドリフト検出の一周）、export セットの検査
- **Phase 5 — 持ち出しセットへの最小反映と引き継ぎ**: export worktree への merge、**hooks の突合（契約 f）のみ**、引き継ぎ内容の提示

### `export/company/` の扱い（20260726・ユーザー判断と設計者の限定的な反論）

**ユーザー判断**: 「export/company 側は元のスキルを元にそのプロジェクト用に修正しているので無視してよい。こちらでワークフローが正常に動作していれば export 側は問題ない」。

**スキル本文についてはこれに従う。** Angular / Jasmine への書き換え・非同梱スキル名の除去・npx の deny 強化はいずれも**意図的な機能差分**であり、master との一致を検証する意味がない。既存の `check_export_stopcontract.py`（停止契約語彙の比較）以上のことはしない。

**hooks についてのみ、限定的に反論して契約 (f) を残す。** 根拠は 20260726 に**このリポジトリ自身が昇格させたルール**（`.steering/archived/20260725-review-followups/codify-log.md` の昇格 2）:

> 「フォークには伝播しない」方針は**機能差分の話であって、防御の欠陥には適用しない**

これは実際の事故から昇格したものである:

| 事故 | 内容 |
|---|---|
| `guard-gated-write.sh` の欠落 | master が High（セキュリティ）として塞いだ Bash 迂回路が、配布物側では**丸ごと欠けたまま**だった。20260726 のレビューで偶然発見 |
| `session-stop.sh` の偽陽性 | 同じバグが master と export の両方に存在し、master を直したときに export も直す必要があった |

hooks はスキル本文と異なり**フォークではなくバイト単位のコピー + 文言調整**（配布版は非同梱スキル名を除いただけ）なので、「master が動けば export も動く」は過去に成立していない。契約 (f) は差分の**内容**を見るのではなく、**既知の変換規則で説明できない差分が出たら報告する**だけなので、意図的な配布加工を妨げない。

**この反論をユーザーが退ける場合は契約 (f) を落とす** — その場合、上記の昇格ルールも同時に撤回対象になる（ルールだけ残して機械化しないと「書いたが効いていない」の在庫が増える）。

### 対象外 — rm / mv ポリシーの再設計（別タスクへ切り出し・内容は維持）

**20260726 にユーザー判断で切り出した。以下は次タスクの設計材料としてそのまま残す。** 既に調査とプレモータムを通っており、決定も一部確定しているため、次タスクは調査からやり直さずに済む。

| 項目 | 内容 |
|---|---|
| 発端 | 承認ゲート（`CLAUDE.md` / `docs/knowledge/` / `docs/decisions/`）は**書き込みだけを塞ぎ、削除・移動は素通し**。`rm -f docs/knowledge/x.md` が実測で素通りした。整合性の穴 |
| permissions の穴 | `rm -R`（macOS で有効）/ `rm --recursive` / `rm -f -r` がどのルールにも当たらない。前置一致では flag の順列を網羅できない |
| ユーザーの決定（論点 3） | **`deny` を使う**（当初案に戻す）。プレモータムが提案した「ask に統一」は採らない |
| ユーザーの決定（論点 4） | rm の判定精度の問題は rm タスク側で扱う |
| **必ず持ち越す技術的制約**（公式 docs で確定・20260726） | (1) **PreToolUse hook は permissions より先に評価される。** hook が沈黙すると通常の permission flow に進むため、**hook は permissions の deny を救済できない**（`permissionDecision: "allow"` を返さない限り）。したがって permissions に置く deny は「プロジェクト内に絶対にマッチしない形」でなければならない — **`Bash(rm -rf /*)` は前置一致で `rm -rf /Users/.../skills/.tmp` にマッチするので使えない** / (2) 入力 JSON には `transcript_path`・`cwd`・`tool_input.description` が**必ず含まれる**ため、**全文検査でパス判定はできない**（プロジェクト外の絶対パスが恒常的に入っている）。`tool_input.command` の構造抽出が必須（`remind-config-docs.sh:31` の `grep -o` + `sed` 手法で `jq` 非依存を維持できる） / (3) `permissionDecision` に指定できる値は `allow` / `deny` / `ask` / `defer` / (4) **非対話モードでは hook の `ask` は deny に落ちる**（`claude-code-config.md:209`） |
| 併せて塞ぐべき穴 | **`mv` は削除と等価にゲートを破る**（`mv docs/knowledge/x.md /tmp/`）。`sed -i` / 任意インタプリタは脅威モデル外 |
| 波及 | `guard-gated-write.sh` のリネーム是非（書き込み以外も見るなら名前がずれる）。配布物側の同名 hook にも同じ変更が要る |

### その他の対象外

- **配布機構の初回実走**（外部プロジェクトへの実配置）— 配置先の選定と実配置は本タスクの外。ただし**配置が動作することの検証は Phase 4 で行う**（tmpdir への実配置で代替する）
- **素通り検査（`passthrough_check.py`）の実行** — 課金するため既定では回さない。スキル本文の停止契約を変更しないため必須ではない。**出荷前に回すかはユーザーが判断する**（→ Phase 4 の注記）
- **`.claude/settings.local.json`** — マシン固有・git 追跡外のため契約の射程外。実測で ask / deny は 0 件
- **`passthrough_check.py --help` の exit コード**（他 3 本と不揃い）— 枝葉。別途まとめて直す
- **CI の新設** — 起動主体は hook と npm script で確保する

## 制約

- **配布が直後に控えている** — main と `export/company/` の両方が検証を通ってから配る。**「直したが動作は未確認」の状態で出荷しない**
- **`export/company` は同一リポジトリの worktree** — 実体は `/Users/kentaro/Desktop/_lab/ai/skills-export-company/`。`git checkout export/company` は main 側で失敗する
- **修正の順序は「main で直す → export へ merge → `export/company/` 側の変換分のみ追随」**
- **`pnpm` のバイナリが破損している**（`blockers.md` に記録済み・本タスクと無関係）。npm script の検証は `npm run <script>`（npm 11.9.0 で動作確認済み）で行う
- **hook は依存ゼロを維持する**（POSIX 標準ユーティリティのみ）。配布物に含まれるため、配置先での追加インストールを要求しない
- **PreToolUse hook の実効性はセッション再起動後にしか確認できない**。かつ **ask / deny の発火は AI 側から観測できない** — 確認は人間が行う
- **配置の実走で `deployments.md` に副作用を出さない** — 検証用の tmpdir がレジストリに残ると、以後の `check_deploy_drift.py` が存在しないパスを巡回する
- `.steering/archived/` 配下は履歴のため変更しない

## 完了条件

### 達成条件 — 修復

- [ ] `python3 scripts/deploy_skills.py <tmpdir> --skills tdd --dry-run` が exit 0 で完走する（**無条件同送経路**）
- [ ] `python3 scripts/deploy_skills.py <tmpdir> --skills design-doc,knowledge-capture,compound,steering,tdd --dry-run` が exit 0 で完走する（**条件付き同送経路**）
- [ ] `--dry-run` が配置先に settings.json が無い場合でも payload をログ出力する（既存分岐との対称化）
- [ ] dry-run が出力する permissions に、パッケージインストールの deny（`pnpm add` / `npm install` 等）と `~/.claude/CLAUDE.md` の ask が**含まれない**ことを機械確認（JSON を読んで assert）

### 達成条件 — 機械化

- [ ] `python3 scripts/check_asset_consistency.py` が全項目 PASS し、**6 契約それぞれを故意に壊すと exit 1 で落ちる**ことを実測で確認（検査が実際に効くことの証明。「書いただけ」で数えない）
- [ ] `.claude/hooks/*.sh` の分類が `expected_hooks()` と `MASTER_ONLY_HOOKS` の**定数として存在し**、hook を 1 本足すと契約 (b) が落ちる
- [ ] README の `.sh` 言及集合 ≡ `ls .claude/hooks/`（現在 6/8 → 8/8）
- [ ] `expected_hooks()` の全可能出力 ⊆ `docs/starter-kit.md` 全文の `.sh` 言及集合
- [ ] `export/company/claude-config/hooks/*.sh` と `.claude/hooks/` の同名ファイルの差分が、既知の変換規則だけで説明できる（契約 f）
- [ ] `npm run validate:assets` が動く

### 達成条件 — 出荷前の動作検証（配布の前提）

- [ ] **hooks 8 本すべて**がフィクスチャで期待どおり動作する。**発火数と誤検知数を両方記録する**。ペイロードは公式 docs の実形式（`session_id` / `transcript_path` / `cwd` / `permission_mode` / `tool_input`）に揃える
- [ ] **配置の実走**: tmpdir へ `--dry-run` 無しで実配置し、(1) スキルの員数が指定と一致 (2) hooks が同送され settings.json に登録されている (3) 各スキルの frontmatter に `source-commit` が打刻されている (4) `.gitignore` にフラグ 3 行が入っている、を機械確認する
- [ ] **配置先で通常の開発コマンドが阻害されない**ことを、生成された settings.json の deny を読んで確認（`npm install` 等が deny に含まれないこと）
- [ ] **`check_deploy_drift.py` を実配置した tmpdir に対して実行**し、3 分類 + hooks 差分 + skill-issues 収集が動作することを確認（配置直後は差分ゼロが正常）
- [ ] 検証後に tmpdir を破棄し、**`deployments.md` に副作用が残っていない**ことを確認
- [ ] `.claude/settings.json` の hooks 登録が実在するファイルのみを指している（登録があるのにファイルが無い、の逆方向も確認）

### 達成条件 — 出荷

- [ ] `export/company/` に Phase 1〜3 の該当分が反映され、`HANDOVER.md` / `MANIFEST.md` / `MIGRATION-GUIDE.md` の hook 本数・permissions 要約が実体と一致している
- [ ] 引き継ぎ内容がユーザーに提示されている（Phase 5）
- [ ] rm / mv ポリシーの後続タスクが起票されている

### 無回帰条件（着手前から満たされている。壊していないことの確認）

- [ ] `python3 scripts/validate_skills.py` が 29/29 PASS
- [ ] `python3 scripts/validate_skills.py <worktree>/export/company/skills` が 10/10 PASS
- [ ] `--portability` が混入 0 件
- [ ] `check_export_stopcontract.py` のサマリが 実質差分 7 / 無害のみ 1 / 差分なし 2 で不変
- [ ] `validate_skills.py` の既存 6 経路と `validate-skill-edit.sh` の既存 2 モードが壊れていない
- [ ] `guard-gated-write.sh` の既存の書き込み判定（`>` / `>>` / `tee`）が発火 / 誤検知とも現状維持

## 調査結果

### 実測（20260726）

```
validate_skills.py            29/29 PASS
--portability                 混入 0 件 / --template PASS
settings.json                 JSON 妥当
hooks 8 本                    bash -n 全て構文 OK
guard-gated-write.sh          書き込み発火 OK / 誤検知なし
remind-config-docs.sh         両分岐で注入 OK
check_deploy_drift.py         レジストリ 0 件で exit 2（フェイルクローズ正常）
check_export_stopcontract.py  worktree 自動発見 OK / exit 0
deploy_skills.py              KeyError: 'guard-gated-write.sh'  ← 全構成で落ちる
settings.local.json           allow 23 / ask 0 / deny 0
README の .sh 言及             6 種すべて hooks のファイル名・ノイズ 0 件
starter-kit の .sh 言及        手順 6 以外にも :47 :48 :104 に存在（節境界のパースが必要）
```

### 既存パターン

- **スクリプトの規約**: `#!/usr/bin/env python3` + 冒頭 docstring に「何をするか / 使い方 / 終了コード」。stdlib のみ。ルートは `Path(__file__).resolve().parent.parent` で自己解決。`PASS  <name>` / `FAIL  <name>` + 6 スペースインデントの詳細
- **`--help` は exit 0 で docstring を表示**（既存 3 本で確立済み）
- **`deploy_skills.py` の import は安全**（プレモータムで確認）— トップレベルは定数定義のみで副作用ゼロ、`main()` は `__main__` ガード下。`check_deploy_drift.py:48-49` が `sys.path.insert` + `from deploy_skills import expected_hooks` の前例を確立済み
- **`validate-skill-edit.sh` の構造**: 依存不在でフェイルオープン → `case "$FILE"` でモード判定 → 検証実行 → 失敗時 `exit 2` + stderr で差し戻し
- **フィクスチャ検証の前例**: `session-stop.sh` の AND 条件を 6 ケースで検証した実績がある（`codify-log.md`）
- **hook のペイロード形式**（公式 docs で確定）: `session_id` / `prompt_id` / `transcript_path` / `cwd` / `permission_mode` / `hook_event_name` の共通フィールド + イベント固有の `tool_name` / `tool_input` / `tool_use_id`。**フィクスチャはこの形式に揃える**

## アプローチ

**「分類し忘れたら壊れる」を「分類し忘れたら機械が落とす」に変える**のが本タスクの軸。個々のバグ修正だけでは同じ型が 3 度目を起こす（既に 2 度起きている）。したがって修正は**必ずペアで行う**: 欠陥を直すと同時に、その欠陥を検出する検査を足す。検査の妥当性は「故意に壊して落ちるか」で確認する。

**そして今回は配布が直後に控えているため、静的検査で締めない。** このリポジトリは「書いただけでは効いていない」を繰り返し踏んでいる（`grep -c` の `0\n0`、セッション中追加の PreToolUse、`expected_hooks()` に足したが `HOOK_REGISTRATIONS` に無い）。配布物が壊れていた場合のコストは配置先での原因不明の摩擦になるため、**hooks は 8 本すべてフィクスチャで動かし、配置は tmpdir に実走する**。

**ドキュメントの突合は集合比較にする。** README は全文の `*.sh` 集合と `ls .claude/hooks/` の**等価**（実測でノイズ 0 件を確認済み）。starter-kit は手順 6 以外にも `.sh` 言及があるため、節境界のパースを避けて**全文集合への包含**にする。等価をやめることで書式非依存を保つ。

**配布 permissions は「配るものを列挙する」形にする。** 除外リスト方式は分類し忘れが配置先を壊す方向（フェイルオープン）に倒れる。列挙方式なら**配られない**方向（フェイルセーフ）に倒れる。突合は**双方向**にする。ただし `DEPLOY_PERMISSIONS` は**ベースライン**であり、最終的なセキュリティルールは配布先に依存する（論点 5 の回答）— `skill-deploy` の dry-run 提示で調整する運用を starter-kit に明記する。

## 主要コンポーネント

> 以下は**暫定**。実装の最初（tasklist の 0.）で変更対象を表す語で全文検索し、表に挙げ漏れた箇所を潰してから着手する。

### Phase 1 — 配置機構の修復

| ファイル | 変更後の状態 |
|---|---|
| `scripts/deploy_skills.py` | `HOOK_REGISTRATIONS` に 2 件追加: `guard-gated-write.sh` →（`PreToolUse`, matcher `Bash`, timeout 10）/ `session-start-check.sh` →（`SessionStart`, timeout 10）。`.claude/settings.json` の現行登録と同形にする |
| `scripts/deploy_skills.py` | `MASTER_ONLY_HOOKS` を**定数として**新設（現状 `remind-config-docs.sh` / `validate-skill-edit.sh`。理由も併記）。現在は docstring の散文にしかなく、契約 (b) が比較できる形になっていない |
| `scripts/deploy_skills.py` | `DEPLOY_PERMISSIONS` を新設（**配るもの**の明示列挙）。`allow`: `ls` / `git status` / `diff` / `log` / `show`。`ask`: `git push*` / `npx *` / `rm -r*` / settings・hooks 自身の編集 / `CLAUDE.md`・`docs/knowledge/**`・`docs/decisions/**` の書き込み（glob 3 形式 × Edit/Write）。`deny`: `.env`・鍵ファイルの読み取り（Bash / Read 両方）/ 破壊的 git / `rm -rf *`・`rm -fr *`（**現状維持** — rm ポリシーの見直しは別タスク） |
| `scripts/deploy_skills.py` | `MASTER_ONLY_PERMISSIONS` を新設し、**配らない理由**を明記: パッケージインストール deny 群（配置先の依存インストールを止める）/ `~/.claude/CLAUDE.md` の ask（配置先を超えたグローバル副作用）。`payload` の `permissions` は `DEPLOY_PERMISSIONS` を参照する |
| `scripts/deploy_skills.py` | **dry-run でも payload をログ出力する**（現状は配置先に既存 settings がある分岐でしか出さないため、新規作成経路の検証手段が無い）。既存分岐との対称化 |

### Phase 2 — 契約突合の機械化

| ファイル | 変更後の状態 |
|---|---|
| `scripts/check_asset_consistency.py`（新規・master-only） | **6 契約**を検査。**(a)** `expected_hooks()` の全可能出力 ⊆ `HOOK_REGISTRATIONS` のキー / **(b)** `expected_hooks()` の全可能出力 ∪ `MASTER_ONLY_HOOKS` ≡ `ls .claude/hooks/`（**集合等価**。hook を 1 本足して分類しなければ落ちる）/ **(c)** README 全文の `*.sh` 言及集合 ≡ `ls .claude/hooks/` / **(d)** `expected_hooks()` の全可能出力 ⊆ `docs/starter-kit.md` **全文**の `*.sh` 言及集合（**包含**。節境界をパースしない）/ **(e)** マスター `settings.json` の各ルールが `DEPLOY_PERMISSIONS` か `MASTER_ONLY_PERMISSIONS` に分類済み **かつ** `DEPLOY_PERMISSIONS` ⊆ マスター settings（**双方向**）/ **(f)** `export/company/claude-config/hooks/*.sh` と `.claude/hooks/` の同名ファイルの差分が既知の変換規則（非同梱スキル名の除去）だけで説明できる。違反は `FAIL  <契約名>` + 詳細で **exit 1**。対象不在は **exit 2**（フェイルクローズ）。`--help` は exit 0。stdlib のみ・`deploy_skills.py` を import して単一情報源にする |
| `package.json` | `scripts` に `validate:assets: "python3 scripts/check_asset_consistency.py"` を追加（**`validate` には含めない** — 論点 2 の回答） |

> **(f) の注記**: export worktree が無い環境（main 単独チェックアウト）では対象不在になる。`check_export_stopcontract.py` と同じく **git worktree からの自動発見 + 発見できなければ exit 2** に揃える。

### Phase 3 — ドキュメントの反映（配線は最後）

| ファイル | 変更後の状態 |
|---|---|
| `README.md` `:30-36` | hooks ツリーに `guard-gated-write.sh` と `remind-config-docs.sh` を追加し 8 本にする |
| `README.md` `:40-45` | `scripts/` ツリーに `check_asset_consistency.py` を追加 |
| `README.md` `:203-` インフラ節 | 3 資産の説明を追加 |
| `README.md` `:214`（**洗い出しで追加・20260726**） | `deploy_skills.py` の説明が「permissions の同送」のまま。**配布用サブセットを配ることと、マスター固有の permission は配らないこと**に改訂する |
| `docs/starter-kit.md` `:90`（**洗い出しで追加・20260726**） | 手動マージの方針が「マスター由来の deny / ask は削らずに追加する」と書かれている。`DEPLOY_PERMISSIONS` 化で「マスター由来」が指すものが変わる（マスターの settings 全部ではなく配布サブセット）ため、**配布サブセットを基準とする**表現に改訂する |
| `docs/starter-kit.md` 手順 6（`:87-98`） | 同送 hook の列挙に `guard-gated-write.sh` を追加。ask の説明に `docs/decisions/**` を追加。**配布 permissions がマスターのサブセットであり、最終的なルールは配布先に依存する**（dry-run 提示で調整する）ことを明記 |
| `docs/starter-kit.md` 手順 8 | スモークテストに「配置先の通常コマンド（依存インストール・テスト実行）が阻害されていないこと」を追加 |
| `.claude/hooks/validate-skill-edit.sh` | **Phase 3 の最後に配線する。** `case` に `assets` モードを追加（`*/.claude/hooks/*.sh` / `*/README.md` / `*/docs/starter-kit.md` / `*/scripts/deploy_skills.py`）。失敗時 `exit 2` + stderr で差し戻し。スクリプト不在時のフェイルオープンは維持 |

### Phase 4 — 出荷前の動作検証

| 対象 | 検証内容 |
|---|---|
| hooks 8 本 | フィクスチャで発火・誤検知を実測。ペイロードは公式 docs の実形式。`session-start-check.sh` / `session-stop.sh` は `.steering/` のフィクスチャを作って分岐を通す。`post-edit-lint.sh` / `stop-typecheck.sh` は**フェイルオープンの確認**（設定が無い環境で素通しすること）。`validate-skill-edit.sh` は skill / template / assets の 3 モード。`guard-env-read.sh` / `guard-gated-write.sh` は発火と誤検知 |
| 配置の実走 | tmpdir へ `--dry-run` 無しで実配置 → スキル員数・hooks の同送と登録・`source-commit` の打刻・`.gitignore` の 3 行を機械確認 → **生成された settings.json の deny に `npm install` 等が入っていないことを確認** → tmpdir 破棄 → `deployments.md` に副作用が残っていないことを確認 |
| ドリフト検出 | 実配置した tmpdir に対して `check_deploy_drift.py` を実行し、3 分類 + hooks 差分 + skill-issues 収集が動作することを確認（配置直後は差分ゼロが正常） |
| settings.json の逆方向 | hooks 登録があるのにファイルが無い、を検出する（契約 (b) は「ファイルがあるのに分類が無い」方向。逆も見る） |
| スキル本文 | 静的検査（29/29・portability 0）。**素通り検査は課金するため既定では回さない** — 出荷前に回すかはユーザーが判断する（承認ゲート系 5 本 × `--runs 4` = 20 run 相当。無料の代替は静的検査とフィクスチャ検証） |

### Phase 5 — 持ち出しセットへの最小反映と引き継ぎ

**スキル本文の突合はしない**（上記「`export/company/` の扱い」）。行うのは merge・hooks の突合・引き継ぎ文書の正確性の 3 点のみ。

| 対象 | 内容 |
|---|---|
| export worktree | main を merge する（`export/company/` 側の改変を潰さないことだけ確認。**内容の一致は検証しない**） |
| **契約 (f) の実行** | `export/company/claude-config/hooks/*.sh` に、既知の変換規則で説明できない差分が無いことを確認。**防御の欠陥が配布物側で開いていないか**の一点のみを見る |
| 配布物 hooks のフィクスチャ検証 | 5 本を master と同じケースで動かし、発火数・誤検知数を記録。master で動くことが export で動くことの証拠にならない（過去の実例）ため、安価な検証は行う |
| `export/company/MIGRATION-GUIDE.md` | **引き継ぎ文書としての正確性**を回復する（master との整合の話ではない）。`:119-120` の permissions 要約に `CLAUDE.md` / `docs/knowledge/**` / `docs/decisions/**` の ask が無く、hooks 登録の列挙に `guard-gated-write` が無い。**この文書は会社側 AI が読む一次情報の一部**なので、配布直前に誤った記述を残さない |
| `export/company/MANIFEST.md` / `HANDOVER.md` | 記述と実体の一致を確認するのみ（hook 本数 5 本・スキル 10 本は不変の見込み）。齟齬が無ければ変更しない |
| （成果物） | 引き継ぎ内容をユーザーに提示。**会社側の作業要否を明示**（未配布のため、持ち出し前に整合させれば会社側の作業は発生しない） |
| （起票） | rm / mv ポリシーの後続タスクを起票する。「対象外」節の内容をそのまま設計材料にする |

## データフロー

**契約突合（Phase 2・恒常）**

```
deploy_skills.py
  ├ expected_hooks()            ─┐
  ├ HOOK_REGISTRATIONS          ─┤
  ├ MASTER_ONLY_HOOKS           ─┤
  ├ DEPLOY_PERMISSIONS          ─┤
  └ MASTER_ONLY_PERMISSIONS     ─┤
                                 ├→ check_asset_consistency.py → PASS / FAIL(exit 1)
.claude/hooks/*.sh              ─┤                                対象不在 → exit 2
.claude/settings.json           ─┤
README.md                       ─┤
docs/starter-kit.md             ─┤
export/company/.../hooks/*.sh   ─┘   ← git worktree から自動発見

起動主体:
  PostToolUse(Edit|Write) → validate-skill-edit.sh の assets モード（Phase 3 の最後に配線）
  npm run validate:assets（人が叩く。validate には含めない）
```

**出荷前検証（Phase 4）**

```
マスター
  ├ hooks 8 本 ──→ フィクスチャ（公式 docs のペイロード形式）→ 発火数 / 誤検知数
  └ deploy_skills.py ──→ tmpdir へ実配置
                            ├→ スキル員数 / hooks 登録 / source-commit / .gitignore
                            ├→ settings.json の deny を読んで開発フロー阻害を確認
                            └→ check_deploy_drift.py で一周（差分ゼロが正常）
                          ↓
                        tmpdir 破棄・deployments.md の副作用ゼロを確認
```

## 影響範囲

- **既に配置済みのプロジェクトは無い**（`deployments.md` の有効行 0 件・`check_deploy_drift.py` が exit 2 で確認済み）。`DEPLOY_PERMISSIONS` 化による既存配置先への影響はゼロ
- **本タスクの直後に配布が行われる** — 検証の漏れは配置先での原因不明の摩擦になる。Phase 4 を省略可能な工程として扱わない
- **`validate-skill-edit.sh` の拡張は既存 2 モードへの回帰リスクがある** — SKILL.md 編集時の挙動が変わらないことを実測で確認する
- **配線を Phase 3 の最後にする理由** — 契約 (c) は着手時点で既に違反している（README 6/8）。先に配線すると Phase 3 の全編集が差し戻され、「契約を満たすため」ではなく「検査を黙らせるため」の修正を誘発する
- **配置の実走は `deployments.md` に副作用を残しうる** — `register_deployment` が呼ばれる経路を確認し、検証後にレジストリが元の状態であることを機械確認する
- **export worktree への反映はブランチをまたぐ** — main で直してから merge する順序を守り、`export/company/` 側の変換分を潰さない
- **rm / mv の穴は本タスクでは塞がらない** — 承認ゲートは書き込みのみを塞ぎ、削除・移動は素通しのまま出荷される。**この限界を `claude-code-config.md` と配布物の記述で正しく表現しているか**は Phase 3 で確認する（既に「削除は非対象」と明記済みだが、`mv` には触れていない）
- **課金なし**（既定）— 素通り検査を回さない限りエージェント起動の課金は発生しない

## テスト方針

- **静的（無回帰）**: 各 Phase 完了時に `validate_skills.py`（29/29）+ export セット（10/10・パス明示）+ `--portability`（0 件）+ `check_export_stopcontract.py`（7/1/2）+ `settings.json` の JSON 妥当性 + `bash -n` 全 hook
- **検査の実効性（Phase 2 の中核）**: `check_asset_consistency.py` を**故意に壊して落ちること**を 6 契約それぞれで確認する。全 PASS だけを見て「効いている」と判断しない
- **hooks（Phase 4）**: 8 本すべてをフィクスチャで動かし、**発火数と誤検知数を両方記録する**。ペイロードは公式 docs の実形式に揃える（`transcript_path` を含む — 全文検査系の hook が誤検知しないことの確認になる）
- **配置（Phase 4）**: 最小セット（`--skills tdd`）と条件付きセットの両方で dry-run が exit 0。その後 tmpdir へ実配置して成果物を機械確認
- **既存経路の無回帰**: `validate_skills.py` の 6 経路 / `validate-skill-edit.sh` の skill・template 2 モード / `check_deploy_drift.py` の 2 経路
- **実効性の限界（明記して閉じる）**: `validate-skill-edit.sh` の assets モードは PostToolUse なのでセッション中の追加でも効く見込みだが（`remind-config-docs.sh` の実績）、**確認できるまで「効いている」と書かない**

## 未解決の論点

**着手前に必要な論点は 20260726 に全て解決済み**（回答は「レビュー前に確定した決定」に反映）。

1. ~~`export/company/` は未配布か~~ — **解決済み: 未配布。** main と `export/company/` のチェックが済み次第、配布する。そのため Phase 4（出荷前の動作検証）を新設した
2. ~~`check_asset_consistency.py` を `npm run validate` に含めるか~~ — **解決済み: 別立て（`validate:assets`）**
3. ~~hook の判定を `ask` に統一するか~~ — **rm タスクへ移送。** ユーザー回答は「deny を使う」。ただし「対象外」節の技術的制約 (1) と衝突しうるため、rm タスクで設計し直す
4. ~~rm / mv の判定精度~~ — **rm タスクへ移送**
5. ~~配布 permissions が `MIGRATION-GUIDE.md:119` と矛盾するか~~ — **解決済み: 矛盾ではない。** セキュリティルールは配布先に依存する。`DEPLOY_PERMISSIONS` はベースラインで、最終形は配置時に調整する
6. ~~`guard-gated-write.sh` のリネーム~~ — **前提が消滅。** rm / mv を切り出した結果この hook は書き込み専用のままなので、名前と実態は一致する。リネームの是非は rm タスクで再検討する

**実装中に判断が要る可能性があるもの**:

- **Phase 4 で新たな不具合が見つかった場合の扱い** — 配布前提のため「見つけたが直さない」は選びにくい。ただしスコープが膨らむ場合は、**配布をブロックするか否か**で切り分ける（ブロックするなら本タスク内で直す / しないなら起票して配布を進める）

## プレモータム所見（design-premortem）

フレッシュな subagent による敵対的レビューを実施し、**公式 docs（`code.claude.com/docs/en/hooks`）とリポジトリ実物で裏取り**したうえで反映した。指摘 14 件。

> **注（20260726・スコープ変更後）**: 下記のうち rm / mv ポリシーに関する 6 件は、Phase 1 の切り出しに伴い**別タスクへ移送**した。技術的な結論は「対象外」節の表に保存してあり、失われていない。本タスクに残るのは 6 件 + 空振り 3 点。

**本タスクに残る反映済み: 6 件**

- 攻撃: `export/company/claude-config/hooks/guard-gated-write.sh` は手写しの第 2 実体で、契約 (a)〜(e) のどれも突合しない。`check_export_stopcontract.py` は skills の停止契約語彙しか比較しない
  影響: このタスクが撲滅を掲げる「単一情報源が実は 2 つある」を、防御コードそのもので新規に制度化する。しかも「機械検査があるから大丈夫」という誤った安心とセットになる
  提案 → 反映: **契約 (f) を追加**。worktree 自動発見 + 不在時 exit 2 で `check_export_stopcontract.py` に揃える
- 攻撃: 完了条件「dry-run が出力する settings.json を assert」は実行不能。`deploy_skills.py:210-220` の実測で、配置先に settings.json が**無い**場合の dry-run は payload を出力しない
  影響: 中核の検証手段が最初から成り立たず、実装時に場当たりで本番実行に流れて `deployments.md` への登録という副作用を伴う検証を回すリスクがある
  提案 → 反映: **dry-run でも payload をログ出力する**を Phase 1 に追加。完了条件をそれ前提に書き換え。**さらにスコープ変更後は、配置の実走そのものを Phase 4 に正式な工程として入れ、`deployments.md` の副作用確認を完了条件にした**
- 攻撃: 契約 (b) には比較先の単一情報源が存在しない。master-only の分類は `deploy_skills.py:161-165` の**docstring 散文**にしかない。かつ完了条件「8 本すべてが分類済み」は着手前から実質満たされている
  影響: 実装時に「散文をパースする」か「新しい定数を作る」の判断が発生し、前者を選ぶと壊れやすい検査が生まれる
  提案 → 反映: `MASTER_ONLY_HOOKS` を定数として新設。(b) を**集合等価**にし、完了条件を「hook を 1 本足すと落ちる」に書き換え
- 攻撃: Phase（hook 配線）をドキュメント修正より先に置くと、契約 (c) が既に違反しているため assets モードが鳴り続ける
  影響: 正しい編集なのに差し戻しが続いて警報疲れが起き、最悪「検査を黙らせるため」に (c)(d) を緩める修正が入る
  提案 → 反映: `validate-skill-edit.sh` への配線を **Phase 3 の最後**に移動
- 攻撃: 契約 (d) だけ書式依存で、(c) を採用した論理と矛盾する。実測で `docs/starter-kit.md` の `.sh` 言及は手順 6 以外にも `:47` `:48` `:104` に存在する
  影響: 節を 1 つ挿入しただけで偽 FAIL / 偽 PASS になる。偽 PASS の方が危険で、**今回まさに直そうとしている欠陥**を検査が見逃す
  提案 → 反映: (d) を全文集合への**包含判定**に変更（等価をやめる）
- 攻撃: 契約 (e) が片方向で、`DEPLOY_PERMISSIONS` にあって master に無いルールを検出しない。目的節の「現実的なセット構成は全滅」も実態より狭く、実測では `--skills tdd` 単独でも `KeyError` で落ちる
  影響: `DEPLOY_PERMISSIONS` が master から静かにドリフトしても誰も気づかない。かつ完了条件が条件付き経路 1 パターンしかテストせず無条件経路の回帰が守られない
  提案 → 反映: (e) を**双方向**に。目的節を「全構成が落ちる」に訂正し、完了条件に最小セット（`--skills tdd`）の dry-run を追加

**別タスクへ移送: 6 件**（技術的結論は「対象外」節に保存）

全文検査では rm のパス判定ができない（`transcript_path` が全ペイロードに入る）／`Bash(rm -rf /*)` がプロジェクト内の絶対パスに前置一致する／hook は permissions の deny を救済できない（評価順は hook → permissions）／`rm -fr` が permissions の網から消える／`mv` が削除と等価にゲートを破る／非対話モードでは hook の ask が deny に落ちる

**分類を変えた / 反論した: 1 件**

- 攻撃「`.claude/settings.local.json` が allow 26 件・`Bash(cd *)` を含み、Phase 1 の検証結果が他マシンで再現しない」→ **部分的に反論**。実測すると allow は 23 件で **ask / deny は 0 件**。検証への影響は無い。ただし「契約の射程外だと明記すべき」は妥当なのでスコープの対象外に記載した

**空振り（設計として妥当と確認された）: 3 点**

- `deploy_skills.py` を import して単一情報源にする案 — トップレベルは定数定義のみで副作用ゼロ、`main()` は `__main__` ガード下。`check_deploy_drift.py:48-49` に前例あり
- README 全文の `*.sh` 集合比較（契約 c）— 実測で 6 種すべてが hooks のファイル名でノイズ 0 件。「現在 6/8」も正確
- 無回帰条件のベースライン数値（29/29・10/10・7/1/2）はすべて実測と一致

（このスキルは設計を承認しない。人間のレビューに戻る）

## 検討した代替案

- **契約突合を `validate_skills.py` に統合** — 却下。ファイル名が実態とずれ、既に 6 経路ある引数分岐がさらに増える。`--skill` で hook が呼ぶ既存経路への回帰リスクを負う理由がない
- **`deploy_skills.py` の import 時 assert だけで済ませる** — 却下。(a) は塞がるが (c)(d) のドキュメント漏れが残り、「なぜ毎回反映が漏れるのか」の主要部分が未解決のままになる
- **配布 permissions を「丸ごとコピー + 除外リスト」** — 却下。新しい deny を足すたびに除外判断が要り、判断し忘れると配置先が壊れる方向（フェイルオープン）に倒れる
- **配置時に settings.json を書かず常に手動マージ案の提示に留める** — 却下。hook をコピーしたのに登録されていない中途半端な状態が生まれうる
- **README のツリーを構文解析して突合する** — 却下。書式変更で壊れる。`*.sh` の集合比較なら書式非依存
- **starter-kit も節境界をパースして等価比較する** — 却下（プレモータム反映）。手順 6 以外にも `.sh` 言及があり、節の挿入で偽 PASS を生む
- **出荷前検証を dry-run だけで済ませる** — 却下（スコープ変更後）。dry-run は `HOOK_REGISTRATIONS` の欠落を検出したが、`source-commit` の打刻・`.gitignore` の追記・生成された settings.json の実際の内容は実配置しないと確認できない。配布が直後に控えている以上、tmpdir への実走のコストは安い
- **rm / mv ポリシーを本タスクに含める（当初案）** — 却下（20260726 のユーザー判断）。配置機構の修復とは独立した問題であり、混ぜると配布のブロッカーが増える。技術的制約は調査済みなので次タスクは調査から始めずに済む
