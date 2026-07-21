# Design: ADR 出力を master-only スキルに切り出す

Status: **APPROVED**
Date: 20260721
Approved: 20260721

## Goal

ADR の起票・維持を master-only スキル `adr` として独立させ、配布可スキル
`knowledge-capture` から ADR の語彙・形式・書き込みを取り除く。

理由は 2 つ。第一に **ADR の意味は配置先で変わる** — このリポジトリの ADR は読者が
起票者本人のみでリポジトリ内に閉じるが、会社プロジェクトでは他人が読み、既存の公式な
決定記録と競合する。批准プロセスを持つ組織で単独生成された ADR ファイルは、
誰もレビューしない個人メモが決定記録のコスプレをする「影の決定ログ」になる。
この非対称性がスキルの配布分類を分ける。第二に **このリポジトリの ADR 群には
判例集としての維持コストがある** — 7 本・週 1 ペースで増え、rule-audit の剪定対象外と
決めた以上、Superseded / Amended の印付け・近縁検出という運用が必要になる。これは
「知見をドキュメントに振り分ける」責務とは別物で、knowledge-capture が片手間で持つには重い。

あわせて glossary 分岐を全削除する。根拠は、独自語（エンジン/カートリッジ・素通り検査・
ハードストップ）が既に `docs/knowledge/skill-design-patterns.md` の節見出しとして定義され
機能しており、切り出すと孤立 subagent が 2 ファイル読む必要が出て悪化するため。
2026-07-03 の rule-audit で実ファイルが削除されて以降 18 日間再作成されなかった事実は
補強に留める（不使用の証拠としては弱い — 発火機会が無かった可能性を排除できない）。

## Scope



### In scope

- 新規 master-only スキル `adr`
  - 起票判定・Nygard 起票・Superseded/Amended 運用・近縁 ADR 検出
  - description に When NOT to use を持つ（既存 ADR の閲覧・decisions.md への記録では発動しない）
  - 書き込み前のハードストップ
- `knowledge-capture` から ADR の語彙・形式・書き込みを完全に削除し、検知時は
`.steering/[task]/decisions.md` への記録 + 「チームの決定記録に上げるか検討してください」の示唆に置き換え
- `knowledge-capture` / `compound` から glossary（語彙）分岐を削除
- ADR の帰属が変わることによる同義箇所の追随。**配布可スキルには** `adr` **の名を書かず、
帰属の記述ごと削除する**（Constraints の「配布可スキルから `adr` を参照しない」を守るため）
- 実装前に `ADR` / `docs/decisions` / `knowledge-capture` の 3 語で全文 grep し、
Key components 表を確定させる（下表は暫定）



### Out of scope

- **既存 7 本の ADR への Superseded 印の遡及適用**（`adr` は機能として持つが、
本タスクでは既存 ADR 本文を書き換えない）
- 蓄積 ADR 群の全件整合監査モード（rule-audit の鮮度シグナルと責務が重なる）
- `export/company` **ブランチへの反映**。持ち出しセットは main には存在せず、
`export/company` ブランチ（worktree `../skills-export-company`）にのみ存在する
**独立フォーク**（`b08ab67`）。会社→マスターの還流経路はセキュリティ制約で存在しないため
skill-harvest は使えない。反映が要る場合は MANIFEST の手順
（`git diff <source-commit> -- .claude/skills/<name>` で差分確認 → Angular 変換を再適用して
再エクスポート、`modified` 付きは手動マージ）に従って**別タスクで判断する**。
その間、会社側には旧仕様の knowledge-capture（ADR 語彙・Nygard 形式・書き込み手順）が残る



## Constraints

- スキル本文は孤立した subagent が単体で読む前提で書く（暗黙のコンテキストを置かない）
- `adr` は master-only。**配布可スキルの本文に** `adr` **というスキル名を出現させない**
（存在確認の条件分岐も置かない）。配置先には存在しないスキルを指す死んだ参照になるため
- 新規スキルは `templates/SKILL.template.md` から書き始める
- 本文（frontmatter 除く）にツール固有 API を書かない（エンジン純度）
- `docs/knowledge/skill-design-patterns.md` の「片側修正の禁止」により、ADR の帰属を
変える以上、同義箇所を全て同一コミットで直す



