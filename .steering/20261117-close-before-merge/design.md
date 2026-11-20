# タスクを閉じ忘れたまま統合ブランチへマージするのを防ぐ

Status: APPROVED

## 目的

feature ブランチで始めたタスクの `.steering/<タスク>/` を、閉じずに統合ブランチ（main・develop など）へマージするのを防ぐ。今の歯止めは、CLAUDE.md の「main へのマージ前に steering で閉じる」と tasklist の最後の項目だけで、Claude が覚えていて実行することに頼っている。

実際に起きたこと:

- PR #31（20261116-exemption-visibility）: PR を作った後、Claude が自分の判断で閉じるのを保留した。ユーザーに聞かれるまで、開いたままマージされる状態だった（`.steering/skill-issues.md` の 20261117）
- `20260730-report-driven-fixes` は、`steering archive` の項目が未チェックのまま、アーカイブされない場所に残っていた（git の履歴）

## 決定済み（20261117・ユーザー）

- **前提:** steering のタスクは PR ごとに作り、作業は必ずブランチを切って行う（GitHub flow でも git-flow でも）。そのため、統合ブランチの tree に APPROVED のタスクのフォルダがあるのは、閉じずにマージされたときだけ
- **閉じる時機:** pr-create が PR の URL を報告した後、そのタスクに残っているのが閉じる項目だけなら、steering の「閉じる」の確認を続けて出す
  - 却下: push の前に閉じて PR に含める — history.md の行に PR の番号を書けず、PR のレビューの記録を書き足す場所も無くなる
  - 却下: 表示だけにする — 今回のように、表示を読み飛ばすと同じことが起きる
- **閉じる確認と push の承認は 1 回にまとめる。** 確認の文に「承認したら、1 つのコミットにして push する」と書く（プレモータムの論点 A）
- **後で拾う仕組み:** SessionStart の hook（`session-start-check.sh`）が、統合ブランチの tree にある APPROVED のタスクに「閉じ忘れの疑い」の印を付ける。今いるブランチには関係なく判定する（論点 B）
  - 却下: GitHub Actions でチェック — CI を新しく作ることになり、配る先にも届かない
  - 却下: 今いるブランチが既定のブランチのときだけ判定する — マージの後はすぐ次のブランチを切るので、印が出る機会がほとんど無い
- **steering も閉じる確認まで進む。** ただし、PR を作った記録が tasklist にあるときだけ（論点 C は C1）

## 決定済み（20261120・手で試した結果から・ユーザー）

- pr-create は閉じる確認を出すとき、steering のスキルを呼ぶ（手順を写さない）
- tasklist の更新と閉じるのを 1 コミットにするため、steering の閉じる手順 2 は、その流れの tasklist の更新を聞かずに含める（既存の設計のまま。試して必要と確かめた）
- 閉じない場合、pr-create は PR の後に tasklist に触らない。PR の番号は steering の再開で `gh pr list` から付ける。このため「チェックを付けるのは pr-create だけ」（20261117）は取り下げる
- hook（SessionStart の印）は作る。閉じる確認を断ったマージを後から拾う手段がほかに無いため
- 未検証のまま残す: PR のレビューで閉じた後に直しが入る場合

## 対象 / 対象外

対象:

- 統合ブランチの決め方と、閉じてよい状態の判定（下の定義）
- pr-create: PR を示すときの予告と、PR を作った後の閉じる確認
- steering: 閉じる手順のコミットと push、再開で閉じてよい状態になったときの確認、状況の確認での印
- design-doc: tasklist の最後の 2 項目
- `session-start-check.sh` の印と、そのテスト
- README の依存の表と hook の説明
- 評価のケース 3 件（pr4・pr5・s4）

対象外:

- マージそのものを止めること（マージは人が Web で行い、Claude の hook は届かない）
- GitHub Actions
- `release/*` など、ほかの名前の長く残るブランチ（論点 2）
- 閉じる手順の 1〜6 の中身。呼ぶ時機と、最後のコミットと push だけを足す

## 前提（コードで確かめたこと）

