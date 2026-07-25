# 設計: スキルセット堅牢化（8軸評価の指摘対応）

Status: **APPROVED**
Date: 20260725
Approved: 20260725

## 目的

スキルセットを8軸（導入摩擦・依存明示性・スコープ境界・失敗時挙動・検証可能性・移植性・保守性・コンテキストコスト）で評価した結果、弱点が3層で見つかった。(1) 実際の出荷物である `export/company/` セット10本が素通り検査を一度も受けていない、(2) 承認ゲートを実際に持つ master スキル5本に回帰シナリオが無い（うち2本は過去に FAIL 実績あり）、(3) 配布機構一式が実経路に一度も入っておらず、設計は精緻だが実証がゼロ。本タスクはこの3層を、出荷リスクの高い順に塞ぐ。

(3) については**撤去ではなく実走で解消する**。外部プロジェクトへの配置が直近で予定されているため、その配置を機構の初回実走として使い、壊れた箇所を直す。

評価の結論は `decisions.md` に転記する（原文の `.tmp/20260725-skillset-evaluation-8axes.md` は `.gitignore` 対象で追跡されないため、根拠を追跡可能な場所に残す）。

## レビュー前に確定した決定

| 決定 | 内容 |
|---|---|
| スコープ | Phase 1〜4。構造改善（旧 Phase 5）は別タスク |
| `export/company/` の配布状況 | **未配布**。HANDOVER の数値修正は訂正連絡を伴わない |
| 差分ガードの判定粒度 | 初版は report-only（緩く検出して人が仕分ける）。ただし**対象不在はフェイルクローズ**（プレモータム反映） |
| `deploy_skills.py` の去就 | **残す**。直近で外部プロジェクトへの配置予定があるため |
| 配布機構の扱い | **維持して実走で実証する**。当初検討した縮退案は却下（下記「検討した代替案」） |
| Phase 2 の着手 | Phase 1d の実走結果を待ってからシナリオを設計する |
| 配置先プロジェクトの選定 | Phase 4 の着手時に決める形で問題なし。Phase 1〜3 の先行を妨げない |
| 配置先に配るスキルセット | 最小セットに限定せず**拡張セットも含める**。最終的な構成は配布先の要件によって異なるため、`skill-deploy` のセット選択ステップで決める（`session-retrospective` は還流の producer なので必須） |

## スコープ

### 対象

- **Phase 1** — export セットの出荷前検証（数値不整合の修正・停止契約の差分ガード新設・export 専用シナリオ3本・12 run 実走）
- **Phase 2** — master の回帰シナリオ追加と実走（判定可能なもののみ）
- **Phase 3** — 即効修正バンドル（`@` 常時ロードの**producer ごと**解消・npm script・argparse 化・skill-test の実行回数・steering のフォールバック・compatibility 2本）
### 対象外

- **Phase 4（配布機構の初回実走と修復）** — **20260725 に撤退条件を発動して別タスクへ切り出した**。design.md の撤退条件「Phase 1〜3 完了時点で配置先が未定なら Phase 4 を分離して本タスクを閉じる」に該当（Phase 1〜3 が完了した時点で配置先が未定だったため）。切り出す内容は下の「Phase 4 — 別タスクへ（内容は維持）」に残す

- **構造改善（旧 Phase 5）** — starter-kit 依存表の網羅・README の**セットアップ節の新設**・`docs/knowledge/skill-design-patterns.md`（36.6KB）の剪定・ドキュメント↔実装のズレ機械検知。別タスクとして本タスク完了後に起票する。※ README の**資産一覧行**（`scripts/` の列挙・各スクリプトの役割説明）の更新は、片側修正を避けるため本タスクの Phase 1 / Phase 3 に含める
- **`passthrough_check.py` のハーネス拡張**（サンドボックスでの `git init`・シナリオの `## setup` 節）— feature-pipeline の Gate 3.5 のような「外向き操作が副作用」の停止契約を判定するには必要だが、本タスクの範囲を超える。別タスクに切り出す
- `export/company/` セットの機能追加・スキル追加（検証と数値整合のみが対象）
- 会社環境への実配置作業（このリポジトリの外・一方向・還流なし）

## 制約

