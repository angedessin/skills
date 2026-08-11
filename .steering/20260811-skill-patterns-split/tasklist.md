# タスクリスト: skill-patterns-split

design.md（Status: DRAFT）承認後に着手する。プレモータム反映済み（20260811）。

## 0. 着手前の前提確認

- [x] `git status --short` が clean であることを確認する
      （20260811 時点で CLAUDE.md / README.md / check_asset_consistency.py が未コミット。
      本設計のベースラインはその差分に依存している）
- [x] ベースラインを記録: `wc -l docs/knowledge/skill-design-patterns.md` /
      `python3 scripts/validate_skills.py` の件数 / `python3 scripts/check_asset_consistency.py` の件数
- [x] 未解決の論点 1（測定ログの置き場）→ **(a) `references/` に同梱**で決着（20260811）
- [x] 未解決の論点 2（472 行で十分か）→ **十分**。追加分割は今は起票しない（20260811）
- [x] 未解決の論点 4（`docs/knowledge/review-workflow.md` の重複解消）→ **解消済み**
      （原本を人が削除・`53288d6`）。着手時点では未了で、本タスクの変更ファイルと重ならないため
      前提を解除して進めた

## 1. 変更対象の確定（実装の一部）

design.md の「主要コンポーネント」は**暫定**。表に挙げ漏れた箇所は片側修正として残るため、
着手時に機械的に洗い出して表を確定させる。

- [x] `grep -rn "skill-design-patterns" --include='*.md' --include='*.py' --include='*.sh' . --exclude-dir=node_modules --exclude-dir=.steering` で参照元を全列挙する
- [x] そのうち**節を名指ししている**参照だけを抽出する（設計の見込みは
      `skill-test/SKILL.md:52` と `scripts/passthrough_check.py:5` の 2 件。増えていたら表に追記）
- [x] `grep -rn "素通り検査\|passthrough" --include='*.md' . --exclude-dir=node_modules --exclude-dir=.steering` を取り、
      **正本の中の**移動対象だけを特定する（他ファイルの 18 件は対象外）
- [x] 洗い出し結果を design.md の「主要コンポーネント」に反映する

## 2. 規律の抽出と固定（圧縮の前にやる）

- [x] 209-383 行から**規律として書かれている文**を機械抽出し、一時ファイルに固定する
- [x] 各規律に抽出元の行番号を対応表として付ける（圧縮後の突合に使う）
- [x] 移動対象（純粋なテスト運用手順）と残す規律を行単位で分類する。
      **311-317 と 325-330 は残す側**（執筆規律。プレモータムで再分類）

## 3. 新ファイルの作成

- [x] `.claude/skills/skill-test/references/passthrough-testing.md` を作成
- [x] `## 素通り検査の手順` — **`skill-test/SKILL.md:48,50` に無い情報だけ**を書く
      （環境圧の添え方・無出力 run は FAIL・シナリオは現実に処理する最も充実した入力で組む・
      薄いシナリオの全 PASS を合格と数えない）
- [x] SHA1 判定 / 自己申告不使用 / 4 run 規律は**書かない**（SKILL.md が正本・複製しない）
- [x] `## 測定ログ` — 20260703-04 / 0709 / 0711 / 0718 / 0724 / 0725 の run 数と FAIL 内訳の表
- [x] 参照ファイルが無い場合の代替動作を書く（`skill-design-patterns.md:42` の規律）

## 4. 正本の再構成

- [x] 規律の箇条書きを節の先頭に置く（**意味を変えない**。箇条書き化による表現変更は可）
- [x] 代表実例 2 件（20260703-04 / 20260724 を仮置き）に絞る。裏付けが足りなければ 3 件に増やす
- [x] 結論を残す（20〜25% で破れる・本文改善に課金を重ねない・書き込み先の広さで機械防御を分ける・
      設計段階で前提チェック型に寄せられないか検討する）
- [x] 末尾に新ファイルへのポインタ 1 行を置く
- [x] 移動した運用手順を本文から削除する
- [x] **削除・移動コマンドは使わない**（Edit のみ。`docs/knowledge/` への rm/mv は hook が deny）

## 5. ポインタの付け替え

- [x] `.claude/skills/skill-test/SKILL.md` の **Step 3 冒頭**に新ファイルを指す 1 文を追加
      （末尾 52 行ではない — シナリオを書く前・コスト提示前に要る情報のため）
- [x] 52 行の既存ポインタ（ハードストップの書き方 = 一次情報）は**残す**
- [x] `scripts/passthrough_check.py:5` の docstring の参照先を新ファイルに付け替える
- [x] 手順 1 で追加検出した「節を名指ししている参照」を付け替える
- [x] `.claude/hooks/remind-config-docs.sh` の skills 分岐を読み、修正不要であることを確認して閉じる
      （プレモータムの裏取りでは不要）

## 6. 検証

- [x] 停止契約節が **85 行以下**（見出し行番号の差で確認）
- [x] `wc -l docs/knowledge/skill-design-patterns.md` → **472 行以下**
      （実装完了時点で **461 行**・`1eb0be3` で達成。その後 knowledge-capture の追記で
      **473 行**になっている — 完了条件は実装時点の値で満たしており、追記は別承認の下での増分）
- [x] `grep -n "素通り検査" docs/knowledge/skill-design-patterns.md` → **許容ヒット 2 件のみ**
      （対象外節 140-208 内の既存 1 件 + 新設した逆ポインタ 1 件）
- [x] `python3 scripts/validate_skills.py` → 全 PASS（着手時ベースラインと同数）
- [x] `python3 scripts/check_asset_consistency.py` → 全 PASS（着手時ベースラインと同数）
- [x] 完了条件の「名指しチェック項目」4 つが正本に残っていることを 1 つずつ確認する
- [x] **フレッシュなサブエージェント**に手順 2 の規律リストと圧縮後の本文を突合させ、
      落ちた規律ゼロを報告させる（実装者本人の自己判定にしない・静的突合のみで無料）
- [x] 素通り検査（課金）は**回さない**（スキル本文の停止契約を変更しないため）

## 7. クローズ

- [x] `git status --short` でステージ内容を確認してからコミットする
- [x] `.steering/BACKLOG.md` 節 1(c) から本タスク該当分を削除する
      （依存表の網羅・README セットアップ節新設は**残す** — 本タスクの対象外）
- [x] 472 行で目的に見合わないと判断した場合、対象外にした 2 節
      （検出ツールの4規律 69 行・リポジトリ構成 75 行）の分離を次タスクとして BACKLOG に起票する
- [x] `knowledge-capture` を実行（案 1・3 を採用し skill-design-patterns.md に追記。案 2 は
      ツール規約であり置き場が違うため見送り）
- [ ] `steering` スキルの archive モードでアーカイブする