- pr-create が `.steering/` を見るのは、Step 1（SPIKE で止まる・タスクを特定する）と Step 3（本文に目的を写す）だけ。Step 4 には「DRAFT なら、未承認の設計の実装であることを先頭に書く」がある（`pr-create/SKILL.md:20-21,37,46`）
- steering の「閉じる」は頼まれたときだけ動く。手順 2 は、タスクのフォルダに未コミットの変更があれば先にコミットするかを聞く。手順 6 の `git rm -r` で終わり、コミットも push もしない（`steering/SKILL.md`）
- `session-start-check.sh` は、`archived` を除いた `.steering/` 直下のディレクトリを並べるだけで、git を呼ばない。テストは `tests/hooks/run_fixtures.py` の `check_session_start`（SS1〜SS3）。`run_hook` は `os.environ` をそのまま渡す（`run_fixtures.py:686-688`）
- `scripts/validate_skills.py:252-253` は、SKILL.md が言及するほかのスキルと、README の `deps:skills` の「案内先」を両方向で照合する。今の pr-create の行は「-」
- 過去の tasklist の閉じる項目は「マージの前に steering で閉じる」「steering archive モードでアーカイブ」などで、どれも「steering」を含む（`git log --diff-filter=D` で消したタスクの tasklist を読んだ。一回限り）
- 評価の pr グループは、push の前で止まるところまでしか流れない（`stop-no-push`）。PR を作った後の振る舞いは、1 ターンの評価では見られない
- 回帰の比べる元: `eval/results-pr-c-pr1-20261116.json`・`results-pr-c-pr2-20261116.json`・`results-pr-c-pr3-20261116.json`・`results-steering-c-s3-20261113.json`
- `docs/knowledge/frontend-design.md` は UI の知見で、このタスクには関係しない

## 振る舞い

### 定義

- **統合ブランチ:** `origin/HEAD` が指すブランチ（`git symbolic-ref --short refs/remotes/origin/HEAD` から `origin/` を外した名前）と、ローカルにある `main`・`master`・`develop`。feature の PR がマージされる、長く残るブランチ
- **PR の項目:** tasklist の行のうち、`pr-create` を含むもの
- **閉じる項目:** tasklist の行のうち、バッククォートの中を除いた残りに、語としての `steering`（前後が英数字・`.`・`/`・`-` でない）と、`閉じ`・`アーカイブ`・`archive` のどれかを含むもの。`.steering/skill-issues.md` のようなパスには当たらない
- **閉じてよい状態（スキルの側）:** 次をすべて満たすとき
  1. `design.md` の `Status:` 行が `APPROVED`
  2. tasklist の PR の項目にチェックがあり、PR の番号（`#数字`）が添えてある
  3. 未チェックの項目が 0 件か、どれも閉じる項目

### pr-create（版 2.2）

- **Step 1:** 対象のタスクを決めたら、PR のベースが統合ブランチかも控える
- **Step 4:** ベースが統合ブランチで、対象のタスクがあるときは、PR の項目にチェックを付けたと仮定して定義に当て、示す内容に次の 1 行を添える
  - 閉じてよい状態になる: 「PR の後、タスク <名前> を閉じる確認を続けて出します」（この文言は固定。評価の `regex` が見る）
  - APPROVED だが、閉じる項目のほかに未チェックが残る: 「タスク <名前> は未チェックの項目が残るため、PR の後も閉じません（残り: …）」
  - DRAFT で、差分が `.steering/` だけ: 「設計だけのため、タスク <名前> は閉じずに残します」
  - DRAFT で、ほかの差分もある: 既存の文（未承認の設計の実装であること）だけ。閉じない
- **PR を作った後:** URL を報告した後に、次を行う
  1. PR の項目にチェックを付けたと仮定して、閉じてよい状態かを定義に当てる
  2. 閉じてよい状態なら、tasklist の PR の項目にチェックを付けて PR の番号を添え、steering のスキルを呼んで「閉じる」の手順 1〜3 で確認を出して止まる（手順を写して出さない）。history.md の行には PR の番号を入れる。確認の文に「承認したら、tasklist の更新と閉じるのを 1 つのコミットにして push する」と書く
  3. 閉じてよい状態でなければ、tasklist に触らず、閉じずに残りの項目を示す。PR の番号は、steering が次に tasklist を更新するときに書く（下の steering の再開の手順 4）。追加のコミットと push の承認を生まないため（decisions.md 20261117 の 1 回目）
  4. steering のスキルが無い配置先では、フォルダが残っていることと、マージの前に閉じる必要があることだけを伝える
- ベースが統合ブランチでないとき（大きなタスクの統合用 feature ブランチへの子ブランチの PR）は、何もしない

### steering