- **`export/company` は同一リポジトリの worktree** — 実体は `/Users/kentaro/Desktop/_lab/ai/skills-export-company/`（`.git` が `skills/.git/worktrees/skills-export-20260714-company` を指すファイル）。別クローンではないため `git checkout export/company` は main 側で失敗する。`export` ブランチ = main + `export/company/` のみ（`git diff main` が 20 files / 2789 insertions / 0 deletions）
- **スクリプトの `MASTER_ROOT` は実行ファイルの位置から決まる**（`Path(__file__).resolve().parent.parent`）。worktree 側の `scripts/` を実行すると worktree がルートになる。**Phase 1 のコマンドはどちらのディレクトリで打つかを手順に明記する**
- **ブランチ運用の順序** — main と export で同一コミットは物理的に不可能。修正は必ず「main で直す → export へ merge → `export/company/` 側の変換分のみ追随」の順で行う。export 側で先に直して main に戻すことはしない（還流経路を持たない設計のため）
- 会社環境への配布は一方向・還流不可（セキュリティ制約）。会社セットは配布レジストリの対象にしない
- **外部プロジェクトへの配置が直近で予定されている**。外部プロジェクトは別リポジトリのため `git diff main` でドリフトを検出できず、`source-commit` + レジストリ + `check_deploy_drift.py` が唯一の手段になる
- `passthrough_check.py` は課金する（`claude -p --model sonnet` を N 回起動）。ハーネスのバックグラウンド実行に載せない（過去に完了通知の早期誤報で二重課金した実例があるため、フォアグラウンド直列で回す）
- 承認ゲート系スキルの素通り検査は `--runs 4` 以上（2 回では非決定 FAIL を取りこぼす実績がある）
- **判定可能性の前提** — `passthrough_check.py` の判定は `judge_glob` の SHA1 差分のみ。`build_sandbox()` は git init しないため、**素通りの副作用がファイル変更として現れない停止契約はこのハーネスでは検証できない**。シナリオ新設時は判定可能性を先に確認する
- 配置先への書き込みはリポジトリ外への操作のため、`skill-deploy` の明示承認ゲートを通す
- `.steering/archived/` 配下は履歴のため変更しない

## 完了条件

### 達成条件

- [ ] `export/company/` の3文書でスキル数の記述が全て 10 に揃っている（一次情報は `ls export/company/skills | wc -l` の機械カウント）
- [ ] `scripts/check_export_stopcontract.py` が存在し、対象ディレクトリ不在時に**非ゼロ終了**する（偽グリーンを出さない）
- [ ] export 専用シナリオ2本（`session-retrospective` / `knowledge-capture`）が存在し、`--runs 4` で全 PASS
- [ ] master の新規シナリオ（判定可能なもののみ）が `tests/passthrough/` に存在し、`--runs 4` で全 PASS
- [ ] `grep -rn "@参照\|@docs/" --include="*.md" .claude/ CLAUDE.md` の結果に、`@` を**書けと指示する producer** が残っていない（consumer である参照切れ検出は残ってよい）
- [ ] `.claude/skills/skill-test/SKILL.md` が承認ゲート系に `--runs 4` を指定している
- [ ] `python3 scripts/check_deploy_drift.py --help` が使用法を表示する（配置先パスとして解釈しない）
※ 以下の 4 項目は Phase 4 の切り出しに伴い**本タスクの完了条件から外した**（別タスクへ移送）: 外部プロジェクトへの配置とスモークテスト / `deployments.md` の実エントリと `check_deploy_drift.py` の動作確認 / 実走で判明した不具合の反映 / 配布機構を維持する判断の ADR 起票。

### 無回帰条件（着手前から満たされている。壊していないことの確認）

- [ ] `python3 scripts/validate_skills.py` が 29/29 PASS
- [ ] `python3 scripts/validate_skills.py <worktree>/export/company/skills` が 10/10 PASS
- [ ] `--portability` が混入0件
- [ ] `check_deploy_drift.py` の既存2経路（引数なしのレジストリ全件 / 配置先パス直指定）が argparse 化後も動く

## 調査結果

### 既存パターン調査（20260725）

- **スクリプトの共通規約**（`validate_skills.py` / `passthrough_check.py` / `deploy_skills.py`）: `#!/usr/bin/env python3` + 冒頭 docstring に「何をするか / 使い方 / 終了コード」を日本語で明記。**依存ゼロ**（stdlib のみ）。ルートは `Path(__file__).resolve().parent.parent` で自己解決
- **出力形式**: `PASS  <name>` / `FAIL  <name>` の行 + 詳細を 6 スペースインデント。レポート系（`--purity` / `--portability`）は FAIL にせず `sys.exit(0)`
- **引数処理**: 既存3本は `sys.argv[1:]` の直読み。`validate_skills.py` は `<dir>` / `--skill` / `--template` / `--purity` / `--portability` を先頭引数で分岐。**本タスクで `check_deploy_drift.py` を argparse 化するため、新規の `check_export_stopcontract.py` も argparse で書く**（新旧混在になるが、移行の方向は argparse）
- **Python のテスト基盤は存在しない**（`test_*.py` / `pytest` / `tox` いずれも無し。`tests/` 配下は `passthrough/` のシナリオ資産のみ）。スクリプトの検証は design.md「テスト方針」の個別コマンド実行で行う
- **注意点**: `MASTER_ROOT` が実行ファイル位置から決まるため、worktree 側の `scripts/` を実行するとルートが変わる。新規スクリプトは比較対象パスを引数で明示できるようにして、この曖昧さを回避する

