# レビュー結果: skillset-hardening

Date: 20261031
Status: OPEN
範囲: HEAD（5b2e993）との未コミット差分（内容変更 18 ファイル。filemode のみの変更約 140 件は除外）+ 未追跡 4 ファイル
モード: フル（impl / correctness / security の 3 体をフレッシュエージェントで並列実行）

> **design 同期が先（OPEN のままマージ前提にしない）** — impl-review Axis 1 に設計契約コア不一致（High）が 3 件ある。

## 実施状況

- フレッシュエージェント 3 体が完走した（前回 20260725 は 3 体とも中断して自己レビューで代替していた → 今回でその暫定状態は解消）
- 対象なし: test-agent（`.test.ts` / `.spec.ts` なし）/ perf-agent / a11y-agent / ui-agent（`.ts` / `.tsx` / `.css` なし）
- `.claude/agents/` が無いため、汎用エージェントにテンプレートを渡してディスパッチした。読み取り専用はプロンプトでの指示のみ
- export worktree（`/Users/...`）はサンドボックスの読み取り禁止範囲にあり、未レビュー
- `pnpm audit` はネットワーク遮断（403）で未実行

## 実装（impl-review）

| Axis | 指摘 | ファイル | 重要度 | 再現 | 修正状況 |
|------|------|----------|--------|------|----------|
| 設計整合性 | 課金承認ゲートの見積が「シナリオ数 × 2 回／× 2 run」のままで、:50 が指示する `--runs 4` の半額を提示する。design.md:133「コスト見積の文言も倍に直す」が未実施なのに tasklist では完了扱い | `.claude/skills/skill-test/SKILL.md:36,39` | High（設計契約コア） | 再現済み（grep） | [ ] |
| 設計整合性 | `stop_lines()` は停止語彙を含む行しか抜き出さず、design.md が約束する「見出しとその文脈」を比べていない。`STOP_VOCAB` に「止まって」「応答を待つ」「書き込みに入らない」等が無い。correctness も同じ指摘（統合） | `scripts/check_export_stopcontract.py:39-51,94-100` | High（設計契約コア） | 再現済み: design-doc:11,145 と adr:117 を削除した export が「差分なし: 2 スキル」で exit 0 | [ ] |
| 設計整合性 | 比較件数が 0 でも「停止契約は master と実質同一」と出して exit 0（偽グリーン防止の穴）。`--master` の指定ミスや同一パス指定でも同様。correctness も同じ指摘（統合） | `scripts/check_export_stopcontract.py:230-235,246-276` | High（設計契約コア） | 再現済み: `--export .claude/skills --master .claude` → 0/0/0 で「実質同一」、exit 0 | [ ] |
| 設計整合性 | design.md の表に無い変更（settings.json の ask 14 行、starter-kit、adr / debug のターン境界、session-retrospective の Step 再構成）が入っているのに design.md が未更新。tasklist Step 0 に反する。tasklist の「B 案」も decisions.md に記録が無い | `design.md:95-139`、`tasklist.md:14,35` | Medium | 推論（文書の突き合わせ） | [ ] |
| 設計整合性 | 未解決の論点 4（除外分類の永続化先）。decisions.md:84 で「既知差分として登録する」と決めたが、スクリプトに登録の仕組みが無く、無害差分 7 件が毎回出続ける | `design.md:220-221`、`decisions.md:84` | Medium | 推論 | [ ] |
| プロジェクト規約 | 片側だけの修正。starter-kit 手順 6 に `docs/decisions/` の ask と 3 形式での列挙が無い（adr を配置しても機械防御が配られない）。security も同じ指摘（統合） | `docs/starter-kit.md:88-89` | Medium | 再現済み（grep） | [ ] |
| プロジェクト規約 | 停止契約を変えた adr / debug / session-retrospective / skill-test / steering で `metadata.version` が据え置き | 各 `SKILL.md:5` | Low | — | [ ] |
| コード品質 | `read_body()` の戻り値注釈 `list[str]` が実体（`(行番号, 行)` のタプル）と合わない（3 体が指摘・統合） | `scripts/check_export_stopcontract.py:81` | Low | — | [ ] |
| コード品質 | プレースホルダの無い f-string（F541）（3 体が指摘・統合） | `scripts/check_export_stopcontract.py:212` | Low | — | [ ] |
| コード品質 | コメントの「既存 5 経路」が tasklist:92 の「6 経路」と合わない | `scripts/validate_skills.py:189` | Low | — | [ ] |
| プロジェクト規約 | README が 3 形式列挙の根拠として claude-code-config.md を引いているが、引用先の規則はファイル名の前後の話でディレクトリの深さの話ではない | `README.md:216` | Info | — | — |
| シナリオ | `--runs 4` はコメントにあるだけで強制されていない | `tests/passthrough/{adr,debug,impl-from-design}/scenario.md` | Info | — | — |
| シナリオ | 症状記述「￥-∞ 〜 ￥∞」が実際の挙動（min=Infinity / max=-Infinity）と逆。判定には影響しない | `tests/passthrough/debug/scenario.md:101-102` | Info | — | — |

