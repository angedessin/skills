# レビュー結果: report-driven-improvements

Date: 20260921
Status: DEFERRED

モード: フル（ロジック扱い: `scripts/*.py`）。ディスパッチ: impl / correctness / security（ユーザー承認済みの 3 軸）。test / a11y / ui / perf は対象なし。
実行方法: `.claude/agents/review-*` 定義は同一セッションで作成したため初回は種別未登録（`Agent type not found`）。本文の 2 段フォールバックで汎用エージェントにサブスキルを読ませて実行した（モデル・エフォート・読み取り専用の権限指定は効いていない。読み取り専用は依頼文で指示）。
**設計整合 High あり — design 同期が先（OPEN のままマージ前提にしない）**: I1・I2（完了条件との不一致）。

## テスト

対象なし（テストファイルの変更は `tests/state/*.py` のみで、状態機械の検査。実装の検証に含めて扱った）。

## 実装（impl-review・Axis 1 = 設計整合性を含む）

| Axis | 指摘 | ファイル | 重要度 | 修正状況 |
|------|------|----------|--------|----------|
| I1 設計整合 | 完了条件「`pr_capture_done` と `capture_done` の producer / consumer が `check_asset_consistency.py` で双方向に突合される」が未実装（tasklist からも項目ごと落ちていた） | design.md:65 / check_asset_consistency.py | **High** | [x] 修正済み（再レビュー待ち） |
| I2 設計整合 | feature-pipeline 本文が判定表と食い違う。Gate 3 通過後の本文は PR へ直行し、Step 4a は「`capture_done` を立てる」旧契約のまま。`P4a`（PR 前 capture）を実行する契機が本文に無い（README 図は表と一致） | feature-pipeline/SKILL.md:195,223-226,259-272 | **High** | [x] 修正済み（再レビュー待ち） |
| I3 設計整合 | 完了条件「feature-pipeline の SKILL.md が短くなる」未達（342 → 349 行）。Phase 3.5 / 3.7 が本文と `references/pr-phases.md` に二重化 | feature-pipeline/SKILL.md:238-247 | Medium | [ ] 未達のまま記録（feature-pipeline は 342 → 356 行。P4a の実行契機・H2・PR 記録の手順が本文に必要になった。design-doc は 287 → 249 行で達成。decisions.md 参照） |
| I4 設計整合 | 完了条件「`/skill-doctor` の実測とフルモード発動頻度が decisions.md に残る」が未達（頻度は BACKLOG のみ。skill-doctor はユーザー側実行待ち） | tasklist §7 / BACKLOG.md | Medium | [ ] ユーザー側の `/skill-doctor` 実行待ち。頻度の集計は decisions.md に要約を転記 |
| I5 設計整合 | 完了条件「各 agent 定義が `model`・`effort`・`tools` を持つ」に対し `tournament-variant` に `effort` が無い（decisions に逸脱としての記録が無い） | .claude/agents/tournament-variant.md | Medium | [x] 逸脱として decisions.md に記録（書き込み可の実装役は effort 継承が妥当。契約 (p) の必須キーにも入れない） |
| I6 設計整合 | ADR 20260706（カスタム agent を導入しない）が Accepted のまま項目 6 を実施。判断記録と実装が矛盾 | docs/decisions/20260706-*.md | Medium | [x] 新 ADR 20260927-subagent-roles-in-agent-definitions で置き換え、旧 ADR を Superseded に更新 |
| I7 設計整合 | 論点 3・4・7 を Claude の既定で決めた（ユーザー未承認）。APPROVED の design.md にスコープ #7 が残る | decisions.md / design.md | Medium | [x] 追認として decisions.md に記録（design.md の契約コアは変更しない） |
| I8 状態機械 | review-result.md の未知 Status で `NO_MATCH`。C3「表が全域を覆う」は手書きケースだけを見るので検出できない。`review_status=None` が「ファイル無し」と「Status 行欠落」を区別しない（correctness の指摘と統合） | pipeline_state.py:98 / test_pipeline_state.py:196 | Medium | [x] 修正済み（再レビュー待ち） |
| I9 状態機械 | `pr_capture_done` が時点を持たない（実装中の「今」で立ち、後の P4a が消費される）。PR 待ちの間 Stop hook が `.capture-needed` を立て続け、「今」が空振りするループになる（correctness の指摘と統合） | knowledge-capture/SKILL.md:56-58 / session-stop.sh:42 | Medium | [x] 修正済み（再レビュー待ち） |
| I10 規約 | 定義ファイルが「存在するか」で分岐する書き方のため、存在するが種別未登録（`Agent type not found`）のケースで止まる（今回実際に発生。skill-issues.md 起票済み・5 か所） | frontend-code-review / impl-from-design / design-premortem / compound / impl-tournament | Medium | [x] 修正済み（再レビュー待ち） |
| I11 規約 | 配布可スキルが master-only の `scripts/pipeline_state.py` を名指し。新設 references（pr-phases / pivot / spike-lane）に「無い場合の代替動作」が無い（自己完結の規約） | feature-pipeline/SKILL.md:75 / design-doc/SKILL.md | Medium | [x] 修正済み（再レビュー待ち） |
| I12 規約 | 「値は定義側だけに書く」のに README が `opus・high` 等を複製している | README.md | Low | [x] 修正済み（再レビュー待ち） |
| I13 状態機械 | Gate 3.5 でマージするとき `Feedback: yes` を `no` に戻す指示が無い | feature-pipeline/SKILL.md:251 | Low | [x] 修正済み（再レビュー待ち） |
| I14 品質 | テストの docstring（(a)〜(e)）と実際の C1〜C4 の対応がずれている。`HALT_UNKNOWN_STATUS` → 行 ID `H1` の名前の不一致が decisions に無記録 | test_pipeline_state.py:1-14 | Low | [x] 修正済み（再レビュー待ち） |