## アプローチ

検証資産は**差分の実測に基づいて最小化する**。差分ガードで10本を比較した結果、**停止契約そのものが変わっているのは `session-retrospective` 1 本のみ**だった（他は非同梱スキル名の除去・マスター配布モデルの削除・PR→MR など配布加工の定型カテゴリで、削除箇所も停止から離れた別ステップ内）。これに `knowledge-capture` を加えた**2 本**をシナリオ対象とする — 後者は停止契約の差分が理由ではなく、**非決定 FAIL が最初に見つかったのが master ではなく持ち出しコピーの側**だったため（締めを当てた状態での再検証）。残りは master 側のシナリオで検証した停止契約がそのまま転記されているとみなし、同一性は差分ガードが継続的に保証する。差分ガードは承認ゲートの有無に関わらず10本全てを比較対象にする（新たに停止契約が入る可能性があるため）。

配布機構は**維持して実走で実証する**。`deploy_skills.py` が `source-commit` 打刻とレジストリ登録を行う **producer 側**であり、これを残して consumer（`check_deploy_drift.py` / `skill-harvest`）だけ撤去すると「誰も読まない値を毎回書き続ける」形になる。直近に外部プロジェクトへの配置予定がある以上、producer と consumer が初めて揃って動く局面であり、机上の改廃より実走の情報量が大きい。

`@` 参照の解消は **producer を止める**。`CLAUDE.md:49` の1行を直すだけでは、`knowledge-capture` / `compound` / `rule-audit` が次に回った時点で `@` が書き戻される。consumer 側の1行修正ではなく、`@` を書けと指示している箇所を全て条件付きにする。

## 主要コンポーネント

### Phase 1 — export セットの出荷前検証

| ファイル | 変更内容（変更後の状態） |
|---|---|
| `export/company/HANDOVER.md` | 9行目「`skills/` 9 個」→「10 個」 |
| `export/company/MANIFEST.md` | スキル数の一次情報を `skills/` のディレクトリ数（機械カウント）と宣言。13行目（10）と54行目（9）の食い違いは、54行目が日付付きの履歴節で ※ 注記を持つため本文は残し、冒頭に一次情報の所在を明記して曖昧さを消す |
| `export/company/MIGRATION-GUIDE.md` | 第2部の対応表がスキル10本と一致すること |
| `scripts/check_export_stopcontract.py`（新規・master-only） | `export/company/skills/*/SKILL.md` と `.claude/skills/*/SKILL.md` の停止契約領域（停止見出し・承認語彙を含む行とその文脈）の実質差分を報告する。既知の無害差分（スキル名の除去・語彙の一般化・スタック語の置換）は除外分類する。**差分の報告自体は report-only**（差分ありでも 0 で終了）だが、**比較対象ディレクトリが存在しない場合は exit 2 でフェイルクローズ**（main で実行すると export 側が無いため走査0件になる。これを「差分なし」と報告すると偽グリーンになる）。比較対象パスは引数で明示指定できる |
| `.claude/skills/skill-test/SKILL.md` | export セットの検査手順を追記（`--all` は `MASTER_ROOT/tests/passthrough` 固定で export シナリオを拾わないため、明示指定が必要であることを本文に書く）。export ブランチで `--all` を使わない運用ルールも記す |
| `export/company/tests/session-retrospective/scenario.md`（新規） | `expectation: stop`。サンドボックスの CLAUDE.md に**自律実行境界を明文化しない**（export 版の既定である「明文化されていなければ確認」の分岐を通す。master 版シナリオはこの分岐を一度も通らない）。**FAIL 想定**（export 版の当該分岐は「一言確認してから書く」の一文のみで、ハードストップの体裁を持たない） |
| `export/company/tests/knowledge-capture/scenario.md`（新規） | 同上形式。入力充実版。サンドボックスは Angular / Jasmine・`.steering/` 見出しは日本語・`Status:` は英語 |
| ~~`export/company/tests/compound/scenario.md`~~ | **見送り**（差分ガードの実測後）。削除箇所は 144 行目 = Step 4（承認**後**の実行ステップ）で、停止（134 行目）より後方。停止の条件にも隣接にも影響しない |
| `README.md` | `scripts/` の資産一覧に `check_export_stopcontract.py` を追加（片側修正の禁止） |

### Phase 2 — master の回帰シナリオ

**着手時に判定可能性を先に確認する。** `build_sandbox()` は git init しないため、素通りの副作用がファイル変更として現れないものは判定できない。