## 正当性（review-correctness）

| Axis | 指摘 | ファイル | 重要度 | 再現 | 修正状況 |
|------|------|----------|--------|------|----------|
| 終了コード / 握りつぶし | SKILL.md が無いスキルディレクトリ（SKIP）がドリフト件数にも分母にも入らず、「1/1 ドリフトなし」で exit 0 になる（今回の差分より前からある問題） | `scripts/check_deploy_drift.py:167-171,199-201` | Medium | 再現済み: `skills/foo/` だけの配置先で「SKIP foo」「1/1 ドリフトなし」、exit 0 | [ ] |
| 境界条件 | `read_body` の frontmatter 正規表現が `\n` 固定で、CRLF では frontmatter が除去されない（他 2 本も同じ形） | `scripts/check_export_stopcontract.py:88` | Low | — | [ ] |
| 境界条件 | `normalize` が非同梱スキル名を境界なしの部分文字列で消す（`debugger` → `ger`）。修正済みの `PR` 問題と同じ型（impl も指摘・統合） | `scripts/check_export_stopcontract.py:107-108` | Low | — | [ ] |
| 境界条件 | `target=""` のとき黙ってレジストリモードに入る。`is not None` で判定すべき | `scripts/check_deploy_drift.py:235` | Low | エージェントが実行して確認 | [ ] |
| 境界条件 | `--help` が先頭引数のときしか効かず、未知フラグは Traceback になる（security も指摘・統合） | `scripts/validate_skills.py:190-214,266-269` | Low | — | [ ] |
| 状態 | worktree 側の `scripts/` から実行すると、`--master` の既定値が古い master を指す | `scripts/check_export_stopcontract.py:37,189-192` | Low | — | [ ] |
| 終了コード | 読み込み例外が exit 1 になり、check_deploy_drift の「ドリフトあり」と区別できない | `check_export_stopcontract.py:87` / `check_deploy_drift.py:52-57,77` | Low | — | [ ] |
| — | ask の `*` / `**` / `**/*` の 3 重指定は冗長（ただし実効性の確認が済むまでは残してよい） | `.claude/settings.json:21-34` | Info | — | — |

## セキュリティ（review-security）

