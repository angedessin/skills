# 設計: gate-bypass-s7-s8

Created: 20260927
Status: **APPROVED**
Approved: 20260927（方針転換後の再承認）

## 目的

allow に入っている git の読み取り系コマンドが前置一致（`Bash(git diff*)` 等）で書かれているため、次の 3 つが実測で成立する（`20260917-report-driven-improvements` のレビュー S7・S8。20260927 に headless で再現）。
(1) `--output=<path>` で、承認制パスを含む任意のファイルへ無音で書き込める。
(2) `git difftool -x '<cmd>'` で任意のコマンドを実行できる。
(3) `git diff [--no-index] /dev/null <作業ツリー外のパス>` で、`Read(~/.ssh/**)` の deny を迂回して非 .env の秘匿ファイルを読める。
20260927 の実測で、**穴の原因はこの allow そのもの**だと分かった。Claude Code（2.1.283）には組み込みの読み取り専用コマンドの判定がある。allow が無ければ、`git diff --stat` などはプロンプトなしで通し、上の危険な形はすべて止める（default / acceptEdits の両モードで確認）。前置一致の allow はこの判定を上書きし、危険な形まで許してしまう。
さらに、承認制パスへのリダイレクト（`git show HEAD:a > CLAUDE.md`）は、acceptEdits モードでは `Edit(./CLAUDE.md)` の ask があっても通って上書きされた（Claude Code のリダイレクト検査は ask を見ない）。そのため、Bash 側の書き込みゲート（hook）は引き続き必要である。
このタスクでは、git の allow を削除し、書き込み hook の対象パスを permissions.ask の Edit 対象に揃える。同じ修正を、配布用の定義・`export/company`・登録済みの配置先 2 件にも当てる（防御はマスターを上流とする方針。`docs/knowledge/claude-code-config.md`「独立フォークにも防御は追随させる」）。

元ネタ: `.steering/BACKLOG.md` §0（このタスクへ移設済み）。

## スコープ

### 対象
- **S8 git の allow を削除する**: `Bash(git status*)` / `Bash(git diff*)` / `Bash(git log*)` / `Bash(git show*)` の 4 件を、マスターの settings.json と `DEPLOY_PERMISSIONS` から削除する。`Bash(ls)` / `Bash(ls *)` は残す。git の読み取りは組み込みの判定に任せる
- **再発防止の契約**: 「マスターの settings.json と `DEPLOY_PERMISSIONS` の allow に `Bash(git ...)` のルールを置かない」を `check_asset_consistency.py` の契約にする（組み込みの判定を上書きして穴を開けるため）。変異テストも付ける
- **S7 書き込み hook の対象の拡張**: `guard-gated-write.sh` のリダイレクト（`>` / `>>`）と `tee` の判定対象に、`.claude/settings.json` / `.claude/settings.local.json` / `.claude/hooks/` を足す（permissions.ask の Edit 対象と揃える）。あわせて、`git mv` の宛先が対象パスなら ask にする（settings.local.json の `Bash(git mv *)` 対策。20260927 の論点確定）
- **書き込み hook の判定仕様**:
  - `tool_input.command` を python3 標準ライブラリで抽出する。`shlex`（`punctuation_chars`）でトークン化し、`&&` / `||` / `;` / `|` / 改行 / `{ }` / `( )` で区切った**すべての部分**を判定する（現行の全文検査は連鎖の中も拾っているので、それより後退させない）
  - 出力する JSON は最大 1 つで、最初にヒットした時点で終了する
  - **python3 が無い・抽出に失敗した場合は、現行の全文 grep（元の 3 系統のパス・リダイレクトと tee）に縮退する**
  - 対象パスの正本は、hook のヘッダのマーカー行 1 か所に置く
