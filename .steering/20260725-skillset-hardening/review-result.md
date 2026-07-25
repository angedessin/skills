# レビュー結果: skillset-hardening

Date: 20260725
Status: OPEN
範囲: `HEAD~5..HEAD`（0f6439d / a875ba7 / 2e58fe4 / 1c34091 / 309b950・30 ファイル）
モード: フルモード（スコープ読み替え）— **2 回目で完走**

## 実施経緯

1 回目（20260725 前半）: impl / correctness / security の 3 エージェントが**全てセッション上限で中断・所見ゼロ**。自己レビューで代替し 2 件を修正（`ask` の glob 3 形式化・`normalize()` の契約値破壊）。
2 回目（上限リセット後）: 探索範囲を絞った指示で再ディスパッチし **3 体とも完走**。**1 回目の自己レビューが見落としていた High が 3 件**出た。

ディスパッチ対象外（該当ファイルなし）: perf-agent / a11y-agent / ui-agent / test-agent は「対象なし」。

### 指摘事項

- [x] **[High] [セキュリティ] `ask` は Bash 経由で迂回できる — 機械防御が成立していなかった** `.claude/settings.json` — **対応済み（ただし未検証）**
  `ask` に足したのは `Edit` / `Write` のみ。`allow` の `Bash(git show*)` / `Bash(git diff*)` は前置一致のため `git show HEAD:x > CLAUDE.md` が素通りし、Edit/Write を経由しないので ask は発火しない。`settings.local.json` の `Bash(cd *)` はさらに広い。
  **これはリポジトリ自身の記録済みルール違反**: `docs/knowledge/claude-code-config.md:5-22`「ファイルにアクセスできる**全ツール分**（Bash / Read、必要なら Edit / Write）のルールを揃える」。`.env` 保護では Bash と Read を対で揃えているのに、承認ゲートでは Edit/Write 側だけを書いていた。
  対応: `.claude/hooks/guard-gated-write.sh` を新設し `PreToolUse(Bash)` に登録。`CLAUDE.md` / `docs/knowledge/` / `docs/decisions/` への書き込みリダイレクト（`>` / `>>` / `tee`）を ask に落とす。単体テストで**発火 5/5・誤検知 0/5** を実測。
  **残存**: 明示リダイレクトのみ対象。`sed -i` や任意インタプリタ経由は塞がない（脅威モデルは敵対者ではなく「停止契約を滑った善意のエージェント」で、実測 20 run の FAIL はいずれも Edit/Write 経由だった）。**「機械的に完全にゲートした」とは言えない。**

- [x] **[High] [正当性] 差分ガードが master 側で偽グリーンを出す** `scripts/check_export_stopcontract.py` — **対応済み・実測確認**
  フェイルクローズを export 側にしか付けておらず、`--master` が空だと 1 ペアも比較しないまま「→ 停止契約は master と実質同一。追加シナリオは不要」＋ exit 0 を出した。スクリプト自身の docstring が防ぐと宣言している偽グリーンそのもの。impl / correctness の 2 エージェントが独立に検出。
  対応: 両側 + 「共通スキル 0 件」の 3 条件を exit 2 に。実測で `--master` 空・`--master scripts` の両方が exit 2 になることを確認。

- [x] **[High] [正当性] `STOP_VOCAB` が本物の停止契約を取りこぼす（フェイルオープン）** `scripts/check_export_stopcontract.py` — **対応済み・実測確認**
  `止まる`（終止形）しか見ておらず、実ファイルの次の行が比較対象外だった: `design-doc:11`「必ず止まって人間のレビューを待つ」/ `design-doc:145`「ユーザーの応答を待つ」/ `knowledge-capture:136`「知見保存ドラフト（案・未書き込み）」（案D の中核）/ `session-retrospective:39`「まだ 1 件も書き込まない」。**export 側でこれらが消えても「差分なし」と報告される**状態で、シナリオを 3 本 → 2 本に減らした根拠（「差分ガードが同一性を保証する」）を直接損なっていた。
  対応: 語幹 `止ま` に変更し `待つ` / `未書き込み` / `書き込まない` / `実装しない` / `中断` を追加。上記 4 行すべての捕捉を実測確認。**修正後も出力は 7/1/2 で不変**のため、シナリオ 2 本の判断自体は維持。

- [x] **[Medium] [プロセス] 検証ゴミ 2 ファイルをコミットに混入させた** — **対応済み**
  `gitshow-write-test.txt`（28KB）/ `gitdiff-write-test.txt` が `1c34091` に含まれていた。1 回目のセキュリティエージェントが「ファイルを変更するな」の指示に反してバイパス実証のために作成したものを、`git add -A` で中身を確認せずコミットした。**`git add -A` の前に何がステージされるかを見ていなかった**のが直接原因。対応: 追跡から削除。

