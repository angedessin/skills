# 決定の記録: report-driven-improvements

## [20260920] — ADR 20260706 を supersede せず項目 6 を実施する

**決定**: `docs/decisions/20260706-no-custom-reviewer-agent.md`（Accepted・カスタム agent 定義を導入しない）の
再検討トリガー（誤編集事故の観測）は未充足だが、ユーザー判断により項目 6（`.claude/agents/` 12 本）を実施する。
**理由**: ユーザーが「ADR は無視して良い。新しい設計のじゃまになる」と明示した。ADR は機械検査を持たないため、
無視しても検査は落ちない。
**影響**: リポジトリの判断記録と実装が食い違う状態が残る。`rule-audit` が陳腐化として拾う対象になる。
Claude の推奨は「無視ではなく Superseded にする」（実装は同じで、コストは新 ADR 1 本）だったが、
`docs/` への書き込みは承認制のため ADR には触れていない。**実装が一段落した時点で再度確認する**。
併せて項目 7（frontmatter への `effort` 追加）は `20260722-agentskills-non-adoption` の
「frontmatter を 4 キーに揃える（可搬性）」と衝突する。下記の論点 3 の既定により、今回は追加しない。

## [20260920] — 未解決の論点 3・4・7 の既定

**決定**:
- 論点 3（frontmatter の `effort`）: **入れない**。tasklist 項目 40 はスキップする。
- 論点 4（agent の `model`）: `sonnet` を明示する。
- 論点 7（配置先ドリフト）: 分類と提示まで。再コピーは実行しない。

**理由**: 論点 3 は、セッションの effort を無言で下げる副作用があり、実測前は無指定が安全。
`20260722-agentskills-non-adoption` の frontmatter 4 キー方針とも整合する。
論点 4 は、配置先の `availableModels` 制限で無効化されてもセッションのモデルが維持される安全側の挙動になる。
論点 7 は design.md の完了条件がすでに「提示まで」と定めている。
**影響**: いずれも Claude が置いた既定で、ユーザーの明示承認は得ていない。覆る場合は該当項目のみやり直す。

## [20260920] — Phase 4 を P4a / P4b の 2 行に分け、P4a を P35 より上に置く

**決定**: 判定表の Phase 4 行を `P4a`（PR 前 capture）と `P4b`（最終 capture）の 2 行にし、
`P4a` を `P35`（PR 作成）より上に配置した。
**理由**: design.md は「Phase 4 行の条件を `pr_capture_done` の有無で PR 前 / 最終を書き分ける」とだけ書き、
行の置き場所を指定していない。tasklist 正本（`design-doc/references/templates.md`）の工程順は
実装 → レビュー → 知見保存(PR 分) → デプロイ なので、`P4a` を `P35` より下に置くと
「デプロイ節に未チェックあり」が先に成立し、PR 前 capture に到達しない（Critical 1 と同型の影）。
**影響**: 行 ID 集合が design.md の想定（`P4` 単一）から `P4a`/`P4b` に増える。
`check_asset_consistency.py` の表 ↔ 関数突合の対象。契約コアの書き換えではなく、
承認済み設計の「書き分ける」の実装解釈として扱った。

## [20260920] — 未知の review Status に対応する行が判定表に無い（未修正の穴）

**決定**: 今回は**修正しない**。`resolve_phase()` は `NO_MATCH` を返す。
**理由**: `review-result.md` の Status が 3 値（`OPEN`/`RESOLVED`/`DEFERRED`）以外だった場合、
判定表のどの行にも当たらない。design.md の `design.md` Status には fail-closed 行（`H1`）があるが、
review Status には無い。行を足すのは承認済み判定表への行追加（契約コアの変更）にあたるため、
実装中の判断で足さずに記録にとどめた。
**影響**: 実運用では `frontend-code-review` が 3 値のみを書き、`validate_skills.py` が語彙を検査するため
発生しにくい。ただし `H1` と同じ穴が review 側に残っている。**ユーザーに提起済み**。

## [20260920] — テストケース T9・T11・T12 の期待値を Red 後に修正した

**決定**: Red を確認した後、`T9`（レビュー通過直後の行き先）・`T11`・`T12` の期待値を修正した。
**理由**: 初版は「レビュー通過直後は PR 作成（P35）」という前提で書いたが、tasklist 正本の工程順では
PR 前 capture が先。前提そのものが誤っていた。
**影響**: Critical の再現ケースである `T10`（Phase 3.7 到達）と `C4`（capture 2 段）は**変更していない**。
この 2 件は Red のまま Green になったので、欠陥の再現としての価値は保たれている。