- **パス集合の突合の機械化**: 書き込み hook のマーカー行のパス集合と、permissions.ask の Edit 対象（プロジェクト相対のもの）が一致することを、新しい契約で検査する。フィクスチャの runner もマーカー行を読み、パスごとに ask のケースを自動生成する。`guard-gated-delete.sh` は「意図的に 3 系統」と宣言した例外にする
- **配布の文書**: README と `docs/starter-kit.md`（スモークテストの手順 8 を含む）を同じコミットで直す
- **export/company の同期**:
  - `export/company/claude-config/settings.example.json` から git の allow 4 件と、死んだ `Write(path)` 規則 10 件を削除する
  - hook を同期する（変換レシピに従い、理由文から非同梱スキル名を除く）
  - 会社側の文書を直す: hook の依存（POSIX のみ / python3）、スモークテスト、MANIFEST の変更履歴節に「allow の再マージ（git の 4 件の削除）が必要」と明記
  - `COMPANY-MAINTENANCE.md` の静的検査 1〜6 と、会社側の hook に対する全フィクスチャを通す（runner の hook ディレクトリを引数で差し替えられるようにする）
- **配置先への反映**（`skill-test` のみ。`hospital-search-mock` は 20260927 にユーザー指示で対象外 — decisions 参照）:
  - settings.json から git の allow 4 件を削除する
  - `guard-gated-write.sh` を個別にコピーする
  - `skill-test` には guard-gated-delete を追加する（20260927 の論点確定）
  - skill-harvest の Step 3 はスキルフォルダしか再コピーしないため、hook と settings は差分を提示して手動で反映する。配置先への書き込みは明示承認を取ってから行う
- **文書の更新**: `docs/knowledge/claude-code-config.md` を直す（「`--output=` 経由は未対処」の記述、組み込みの読み取り専用判定を前置一致の allow が上書きすること、リダイレクト検査は ask を見ないこと）

### 対象外
- permissions に危険な形の ask ルール（`Bash(git *--output*)` 等）を足すこと。組み込みの判定が default / acceptEdits で止めることを実測したため不要（auto / bypassPermissions モードは対象外）
- hook での git の危険フラグ・作業ツリー外パスの判定（旧設計の S8-b）。allow を削除すれば、組み込みの判定が止める
- `guard-gated-delete.sh` の対象を `.claude/` に広げること（削除による迂回は別の穴。必要なら BACKLOG に起票する）
- 敵対者を想定した封鎖（`bash -c`・`git -c` による設定注入・リポジトリの config に仕込まれた external diff など）。脅威モデルは既存 hook と同じく「停止契約を滑った善意のエージェント」
- `export/company` の guard-gated-delete 同梱（`dd962b2` で同梱済み）、export/company ブランチのルートにあるマスターのスナップショット（変換レシピの対象外）
- settings.local.json の allow の棚卸し（ユーザー自身の設定なので、提示だけ行う）
- `deployments.md` の「Frozen handoff」コメント（gitignore 済みで、防御の追随方針とは別の話）

## 制約

- Stack: Bash hooks（JSON 抽出とトークン化は python3 標準ライブラリ。jq や追加パッケージは使わない）/ `settings.json` / `scripts/deploy_skills.py` / `scripts/check_asset_consistency.py` / `tests/hooks/run_fixtures.py` / `tests/assets/run.py`
- `settings.json`・`.claude/hooks/`・`docs/`・README・配置先への書き込みは承認制。実装フェーズで個別に承認を取る
- 登録済みの hook の本文の変更は、即時に効く可能性がある。そのため、scratchpad のコピーで実装し、`bash -n` とフィクスチャを通してから差し替える
- ask が発火したかは AI からは観測できない。ただし headless（`claude -p`）ではブロックされた理由のメッセージがモデルに返るので、AI が機械的に確かめられる（20260927 に確立した手順）
- 同一の event+matcher を配列で分割しない（契約 (f)）

## 完了条件

- [ ] マスターの allow が `Bash(ls)` / `Bash(ls *)` の 2 件になり、`DEPLOY_PERMISSIONS` も同じになっている。git の allow を禁じる契約と契約 (e) が通る
- [ ] hook のフィクスチャに次のケースが入り、`test:hooks` が通る
  - ask になるもの:
    - マーカー行の全パスへのリダイレクト（自動生成）
    - `tee .claude/hooks/x`
    - 連鎖の中の形（`ls && echo x > CLAUDE.md`）
    - `git mv x CLAUDE.md` / `git mv -f x .claude/hooks/y`
  - 沈黙するもの:
    - `git log`
    - `cat .claude/settings.json > /tmp/x`
    - `git mv a b`
    - `transcript_path` だけに `.claude/` を含むペイロード
  - 1 回の呼び出しで JSON が 2 つ出ないこと
  - python3 を PATH から外したときに全文 grep の判定に縮退すること