## Acceptance criteria

- [ ] `.claude/skills/adr/SKILL.md` が存在し、`validate_skills.py` を PASS する
- [ ] `adr` は書き込み前のハードストップ（ドラフト提示 → 明示承認）を手順の Step として持つ
- [ ] `knowledge-capture/SKILL.md` に `ADR` `Nygard` `docs/decisions` が **0 件**（frontmatter 含む）
- [ ] `knowledge-capture/SKILL.md` に「ADR 形式のドラフトを提示しない」旨の明示的な禁止句が手順のステップとして存在する（振る舞いの静的プロキシ。実測は Open questions 4 参照）
- [ ] `compound/SKILL.md` `rule-audit/SKILL.md` `session-retrospective/SKILL.md` `feature-pipeline/SKILL.md` `steering/references/spec.md` に `adr` というスキル名が 0 件（配布可スキルのため）
- [ ] `knowledge-capture/SKILL.md` と `compound/SKILL.md` に `glossary` `語彙` が 0 件（`語彙` はリポジトリ全体では「ツール語彙」「承認語彙」など別義で多数使われるため、検査対象をこの 2 ファイルに限定する）
- [ ] `README.md` / `docs/starter-kit.md` / `CLAUDE.md` に `adr` の記載があり master-only として分類されている
- [ ] `adr` が `skill-deploy` の配布対象に含まれないことを確認済み。除外リストの実体が無い場合は `docs/starter-kit.md` に手動除外の注記がある（未確認のまま本タスクを閉じない）
- [ ] `validate_skills.py` が全スキルで PASS（回帰）



## Approach

**判断エンジンは分割しない、形式と出力を分ける。** 「代替案を却下した決定は記録に値する」
という判断は配置先でも真なので、knowledge-capture は検知能力を保持する。しかし**形式は与えない**
— ADR という語彙も Nygard の節構成も配布版には置かず、決定・理由・却下案を
`.steering/[task]/decisions.md` に記録し、「チームの決定記録に上げるか検討してください」と
添えて終わる。独自の決定記録様式を持つ会社に Nygard 形式の草案を差し出すのは形式の押し付けであり、
「単独生成された ADR 形の成果物」をファイルではなくテキストで再生産することになる。
形式を知っているのは `adr` スキルだけにする。

`adr` は knowledge-capture から委譲されない。ユーザーが decisions.md を見て「adr で起票して」と
呼ぶ。**配布可スキル（knowledge-capture / compound / rule-audit / session-retrospective）の
本文に** `adr` **の名を書かない**ため、境界の相互明記が不要になり、片側修正のリスクが増えない。
配布可スキル側は ADR の帰属を書く代わりに、帰属の記述ごと削除する。

**近縁 ADR 検出の範囲**: 入力は `docs/decisions/` の**ファイル名一覧と各ファイルの見出し行
（**`# Decision:` **行）のみ**。本文全文は読まない。ヒット時は候補を提示して止まり、
Superseded にするかは人が決める。全文読みを避けることで、Out of scope にした全件整合監査と
実装基盤が重複せず、本数が増えてもコンテキストが破綻しない。

**起票条件は「却下した代替案があるか」**に統一する。既存 7 本の実態がそうであり、
Alternatives considered が埋まらない = ADR にしない、で自己判定できる。

## Key components

暫定。実装前の全文 grep で確定させる。