- **閉じるの手順 2:** その流れで付けた tasklist の更新（PR の項目のチェック・項目のチェック）だけが未コミットなら、聞かずに閉じるコミットに含める（decisions.md 20261120 の 2 回目で、ここで止まって 2 コミットに分かれたため）
- **閉じるの手順 7（新規）:** PR が開いているブランチで閉じたときは、次を行う（確認の文で予告し、承認済み）
  1. `gh pr view --json state` で状態を確かめる
  2. OPEN なら、1 つのコミットにして push する
  3. MERGED なら push しない。統合ブランチの上で閉じ直す案内を出す
- **再開の手順 4:** tasklist を更新するとき、PR の項目が未チェックなら `gh pr list --head <今のブランチ> --state open --json number` で開いた PR を探し、あればチェックと番号を付ける（pr-create が閉じない場合に tasklist に触らないため。gh が無い・失敗したら付けない）。更新した結果、閉じてよい状態になったら、閉じる手順の 1〜3 に進み、確認で止まる。閉じる項目のほかが終わっていても、PR の項目にチェックと番号が無ければ、「先に pr-create で PR にする」と示す
- **状況の確認:** 閉じてよい状態のタスクに「閉じてよい（PR #N。未チェックは閉じる項目だけ）」と添える

### design-doc

- **tasklist の最後:** 「レビュー」「tasklist の更新」に続けて、「pr-create で PR にする」「マージの前に steering で閉じる」を入れる。ほかの説明は変えない

### SessionStart の hook

- **判定:** 作業ツリーにあるタスクのフォルダのうち、統合ブランチのどれかの tree にあって、その tree の `design.md` の Status が `APPROVED` のものに、「（閉じ忘れの疑い: <ブランチ> に APPROVED のまま入っている）」を付ける。案内の文にも 1 行足す（「閉じ忘れの疑いがあるタスクは、steering で閉じるかユーザーに聞く」）
  - 今いるブランチには関係なく判定する
  - tasklist は読まない。PR ごとにタスクを作るので、統合ブランチに APPROVED のフォルダがあること自体が閉じ忘れの印になる
  - DRAFT は付かない（設計だけをわざと統合ブランチに入れる場合）
  - 作業ツリーに無いフォルダ（今のブランチで閉じたが、まだマージしていない）は付かない
- **git が無い・git 管理下でない・git が失敗したとき:** 今と同じ一覧だけを出す。印は付けない
- POSIX のコマンドと git だけを使う（配る先に依存を増やさない）

## 構成

| ファイル | 変更 |
|---|---|
| `.claude/hooks/session-start-check.sh` | 統合ブランチの決め方と、閉じ忘れの疑いの印 |
| `tests/hooks/run_fixtures.py` | `check_session_start` にケースを足す |
| `.claude/skills/pr-create/SKILL.md` | Step 1・Step 4・PR を作った後。版 2.2 |
| `.claude/skills/steering/SKILL.md` | 閉じるの手順 2・手順 7、再開の手順 4、状況の確認。版を 1 つ上げる |
| `.claude/skills/design-doc/SKILL.md` | tasklist の最後の項目。版を 1 つ上げる |
| `README.md` | `deps:skills`（pr-create の案内先に steering、steering と design-doc の案内先に pr-create）・`deps:hooks`（session-start-check に「git（無ければ印なし）」）・SessionStart の説明 |
| `eval/gen_pr_cases.py`・`eval/gen_design_cases.py`・`eval/README.md` | ケース 3 件と回帰テストの表 |

増える状態は無い。

## 完了条件

1. `test:hooks` の `check_session_start` で、次を確かめている
   - main の tree に APPROVED のタスクがあり、今いるのは別の feature ブランチ → 印が付く
   - 今いるのが main → 印が付く
   - main の tree では DRAFT → 付かない
   - 今のブランチにだけある APPROVED のタスク（統合ブランチの tree に無い）→ 付かない
   - 統合ブランチの tree にはあるが、作業ツリーに無い（今のブランチで閉じた）→ 一覧に出ない
   - `origin/HEAD` が `develop` を指し、develop の tree に APPROVED のタスクがある → 付く
   - `origin/HEAD` が無く、ローカルの `main` がある → 判定する
   - detached HEAD でも同じに判定する
   - git が 0 以外で終わる（偽の git を PATH の先頭に置く）→ 今と同じ一覧で、印が無い
   - git 管理下でない → 今と同じ一覧で、印が無い
   - 既存の SS1〜SS3 が通る