- [ ] 新しい契約（パス集合の突合・git の allow の禁止）が `check_asset_consistency.py` に入り、変異テストが `tests/assets/run.py` に入っている
- [ ] **headless での機械確認**（AI が実施・課金は haiku で数回）: scratchpad のリポジトリで、`--permission-mode acceptEdits` と `--settings` による hook の登録を使って、次を確かめる。結果を decisions.md に残す
  - `git show HEAD:a > CLAUDE.md` と `... > .claude/hooks/x` が hook の理由付きでブロックされる
  - `git show HEAD:a > other.txt` は通る
  - マスターと同じ allow の設定で、`git diff --output=x` / `git difftool -x` がブロックされる
- [ ] **人間確認（再起動後・1 回）**: このリポジトリで acceptEdits にした状態で、AI が `git show HEAD:README.md > .claude/hooks/zz-probe.txt` を実行し、人間がプロンプトの有無を記録する（人間は拒否する）。あわせて、`git diff` と `git log --oneline -3` がプロンプトなしで動くことを確かめる
- [ ] export/company: 同期した状態で、静的検査 1〜6 と、会社側の hook に対する全フィクスチャが合格している
- [ ] 配置先 2 件: 承認のうえで反映している。配置先の settings.json を JSON で読み、allow に `Bash(git` が無いことを機械で確かめている。`check_deploy_drift.py` で `guard-gated-write.sh` の差分が消えている
- [ ] README / starter-kit / claude-code-config の記述が新しい挙動と一致している

## アプローチ

git の読み取りは Claude Code の組み込みの読み取り専用判定に任せ、allow には書かない。前置一致の allow は組み込みの判定を上書きして危険な形まで許すことを、実測で確かめた（allow ありでは `--output` と `difftool -x` が通り、allow なしでは止まる）。permissions で文字列パターンを列挙する（旧案 C）、あるいは hook で git のフラグを判定する（旧案 A）よりも、許可そのものを持たない形が最も単純で漏れが少ない。
一方、承認制パスへのリダイレクトは組み込みの検査が ask を見ないため、書き込み hook の担当として残す。対象パスを permissions.ask と揃え、`transcript_path` の混入を避けるために構造抽出へ移す。

## 主要コンポーネント

| コンポーネント | 場所 | 変更後の姿 |
|---|---|---|
| マスター permissions | `.claude/settings.json` | allow: `Bash(ls)` / `Bash(ls *)` のみ。ask / deny は変更しない |
| 書き込み hook | `.claude/hooks/guard-gated-write.sh` | 入力: `tool_input.command` を python3 で抽出し shlex でトークン化（失敗したら現行の全文 grep に縮退）。連鎖の全部分について、次のどれかなら ask を出す（最大 1 JSON）: リダイレクト / `tee` の先が対象パス、または `git mv` の宛先が対象パス。対象パス: `CLAUDE.md` / `docs/knowledge/` / `docs/decisions/` / `.claude/settings.json` / `.claude/settings.local.json` / `.claude/hooks/`（ヘッダのマーカー行が正本） |
| 削除 hook | `.claude/hooks/guard-gated-delete.sh` | 判定は変更しない。ヘッダの「手同期・3 系統」を「意図的に 3 系統・新しい契約の例外」に書き換える |
| 配布定義 | `scripts/deploy_skills.py` | `DEPLOY_PERMISSIONS["allow"]` は ls の 2 件のみ。hook の依存コメントを「write / delete は python3 stdlib（write は無い場合に縮退・delete は沈黙）」に更新する |
| 資産契約 | `scripts/check_asset_consistency.py` / `tests/assets/run.py` | 新しい契約 (s): 書き込み hook のマーカー行のパス集合 ≡ マスターの permissions.ask の `Edit(./...)` を正規化した集合。新しい契約 (t): マスターの settings / `DEPLOY_PERMISSIONS` の allow に `Bash(git` で始まるルールが無い。それぞれに変異ケースを付ける。README の契約レター一覧（契約 (k)）と変異テストの対象一覧にも追記する |
| hook のフィクスチャ | `tests/hooks/run_fixtures.py` | 完了条件のケースを追加する。マーカー行からのケース自動生成、hook ディレクトリを差し替える引数、PATH を差し替えるケースを足す。既存の D21 / D22 は維持する |
| 文書 | `README.md`（34・216・223 行付近）/ `docs/starter-kit.md`（88・94・104〜110 行付近）/ `docs/knowledge/claude-code-config.md`（「deny ルールはツールごとに独立評価される」節と「サブエージェント定義の落とし穴」節） | allow に git を書かない理由（組み込みの判定の上書き）、書き込み hook の対象（6 系統と `git mv`）、リダイレクト検査が ask を見ないことを書く。headless で permission の挙動を測る手順を knowledge に残す |
| export/company | `../skills-export-company/export/company/claude-config/hooks/guard-gated-write.sh` / `settings.example.json`（allow・死んだ Write 規則・`_comment`）/ `HANDOVER.md`・`MANIFEST.md`（依存・スモークテスト・変更履歴） | hook はマスターのものに理由文の変換だけを適用する（コメントに `pnpm` / `npx` を書かない）。コミットは export/company ブランチに行う |
| 配置先 | `skill-test` / `hospital-search-mock` の `.claude/settings.json` の allow と `.claude/hooks/guard-gated-write.sh`（`skill-test` は `guard-gated-delete.sh` と登録も） | 差分を提示し、承認のうえで手動反映する。`hospital-search-mock` の独自 hook（`guard-draft-implementation.sh` / `guard-spike-outbound.sh` / `lib/`）には触れない |
| BACKLOG | `.steering/BACKLOG.md` §0 | 削除済み（このタスクへ移設） |