| ファイル                                            | 配布分類            | 変更後の記述                                                                                                                                                                                                                          |
| ----------------------------------------------- | --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `.claude/skills/adr/SKILL.md`                   | **master-only** | 新規。起票判定 / 近縁検出 / Nygard 起票 / Superseded・Amended / 書き込み前ハードストップ                                                                                                                                                                  |
| `.claude/skills/knowledge-capture/SKILL.md`     | 配布可             | ADR 節・Superseded 段落・glossary 節を削除。決定木は「却下した代替案がある → decisions.md に記録し、チームの決定記録に上げるか検討を促す」                                                                                                                                       |
| `.claude/skills/compound/SKILL.md`              | 配布可             | **4 箇所**（:17 When NOT to use / :21 境界 / :64 昇格候補 4 / :228 Related skills）から「ADR・語彙」を削除。`adr` の名は書かない                                                                                                                            |
| `.claude/skills/rule-audit/SKILL.md`            | 配布可             | **2 箇所**: :19「ドキュメント（ADR・パターン集）→ knowledge-capture」から ADR を削除 / :60 を「決定の変更は Superseded / Amended 印で扱う」で止め「knowledge-capture の担当」を削除                                                                                            |
| `.claude/skills/session-retrospective/SKILL.md` | 配布可             | :16 から `docs/decisions/` を削除（「`docs/knowledge/`・CLAUDE.md への保存 → knowledge-capture」に）                                                                                                                                           |
| `.claude/skills/feature-pipeline/SKILL.md`      | 配布可             | :240 の知見保存フェーズから `docs/decisions/` を削除                                                                                                                                                                                          |
| `.claude/skills/steering/references/spec.md`    | 配布可             | :143「ADR（`docs/decisions/`）にする前の中間記録」から ADR 参照を削除（references も配布されるため対象）                                                                                                                                                        |
| `CLAUDE.md`                                     | —               | 「ナレッジ保存先のルール」表の ADR 行を `adr` スキル経由と明記                                                                                                                                                                                           |
| `README.md`                                     | —               | **必須 3 箇所**（ADR / glossary を含む）: :46 ディレクトリツリー / :158 knowledge-capture 説明 / :177 データフロー図。加えてスキル一覧に `adr` を追加。**判断**: :73 / :92 のワークフロー図に `adr` を足すかは要検討（`adr` は随時起動でメインワークフローの一部ではないため、推奨は足さない。足す場合は feature-pipeline と同一コミット） |
| `docs/user-guide.md`                            | —               | :43 のスキル分類。`knowledge-capture` の説明を更新し、`adr` を**手動起動**側に追加（自動発動・パイプライン内部ではない）                                                                                                                                                   |
| `docs/starter-kit.md`                           | —               | :31 master-only 行に `adr` を追加。:4 / :15 の ADR 参照は ADR そのものを指すため変更不要                                                                                                                                                               |
| `scripts/deploy_skills.py`                      | master 専用ツール    | :45 `MASTER_ONLY` に `"adr"` を追加（:216 で配置を機械的に拒否する実体）                                                                                                                                                                            |
| `.claude/skills/skill-deploy/SKILL.md`          | **master-only** | :51 の master-only 列挙に `adr` を追加（`deploy_skills.py:6` の「同一コミットで改訂する」規律により上と同一コミット）                                                                                                                                             |

## Research

### 配布除外リストの実体（20260721・Open questions 5 の解決）

- `scripts/deploy_skills.py:45` に `MASTER_ONLY = {"skill-test", "skill-harvest", "skill-deploy"}` があり、
  :216 で配置対象に含まれていたら実行時に拒否する。**実体あり**
- 同じリストが `.claude/skills/skill-deploy/SKILL.md:51` にも本文として存在する
- `deploy_skills.py:6` に「同一コミットで改訂する（片側修正の禁止）」と明記されているため、両方を同時に直す
- 結論: `docs/starter-kit.md` への手動除外注記は不要。`MASTER_ONLY` に `adr` を足せば機械的に防がれる

### 既存パターン（本セッションで実測済み・code-explorer 不使用）

- master-only スキルの書式: description 冒頭に「マスター専用スキル」、H1 見出しに「（マスター専用）」
  （`skill-harvest` / `skill-test` に共通）
- 新規スキルは `templates/SKILL.template.md` から書き始める。テンプレは前提チェック・ハードストップの
  雛形を HTML コメントとして持つ（埋めたら削除する）
- `validate_skills.py` は 7 項目を検査。承認語彙があってハードストップが無いと FAIL する




## Data flow