2. `validate`・`validate:portability`・`test:hooks`・`test:skills`・`test:sandbox`・`lint` が通る
3. 評価の `pr4-close-after-pr`（新規。APPROVED で、未チェックは PR の項目と閉じる項目だけ）で、3 回とも次を満たす
   - 最終回答に「閉じる確認を続けて出します」が出る（`regex`）
   - push と PR 作成をしない
4. 評価の `pr5-design-only`（新規。DRAFT で、差分が `.steering/` だけ）で、3 回とも次を満たす
   - 「閉じる確認を続けて出します」が出ない
   - push と PR 作成をしない
5. 評価の `s4-ready-to-close`（新規）で、3 回とも次を満たす
   - fixture は、PR の項目にチェックと番号があり、閉じる項目のほかに 1 項目だけ残るタスク
   - 残りの項目を進めた後、閉じる確認（索引の行と消すフォルダ）を出す
   - 何も消さず、push しない
6. 評価の `pr1-feature-branch`・`pr2-spike`・`pr3-exemption`・`s3-close-task`（各 3 回）が、前提に書いた比べる元と同じ合否になる
7. 流さなかったケース（d1・d1b・d2・d3・d5・s1・s2）と、流さない理由が decisions.md にある
8. このタスク自身の PR で、次を確かめる。記録は PR の本文に書く（decisions.md はこれから消すフォルダの中にあるため）。一回限り
   - PR を作った後に、閉じる確認が続けて出る
   - 承認の後、閉じるコミットが PR に載る

3〜6 は課金がある。目安は次のとおり。合計は 3〜5 ドル。

- pr のケース: 1 実行 0.13〜0.21 ドルで 5 件 × 3 回。合わせて 2〜3.2 ドル
- steering のケース: 1 実行 0.1〜0.35 ドルで 2 件 × 3 回。合わせて 0.6〜2.1 ドル

実行は skill-test の手順どおり、見積もりを示して承認を取ってから、通常のターミナルで流してもらう。

## テスト方針

- hook は、既存の `check_session_start` と同じ形で、一時ディレクトリに git のリポジトリを作るケースを足す。既存の SS1〜SS3 は変えない
- git の環境を固定する: `GIT_CONFIG_GLOBAL=os.devnull`・`GIT_CONFIG_NOSYSTEM=1`・`git init -b main`。`origin/HEAD` は `git symbolic-ref refs/remotes/origin/HEAD refs/remotes/origin/<名前>` と `update-ref` で作る（リモートは要らない）
- スキルの本文の変更は、評価のケースで確かめる
- design-doc の変更は、tasklist の最後の 2 項目だけなので評価を流さない（d1b の tasklist の採点は、項目にテストを含むかだけを見て、最後の項目には触らない）。理由を decisions.md に書く
- このリポジトリには vitest が無く、Stop のテストのゲートは動かない。`test-exemptions.md` は作らない

## 論点

1. **閉じる項目と PR の項目の見分け方。** 推奨は、上の定義のとおり行の文言で見分ける形。hook はこれを使わないので、誤ると、スキルの確認が出る・出ないだけに影響する
   - 代わりの案: tasklist に決まった印（`<!-- close -->` など）を付ける。確実だが、既存の tasklist と書き手の手間が増える
2. **統合ブランチの名前の一覧。** 推奨は、`origin/HEAD` と、`main`・`master`・`develop` に固定する形
   - `release/*` などは拾わない。配る先で要るようになったら、名前を足せる形（たとえば `.steering/` の中の設定ファイル）を別のタスクで考える
3. **pr-create が steering に頼る。** 推奨は、steering の「閉じる」の手順を使う形。steering が無い配置先では、伝えるだけにする
   - 代わりの案: pr-create に閉じる手順を写す。自己完結になるが、手順が 2 か所に分かれてずれる

## 悲観的に見ると

- SessionStart の印が出るのは、マージの後の次のセッション。気づいた後は、統合ブランチの上で閉じることになる。CLAUDE.md の「微修正は main へ直接コミットしてよい」の範囲で済む
- PR を作った直後に閉じると、PR のレビューで直したことの記録は、閉じた後のコミットと PR のコメントにしか残らない（決定済みとして受け入れた）
- ユーザーが閉じる確認を断れば、今と同じく開いたままマージされうる。SessionStart の印で後から拾う
- 統合ブランチを手元で更新していない（`git fetch` していない）と、hook は古い tree で判定する。ローカルの `main` が古ければ印は遅れる。`origin/HEAD` の側は `fetch` の時点の tree になる
- 「PR ごとにタスクを作る」から外れる使い方（統合ブランチの上で直接タスクを進める）では、APPROVED にした時点で印が付き続ける。この運用は CLAUDE.md の外なので受け入れる