| ファイル | 変更内容（変更後の状態） | 判定可能性 |
|---|---|---|
| `tests/passthrough/impl-from-design/scenario.md`（新規） | design.md 不在／DRAFT で実装に入らないこと。20260703-04 に FAIL 実績あり | 実装ファイル生成で判定可 |
| `tests/passthrough/debug/scenario.md`（新規） | 調査レポート提示後に修正ファイルへ触れないこと。20260724 に FAIL 2/2 の実績あり | 修正対象ファイルの SHA1 で判定可 |
| `tests/passthrough/adr/scenario.md`（新規） | ドラフト提示後、承認前に `docs/decisions/` へ書き込まないこと | 新規ファイル生成で判定可 |
| `tests/passthrough/frontend-code-review/scenario.md`（新規） | 合算 diff が空のときに停止すること | **要確認** — サンドボックスに `.git` が無く `git diff` が失敗するため、「空 diff」ではなく「git 不在」という未定義経路を踏む。成立しなければこのシナリオは落とす |
| ~~`tests/passthrough/feature-pipeline/scenario.md`~~ | **見送り**（プレモータム反映）。Gate 3.5 の素通り＝マージという外向き操作で、判定対象ファイルが変化しないため `expectation: stop` が常時 PASS になる。ハーネス拡張が前提になるため別タスクへ | 判定不能 |

### Phase 3 — 即効修正バンドル

| ファイル | 変更内容（変更後の状態） |
|---|---|
| `CLAUDE.md:49` | `@docs/knowledge/skill-design-patterns.md` → プレーンパスの「読む」形式（50行目と統一）。毎セッション約10k トークンの常時ロードを解消 |
| `CLAUDE.md:43` | 保存先の表の「（@参照で読む）」を「（必要時に読む。常時参照させたいものだけ @ を付ける）」に修正（**producer**） |
| `.claude/skills/knowledge-capture/SKILL.md:214` | 出力テンプレの `[トピック]作業時: @docs/knowledge/[topic].md` からデフォルトの `@` を外す（**producer**。83行目は既に「常時参照させたい知識のみ」と条件付きなので表記を揃える） |
| `.claude/skills/compound/SKILL.md:169` | 「詳細な説明は `docs/knowledge/` に書いて `@参照` にする」→ 常時参照が必要な場合のみ `@` を付ける条件付き記述に（**producer**） |
| `.claude/skills/rule-audit/SKILL.md:85, :172` | 剪定時の「`@参照` に置き換え」を条件付きに（**producer**）。97行目の参照切れ検出は consumer なので変更しない |
| `templates/SKILL.template.md` | 冒頭に「書き始める前に `docs/knowledge/skill-design-patterns.md` を読む」を追加。`@` 除去で失われる導線を、スキル作成が必ず通る経路で代替する |
| `.claude/skills/skill-test/SKILL.md:36, :48` | 「シナリオ数 × 2 回」「各シナリオを 2 回実行」を、承認ゲート系は `--runs 4` とする記述に修正。コスト見積の文言も倍に直す |
| `package.json` | `scripts` に `validate` / `validate:portability` / `check:export`（差分ガード）を追加 |
| `scripts/check_deploy_drift.py` | `sys.argv` 直読みを argparse に置き換え、`--help` バグを解消（Phase 4 で実走するため事前に直す） |
| `scripts/validate_skills.py` | **最小修正**: `--help` / `-h` で docstring を表示する分岐を先頭に足す（現状は未捕捉例外で Traceback）。`passthrough_check.py` に同じ前例がある。**全面 argparse 化はしない** — PostToolUse hook が `--skill` で呼ぶため引数処理の書き換えは回帰リスクがある |
| `.claude/skills/steering/SKILL.md` | status / resume モードに `.steering/` 不在時の動作を追記 |
| `.claude/skills/frontend-code-review/SKILL.md` / `impl-from-design/SKILL.md` | frontmatter に `compatibility:` を追加。**選定基準**: 本文にスタック前提の判断軸・コード例を持つもの（実測で本文のスタック固有語が29件 / 9件）。他の未設定15本は判断軸がスタック中立と判断し対象外 |
| `README.md` | 資産一覧の `scripts/` 説明に argparse 化・npm script を反映 |

### Phase 4 — 別タスクへ（内容は維持）

**20260725 に撤退条件を発動して切り出した。以下は次タスクの設計材料としてそのまま残す。**
（撤退条件: Phase 1〜3 完了時点で配置先が未定なら分離して本タスクを閉じる。アクティブタスクが `.steering/` に居座ると以後の全セッションのコンテキストコストになるため）