| Axis | 指摘 | ファイル | 重要度 | 再現 | 修正状況 |
|------|------|----------|--------|------|----------|
| 権限 | allow の `Bash(git diff*)` / `git log*` / `git show*` に `--output=<file>` を付けると、確認なしで任意の内容を書ける。今回足した CLAUDE.md・docs/knowledge・docs/decisions の ask（Edit/Write にしか効かない）を迂回できる。allow 自体は既存の設定 | `.claude/settings.json:7-9` | High | 一部再現: git の機能としては `git log -1 --format='format:probe' --output=$TMPDIR/probe.txt` で任意の内容を書けることを確認。**確認プロンプトなしで通るかは未検証**（推論） | [ ] |
| 権限 | `Bash(git diff*)` は空白なしの前方一致なので `git difftool` にもマッチし、`-x <cmd>` で任意コマンドを実行できる | `.claude/settings.json:7` | High | 一部再現: git 2.53.0 に `-x, --extcmd` があることを確認。**allow へのマッチは未検証**（推論） | [ ] |
| 権限 | ask は Edit/Write にしか効かず、Bash からの書き込み（tee / sed -i / リダイレクト）は対象外。受け入れモードや allow を広げたときに無防備になる | `.claude/settings.json:21-34` | Medium | 推論 | [ ] |
| 権限 | `./` パスがセッションのカレントからの相対パスとして解釈されると、サブディレクトリで起動したセッションで ask が効かない | `.claude/settings.json:21-34` | Medium（要確認） | 推論・公式ドキュメントで要確認 | [ ] |
| 権限 | README が「docs/ への書き込みは承認制」に機械的な裏づけを与えたと書いているが、実際の対象は knowledge / decisions だけで言い過ぎ | `README.md:216` | Low | — | [ ] |
| 権限 | hook が呼ぶ `scripts/` は ask で守られておらず、hook を経由した間接的な自己改変が通る | `.claude/hooks/validate-skill-edit.sh:28-36` | Low | — | [ ] |
| 権限 | サブエージェントの読み取り専用は `.claude/agents/` が無いとプロンプトの指示だけになる | `.claude/skills/frontend-code-review/SKILL.md:100-118` | Low | — | [ ] |
| env | ルートの未追跡 `gitshow-write-test.txt`（別リポジトリの `git show` 全文。作者名とメールアドレスを含む）と `gitdiff-write-test.txt`（空）。.gitignore の対象外なので `git add -A` で混入する。`--output` 書き込みを試した残骸と見られるが、どこにも記録が無い | ルート | Low | — | [ ] |
| env | 新規の steering 文書にユーザー名を含む絶対パスがある（.gitignore:13-14 の方針と食い違う） | `blockers.md:8`、`design.md:46` | Low | — | [ ] |
| — | skill-test の worktree 側 `scripts/` を実行する前に `git diff main -- scripts/` で確認する一文を足すとよい / source-commit を git に渡すときに `--end-of-options` を付けると堅牢 / passthrough の `### file:` に入る `../` を止めていない（既存） / `pnpm audit` 未実行 | 各所 | Info | — | — |

## テスト / パフォーマンス / アクセシビリティ / UI

対象なし（該当する拡張子のファイルが diff に無い）。

## 前回（20260725）の指摘の扱い

- [x] [High] ask の glob が 1 形式のみ — DONE（3 形式の列挙を今回のレビューでも確認）。**実際に確認プロンプトが出るかは依然として人が確かめる必要がある**
- [x] [Medium] `normalize()` の `PR` 置換が `APPROVED` を壊す — DONE（`GENERALIZE_RE` を確認。同じ型の問題が非同梱スキル名に残っている → 正当性の Low）
- [x] [Medium] レビューが完遂していない — DONE（20261031 にフレッシュエージェント 3 体で再レビューした）
- [x] [Low] passthrough シナリオ 3 本がどのレビューにも回っていない — DONE（今回は impl-agent の Axis 4 で確認）。ただし担当が正式に決まっていない点は残る
- [ ] [Info] `.steering/` 配下はレビュー対象外 — 継続

## 全体サマリー

- 合計の重要な問題（Medium 以上）: **11 件**（High 5 / Medium 6）
  - 実装: High 3 / Medium 3 ・ 正当性: Medium 1 ・ セキュリティ: High 2 / Medium 2
- Low: 15 件 / Info: 9 件
- 重複統合: 9 件
- 誤検知（再現せず）: 0 件
- モード: フル