```
[共通] 決定が発生
  → knowledge-capture が .steering/[task]/decisions.md に記録（決定・理由・却下案）
  → .steering/ のタスクディレクトリが無い場合は会話で提示して終わる（ファイルを作らない）
  → 却下した代替案があれば「チームの決定記録に上げるか検討してください」と添えて終わる
  → ここまで master でも配置先でも同一。ADR 形式は登場しない

[master のみ] 人が decisions.md を見て判断
  → 「adr で起票して」→ adr が近縁 ADR を検出（ファイル名 + 見出し行のみ）
  → ドラフト提示 → 明示承認 → docs/decisions/ に Nygard 形式で書き込み
  → decisions.md の該当項目に ADR へのリンク行を追記する
     （二重化した情報源のうち、どちらが現行かを後から読む者が判別できるようにする）
  → 既存決定を置き換える場合は旧 ADR に Superseded 印 + 相互リンク

[配置先のみ] 人がチームの決定記録（社内様式 / Confluence 等）に起票するか判断
  → スキルは形式を与えず、ファイルも書かない
```



## Test strategy

- **静的**: `scripts/validate_skills.py` を全スキルに実行（回帰）。`adr` は承認語彙を含むため
停止契約検査（承認語彙 → ハードストップ）にかかる。ハードストップが手順として存在しないと FAIL する
- **純度**: `validate_skills.py --purity` で `adr` 本文のツール語彙出現数を確認（目標ほぼゼロ）
- **grep 回帰**: Acceptance criteria に列挙した「ファイル指定 + 語 + 期待件数」の形で機械判定する。
`語彙` のようなリポジトリ全体で多義な語は、対象ファイルを限定してから数える
- **素通り検査（任意・課金）**: Open questions 4 で人間が判断する



## Open questions

1. **起票条件の緩さ** — 「却下した代替案があるか」は、design-doc が Alternatives considered を
  標準セクションに持つため、design-doc を通ったタスクがほぼ全て該当する（この design.md 自身も
   7 件持つ）。維持コスト削減という Goal と逆行しないか。
   **反論**: `adr` は人手トリガーのみで自動起票されないため、実際の起票量は人間のゲートが決める。
   条件は「呼んだときの妥当性チェック」として機能すれば足りる。
   **判断が要る**: この反論を採るか、第二の軸（「却下が後続の前提になる決定に限る」等）を足すか
2. `adr` **が呼ばれなくなるリスク** — 人手トリガーのみにした結果、3 ヶ月後に
  「起票実績ゼロ = 不要」と判断されうる（glossary を削除したのと同じ論法）。
   呼ばれないのは設計の帰結であって需要の不在ではないが、区別できない。再評価基準をどう置くか
3. ~~**Superseded 済み ADR を近縁検出の対象に含めるか**~~ → **解決済み（20260721）: 含める**。
  除くと置き換え済みの決定を再提案しても検出されない穴が開く。候補提示時に
  「Superseded 済み」と明示すれば「なぜ古い決定を読むのか」にも答えられる（adr Step 2 に反映済み）
4. ~~**「ADR 形式のドラフトを生成しない」の実測**~~ → **解決済み（20260721）: 静的で締める**。
  禁止句を明示ステップ化し grep で 3 件確認済み。素通り検査は課金が発生するため、
  実際に定型フォーマットを生成する事象が観測されてから回す（「自動化は摩擦が実証されてから」
  と同じ判断）。**再検討トリガー**: knowledge-capture が決定記録の定型フォーマットを
  生成したのを一度でも観測したら、`tests/passthrough_check.py` にシナリオを追加する
5. ~~**次回配布時の除外**~~ → **解決済み（20260721）**。除外リストの実体は
  `scripts/deploy_skills.py:45` の `MASTER_ONLY` と `skill-deploy/SKILL.md:51` の 2 箇所。
  両方に `adr` を追加する（Research 参照）。starter-kit への手動注記は不要
6. **本タスク自体の ADR 化** — 「ADR を master-only に切り出す」判断は却下した代替案を 6 件持つため
  新起票条件を満たす。これは**新しい起票条件の初の実地検証**でもあるため、実装後ではなく
   **承認時に「この design は起票に値するか」を判断する**方が安い。値しないなら条件が緩すぎる証拠になる