- [x] **[Medium] [設計整合性] `design.md` の「アプローチ」が修正前の測定結果を現在形で書いている** — **対応済み**
  「停止契約そのものが変わっているのは session-retrospective 1 本のみ」は本数を決めた時点の測定。その後の修正で master と export が揃い、現在のガードは同スキルを「無害差分のみ」と報告する。注記を追加し、「この出力をそのままシナリオ選定に使わない（選定根拠は本文の分析）」を明記。

- [ ] **[Medium] [検証] `ask` と hook のどちらも実効性が未確認** — **未解決**
  `ask`: CLAUDE.md 編集時にプロンプトが観測されなかったが、権限モードの上書きかパターン不一致かを区別できていない。
  `hook`: 単体テストは通るが、**セッション内で登録した hook はこのセッションで有効にならない**（実測: 登録後に `echo x > docs/knowledge/_hook_probe.md` が無プロンプトで通過。プローブは削除済み）。
  **確認手順（セッション再起動後）**: `echo test > docs/knowledge/_probe.md` を AI に実行させ、確認が出るか見る。出れば hook は機能。出なければ機械防御は成立せず、Phase 1・2 の結論を撤回する必要がある。

- [ ] **[Medium] [正当性] `validate_skills.py` は `--help` 以外の未知フラグで Traceback** `scripts/validate_skills.py` — **未対応**
  `--protability` のような打ち間違いで `FileNotFoundError` の生スタックトレース。`args[0].startswith("-")` の一般ガードなら既存 6 経路に触れず閉じられる（impl-agent 指摘）。

- [ ] **[Medium] [正当性] `--verbose` が docstring の説明と一致しない** `scripts/check_export_stopcontract.py` — **未対応**
  「無害差分も行単位で表示」と書いてあるが、実装は「無害差分のみ」のスキルに件数 1 行を出すだけ。実質差分ありスキルの無害差分行は verbose でも出ない。

- [ ] **[Medium] [正当性] 報告の `[:120]` 切り詰めで差分の実体が見えないことがある** `scripts/check_export_stopcontract.py` — **未対応**
  `design-doc` の実質差分は 192 文字目にあり、レポート上は両行の先頭 120 文字が同一に見えて何が変わったか読めない。

- [ ] **[Low] 非同梱スキル名の除去が語境界を見ない** — 未対応。`adr` / `e2e` / `tdd` のような短い名が `adrenaline` → `enaline` のように巻き添えになる（両側同処理なので偽陰性方向）。`PR` に語境界を入れたのと同じ配慮が要る。
- [ ] **[Low] `read_body()` の戻り値注釈が実体と不一致** — `list[str]` と宣言して `list[tuple[int, str]]` を返す。
- [ ] **[Low] `.test.tsx` / `.spec.tsx` が `STACK_WORDS` に無い** — RTL→Angular 変換で非対称になり偽陽性を生む。
- [ ] **[Low] `--master` 不在時のエラー文言が export 用のまま** — `--master` のパス誤りで誤誘導する。
- [ ] **[Info] 配布物 `settings.example.json` に `docs/decisions/` の ask が無い** — export セットは `rule-audit` を同梱し `docs/decisions` を参照する。
- [ ] **[Info] `~/.claude/CLAUDE.md`（global）と `.claude/skills/**` が ask の射程外** — `knowledge-capture` は global CLAUDE.md を、`compound` はスキル本文を保存先候補にしている。

### 全体サマリー

- 合計の重要な問題（Medium 以上）: **10 件**（High 3 / Medium 7）
- Low: 4 件 / Info: 2 件
- 対応済み: 5 件（High 3 + Medium 2）/ 未対応: 5 件（Medium）+ Low 4 + Info 2
- 重複統合: 1 件（master 側フェイルクローズを impl / correctness が独立に検出）
- モード: フルモード（3/7 エージェント。他 4 体は対象なし）

### この再レビューが示したこと

1 回目の自己レビューは High を 1 件しか出せず、**3 件を見落としていた**。うち 2 件（master 側フェイルクローズ・`STOP_VOCAB` の取りこぼし）は**自分が書いたスクリプトの中核ロジック**で、自己レビューでは構造的に見つけにくい種類だった。`design-premortem` を別エージェントに回す規律を、コードレビューでも守る価値が実測で裏づけられた。