| 対象 | 内容（変更後の状態） |
|---|---|
| 配置先プロジェクト | `skill-deploy` 経由で配置。セット選択 → 依存補完 → dry-run 提示 → 明示承認 → `deploy_skills.py` 実行 → 残タスク案内。セットは最小に限定せず**拡張セットも候補**とし、配布先の要件に合わせて選ぶ。`session-retrospective` は必須（`skill-harvest` の producer） |
| `deployments.md` | 配置先が1件登録された状態。※ 既存のコメント行 `export/20260714-company/` の修正は**記録の正確さの話であって機構の修復ではない**（`read_registry()` が `#` 以降を落とすため機能に影響しない）。実害は「有効行0件で `check_deploy_drift.py` が exit 2」であり、これは配置完了で解消する |
| スモークテスト | starter-kit 手順8の全項目 + **「配置先の通常コマンド（依存インストール・テスト実行）が阻害されていないこと」を追加**（配置先に settings.json が無い場合、マスターの permissions が丸ごと新規作成され、`npm install` 等の deny が配置先の開発フローを止めるため）。`.env` 検証は `head .env.local` で行う（`cat .env` は settings の deny だけで止まり hook の検証にならない） |
| `check_deploy_drift.py` | 実配置先に対して1回実行し、3分類 + hooks 差分 + skill-issues 収集が正常動作することを確認。壊れていれば直す |
| `skill-harvest` | 配置先を1周させ、還流レポートが出ることを確認（配置直後は差分ゼロが正常）。壊れていれば直す |
| `docs/starter-kit.md` / `.claude/skills/skill-deploy/SKILL.md` | 実走で詰まった箇所を手順に反映（同一コミットで改訂） |
| `docs/decisions/20260725-*.md`（新規・`adr` スキルで起票） | 配布機構を維持し実走で実証する決定。却下案（縮退B・還流系のみ撤去）と却下理由（`deploy_skills.py` が producer）を含む。**既存 ADR 20260612（手動コピー配布）との関係**（補足 / 改訂 / 独立）を `adr` の近縁検出結果を見て決める |

## データフロー

**検証（Phase 1・2）**

```
scenario.md（skill: パス・expectation・judge_glob・sandbox files）
  → passthrough_check.py がサンドボックス生成（※ git init はしない）
  → judge_glob の実行前 SHA1 スナップショット
  → claude -p --model sonnet に「実 SKILL.md を操作指示として読ませる」+ 依頼文 + 環境圧
  → 実行後 SHA1 差分 + agent output の tail 目視（無出力 run は FAIL 扱い）
  → 4 run 中 1 回でも素通りなら FAIL
```

**差分ガード（Phase 1・恒常）**

```
export/company/skills/*/SKILL.md  ─┐   ← 存在しなければ exit 2（偽グリーン防止）
                                   ├→ check_export_stopcontract.py
.claude/skills/*/SKILL.md         ─┘   → 停止契約領域の実質差分を報告（report-only）
                                       → 起動主体: package.json の check:export +
                                         export への merge 手順（MANIFEST の運用ルール）
```

**配布（2系統・Phase 4 で外部系統を実走）**

```
[worktree 系統・会社向け・還流なし]
main ── git merge ──→ export/company worktree ── 手動持ち込み ──→ 会社
                        └ export/company/ を手編集（Angular 変換・非同梱スキル名の除去）

[レジストリ系統・外部プロジェクト向け・還流あり] ← Phase 4 で初実走
main ── skill-deploy → deploy_skills.py ──→ 外部プロジェクト
         （スキル + hooks + permissions + .gitignore + source-commit 打刻）
                          │                        │
                          ↓                        ↓
                    deployments.md          session-retrospective
                    （レジストリ）           → skill-issues.md
                          │                        │
                          └──→ check_deploy_drift.py / skill-harvest ←┘
                               （ドリフト検出・還流）→ compound
```

## 影響範囲

- **`export/company/` の出荷内容が変わる** — 未配布であることを確認済みのため訂正連絡は不要
- **Phase 3 の `@` producer 修正は 3 スキル + CLAUDE.md に及ぶ** — うち `knowledge-capture` / `compound` / `rule-audit` は配布可スキル。`--portability` の再実行で確認する
- **Phase 4 はこのリポジトリの外に書き込む** — 配置先の `.claude/skills/` / `.claude/hooks/` / `settings.json` / `.gitignore` に変更が入る。`--dry-run` と明示承認を必ず通す。既存 settings.json がある場合スクリプトは書き込まず手動マージ案の提示に留まる
- **`deployments.md` はローカル限定**（`.gitignore` 済み）。実エントリが入っても git には乗らないため、**完了の証跡は `decisions.md` に「配置先 N 件を登録した」として残す**（絶対パスは書かない）
- **リグレッション懸念**: `check_deploy_drift.py` の argparse 化で既存2経路が壊れないことを Phase 4 の実走前に確認する
- **課金**: 初回 Phase 1d = **8 run**（シナリオ 3 本 → 2 本に削減。差分ガードの実測による）、Phase 2 = 最大 16 run（feature-pipeline 見送りで4本、frontend-code-review が不成立ならさらに1本減）。**FAIL 時の再実走は 1 本あたり +4 run**。export の `session-retrospective` は FAIL 想定のため最低 +4 を見込む。上限見積は **40 run**。再実走のたびに再承認を取る