## 未解決の論点

再承認時（20260927）に異議がなかったため、各論点の推奨案で確定した。

- [x] **auto / bypassPermissions モードでの挙動は測っていない**: auto モードは分類器が判断し、bypassPermissions は全部通す。このタスクの防御範囲は default / acceptEdits とし、それ以外は対象外と明記する想定（推奨: そのまま受容し、knowledge に書く）
- [x] **ユーザーの「今後は確認しない」による allow の再流入**: git の読み取りは組み込みでプロンプトが出ないため、再流入は起きにくい。危険な形を承認すると、そのコマンドの完全一致ルールが local に保存される（前置一致にはならない）ため、影響は小さいと見ている（推奨: 受容。契約 (t) はマスターの settings.json だけを見る）
- [x] **旧設計の hook での git の危険フラグ判定（S8-b）を多層防御として残すか**: 古い allow が残る環境（会社側で再マージが漏れた場合など）の保険にはなる。ただし、今回の変更で最も複雑な部分であり、組み込みの判定と二重になる（推奨: 残さない。会社側は変更履歴で再マージを告知し、配置先は機械検査で確かめる）

---

<!-- design-doc-boundary: appendix -->

> **付録** — 実装入口・resume の既定では読まない。プレモータム・TDD 突入・乖離調査など、当該節が必要なときだけ読む。人間の Phase 3 承認前は `影響範囲` と `検討した代替案` を必読。

## プレモータム所見

> 20260927 の方針転換（git の allow の削除）で、H1・M1・M2・M3 の git のフラグ判定に関する所見は対象外になった（組み込みの判定が止めることを実測）。H2・H3・M4〜M10・L2 は、書き込み hook と配布の部分に引き続き適用する。H3 の人間確認のプローブは、acceptEdits で判別力のある形に作り直した。

（20260927・design-premortem。攻撃役は会話の経緯を持たないサブエージェント。High 3 / Medium 12 / Low 5 件。主要な主張は scratchpad の使い捨てリポジトリ（git 2.53.0）で裏取りした）

- 攻撃（H1）: `git diff /dev/null ~/.ssh/id_rsa` は `--no-index` を書かなくても no-index モードになる。パスの片方が作業ツリーの外を指すため
  影響: フラグで判定する hook では原理的に塞げない。目的 (3) が開いたまま完了扱いになる
  提案: **プレモータム反映済み**（実測で再現）。S8-b に「作業ツリー外のパス」の判定を加え、フィクスチャと人間確認のプローブに入れた
- 攻撃（H2）: 構造抽出を delete hook の流儀（先頭トークンだけ・最初の演算子で打ち切る）で書くと、`ls && echo x > CLAUDE.md` のような連鎖の中の書き込みを取りこぼす。現行の全文検査より後退する
  影響: `cd x && git diff --output=...` のような、日常的に書かれる連鎖が素通りする
  提案: **プレモータム反映済み**。判定仕様として、連鎖のすべての部分を判定すると定めた。「コマンド連鎖」を対象外から外し、回帰フィクスチャを足した