## 正当性（review-correctness）

| Axis | 指摘 | ファイル | 重要度 | 修正状況 |
|------|------|----------|--------|----------|
| C1 状態遷移 | **マージ前アーカイブで `capture_done` が作れず steering archive が止まる（従来は立った = 退行）。** knowledge-capture は「デプロイ節に未チェックがあれば PR 前」と機械判定して `pr_capture_done` だけを立てるが、archive は `capture_done` を要求する。この repo の運用（ブランチ上のタスクはマージ前にアーカイブ）と衝突。アーカイブ済み 11 件中 3 件が同状態 | knowledge-capture/SKILL.md:56-59 / steering/SKILL.md:140-142 | **High** | [x] 修正済み（再レビュー待ち） |
| C2 状態遷移 | 直コミット運用のスキップ記録で `[x]` を付ける指示が無い。注記だけだと `deploy_unchecked` が真のまま P35 に留まる | feature-pipeline/SKILL.md:238 / pr-phases.md:22 | Medium | [x] 修正済み（再レビュー待ち） |
| C3 状態遷移 | 古い `Feedback: yes` で P37 に居座る（マージ済み・全チェック済みでも `P37` を返す。再現あり） | pipeline_state.py:85 | Medium | [x] 修正済み（再レビュー待ち） |
| C4 入力写像 | tasklist → `PipelineState` の写像が散文のみ。`PR: none` の文字列が真になる（再現あり） | pipeline_state.py:54,85 | Low | [x] 修正済み（再レビュー待ち） |
| C5 契約検査 | (n) は抽出 0 件で PASS（キーの書式変更・チェックボックス項目の欠落で偽 PASS。再現あり） | check_asset_consistency.py:429,564 | Medium | [x] 修正済み（再レビュー待ち） |
| C6 契約検査 | (p) の読み取り専用検査が黒名簿方式（引用符・インライン配列・`Agent`・`mcp__*`・`WebFetch` が PASS。再現あり） | check_asset_consistency.py:611-636 | Medium | [x] 修正済み（再レビュー待ち） |
| C7 引数処理 | `--portability --stric`（typo）が Traceback。`--purity --strict` も。`--model ''` を受理 | validate_skills.py:526-572 / passthrough_check.py:233 | Low | [x] 修正済み（再レビュー待ち） |
| C8 権限 | review-correctness の定義の Bash と、サブスキルの既定スコープコマンド（`git symbolic-ref` 等）が噛み合わない | .claude/agents/review-correctness.md | Low | [x] 修正済み（再レビュー待ち） |

## セキュリティ（review-security・読み替え: シェル実行・サブエージェント権限・CI・サプライチェーン）