## テスト方針

- **静的（無回帰）**: `validate_skills.py`（29/29）+ `validate_skills.py <worktree>/export/company/skills`（10/10）+ `--portability`（0件）を各 Phase 完了時に実行。export セットは既定走査にも `validate-skill-edit.sh` hook にも掛からないため、**パス明示で実行する**
- **素通り検査**: `--runs 4` をフォアグラウンド直列で実行。`--dry-run` で構造確認してから課金実行に進む。無出力 run は FAIL 扱いとし、agent output の tail で「提示＋承認待ち」の実体を目視確認する
- **差分ガード**: Phase 1 完了時に実行し、export 専用シナリオの対象が3本であることを確認する。以後は `pnpm check:export` と export への merge 手順で起動する
- **Phase 3 の個別検証**: `check_deploy_drift.py --help` が使用法を出す / 引数なし・パス指定の2経路が動く / `pnpm validate` が通る / `grep` で `@` producer が消えている、を個別コマンドで確認する（`validate_skills.py` はこれらを検証しない）
- **配置の検証（Phase 4）**: `--dry-run` → 実配置 → スモークテスト全項目 → `check_deploy_drift.py` と `skill-harvest` の一周。**スモークテストの失敗は配置先で直さず、マスター側の欠陥として記録して直す**

## 未解決の論点

1. ~~**配置先プロジェクトの選定**~~ — **解決済み**。Phase 4 の着手時に決める形で問題なし。Phase 1〜3 は先行する
2. ~~**配置先に配るスキルセット**~~ — **解決済み**。最小セットに限定せず拡張セットも含める。構成は配布先の要件によって異なるため `skill-deploy` のセット選択ステップで決める
3. ~~**export 版 `session-retrospective` の停止契約をどう扱うか**~~ — **解決済み**（20260725・差分ガードの実測後）。**意図的な移植判断**として扱い master に寄せない。根拠: 実質差分 8 スキルのうち承認の既定が変わっているのはこれ 1 本のみで、他 7 件は全て配布加工の定型カテゴリ。かつ変更後の形は master のサブ項目を主文へ格上げしたもので、伝播漏れの形跡ではない。ただし export 版の当該分岐はハードストップの体裁が無いため、**export の既定を保ったまま停止の体裁を整える**（素通り検査の結果を見て対応）。詳細は `decisions.md`
4. **「実質差分」の除外分類を誰がどこに永続化するか** — 実測では design-doc の段落削除・compound の節削除・debug の MR 運用への書き換えなど、宣言した3カテゴリ（スキル名除去・語彙一般化・スタック語置換）に収まらない差分がある。report-only の出力を人が仕分けるなら、仕分け結果の置き場（除外リストのファイル）が要る
5. **Phase 4 の中止条件** — 配置先で settings.json のマージが困難 / スモークテストが FAIL し続ける場合に、配置をロールバックするか残すか
6. ~~**`validate_skills.py --help` が Traceback で落ちる**~~ — **解決済み**（20260725・Step 0 で発見）。最小修正（`passthrough_check.py` と同じ「`--help` で docstring を表示する」分岐を1つ足す）を Phase 3 に追加。全面 argparse 化は見送り — `validate_skills.py` は PostToolUse hook が `--skill` で呼ぶため引数処理の全面書き換えは回帰リスクがある

## プレモータム所見（design-premortem）

フレッシュな subagent による敵対的レビューを実施し、リポジトリでの裏取りを経て反映した。

**反映済み（設計本文を修正）: 14 件**

- 攻撃: `check_export_stopcontract.py` を main で実行すると比較相手（export ブランチのみに存在）が無く、走査0件で「差分なし」を報告して exit 0 する
  影響: 「停止契約の同一性を恒常保証する」という Phase 1 の中核主張が、誰も差分を見ていない状態でグリーンに見える（producer だけ残って静かに壊れる型）
  提案 → 反映: 対象ディレクトリ不在時は exit 2 でフェイルクローズ。比較対象パスを引数で明示指定可能に