- 攻撃（H3）: 人間確認のプローブ `echo x > .claude/settings.local.json` は allow に無いので、hook が壊れていてもプロンプトが出る（判別力がない）。誤って承認すると、gitignore 済みの local 設定が消える
  影響: `.claude/` への拡張が効いているかを誰も確かめないまま完了する
  提案: **プレモータム反映済み**。プローブを allow に当たる形にし、新規ファイルを宛先にした。「人間は必ず拒否する」と、事前の退避を完了条件に入れた
- 攻撃（M1）: hook の危険フラグの列挙も、却下した代替案 C と同じ列挙の弱さを持つ。git のバージョン差、設定経由の external diff / textconv / fsmonitor、環境変数を前置した形がある
  影響: git の更新のたびに denylist を継ぎ足す軍拡になる
  提案: 人間の判断に委ねる（未解決の論点「denylist か allowlist か」）。反論: 2.53 では diff のオプションの略記が通らないことを実測した。設定経由の実行は、リポジトリの config を書き換える前提が要るので、脅威モデルの対象外とした（対象外に明記済み）。環境変数を前置した形の扱いは T1 で確認する
- 攻撃（M2）: 「前方一致」の向きや、引数を分けた形・リビジョンの後ろの形・`--` の後ろ・コミットメッセージ内の文字列の扱いが未定義
  影響: 実装者の解釈次第で、素通りや恒常的な誤検知が出る
  提案: **プレモータム反映済み**。スコープに「判定仕様」を追加した（shlex でトークン化 → サブコマンド → `--` まで）。実測で、`--output <file>` と `git diff HEAD --output=` が書き込めることを確認した
- 攻撃（M3）: 古い `Bash(git diff*)` が残った環境（手動マージの会社側・既存の配置先）では、`difftool` と `diff-files` 等が開いたまま
  影響: allow の再マージが漏れた環境で、S8 の実行経路が残る
  提案: **プレモータム反映済み**。hook の対象サブコマンドに `difftool` と `diff-*` を加えた（`git diff-files --output=` で書き込めることを実測）。会社側への告知は未解決の論点に上げた
- 攻撃（M4）: python3 が無い環境では、今 POSIX で動いている書き込みゲートが沈黙する（後退）
  影響: 書き込みゲートと削除ゲートが同時に、警告なく死ぬ
  提案: **プレモータム反映済み**。python3 が使えないときは現行の全文 grep に縮退させ、フィクスチャで固定する
- 攻撃（M5）: 登録済みの hook の本文は即時に効く。構文エラーを入れると、その場で全 Bash が止まりうる
  影響: 実装中に自分のセッションを壊す
  提案: **プレモータム反映済み**（制約を修正）。scratchpad のコピーで `bash -n` とフィクスチャを通してから差し替える。本文が即時に効くかは T1 で確認する
- 攻撃（M6）: マーカー行と実際の判定ロジックが乖離しても、新しい契約は緑になる。delete hook のヘッダの「手同期・3 系統」も偽になる
  影響: 単一情報源の崩れを検出できない
  提案: **プレモータム反映済み**。runner がマーカー行から ask のケースを自動生成する。delete hook は例外と宣言する
- 攻撃（M7）: 「片側だけ変えると落ちることを確認した」は一回限りの手作業
  影響: 新しい契約の検査器自体が退行しても検出されない
  提案: **プレモータム反映済み**。`tests/assets/run.py` に変異ケースを追加する
- 攻撃（M8）: skill-harvest はスキルフォルダしか再コピーせず、`check_deploy_drift.py` は permissions を見ない。完了条件の「期待どおり」に期待値が無い
  影響: 配置先で allow の狭め込みが漏れても完了扱いになる
  提案: **プレモータム反映済み**。反映手順（hook は個別にコピー・settings は手動マージ）と、JSON を読む機械検査を完了条件に入れた