## [20260921] — P4a の条件に「capture_done が無い」を加えた（前回実装の穴）

**決定**: `P4a` の条件を「`pr_capture_done` が無い」から「`pr_capture_done` と `capture_done` のどちらも無い」に変更した。
`pipeline_state.py` と SKILL.md の表を同時に直し、テスト `T14` を追加した（Red を確認してから修正）。併せて `T15`
（`Feedback: no` の PR は P37 に入らない）を追加した。変異検査で `pr_url` だけで P37 が発火する変異を検出できたのが
C4 だけだったため、専用ケースを持たせた。
**理由**: 前回実装の `P4a` は `capture_done` を見ておらず、PR 工程を省略して最終 capture だけで `capture_done` を立てた
タスク（Phase 3.5 は「スキップ可」）が `P4a` に永久に留まった（再現: 期待 `P5`・実際 `P4a`）。
design.md の「`capture_done` が無い に加え `pr_capture_done` の有無で書き分ける」の文言どおりに直したもので、契約コアの変更ではない。
**影響**: 不変条件は「`capture_done` があれば PR 前の分も包含済み」。knowledge-capture の最終 capture は
`pr_capture_done` を別途立てなくてよい。

## [20260921] — 「順序は検査対象外」コメントは削除せず (l) 限定に書き換えた

**決定**: tasklist §1 最終項目・design.md が「削除」とした `check_asset_consistency.py` docstring の「フェーズの順序は
検査対象外」を、削除ではなく「(l) は順序を見ない。判定表の行順は (m)・tasklist テンプレの節順は (n) が検査する」に書き換えた。
README の (l) 記述も「図の順序は検査対象外」に限定した。
**理由**: 元の記述は契約 (l)（README の図 ↔ パイプラインのスキル集合）についてのもので、いまも真。図では同じスキルが
複数位置に現れ順序比較が書式変更で壊れやすいため、(l) に順序検査は足していない。削除すると真の限界情報が消える。
順序を検査対象にするという設計の意図は (m)（行 ID 列を順序つきで比較）で満たしている。
**影響**: なし（検査の追加は (m)(n) の 2 本。名前は設計の (11)(12) に対応）。(13) は §3 で追加する。

## [20260921] — 既知の副作用: PR 前 capture 後も Stop hook が .capture-needed を立て続ける

**決定**: 今回は変更しない。
**理由**: `session-stop.sh` は `capture_done` の有無だけを見るため、`pr_capture_done` だけの間（PR 待ち）は
Stop のたびに `.capture-needed` が再び立つ。design.md は「Stop フェイルセーフは無変更で正しく動く」としていたが、
意味は正しくても催促は増える。「後で」を選べば残置で続行できる。
**影響**: PR 往復が長引くと SessionStart の催促が毎回出る。実運用で煩わしければ `session-stop.sh` に
`pr_capture_done` かつデプロイ未完のときは立てない分岐を足す（hooks 変更なので別判断）。

## [20260921] — portability の strict 化は `--portability --strict` の修飾子で足した

**決定**: `validate_skills.py --portability` の既定（常に exit 0・report-only）は変えず、`--strict` 併記時のみ
混入 1 件で exit 1 にした。CI は `python3 scripts/validate_skills.py --portability --strict` を直接呼ぶ。
`--strict` は `--portability` の修飾子なので `KNOWN_FLAGS`（先頭引数のガード）には入れない
（入れると `--strict` 単独が通常走査に落ちてトレースバックになる。実際に一度そうなり、直した）。
**理由**: design.md の完了条件「警告 0 件」を CI が終了コードで判定するには strict 相当が要る（設計時の調査で判明済み）。
既存の report-only 用途（PostToolUse hook・手動確認）の挙動は変えない。
**影響**: npm script `validate:portability` は report-only のまま（README の npm script 一覧と (k) 契約は無変更）。

## [20260921] — CI の actions はメジャータグ固定（SHA 固定にしていない）

**決定**: `actions/checkout@v4` / `pnpm/action-setup@v4` / `actions/setup-node@v4` をメジャータグで指定した。
**理由**: SHA を確認する手段がこのセッションに無く、推測で書くと誤った固定になる。
**影響**: タグの付け替えによるサプライチェーンリスクは残る。CI の permissions は `contents: read` に絞ってある。
気になる場合は SHA 固定へ変更する（`security-audit` の対象にもなる）。

## [20260921] — ローカル環境の落とし穴: `pnpm install` が biome の x64 バイナリを外す

