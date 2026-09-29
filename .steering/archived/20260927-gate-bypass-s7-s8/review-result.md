# レビュー結果: gate-bypass-s7-s8

Date: 20260929
Status: DEFERRED

（20260929: 指摘は修正済み。修正後の再レビューはユーザー判断で省略（代替: フィクスチャ 100/100）。delete hook の Low 2 件は BACKLOG §0.6 へ持ち越し）

モード: フル（impl / correctness / security / test の 4 エージェント並列。perf / a11y / ui は対象ファイルなし）
対象: 未コミット差分（hook 2・scripts 2・tests 2・settings.json・README・docs 2・BACKLOG）

## テスト

| Axis | 指摘 | ファイル | 分類 | 修正状況 |
|------|------|----------|------|----------|
| テストダブル境界 | delete hook の python3 不在（フェイルオープン）経路を固定するケースが無い（Medium） | tests/hooks/run_fixtures.py | test was missing | [ ] 適用済み: BP1 を追加（再レビュー待ち） |
| テストダブル境界 | write hook の縮退経路が git mv を見ないことを固定するケースが無い（Low） | tests/hooks/run_fixtures.py | test was missing | [ ] 適用済み: WP5 を追加 |
| 判定粒度 | 契約 (t) の変異が settings.json 側だけで DEPLOY_PERMISSIONS 側が無い（Low） | tests/assets/run.py | test was missing | [ ] 適用済み: モジュール変数を差し替える deploy_git_allow_case を追加 |
| 実装エコー | マーカー行からの自動生成はエコーの形だが、固定 CASES が 6 系統を独立に持つので緩和済み（Info） | tests/hooks/run_fixtures.py:158-177 | - | 対応不要 |

## 実装

| Axis | 指摘 | ファイル | 修正状況 |
|------|------|----------|----------|
| 設計整合性 | 空白なしの `;` 連鎖で完全一致 3 系統が素通りする（High・設計契約コア不一致として報告） | .claude/hooks/guard-gated-write.sh:62-64 | 誤検知: `punctuation_chars=True` の既定は `();<>\|&` で `;` を含む。`echo x > CLAUDE.md;ls` 等 4 形を hook に通して全て ask を確認（20260929）。design 同期は不要 |
| 設計整合性 | 上記の派生: W15 は tee 側でも ask になり、`;` 連鎖の回帰を単独で固定できない（Low に格下げ） | tests/hooks/run_fixtures.py | [ ] 適用済み: W26 / W27 を追加 |
| 規約 | contract_t と次の関数の間が空行 1 つ（Low） | scripts/check_asset_consistency.py:415 | [ ] 適用済み |
| 保守性 | マーカー行のパーサが hook / 検査器 / runner の 3 か所に重複（Low） | guard-gated-write.sh:42 ほか | 見送り: 文字列の正本は 1 つで契約 (s) と自動生成ケースが突合する。パーサ共通化は hook の自己完結（配布先に scripts が無い）と両立しない |

## 正当性

| Axis | 指摘 | ファイル | 修正状況 |
|------|------|----------|----------|
| 引数処理 | `git -C <対象ディレクトリ> mv a b` が素通りする。`-C` の値を読み飛ばすだけで宛先と合成しない（High。`git -C .claude/hooks mv old.sh new.sh` / `git -C docs/knowledge mv x.md y.md` で SILENT を実測） | .claude/hooks/guard-gated-write.sh:109-116 | [ ] 適用済み: `-C` の値を宛先と合成して判定（W28-W30・W37-W38） |
| 引数処理 | ラッパー集合に `env` / `exec` / `sudo` が無く、`env FOO=bar tee CLAUDE.md` / `echo x \| env A=1 tee CLAUDE.md` / `exec git mv a docs/knowledge/x.md` が素通り（Medium。実測で SILENT） | .claude/hooks/guard-gated-write.sh:68 | [ ] 適用済み: `env` / `exec` / `sudo` をラッパーに追加し、`-u` / `-g` の値を読み飛ばす（W31-W34・W39） |
| 引数処理 | 対象パスの照合が大文字小文字を区別し、`> CLAUDE.MD` / `>> DOCS/Knowledge/y.md` が素通り。macOS の既定 FS は区別しないので実ファイルが書き換わる（Medium。実測で SILENT） | .claude/hooks/guard-gated-write.sh:45-53 | [ ] 適用済み: 構造判定は `re.I`、縮退の grep は `-i`（W35-W36・W40・WP6） |
| 引数処理 | delete hook も大文字小文字を区別する（Low。本 diff ではロジック未変更） | .claude/hooks/guard-gated-delete.sh:63 | 持ち越し: BACKLOG §0.6（ユーザー選択） |
| 引数処理 | delete hook は `FOO=1 rm ...` の代入前置で沈黙。ヘッダの既知の沈黙形に無い（Low。本 diff ではロジック未変更） | .claude/hooks/guard-gated-delete.sh:52-59 | 持ち越し: BACKLOG §0.6（ユーザー選択） |
| 状態遷移 | 抽出失敗・python3 不在の縮退で、保護が 6 系統から 3 系統に落ちる（`.claude/` 系が無保護）（Medium。security の Low と統合） | .claude/hooks/guard-gated-write.sh:133-142 | 受容済みのトレードオフ（M4）のまま。[ ] 適用済み: claude-code-config.md と hook のヘッダに明記 |
| 境界条件 | GIT_ALLOW_RE が `Bash(git-lfs ...)` も拾う（過検知方向・Info） | scripts/check_asset_consistency.py:397 | 対応不要 |

## セキュリティ

| 指摘 | ファイル | 修正状況 |
|------|----------|----------|
| 契約 (t) の正規表現が `Bash( git ...)`（括弧直後の空白）を取りこぼす（Low） | scripts/check_asset_consistency.py:397 | [ ] 適用済み: `^Bash\(\s*git\b` にして変異ケースを追加 |
| python3 不在時の `.claude/` 系の無保護（Low → 正当性の縮退指摘に統合） | .claude/hooks/guard-gated-write.sh:133-142 | 正当性の行を参照 |
| `$(...)` / 変数展開の宛先・`env` 前置等は検出しない（Info。敵対的封鎖は design の対象外。ただし `env` は正当性の Medium で扱う） | .claude/hooks/guard-gated-write.sh | 対象外 |

## パフォーマンス

対象なし

## アクセシビリティ

対象なし

## UI

対象なし

## 全体サマリー

- 重要な問題（Medium 以上・誤検知を除く）: 5 件（High 1・Medium 4。うち test の Medium 1 件は修正を適用済み）
- 重複統合: 2 件（縮退 6→3 系統: correctness 軸 2 / 軸 4 / security を 1 件に。impl の `;` 指摘の Axis 1 / Axis 3 を 1 件に）
- 誤検知: 1 件（impl の `;` High。実測で否定）
- 修正適用後のテスト: tests/assets/run.py 33/33、test:hooks 100/100、validate:assets 18/18、lint OK
- 配置先への反映: なし（skill-test は 20260929 に廃止。decisions 参照）