- 攻撃（M9）: settings.local.json の `Bash(git mv *)` で承認制パスを上書きでき、delete hook も `git mv` を見ない
  影響: project の allow を狭めても、local の allow との和集合で穴が残る
  提案: 人間の判断に委ねる（未解決の論点。推奨は `git mv` だけを判定 1 に加えること）
- 攻撃（M10）: スモークテストにも会社側の検査にも、新しい判定を確かめる手段が無い。変換で hook が壊れても、静的検査 1〜6（grep と件数）では検出できない
  影響: 会社側・今後の配置で効き目が確かめられない
  提案: **プレモータム反映済み**。会社側の hook にも全フィクスチャを通し、スモークテストに allow に当たるプローブを足す
- 攻撃（M11・M12）: `--output` はパスによらず ask にするのに、`git diff > ~/.zshrc` は沈黙のまま（非対称）。逆にパスによらず ask にすると、frontend-code-review の diff の書き出しが毎回 ask になる
  影響: 目的の半分が未達、または日常のレビューで摩擦が出る
  提案: 人間の判断に委ねる（未解決の論点。推奨は非対称のまま受容すること）
- 攻撃（L1）: 会社側 settings.example.json に、死んだ `Write(path)` 規則 10 件が残っている
  提案: 人間の判断に委ねる（推奨は同じコミットで消すこと）
- 攻撃（L2）: 2 つの判定が同時に当たると、JSON が 2 つ出る恐れがある
  提案: **プレモータム反映済み**（最大 1 JSON で即終了。フィクスチャを追加）
- 攻撃（L3）: 完了条件の「8 件」とコンポーネント表の「10 件」が食い違っている。`.env` ガードを迂回できるという記述は不正確（guard-env-read は `/.env` を拾う）
  提案: **プレモータム反映済み**（10 件に統一。目的 (3) を「非 .env の秘匿ファイル」に修正）
- 攻撃（L4）: `deployments.md` は gitignore 済みで、「Frozen」の記述は防御の追随方針とは別の話
  提案: **プレモータム反映済み**（未解決の論点から外し、対象外に移した）
- 攻撃（L5）: Claude Code に組み込みの読み取り専用コマンドの自動許可があるなら、代替案 B の却下理由の前提が変わる
  提案: T1 に「allow を外したときの `git diff` の挙動」を加えた。前提が崩れても、決定インタビューでの A の選択（allow の狭め込み + hook）は hook の判定があるぶん B より強い

## データフロー

```
Bash ツールの呼び出し
  → PreToolUse(Bash) の 3 本（delete / env-read / write。1 つの matcher に並べる）
      write: tool_input.command を抽出し、連鎖の全部分について判定
        ├ リダイレクト / tee の先が対象パス   → ask
        ├ git mv の宛先が対象パス             → ask
        └ それ以外                            → 沈黙
        （python3 が無い・抽出失敗 → 現行の全文 grep に縮退）
  → permissions（deny > ask > allow）。allow に git は無い
  → 組み込みの読み取り専用判定: git diff --stat 等は通す。--output / difftool / --ext-diff / 作業ツリー外は承認が要る
  → リダイレクト先の検査（Edit の allow / deny・作業ディレクトリ。ask は見ない）
```

## 影響範囲

- システム / 外部連携: `export/company` ブランチ（別 worktree へのコミット）。配置先 2 件（リポジトリ外への書き込み）
- データ: なし
- 他チーム / 利用者: 会社側の配置者は、`settings.example.json` を再マージする必要がある（手動マージの雛形のため、自動では伝わらない）。MANIFEST の変更履歴で告知する
- リグレッション懸念:
  - **allow を消したことによる新たなプロンプト**: 組み込みの判定が git の読み取り形を通すことは実測済み（`git diff --stat`）。ただし、組み込みの判定が「読み取り形」と見なさない正当な形（引用なしのグロブを含む git コマンド、`cd` で別ディレクトリへ移ってからの git など。docs に記載あり）では、これまで出なかったプロンプトが出る。安全側の摩擦として受容する
  - **frontend-code-review の差分の書き出し**（`git diff > .tmp/review.patch` など）: これまで allow で無音だった場合、今後はリダイレクト先の検査でプロンプトが出る可能性がある（default モードで作業ディレクトリ内への書き込み）。人間確認で 1 回見る
  - **構造抽出への移行による取りこぼし**: 現行の D21（`echo x > CLAUDE.md` が ask）の維持と、連鎖の中の形をフィクスチャで守る
  - **`.claude/` を対象に足したことによる誤検知**: `cat .claude/settings.json > /tmp/x` は沈黙すべき。フィクスチャに入れる
  - **既存の配置先の独自 hook**（hospital-search-mock）を上書きで壊すこと。差分を提示して承認を取ってから書く