（解決済み: 配布版のドラフト形式 → 形式を一切与えないことに決定。Alternatives considered 参照）

## Alternatives considered


| Alternative                                                                  | Reason rejected                                                                                                                                         |
| ---------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 出力先をカートリッジ化する（配置先の既存 ADR 方式を検出して出力先を切り替える）                                   | 問題は置き場所ではなく**権限**。批准プロセスを持たないチームでは、どこに置いても単独生成された ADR は決定記録のコスプレになる。検出ロジックを足しても本質が解決しない                                                                 |
| knowledge-capture に ADR 枝を残し「配布版はドラフトのみ」の 1 分岐にする                            | 本文 245 行中 40 行強が ADR 専用で、master 側には Superseded / 近縁検出という成長余地がある。判例集の維持は「知見を振り分ける」責務と別物。また分岐は孤立 subagent の誤読余地を残す                                        |
| `adr` も配布可にする                                                                | ADR は一人で決める成果物ではない。批准プロセスを持たない配置先で単独生成すると無用なドキュメントが増える（ユーザー指摘）                                                                                          |
| 配布版が Nygard 全節（または簡易 4 項目）の ADR ドラフトを提示する                                    | 配布版の本文に ADR 形式の定義が残り、master-only になるのが「ファイル書き込み」だけになる（分割が半分で終わる）。また独自の決定記録様式を持つ会社に Nygard 形式を差し出すのは形式の押し付けで、「単独生成された ADR 形の成果物」をテキストで再生産することになる（ユーザー指摘） |
| 配布可スキル（compound / rule-audit / session-retrospective）に ADR の帰属先として `adr` を書く | 配置先には存在しないスキル名を指す死んだ参照になる。Constraints 違反（Premortem で検出・本文修正済み）                                                                                          |
| glossary の起票条件を書いて残す（「同じ概念に 2 つ以上の呼び名が観測されたとき」）                              | 個人開発では発火しない。独自語は既に `skill-design-patterns.md` の節見出しが定義として機能しており、切り出すと subagent が 2 ファイル読む必要が出て悪化する                                                      |
| ADR 起票条件を現行維持（「一回限りの設計・アーキテクチャ判断」）                                           | 発火条件が主観的。ただし新条件も緩いという指摘があり Open questions 1 で未決着                                                                                                        |




## Premortem

design-premortem をフレッシュな subagent で実行（design.md のみを渡し、リポジトリ探索を禁止）。

### 反映済み（設計本文を修正）: 11 件