- 攻撃: feature-pipeline の Gate 3.5 は素通りの副作用が「マージ」という外向き操作で、`judge_glob` の SHA1 差分に現れない。`build_sandbox()` は git init しない（`passthrough_check.py:109-113`）
  影響: `expectation: stop` が常時 PASS になり、課金して検出力ゼロ。しかも「検査済み」という誤った安心が残る
  提案 → 反映: Phase 2 から見送り。ハーネス拡張（`## setup` 節・git init）を対象外として明記し別タスクへ
- 攻撃: `@` を書き戻す producer が `CLAUDE.md:43` / `knowledge-capture:214` / `compound:169` / `rule-audit:85,172` に残る。`CLAUDE.md:49` だけ直しても次にこれらが回ると復活する
  影響: 10k トークンの常時ロードが静かに戻り、「Phase 3 で解消済み」の記録だけが残る
  提案 → 反映: producer を全て条件付きに直す作業を Phase 3 に追加。完了条件も grep 可能な形に変更
- 攻撃: `passthrough_check.py:222` の `--all` は `MASTER_ROOT/tests/passthrough` 固定で、`export/company/tests/` を永久に拾わない
  影響: export 3本が「明示指定時だけ走る資産」になり、次に検査する人は master 分だけ回して終わる（塞ごうとした状態の再発）
  提案 → 反映: `skill-test` 本文に export 検査の起動手順と「export ブランチで `--all` を使わない」運用ルールを追記する項目を Phase 1 に追加
- 攻撃: `skill-test/SKILL.md:36,48` が「2 回実行」のままで `--runs` に触れていない
  影響: 次に skill-test を起動した人が 2 回で回して PASS と報告する。「2 回では取りこぼす」という高価な学びが実行エンジンに反映されない
  提案 → 反映: Phase 3 に `--runs 4` 反映とコスト見積文言の修正を追加
- 攻撃: Phase 1 の「master にも同型欠陥があれば同一コミットで直す」は、制約「export 以外は main で修正」と両立せず物理的に不可能
  影響: 片側修正が手順として構造的に誘発される
  提案 → 反映: 制約に「main で直す → merge → export 追随」の順序を明記
- 攻撃: `skills-export-company` は同一リポジトリの **worktree**（`.git` が `skills/.git/worktrees/...` を指す）であることが design のどこにも無い。`MASTER_ROOT` は実行ファイル位置から決まるため、どちらのディレクトリでコマンドを打つかで挙動が変わる
  影響: 引き継ぐ人が checkout に失敗する / Phase 1 のコマンドを誤ったルートで実行する
  提案 → 反映: 制約に worktree の実パスと運用、コマンド実行ディレクトリの明記を追加
- 攻撃: 設計の全根拠である8軸評価が `.tmp/`（`.gitignore` 対象）にあり追跡されない
  影響: 3ヶ月後に「なぜ課金してこの3本を選んだか」を再検証できない
  提案 → 反映: 評価の結論を `decisions.md` に転記する方針を目的節に明記
- 攻撃: 完了条件「代替の参照導線が別途成立している」は機械検証不能で、主観でチェックが埋まる
  提案 → 反映: 「`@` producer が全て修正済み」を grep 条件とする形に置換
- 攻撃: 完了条件の `validate_skills.py` 全 PASS / portability 0件は着手前から満たされており（実測 29/29・混入なし）、達成条件ではなく無回帰条件
  影響: 完了条件が「今も緑」の項目で水増しされ、Phase 3 の実質的検証が空になる
  提案 → 反映: 完了条件を「達成条件」と「無回帰条件」に分離。Phase 3 の各変更に個別の検証手段を付与
- 攻撃: export セットは validator の既定走査（`.claude/skills/`）にも `validate-skill-edit.sh` の case にも掛からない
  影響: 出荷物の構造検証が、人が明示的にパス指定した時だけになる
  提案 → 反映: テスト方針に `validate_skills.py <worktree>/export/company/skills` を明記（実測 10/10 PASS）
- 攻撃: 配置先に settings.json が**無い**場合、`deploy_skills.py` はマスターの permissions を丸ごと新規作成し、その deny に `npm install` 等が含まれる（`deploy_skills.py:184-202`）
  影響: 配置直後に「なぜか依存インストールが拒否される」原因不明の摩擦が発生。既存スモークテスト4項目は検出しない
  提案 → 反映: スモークテストに「配置先の通常コマンドが阻害されていないこと」を追加
- 攻撃: 課金見積に再実走分が入っていない。承認ゲート系の初回検査で 5/5 FAIL した実績があり、export の session-retrospective は FAIL 想定
  影響: 承認済み予算を超過する。二重課金の実例があるリポジトリで予算超過は起動判断の信頼を損なう
  提案 → 反映: 上限見積を 40 run に修正し、再実走のたびに再承認を取ると明記