## テスト方針

- Unit（hook のフィクスチャ）: `tests/hooks/run_fixtures.py` に ask / 沈黙のケースを追加し、`mise exec -- pnpm run test:hooks` で回す
- 契約: `mise exec -- pnpm run validate:assets`（(e)・(s)・(t)・(f)・(k)）と `tests/assets/run.py` の変異テスト
- headless での機械確認（課金・haiku・`--max-budget-usd` で上限を付ける）: scratchpad のリポジトリで `--setting-sources project,local` を使ってユーザー設定を外す。allow は `--allowedTools` で与える（未信頼のワークスペースでは project の allow が無視されるため）。hook は `--settings` で登録する。ブロックの理由はモデルに返るので、AI が判定できる
- 人間確認（再起動後・1 回）: このリポジトリの実環境で hook が発火することだけを見る
- export/company: `COMPANY-MAINTENANCE.md` の静的検査 1〜6（無課金）と、会社側の hook に対するフィクスチャ。素通り検査（課金）は不要（スキル本文を変えないため）

## 検討した代替案

| 代替案 | 却下理由 |
|---|---|
| allow を空白付きの形に狭め、hook で git の危険フラグを判定する（旧案 A。20260927 の最初の承認案） | 公式 docs と実測で、組み込みの読み取り専用判定が危険な形を止めること、前置一致の allow がそれを上書きしていることが分かった。allow を残して hook で穴を埋め直すより、allow を持たないほうが単純で漏れが少ない（方針転換） |
| permissions の ask に途中ワイルドカードで危険な形を列挙する（旧案 C） | 組み込みの判定が default / acceptEdits で止めるため、列挙の保守をする理由がない |
| hook の危険フラグ判定を多層防御として残す | 未解決の論点を参照（推奨は残さない） |
| 書き込み hook の対象パスを今の 3 系統のままにする（決定 2 の B） | `> .claude/settings.json` 型のリダイレクトが残る。acceptEdits では ask があっても通ることを実測した |
| 配置先への反映を別タスクにする（決定 3 の B） | マスターだけ塞がって配布先が開いたままになる（20260726 の前例）。書き込みは承認制なので、同じタスクに含めても勝手には進まない |
| 全文検査のまま対象パスを足す | `transcript_path` に `~/.claude/projects/...` が常に入るため、`.claude/` 系の判定が恒常的に誤検知の種になる |
| リダイレクトの防御も Claude Code の組み込み検査に任せ、hook を廃止する | 組み込みのリダイレクト検査は ask を見ない。acceptEdits で `> CLAUDE.md` が ask をすり抜けて上書きされたことを実測した |

## 調査結果

（20260927・design-doc の事実確認）
- `export/company` の `guard-gated-delete.sh` は `dd962b2` で同梱済みで、マスターと同一。`settings.example.json` の PreToolUse にも登録済み。`guard-gated-write.sh` の差分は理由文の `adr` の除去だけ（変換レシピどおり）
- 配置先: `skill-test` は `git diff*` / `git show*` 形の allow を持ち、guard-gated-delete が無い。`hospital-search-mock` は同じ allow を持ち、マスターに無い hook（`guard-draft-implementation.sh` / `guard-spike-outbound.sh` / `lib/`）がある
- git 2.53.0 での実測（scratchpad）:
  - `git diff /dev/null ../outside.txt`（フラグなし）→ 作業ツリー外のファイルが読める
  - `--outp=` / `--outpu=` → 拒否（diff のオプションは略記不可）。`--no-ind` → 候補が複数あって解決できない
  - `git diff --output o4.txt`（引数を分けた形）/ `git diff HEAD --output=`（リビジョンの後ろ）/ `git show --output=` / `git diff-files -p --output=` → いずれも書き込める