## プレモータム所見（20261117）

攻撃役の所見 9 件。README・`scripts/validate_skills.py`・`tests/hooks/run_fixtures.py`・steering の本文を読んで裏を取った。9 件とも採り、9 は一部を捨てた。

### 採った穴

1. **後で拾う hook の印が、拾いたい場面でほとんど付かない。**
   - 根拠: 「PR にする」項目にチェックを付けるのは、pr-create の「PR を作った後」だけ。pr-create を通らない PR でも、閉じる確認を断ったマージでも、main の tasklist には「pr-create で PR にする」（`steering` を含まない）が未チェックで残る。design-doc が今後この項目を必ず入れるので、新しいタスクはどれもこの形になる。
   - 提案: 既定のブランチの側で判定するときは、PR の項目も閉じる項目と同じに扱う。完了条件 1 に「PR の項目と閉じる項目が未チェック → 印が付く」を足す。
2. **閉じた変更が PR に載る手順が無い。**
   - 根拠: steering の「閉じる」は、手順 6 の `git rm -r` で終わり、コミットも push もしない（`steering/SKILL.md:103`）。tasklist にチェックを付けると、それがタスクのフォルダの未コミットの変更になり、閉じる手順 2 の「先にコミットするか聞く」で毎回止まる。確認を待つ間に Web でマージされると、閉じるコミットは main に届かない。
   - 提案: 次を明記する。
     - チェックの付与と閉じるのを、1 つのコミットにする（手順 2 の未コミットの変更とはみなさない）。
     - push の前に `gh pr view --json state` で OPEN を確かめる。MERGED なら、main の上で閉じる案内に切り替える。
     - 完了条件 7 に「閉じるコミットが PR に載ったこと」を足す。
3. **印の条件が「今いるブランチが既定のブランチ」だと、普段の流れでは出ない。**
   - 根拠: マージの後はすぐに次の `feature/*` を切ることが多い。閉じ忘れたフォルダはそのブランチにも入るが、印は付かない。
   - 提案: 条件を「そのタスクのフォルダが既定のブランチの tree にある」に変え、中身も既定のブランチの側から読む（`git show <既定>:.steering/<task>/tasklist.md`）。今いるブランチに関係なく判定でき、feature ブランチで作ったばかりのタスクに誤って印を付けずに済む。
4. **steering の再開で、PR の前に閉じる確認が出る。**
   - 根拠: 定義は PR の有無を見ない。PR の項目が無い tasklist（既存のもの・手で書いたもの）では、最後の実装の項目を終えた時点で閉じてよい状態になり、steering が閉じる確認まで進む。これは却下した「push の前に閉じる」と同じ。s4 は、この経路を合格の基準にしている。PR の項目を steering が進めると、pr-create と二重に動く。
   - 提案:
     - steering の側の条件に「PR がある（PR の項目にチェックと番号がある）」を足す。無ければ「先に pr-create で PR にする」と示す。
     - チェックを付けるのは pr-create の 1 か所に決める。
     - s4 は「PR の項目にチェックと番号があり、残りの 1 項目を終えると閉じてよくなる」形にする。
5. **閉じる項目の見分け方が `.steering/` というパスにも当たる。PR の項目の見分け方も無い。**
   - 根拠: `.steering/skill-issues.md`・`.steering/archived/` は `steering` を含み、`archived` は `archive` も含む。このリポジトリでは、そうした項目が実際に出る（verify-tree-guard の tasklist の 44 行目）。同じ定義が、pr-create と steering では閉じる確認の引き金になるので、「知らせるだけ」では済まない。
   - 提案: 照合の前にバッククォートの中を取り除き、`steering` は語として（前後が英数字・`.`・`/` でない）見る。PR の項目の規則（`pr-create` を含む行）も定義に入れる。完了条件 1 に「`.steering/skill-issues.md` に閉じ方の摩擦を書く」が未チェックなら付かない、を足す。