- 攻撃: Constraints「配布可スキルから `adr` を参照しない」と Key components「session-retrospective の
帰属を `adr` に変更」が直接矛盾する。session-retrospective / compound / rule-audit はいずれも配布可。
影響: 配置先で存在しないスキル名を指す死んだ参照になり、「境界の相互明記が不要」という
設計最大の利点が実装時に崩れる。崩れたことに気づくのは配置先で誤読が起きたとき。
提案 → **反映**: Key components に配布分類の列を追加し、配布可スキルは「`adr` に変更」ではなく
「帰属の記述ごと削除」に変更。Constraints・Approach・Acceptance criteria にも明記。
**この 1 件だけで実装前に止める価値があった**
- 攻撃: `.steering/` が無い配置先での出口が未定義。「振る舞いは完全に同一」という主張が破れる。
影響: 分岐を消すために ADR を切り出したのに、分岐が別の場所に移動する。
提案 → **反映**: Data flow に「タスクディレクトリが無ければ会話で提示して終わる」を明記。
反論として、この分岐は出力先の有無であって ADR 形式の有無ではないため性質が異なる旨も本文に含めた
- 攻撃: In scope の Superseded 運用と Out of scope「既存 7 本の書き換え」が矛盾する。
提案 → **反映**: Out of scope を「遡及適用しない（機能としては持つ）」に限定して書き直し
- 攻撃: 近縁検出の入力・判定単位が未定義で、実装時に「全件 Read して主観判定」に落ちる。
30 本でコンテキストが破綻し、静かに検出漏れする。
提案 → **反映**: Approach に「ファイル名 + 見出し行のみ。本文全文は読まない」を確定として記載
- 攻撃: `adr` の description / When NOT to use が未定義で誤発動しうる。
提案 → **反映**: In scope と Key components に明記
- 攻撃: decisions.md と docs/decisions/ の二重化。起票後の decisions.md の扱いが無い。
配置先の影の決定ログを防ぐ設計が、master 内部に影の決定ログを作る。
提案 → **反映**: Data flow に「decisions.md に ADR へのリンク行を追記」を追加
- 攻撃: `skill-deploy` の除外リスト未確認を Open のまま閉じられる。実体が無ければ `adr` が
配置先にコピーされ、この設計が防ごうとした事故そのものが起きる。
提案 → **反映**: Acceptance criteria に昇格（未確認のまま閉じない）
- 攻撃: `語彙` は多義語（ツール語彙・承認語彙）でリポジトリ全体 grep は機械判定にならない。
提案 → **反映**: 検査対象を knowledge-capture / compound の 2 ファイルに限定
- 攻撃: 「帰属先が knowledge-capture のままの箇所がゼロ」は人間の読解で PASS/FAIL が出せない。
提案 → **反映**: Acceptance criteria を「ファイル指定 + 語 + 期待件数」に分解
- 攻撃: Goal の第一理由「ADR は一人で決める成果物ではない」がこのリポジトリ自身
（個人開発・main 直コミット・批准プロセス無し）にも当てはまり、論理が自壊する。
影響: 3 ヶ月後に根拠を再構成できず、`adr` を残すか消すかの判断ができない。
提案 → **反映**: 第一理由を「配置先では ADR の意味が変わる（他人が読む・公式記録と競合する）」
という非対称性の説明に書き直した
- 攻撃: glossary 削除の根拠「18 日間再作成されなかった」は不使用の証拠として弱く、
「N 日発火しなかったから削除」が前例になると季節性のある機能が順次削られる。
提案 → **反映**: Goal の根拠を「節見出しが定義として機能している」に差し替え、18 日は補強に降格



### 人間の判断に委ねる: 4 件

Open questions 1〜4 に転記済み（起票条件の緩さ / `adr` が呼ばれなくなるリスク /
Superseded を近縁検出に含めるか / 中核主張を実測するか静的で締めるか）。

なお Open questions 1 と 2 は**互いに逆方向のリスク**を指している（条件が緩く起票が増える vs
人手トリガーのみで起票されなくなる）。両方が同時に最大化することはないため、
どちらを警戒するかは運用開始後の実績で決めるという選択肢もある。

### 反論（本文を変えない）: 1 件

- 攻撃: `validate_skills.py --purity` の存在が未確認のまま断定形で書かれている。
**反論**: `README.md`:197 に「`--purity` でツール純度レポート」と記載があり実在する。
subagent はリポジトリ探索を禁止されていたため確認できなかった。本文は変更しない



### 前提が誤っていた所見: 1 件

- 攻撃: 「`export/` を Out of scope にすると、既存配置先に旧仕様が残り、次回 skill-harvest まで
実害が残る。harvest がいつ行われるかは未定」
**実態**（ユーザー指摘 → git で確認）: 持ち出しセットは main には存在せず `export/company`
ブランチの独立フォークで、**還流経路そのものが無い**（`b08 Pre-implementationab67`・セキュリティ制約）。
skill-harvest は使えないため、攻撃の前提（harvest による回収）が成立しない。
→ Out of scope の記述を MANIFEST の再エクスポート手順に基づくものへ全面的に書き直した。
なお design.md がパス名を旧名 `export/20260714-company/`（同日 `e037440` で `export/company` に
リネーム済み）で書いていたことも、この過程で判明して修正した



### 付随所見（自己完結性）

design.md 単体では各対象スキルの配布分類が判断できず、それが最重要指摘の直接原因だった。
Key components 表に「変更後の記述」列を足したことで、レビュアーが原本を開かずに矛盾を検出できる。

（このスキルは設計を承認しない。design-doc の Phase 3 STOP に戻る）