- マスターの settings.local.json の allow に `Bash(git mv *)` / `Bash(cd *)` / `Bash(git add *)` がある（gitignore 済み・配布されない）
- `guard-gated-write.sh` の現在の対象パスは `CLAUDE.md` / `docs/knowledge/` / `docs/decisions/` のみ。permissions.ask の Edit 対象（`.claude/settings*.json` / `.claude/hooks/**`）と揃っていない

### headless での実測（20260927・方針転換の根拠）

Claude Code 2.1.283、`claude -p --model haiku`、`--setting-sources project,local`、scratchpad の使い捨てリポジトリ。4 回の実行で、いずれも `--max-budget-usd 0.5` の範囲内。
- **A（allow なし・default）**: `git diff --stat` は通った。次はすべて止まった（「This command requires approval」、作業ツリー外は「git in '...' was blocked ... only access files with git from the allowed working directories」）。ファイルは 1 つも作られなかった
  - `git diff --output=` / `git log -1 --output=` / `timeout 5 git diff --output=`
  - `git diff /dev/null ../outside.txt` / `git diff --no-index /dev/null ../outside.txt`
  - `git difftool -y -x 'touch pwned' HEAD` / `git diff --ext-diff`
- **B（マスターと同じ前置一致の allow を `--allowedTools` で付与）**: `git diff --output=o1.txt`・`git difftool -x 'touch pwned'`・`--ext-diff` がすべて実行された（`o1.txt` と `pwned` が作られた）。穴の原因は allow そのもの
  - 補足: project の `.claude/settings.json` に書いた allow は、「workspace has not been trusted」で無視された。検証では `--allowedTools` を使う
- **C（acceptEdits・`--settings` で `Edit(./CLAUDE.md)` を ask）**: `git show HEAD:a > CLAUDE.md` は**実行され、CLAUDE.md が上書きされた**。`git log -1 | tee CLAUDE.md` は「The following part requires approval: tee CLAUDE.md」で止まった。`> other.txt` は通った
- **D（acceptEdits・allow なし）**: `--output`・`difftool -x`・作業ツリー外・`git log --output` はすべて止まった
- 公式 docs（code.claude.com/docs/en/permissions）の関連記述:
  - 組み込みの読み取り専用コマンド（git の読み取り形を含む）は、全モードでプロンプトなしで動く
  - ラッパー（`timeout` / `nice` / `nohup` / `stdbuf` / `command` / `builtin` / `noglob` / フラグ無しの `xargs`）は、照合の前に剥がされる
  - ask / deny は、環境変数を前置した形やサブシェルの中まで当たる
  - 出力リダイレクトの検査は Edit の allow / deny・保護パス・作業ディレクトリを見る（ask への言及はない）

### 既存パターン調査（20260927）
- hook のフィクスチャ（`tests/hooks/run_fixtures.py`）:
  - `CASES` の各要素は `id` / `hook` / `command` / `expect`（`deny` / `ask` / `silence`）で、必要に応じて `payload` / `note` を持つ
  - ペイロードは `base_payload()` が組み立てる（`transcript_path` は `/tmp/claude/...`、`cwd` はリポジトリルート）
  - hook の場所は `HOOKS = ROOT/.claude/hooks` に固定されている
  - ID の意味: A = delete の deny / B = delete の沈黙 / D = write の回帰
- python3 の埋め込み: `python3 -c '...' 2>/dev/null` の形で、例外はすべて握りつぶす。`set -e` と process substitution は使わない。行継続の畳み込みは delete hook の 36〜47 行が前例
- 資産契約:
  - 関数は `contract_x() -> tuple[str, list[str]]`（PASS / FAIL / SKIP と詳細行）で、登録表は 901〜918 行
  - 契約 (k) は、README の「資産どうしの契約突合」箇条にある `(x) ` 形式の文字列と `contract_*` を突合する
- 変異テスト（`tests/assets/run.py`）: `patched()` で PATH 定数を一時ディレクトリのコピーに差し替え、`run_contract(letter, contract, files, target, cases, target_files)` で「壊した入力は FAIL」「壊していない入力は PASS（対照）」の両方を確かめる
- 注意点:
  - GNU grep は、パターンに生の `[` を含むと exit 2 になる
  - ディレクトリの Edit 規則は `*` / `**` / `**/*` の 3 形式が並ぶので、新しい契約で正規化するときに 1 つに畳む
  - 実装中に README の契約の箇条の書式を崩すと、契約 (k) が落ちる