**事象**: CI 再現のため `pnpm install --frozen-lockfile --offline` を実行したところ、`node_modules` から
`@biomejs/cli-darwin-x64` が外れ `pnpm run lint` が MODULE_NOT_FOUND で落ちた。
この Bash セッションは Rosetta 下（`arch` = i386）で mise の Node は x64 だが、pnpm は arm64 版だけを入れる。
**復旧**: 一時的に `pnpm-workspace.yaml` へ `supportedArchitectures: {os: [darwin], cpu: [x64, arm64]}` を置いて
`pnpm install --frozen-lockfile` → 削除。`node_modules` は gitignore 対象で git 上の変更は無い。
**教訓**: このマシンでは `node_modules` を再インストールしない。CI 再現は各コマンドを個別に回すだけで足りる。

## [20260921] — agent 定義 12 本の実装（frontmatter 書式は公式 docs で裏取り済み）

**決定**: `.claude/agents/` に 12 本を作成した。レビュー 7 軸は `model: sonnet`・`tools` は `Read`/`Grep`/`Glob` と読み取り系 git（`Bash(git diff|log|show *)`）のみ・
`effort` は security / correctness / impl = high、test / a11y / performance / ui = medium。`premortem-attacker` = opus / high、`tournament-scorer` = opus / high、
`codebase-explorer` / `knowledge-scanner` = haiku / low、`tournament-variant` = sonnet（書き込み可・effort 指定なし）。
**裏取り**: `tools` の `Bash(git diff *)` 指定・YAML リスト書式・`skills` のプリロード・`effort` の値域は
公式 docs（code.claude.com/docs/en/sub-agents）で確認した（設計時点で未了だった項目）。
**判断した点**:
- レビュー agent は `pnpm audit` を実行できない（読み取り専用の権限のため）。`review-security` の本文にある「audit 実行不可」の書式に落ちる。
  権限を緩めるより、その書式を使う方を選んだ
- `tournament-variant` に `isolation: worktree` は付けない。worktree は `references/commands.md` の手順で切るため二重になる
- 定義本文には指示の正本（サブスキルの手順）を写さず、役割・権限・入出力契約だけを書いた
**検査**: (o) 参照の双方向突合・(p) frontmatter（必須キー・既知キー・model / effort の値・skills の実在・読み取り専用）を追加。
壊した入力 11 通り（定義の削除・孤児・Edit 混入・素の Bash・書き込み系 Bash 指定・effort 不正・キー打ち間違い・skills 不在・name 不一致・model 不正）で FAIL を確認した（一回限りの検証）。
**ADR**: 20260927 に `docs/decisions/20260927-subagent-roles-in-agent-definitions.md` として起票し、ADR 20260706 を Superseded にした（この項目とレビュー対応の項目が材料。現行は ADR 側）。
**（起票前の記録）**: ADR 20260706（カスタム agent 定義を導入しない）は Accepted のまま。ユーザーは「ADR は無視して良い」と判断済みだが、
Superseded にするかは `docs/` 書き込みなので承認待ち（実装完了後に確認する）。
**影響**: agent 定義は配置先に配布しない（`deploy_skills.py` は `.claude/agents/` を対象にしない）。
配置先では本文のフォールバック（汎用エージェント・自己実行・`feature-dev:code-explorer`）に落ちる。

## [20260921] — レビュー（3 軸）の指摘への対応と、直さなかったものの理由

**結果**: `review-result.md`（Status: OPEN）に統合。Medium 以上 23 件（High 5）・Low 9 件。修正の中身は下記。
**主な設計判断**:
- **読み取り専用 agent から Bash を外した**（`Read` / `Grep` / `Glob` のみ）。`Bash(git diff *)` でも `--output=<path>` で任意ファイルへ書けることが実測で示され
  （security・correctness の 2 軸が独立に再現）、コマンド単位で絞る方法も無いため。diff は呼び出し側が一時ファイルに書き出して渡す（frontend-code-review 本文に追記）。
  契約 (p) は黒名簿（Edit を禁止）から**ホワイトリスト**（許可は Read / Grep / Glob のみ）へ変えた。前回の「Bash(git diff *) は読み取り専用」という判断（下の 20260921 の agent 定義の項）は**誤りだった**
- **knowledge-capture の判定を 4 分岐にした**（最終 / 最終 / PR 前 / 途中）。旧規則「デプロイ節に未チェックがあれば PR 前」は、この repo の運用（マージ前にアーカイブ）で `capture_done` が立たず
  steering archive が止まる退行を生んだ。明示指定（archive・オーケストレーター・ユーザー）を最優先にし、レビュー未通過の途中 capture はフラグを立てない