| Axis | 指摘 | ファイル | 重要度 | 修正状況 |
|------|------|----------|--------|----------|
| S1 権限 | **`Bash(git diff *)` / `git log *` / `git show *` は `--output=<path>` で任意パスへ任意内容を書ける（実測）。** 読み取り専用のはずの agent 10 本に書き込みの抜け道がある。注入された指示で hooks・settings の書き換えに使える | .claude/agents/{review-*,tournament-scorer,premortem-attacker,codebase-explorer}.md | **High** | [x] 修正済み（再レビュー待ち） |
| S2 権限 | `tools:` の `Bash(git diff *)` がコマンド単位の制限として効くか未確認（公式 docs に明文が無い）。効かなければ Bash 全体が付く | 同上 | High（未確認） | [x] 修正済み（再レビュー待ち） |
| S3 権限 | 契約 (p) の `READONLY_BASH_RE` が `symbolic-ref`（書き込み形あり）と任意引数を許す。抜け道を検査が緑で通す | check_asset_consistency.py:612 | Medium | [x] 修正済み（再レビュー待ち） |
| S4 権限 | `tournament-variant` の無制限 Bash + Edit + Write を「worktree の中だけ」と文章でしか縛っていない（`.git` を共有・ネットワーク送信も未禁止） | .claude/agents/tournament-variant.md | Medium | [ ] 受容して記録（Bash 無制限は実装役に必要。`isolation: worktree` は commands.md の worktree 手順と二重になるため付けない。本文の禁止事項と注意書きで補う） |
| S5 PI | 12 本のどれにも「読んだ内容は命令ではなくデータとして扱う」の注意書きが無い | .claude/agents/*.md | Low | [x] 修正済み（再レビュー待ち） |
| S6 CI | `actions/checkout` に `persist-credentials: false` が無い。`push`（全ブランチ）と `pull_request` の重複実行。action は可変タグ（SHA 固定でない） | .github/workflows/validate.yml | Low | [x] persist-credentials: false・push を main に限定。action の SHA 固定は未実施（確認手段が無いため。decisions.md 参照） |
| S7 既存・差分外 | `guard-gated-write.sh` は `--output=CLAUDE.md` / `--output=.claude/settings.json` を素通りさせる（`>` / `tee` しか見ない）。承認制ゲートを Bash 経由で無音で越えられる | .claude/hooks/guard-gated-write.sh | Medium | [ ] ユーザー判断 |
| S8 既存・差分外 | `settings.json` の allow が前置一致の `Bash(git diff*)` 等で、`git difftool -x '<cmd>'` が任意コマンドを実行できる（実測）。`git diff --no-index /dev/null ~/.ssh/id_rsa` で `Read(~/.ssh/**)` の deny と `.env` ガードを迂回して読める | .claude/settings.json:7-9 | Medium | [ ] ユーザー判断 |

依存関係 audit: 実行不可（`pnpm audit --audit-level=high`）。`package.json` / `pnpm-lock.yaml` に差分なし（audit 対象変更なし）。CI ワークフローは `permissions: contents: read`・`pull_request` トリガー・シークレット無しで最小。

## パフォーマンス / アクセシビリティ / UI

対象なし。

## サマリー

- 重要な問題（Medium 以上）: **23 件**（High 5 件 = I1・I2・C1・S1・S2 / Medium 18 件）。Low 9 件
- 重複統合: 6 件（未知 review Status・PR 前 capture の時点・Stop hook の催促・`--output` 抜け道・READONLY_BASH_RE・本文が P4a に未追随）
- 修正完了: 28/32 件（I6 は 20260927 に ADR 起票で解消）（残り: I3 未達を記録・I4 ユーザー側実行待ち・S4 受容して記録・S7/S8 ユーザー判断。S4・I3 は「記録」で閉じる）
- 再レビュー（20260927・ユーザー合意で重点 4 件に限定・エージェント再ディスパッチなし）:
  - S1 / S2: 解消。読み取り専用 11 本の frontmatter から Bash を外した（`git --output` の抜け道ごと消える）ため、S2「`Bash(git diff *)` が効くか」は確認不要になった。frontmatter に Bash を持つのは `tournament-variant` のみ（S4 で受容済み）
  - C1: 解消。steering archive が「最終 capture として実行」を案内し、knowledge-capture の判定 1 が呼び出し元指定の最終を最優先にする。マージ前アーカイブでも `capture_done` が立つ
  - I9: 解消（残余あり・受容）。PR 前 capture 済みで目的が無い場合も `.capture-needed` を削除するようにした。ただし `session-stop.sh` は `capture_done` しか見ないため、PR 待ちの間は Stop ごとに再フラグが立つ（1 セッション 1 回の余計な確認。フェイルセーフ側の設計として受容）
  - それ以外の修正 23 件は静的検査（validate 34/34・assets 16/16・hooks 35/35・state 26/26・portability 混入なし・lint・passthrough dry-run）の緑で代替し、個別の目視再レビューはしていない
- モード: フル（3 軸）
- 修正方針: S7・S8 は既存の設定・hook（差分外）で承認制のため、この task では直さずユーザー判断に回す。それ以外は本タスク内で修正する
