# タスクリスト: レビュー積み残しの解消

## 0. 最優先（セッション再起動後の最初）— 完了 20260726

- [x] `echo test > docs/decisions/_probe.md` を実行し、確認ダイアログが出るか観察する → **出た**（guard hook の理由文つき）
- [x] `docs/knowledge/` 配下の Edit でも同様に確認する（ask 側）→ **Write / Edit とも出た**（Edit は単独実行で再確認）
- [x] `remind-config-docs.sh` の発火を確認する → **skills / config 両分岐で注入・誤発火なし・セッション 1 回制限も期待通り**
- [x] probe を削除する（`docs/decisions/_probe.md`・`docs/knowledge/_probe.md`・`.claude/hooks/_probe.sh`・`.claude/skills/_probe/`）→ `git status` クリーン
- [x] 結果に応じて記述/実装を訂正する → **撤回は不要**（機械防御は成立）。新たに「削除はゲート対象外」が判明したため 2 に追加

詳細は `design.md` の「実測結果（20260726・セッション再起動後）」。

## 1. スクリプトの品質指摘 — 完了 20260726

- [x] `validate_skills.py`: 未知フラグの Traceback を塞ぐ → `KNOWN_FLAGS` の一般ガードで exit 2。`--protability` / `-x` で Traceback が消え、既存 6 経路は全て exit 0 のまま（実測）
- [x] `check_export_stopcontract.py`: `--verbose` の仕様一致 → `compare()` が無害差分を件数でなく行で返すようにし、**実質差分ありスキルの無害差分行も**表示（合成データで実測）
- [x] `check_export_stopcontract.py`: 報告の切り詰めで差分の実体が見えるようにする → `first_diff()` で食い違い位置を求め、`excerpt()` が窓をそこに寄せる。`design-doc` の 192 文字目の差分が読めるようになった
- [x] `check_export_stopcontract.py`: 非同梱スキル名の除去に語境界を入れる → `(?<![A-Za-z0-9-])…(?![A-Za-z0-9-])`。`adrenaline` の巻き添えが消え、和文に埋まった名は従来どおり除去
- [x] `check_export_stopcontract.py`: `read_body()` の型注釈を実体に合わせる → `list[tuple[int, str]]`
- [x] `check_export_stopcontract.py`: `STACK_WORDS` に `.test.tsx` / `.spec.tsx` を追加 → あわせて **長さ順に適用**（`STACK_WORDS_SORTED`）。短い語を先に消すと長い語が壊れる並び順バグを構造で潰した
- [x] `check_export_stopcontract.py`: `--master` 不在時のエラー文言を分ける → 側ごとの助言に分離

**回帰確認**: 実質差分 7 / 無害のみ 1 / 差分なし 2 のサマリは修正前後で不変。`APPROVED` の正規化も無傷。

## 2. 権限の射程 — 完了 20260726

- [x] 配布物 `settings.example.json` に `docs/decisions/` の ask を追加 → `*` / `**` / `**/*` の 3 形式 × Edit/Write
- [x] global CLAUDE.md と `.claude/skills/**` を ask に含めるかを判断する
  - **global CLAUDE.md は追加**（master）: `Edit/Write(~/.claude/CLAUDE.md)`。`knowledge-capture` の保存先候補なのに射程外だった。Bash 側は既存 hook の `CLAUDE\.md` パターンが `~` 形式・絶対パス形式とも拾うことを実測で確認済み
  - **`.claude/skills/**` は見送り**（master / export とも）: master ではスキル本文の編集が主活動で確認が常時出る（摩擦大）。export 側も今回は入れない — 入れるなら「配置先で直接編集しない」ルールの機械化として別途判断する
- [x] `docs/knowledge/claude-code-config.md` に「ゲートの対象は書き込みのみ・削除は非対象」を明記する
- [x] **（追加で判明）配布物に `guard-gated-write.sh` が無かった** — master が High として塞いだ Bash 迂回路が export 側では開いたままだった。配布用に文言調整（非同梱の `adr` を除去）して同梱・登録し、hook 4 本 → 5 本。`MANIFEST` / `MIGRATION-GUIDE` / `HANDOVER` の本数記述も同一変更で揃えた
  - 発火 3/3・誤検知 0/2・非同梱スキル名の混入 0 を実測

## 3. 観察

- [x] `remind-config-docs.sh` が**発火するか**を確認する → 20260726 実測で両分岐とも注入を確認
- [x] `remind-config-docs.sh` の**効果**を観察する（1 セッション分）
  - 06:40 に config 分岐の要点が注入され、07:0x の `settings.json` / `settings.example.json` 編集で **`claude-code-config.md` を読まずに**要点 (1)(2) を適用した: global CLAUDE.md を ask に足すとき Bash 側の到達可能性を確認し、`docs/decisions/` は glob 3 形式で並べた
  - ただし**これは 1 セッション・1 事例で、対照が無い**（注入が無くても同じ判断をした可能性は否定できない）。「効いた」と断定せず観察を継続する。外す判断はまだしない

## 4. 完了処理

- [x] 静的検査（29/29 PASS・portability 0 件・停止契約サマリ 7/1/2 で不変）
- [x] コミット（master と `export/company` で別コミット。ブランチが分かれるため 1 コミットにまとめられない）
- [x] `knowledge-capture` — 2 件保存（`claude-code-config.md` に「配布物にも同じ防御が要る」節を新設 / `skill-design-patterns.md` の検出ツール節を 3規律 → 4規律 に改訂）。既に本文に書き込み済みの 3 件は重複として見送り
- [x] `compound` — 3 件昇格（`expected_hooks()` の同送漏れ / compound の洗い出し範囲 / `session-stop.sh` の AND 条件）。既存違反 2 件も同じ承認内で修正。詳細は `codify-log.md`
- [x] `steering` archive

Archived: 20260726