- **P37 の条件に「デプロイ節に未チェックあり」を足した**（古い `Feedback: yes` で居座らないため）。`H2`（未知の review Status は即停止）を追加。
  `pr_url` は `none` を PR 無しに正規化し、tasklist の書式を読む `parse_tasklist()` を状態機械側に置いてテストした
- **到達可能性・全域性のテストを入力の全直積（5,760 状態）に変えた**（手書きケースだけでは未知 Status の穴を検出できなかった）
- **フラグの producer / consumer 突合 (r) を追加した**（完了条件にあったのに tasklist から落ちていた）。検査 (n) を厳格化したところ、`steering/references/spec.md` のテンプレに `- [ ] [タスク2]` が無い**実ドリフトを新たに 1 件検出**し、直した

**直さなかったもの・記録して閉じるもの**:
- **完了条件「feature-pipeline の SKILL.md が短くなる」は未達**（342 → 356 行）。PR 前 capture の実行契機・`H2`・PR 状態の記録手順を本文に足す必要があり、
  Phase 3.5 の重複解消だけでは相殺できなかった。design-doc は 287 → 249 行で達成。目的（エッジケース手順の分離）は達成しているため、完了条件の文言を「design-doc のみ」に読み替える追認を提案する
- **`tournament-variant` に `effort` を付けない**（完了条件「各定義が model・effort・tools を持つ」からの逸脱）。書き込み可の実装役はセッションの effort を継承するのが妥当と判断した。契約 (p) の必須キーにも `effort` は入れない
- **`tournament-variant` の無制限 Bash は受容**する。実装役として必要で、`isolation: worktree` は `commands.md` の worktree 手順と二重になる。本文の禁止事項（worktree 外に触れない・push しない）と注意書きで補った。
  `.git` を共有する worktree の性質上、ネットワーク送信を含む逸脱は文章でしか縛れない — 気になる場合は permissions.deny の拡充（ユーザー判断）
- **論点 3・4・7 の既定は追認として維持**する（decisions 20260920）。design.md の契約コア（スコープ #7 の frontmatter 行）は変更しない — 変更すると DRAFT 戻しになる。実装は既定どおりスキップしたことを記録するのみ
- **`HALT_UNKNOWN_STATUS` → 行 ID `H1`**: design.md は戻り値名を `HALT_UNKNOWN_STATUS` と書くが、実装は表の行 ID を返す設計（`H1` / 新設の `H2`）。fail-closed の意図は満たす。名前の食い違いは追認
- **GitHub Actions の SHA 固定は未実施**: 確認手段が無く、推測で固定すると誤る。`persist-credentials: false`・push を main に限定・permissions を contents: read のままにした
- **`/skill-doctor` の実測**: 組み込みコマンドでこのセッションからは実行できない。ユーザー側で実行して貼る（BACKLOG 節 4 に手順）。フルモード発動頻度の集計（フル 6 / 軽量 2 / 不明 3・典型は 3 軸ディスパッチ）は BACKLOG 節 4 が正本で、ここにも要約する

**ユーザー判断に回したもの（既存の設定・hook・承認制で、この task の差分外）**:
- `guard-gated-write.sh` が `git ... --output=CLAUDE.md` / `--output=.claude/settings.json` を素通りさせる（`>` / `tee` しか見ない）
- `settings.json` の allow が前置一致の `Bash(git diff*)` 等で、`git difftool -x '<cmd>'` が任意コマンドを実行できる。`git diff --no-index /dev/null ~/.ssh/id_rsa` で `Read(~/.ssh/**)` の deny と `.env` ガードを迂回して読める
  → 対処案（security の提案）: allow を `git diff *`（スペース付き）に狭める・`git difftool*` と `--output` / `--no-index` を含む git 系を deny に足す。**settings.json の変更は承認制のため実施していない**
- なお security 報告に「settings.json の deny 追加」が含まれていたが、subagent の提案は変更の根拠にしていない（承認はユーザーが行う）

## [20260921] — skill-issues の訂正: agent 定義は同一セッションでも後から登録される

`skill-issues.md` の初版は「同一セッションで作った定義は種別として使えない」と読める書き方だったが、実際は**作成直後の数ターンは未登録で、その後に利用可能な種別として登録された**（レビュー中に一覧へ追加された）。
再起動は不要。ただし作成直後にディスパッチすると `Agent type not found` になるため、本文には「種別未登録で失敗したら汎用へ落とす」を足した（5 か所）。