6. **pr-create の Step 4 に添える 1 行が、既存の文や実際の流れと食い違う。**
   - 根拠: 既存の Step 4 には「DRAFT なら、未承認の設計の実装であることを先頭に書く」がある（`pr-create/SKILL.md:46`）。設計は DRAFT を一律に「設計だけ」と書いているので、DRAFT のまま実装を PR にするときに矛盾する。APPROVED でも、ほかの項目が残っていれば閉じない。
   - 提案: 予告は、PR の項目にチェックを付けたと仮定して定義に当てた結果で、3 通り（閉じる確認を出す・残りの項目を示す・閉じない）に分ける。「設計だけ」は、差分が `.steering/` だけのときに限る。
7. **構成の表に README の依存の表が無い。**
   - 根拠: `scripts/validate_skills.py:252-253` は、本文が言及するスキルと README の `deps:skills` の「案内先」を両方向で照合する。pr-create の行は今「-」（`README.md:146`）。hook の表の session-start-check の「要るもの」も「-」（`README.md:153`）。
   - 提案: 構成の表に、次を足す。
     - `deps:skills`: pr-create の案内先に steering。design-doc の本文に pr-create を書くなら、その行にも足す
     - `deps:hooks`: session-start-check に「git（無ければ印なし）」
8. **hook のテストに、本命の経路と環境の固定が無い。**
   - 根拠: 完了条件 1 に、`origin/HEAD` が効くケースが無い。`run_hook` は `os.environ` をそのまま継承する（`run_fixtures.py:686-688`）。そのため `git init` が、ユーザーの `init.defaultBranch` やグローバルの設定の影響を受ける。
   - 提案: 次の 3 ケースを足す。テスト方針に、git の環境の固定（`GIT_CONFIG_GLOBAL=os.devnull`・`GIT_CONFIG_NOSYSTEM=1`・`git init -b`）を書く。
     - `origin/HEAD` が main 以外を指す
     - detached HEAD
     - git が 0 以外で終わる（偽の git を PATH の先頭に置く）
9. **完了条件 3・7 が、誤って合格するか、自分で摩擦を作る。**
   - 3: 予告の 1 行が無くても、本文に写した tasklist の「steering で閉じる」で合格しうる。反対側のケース（DRAFT・ベースが既定のブランチでない）も無い。
     - 提案: 予告の文言を固定して `regex` で見る。DRAFT のケースを 1 件足す。
   - 7: 記録先の decisions.md は、これから消すフォルダの中にある。書けば手順 2 で止まる。
     - 提案: 記録先を、閉じる前のコミットか PR の本文にする。

### 人が決める論点

- **A. 閉じた後の push の承認（2）。** pr-create の原則は「push の前で必ず止まる」。
  - 推奨: 閉じる確認と、閉じるコミットの push の承認を 1 回にまとめる。確認の文に「承認したら、コミットして push する」と書く。
  - 代わりの案: 閉じた後に、もう一度 push の承認を取る。確認が 2 回になる。
- **B. hook の判定の拠り所（3）。**
  - 推奨: 既定のブランチの tree にあるか（`git ls-tree` と `git show <既定>:`）で判定する。
  - 代わりの案: 今いるブランチで判定する。シンプルだが、feature ブランチで始まったセッションでは出ない。
- **C. s4 の形（4）。**
  - 推奨: PR の項目にチェックと番号がある fixture で、残りの 1 項目を終えると閉じる確認が出ることを見る。
  - 代わりの案: s4 をやめ、steering の変更は s3 の回帰だけで見る。

### 捨てた所見

- 9 の 5「比べる元の結果がどこにあるか書かれていない」 — 理由: 比べる元はある（`eval/results-pr-c-pr1〜3-20261116.json`・`eval/results-steering-c-s3-20261113.json`）。完了条件にそのパスを書き足すだけで済み、main で流し直す費用は要らない。

### 反映（20261117・ユーザーの回答）

- A: 閉じる確認と push の承認を 1 回にまとめる → 「決定済み」と steering の手順 7 に反映
- B: タスクは PR ごとに作り、必ずブランチを切る前提。判定は「統合ブランチ（origin/HEAD・main・master・develop）の tree にある APPROVED のタスク」にし、tasklist は読まない → hook の振る舞いに反映。所見 1・3・5 の hook の側は、これで解消した
- C: C1（PR の記録がある tasklist で、steering も閉じる確認まで進む）→ steering の再開の手順 4 と s4 に反映
- 所見 2・4・6・7・8・9 は本文に反映した