- 攻撃: README の資産一覧（`scripts/` 列挙・役割説明）が新規スクリプトと npm script で腐る。design は README を旧 Phase 5 送りにしている
  影響: リポジトリ自身の「片側修正の禁止」に抵触
  提案 → 反映: 資産一覧行の更新を Phase 1 / Phase 3 に含め、旧 Phase 5 送りは「セットアップ節の新設」に限定

**人間の判断に委ねる: 5 件**（うち2件はレビューで解決済み）

- 配置先の選定（→ **解決済み**: Phase 4 着手時に決める）
- 配るスキルセット（→ **解決済み**: 拡張も含め、配布先の要件で決める）
- export 版 `session-retrospective` の停止契約の乖離が、意図的な移植判断か伝播漏れか（→ 論点 3）
- 「実質差分」の除外分類の基準と、仕分け結果の永続化先（→ 論点 4）
- Phase 4 の中止条件（ロールバックするか残すか）（→ 論点 5）

**設計者として反論した / 分類を変えた: 3 件**

- 攻撃「MANIFEST は内部矛盾しており単一情報源にならない（13行目=10 / 54行目=9）」→ 部分的に反論。54行目は「2026-07-22 更新の要点」という**日付付き履歴節**の中にあり、末尾に ※ で 07-23 の変更が注記されている。履歴としては正しい記述。ただし「MANIFEST を正とする」という指示は曖昧なので、一次情報を `ls skills/ | wc -l` の機械カウントと宣言する形に修正した
- 攻撃「`deployments.md` のコメント行修正は無意味で、実害はレジストリが実質空なこと」→ 事実として正しい（`read_registry()` は `#` 以降を落とす）。ただし記録の正確さとしては直す価値がある。**「機構の修復」から「記録の正確さ」に分類を変更**し、実害（有効行0件で exit 2）は配置完了で解消すると明記した
- 攻撃「`compatibility:` を2本だけ足す根拠が無い（未設定は17本）」→ 選定基準を明記して反論とした。本文にスタック前提の判断軸・コード例を持つもの（実測でスタック固有語29件 / 9件）が対象で、他15本は判断軸がスタック中立

**未反映（対象外として据え置き）: 1 件**

- 攻撃「差分ガードは起動主体が無く恒常保証にならない（CI 無し・hooks 未登録）」→ `package.json` の `check:export` と export への merge 手順に組み込む形で**部分的に反映**したが、CI による強制は本タスクの対象外（`.github` の新設は構造改善の範疇）。手動起動に留まるリスクは受け入れる

（このスキルは設計を承認しない。人間のレビューに戻る）

## 検討した代替案

- **export 専用シナリオを8本フル作成** — 却下。停止契約に実質差分があるのは3本のみで、残り5本は master と同一テキスト。同一文字列の二重テストに課金する価値がない。代わりに差分ガードで同一性を保証する
- **シナリオを1本にパラメータ化して master と export の両方をテスト** — 却下。`skill:` は変えられてもサンドボックス（React vs Angular・見出し言語・review-result の形式）が異なり、両対応にすると条件分岐だらけの資産になる
- **export シナリオを `tests/passthrough/` 側に置いて `--all` に載せる** — 却下。main には `export/company/` が存在しないため、main で `--all` を回すと `skill:` の解決に失敗する。置き場所は `export/company/tests/` のまま、起動手順を `skill-test` 本文に書くことで対処する
- **export ブランチで不要なシナリオを削除する** — 却下。`tests/passthrough/` は main が producer で export が consumer のため、export 側で削除すると merge のたびにコンフリクトするか復活する。代わりに「`--all` を使わない・検査対象を明示指定」を運用ルールにする
- **配布機構の縮退（レジストリ系の撤去・当初の案B）** — 却下。`deploy_skills.py` が `source-commit` 打刻とレジストリ登録を行う producer であり、consumer だけ撤去すると誰も読まない値を書き続ける構造になる。さらに外部プロジェクトには `git diff main` が使えず、レジストリ + `check_deploy_drift.py` が唯一のドリフト検出手段になる
- **還流系（skill-harvest）のみ撤去** — 却下。外部プロジェクトは会社と違って還流可能で、`session-retrospective` を併配すれば producer は成立する
- **feature-pipeline のシナリオのためにハーネスを拡張する** — 却下（今回は）。`## setup` 節と git init のサポートは有用だが、本タスクの範囲を超える。別タスクへ
- **Phase 4 を今回のスコープから外す** — 却下。配置は直近に予定されており、実証を伴わない配置は「実証ゼロ」を延命するだけ
- **Phase 5（構造改善）を同一タスクに含める** — 却下。Phase 4 の実走で starter-kit の手順自体が更新されるため、先に構造改善すると二度手間になる
