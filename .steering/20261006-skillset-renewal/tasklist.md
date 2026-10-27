# タスクリスト: skillset-renewal

Last updated: 20261026（設計グループの B を実行・D1b を追加）

## 0. 計測（実施済み）

- [x] `/doctor prompt-audit` と `/skill-doctor` を `claude -p` で実行し、結果を measure/ と decisions.md に残した

## 0.5 評価の試作（design.md の承認前。`feature/eval-pilot` で行う）

- [x] サンプルアプリの最小版を `~/Desktop/_lab/ai/skills-eval-app/` に作る（商品検索・MSW・テスト 3 件。git 管理）
- [x] 現行の design-doc を評価用の `plugin.json` で包み、ケースを 2 件書く（無料。`eval-pilot/`。実行環境の確認用に smoke 1 件を追加）
- [x] 費用を見積もってユーザーの承認を取り、小さく回す（縮小版: `--runs 1` の 6 実行に変更。結果は decisions.md）
- [x] 確かめる: plugin として読み込まれるか・準備スクリプトでの複製とテスト実行（`node_modules` を含む）・`tool_used` による停止の判定・`append_system_prompt` での CLAUDE.md の近似・1 回あたりの実費
- [x] 再実行（結果は decisions.md。hook での注入は動いた。直した `src/` 判定の確認と、B・C の CLAUDE.md を plugin 同梱の SessionStart hook で注入できるかの確認。design-doc 2 ケース × あり・なし × `--runs 1` の 4 実行。前後の `/usage` を記録して 1 実行あたりの利用枠を測る。`--keep-temp` を付ける）
- [x] A の定義を決める（推奨案で決定: 素のモデル＋スキルに触れない CLAUDE.md。共通部分は `append_system_prompt`、スキルに触れる部分は B・C の plugin の hook で注入）
- [x] 本番の規模を、測った利用枠から見積もってユーザーと決める（決定: まず設計グループの約 70 実行だけ。週間枠の消費を測ってから残りを決める。全体の見込みは約 440 実行・5 時間枠 11 回分）
- [x] 結果を decisions.md に残し、設計を直すか承認するかをユーザーと決める（20261013 承認）
- [x] `feature/eval-pilot` を PR で develop にマージする（PR #17。20261015 マージ）

## 1. 準備

- [x] リポジトリ `angedessin/skills` を非公開にする（ユーザーの操作）。非公開になったことを `gh repo view --json visibility` で確かめる（20261015 確認済み）
前提: git-flow への移行（`develop` の作成・CLAUDE.md のブランチ運用）が済んでいること。移行は本タスクの外で行う

- [x] develop からマージ用ブランチ `feature/skillset-renewal` を作り、タグ `pre-renewal-20261006` を打ってリモートに push する（20261015。タグは develop の `22da4db`）。区切り（2〜3 / 4〜5 / 6〜7）ごとに子ブランチ（`feature/renewal-01-reset` など）をマージ用ブランチから切り、マージ用ブランチへ PR でマージする
- [x] 過去の review-result.md から、誤検知と修正済みの指摘を抜き出し、指摘時点のコミットを特定する（評価セットの材料。特定できないものは使わない）（20261015。eval-material.md。真の指摘 21 件・誤検知 4 件）
- [x] skill-issues.md・blockers.md・decisions.md から「モデルが実際に崩れた事例」を抜き出す（評価課題の材料）（20261015。eval-material.md。候補 17 件）
- [x] 現行 `docs/knowledge/` 3 ファイルから、新しいスキルが参照しそうな項目だけを候補に絞り、その候補だけをユーザーにレビューしてもらう（20261015。knowledge は空で始め、残す項目はコードの隣へ移す。knowledge-candidates.md）
- [x] BACKLOG を棚卸しする案を作り、ユーザーに確認する（20261015。棚卸しせず丸ごと削除に決定。CI の削除を 2 へ前倒し）

## 2. 白紙化

- [x] `.steering/archived/` を作業ツリーから削除する（20261015。追跡外の空フラグ 34 個もユーザー承認で削除）
- [x] `docs/knowledge/` を空で作り直す（現行 3 ファイルを削除。フロントエンドの知識は 5 の評価で実際に間違えたところから溜める）。同じコミットで CLAUDE.md・hook（guard-gated-write・remind-config-docs）・`validate_skills.py`・`check_asset_consistency.py` の参照を外し、静的検査が緑のままか確かめる（承認制のファイルはそのとき承認を取る。スキル本文・README・テンプレートの死んだ参照は書き直しまで許容）（20261015。remind-config-docs.sh も削除。ユーザー承認）
- [x] 旧 ADR 10 本を削除する（20261015。ADR の運用をやめ、刷新の ADR は書かない。ユーザー決定。CLAUDE.md の ADR 行も削除）
- [x] `.steering/BACKLOG.md` を削除する（棚卸しはしない。`session-start-check.sh` のバックログ注入も同じコミットで外す）（20261015 済み。knowledge-capture 本文の BACKLOG への言及は書き直しまで残す）
- [x] `.github/workflows/validate.yml` を削除する（20261015 済み。7 から前倒し。2026-10-19 の ubuntu-latest 移行より前に）

## 3. 構造の判断で削る（検査・passthrough シナリオ・README の記述を同じコミットで消す）

区切り 1（2〜3）: `feature/renewal-01-reset` → `feature/skillset-renewal` の PR #18（20261015 作成・20261015 マージ済み）

- [x] feature-pipeline・`pipeline_state.py`・`tests/state/` を削除する（README のワークフロー図も同じコミットで直す）（20261015。契約 (l)(m) も削除）
- [x] empirical-prompt-tuning を削除する（20261015）
- [x] adr スキルと `tests/passthrough/adr/` を削除する（20261015 済み。guard-gated-write の警告文の adr は 6 で直す）（20261015 決定。書き直さない。README・validate・deploy の分類・他スキルの言及を同じコミットで直す）
- [x] フラグを撤去する: `session-stop.sh` を削除し、`session-start-check.sh` を縮める（スキル本文のフラグ記述は 5 の書き直しで消える）（20261015 済み。このタスクの `.capture-needed` は残っているが催促は出ない。知見保存の項目で回収する）
- [x] skill-deploy・skill-harvest・`deploy_skills.py`・`check_deploy_drift.py`・`deployments*.md` を削除する（permissions の雛形とコピー手順は 7 で作る）（20261015 済み。`check_asset_consistency.py`・`tests/assets/` も丸ごと削除。ユーザー決定）

## 4. 評価の土台

20261015 決定: 4 は設計グループの分だけ先に作る（サンプルアプリ・B の一式・設計グループの課題と採点基準・plugin eval のケース）。他グループの課題・`tests/review-eval/`・現行レビューの基準値は、そのグループの順番が来たときに作る（C を書く前に固定する原則はグループ単位で守る）。CLAUDE.md の共通部分は今の CLAUDE.md から取り、評価の期間中は固定する。B のスキルに触れる部分はタグの CLAUDE.md から取る

- [x] サンプルアプリを作る（置き場所と中身は論点のとおり）。1 回ごとに別のパスへ新しく複製する手順を用意する（20261016。設計グループは今の 1 画面で足りるため追加なし。複製は準備スクリプトの `cp -cR`。eval-design-group.md の 3）
- [x] タグから「B の一式」（`.claude/` 全体・CLAUDE.md・必要な scripts）を作り、条件ごとに入れるものの表を書く（20261016 設計グループの分。B は 3 スキル＋premortem-attacker＋hook 1 本で、scripts は不要。`eval/prepare.sh b` がタグから組む。他グループは順番が来たら `prepare.sh` に足す）
- [x] 設計グループの課題（D1 絞り込みの設計・D2 曖昧な依頼・D3 小さな依頼・S1 再開・S2 未承認での実装依頼・P1 穴を仕込んだ設計・再評価用 D4）の採点基準を書き、全条件共通の CLAUDE.md（`.steering` の行動ルール 5 行を含む）を固定する（20261015 決定）（20261016 固定。eval-design-group.md）
- [ ] グループごとに作業課題（スキル 1 本あたり 2〜3 件）・再評価用の課題 1 件・採点基準を書き、ユーザーに確認してコミットで固定する（C を書き始める前）
- [x] 評価のケースを `claude plugin eval` の形式で書く（20261016 設計グループの 6 件＋再評価用 D4。`eval/`。B と C は 1 つの plugin ディレクトリの中身を入れ替え、ケースは 1 か所。`history_file` は使わず、再開は準備スクリプトで `.steering/` を置く形にした。B・C 用の評価用 `plugin.json`、サンプルアプリを複製する準備スクリプト、停止の判定は `tool_used`、続きからの再開は `history_file`、採点は最終回答と生成ファイル中心で `--judge-model` を実行と別のモデルに。CLAUDE.md はスキルに触れない部分を `append_system_prompt`、触れる部分を B・C の plugin の SessionStart hook で入れる）
- [ ] `tests/review-eval/` を作る（過去の誤検知・真の指摘＋仕込みバグ＋公開事例）。仕込みバグは新しい agent の観点を書く前に固定する
- [ ] 現行レビュー（タグの一式）の基準値を取り、人がラベル付けする
- [ ] 評価は、sandbox を有効にした Claude Code の中ではなく通常のターミナルから実行する

## 5. グループごとの書き直しと評価（設計 → 実装 → レビュー → 知識の順）

- [ ] 設計（design-doc・steering・design-premortem）: 書き直し → A・B・C を回す → 判定。ここで実費を測り、残りの規模をユーザーと決める
  - [x] C を書く（20261026。`eval/conditions/c/`。スキルに触れる CLAUDE.md は C に入れない。decisions.md）
  - [x] C の見直し（20261026。決定インタビューを戻す・steering の再開は依頼が曖昧なら止まる・premortem の捨てた所見を残す。decisions.md）
  - [x] B（＋A）を回す（20261026。36 実行・5 時間枠 70%。結果は decisions.md）
  - [x] B の S1 を流し直す（20261026。質 2.7/3・A は 2.3/3。steering は発動せず）
  - [x] D1b を A・B で回す（20261027。A・B とも質 6/7）
  - [x] C を回す（20261027。21 実行・5 時間枠 40%。集計は decisions.md）
  - [x] design-doc は例外として C を残し、先に聞く条件を絞る（20261027）
  - [x] P2（自分の設計の見直し）を A・C で回し、design-premortem を判定する（20261027。削除）
  - [x] 判定表を decisions.md に書き、マスターを入れ替える（20261027。design-doc・steering は C、design-premortem は削除）
  - [ ] 週間の利用枠を確かめ、残り 3 グループの規模をユーザーと決める
  - [ ] 人の採点（2 件）と採点役の一致を確かめ、判定を decisions.md に残す
- [ ] 実装（impl-from-design・tdd・e2e）
- [ ] レビュー（frontend-code-review と agent を公式の構成で作り直し、review-* スキル・impl-review・test-review を削除する。評価セットで誤検知と見逃しを比べる）
- [ ] 知識（knowledge-capture・compound・rule-audit・session-retrospective）
- [ ] 評価しないスキル: pr-create を新しい型で書き直す。debug・pr-feedback・security-audit・impl-tournament を削除する（README の記述も同じコミットで消す）
- [ ] 採用した一式を普段の環境（plugin あり）で 1 回流し、誤発動・二重実行が無いか確かめる
- [ ] マスター専用（skill-test）を新しい型で書き直す
- [ ] 各グループの判定を decisions.md に残す
- [ ] 残したスキルごとに回帰テスト用のテストケースを残す（評価の課題を転用する。形式は `claude plugin eval`）
- [ ] 書き直し後のスキルに prompt-audit をもう一度回す
- [ ] `CLAUDE.md` を 50 行以内の行動ルールに書き直す（小さな作業の決め方を含む）
- [ ] `templates/`・`prompts/`・`docs/user-guide.md`・`docs/starter-kit.md`・`README.md` を直す

## 6. settings.json

- [ ] スキルの削除（3・5）が済んでいることを確かめる（sandbox 下では `.claude/` への書き込みが標準で禁止される）
- [ ] `tests/sandbox/` を作る（hook・lint・pnpm・検査スクリプトが動く、`.env` を `cat`・`grep -r`・`python` で読めない、SSH の push・`gh pr create`・ブランチ切り替え・マージが通る）
- [ ] `.claude/settings.json` を変更案（design.md）どおりに直し、`tests/sandbox/` を流す
- [ ] guard-env-read を削除する（guard-gated-write・guard-gated-delete は残す）
- [ ] 承認ゲートの対象から `docs/decisions/` を外す（guard hook 2 本・permissions.ask・フィクスチャ）。`docs/decisions/.gitkeep` も消す。guard-gated-write の警告文の adr と、コメントの `check_asset_consistency.py` 契約 (s) への参照も直す
- [ ] 旧 `check_asset_consistency.py` の契約 (s)(t)(j) を `tests/sandbox/` に移す: guard-gated-write の `# GATED_PATHS:` 行 ≡ permissions.ask の `Edit(./...)`・allow に `Bash(git ...)` が無い・死んだ `Write|NotebookEdit|MultiEdit(path)` が無い
- [ ] guard-gated-delete の取りこぼし（大文字小文字・`FOO=1 rm` の代入前置）を、hook の冒頭コメントに「守らない形」として移すか捨てる（旧 BACKLOG 0.6）
- [ ] 残す guard hook 2 本の冒頭コメントに、旧 knowledge の落とし穴を移す（パス判定は command を取り出してから・Bash 経由の承認迂回・`git -C`／前置ラッパー／大文字小文字の取りこぼし。knowledge-candidates.md）。移す前に今のバージョンで成り立つかを `tests/sandbox/` で確かめる

## 7. 配る準備

- [ ] `templates/settings.template.json` を作る（permissions・sandbox・配る hook の登録）。README の手順に「allow に git の読み取り系を書かない」を添える（今のバージョンで確かめてから）
- [ ] README にコピー手順と依存の一覧（一緒に持っていくもの・マスター専用の印）を書く
- [ ] validate に、依存の一覧と実際のスキル・agent の参照の突き合わせを足す
- [ ] `validate_skills.py` を新構成に合わせる（`check_asset_consistency.py`・`tests/assets/` は 3 で削除済み。新構成で本当に要る突き合わせだけを、必要になったら書く。残すスクリプトには、検査スクリプトの規律と hook の JSON を `printf` で確かめる件を docstring に移す）
- [ ] CLAUDE.md の配布のルール（配置先で直接編集しない・マスターに還元して再コピー・配布分類の確認）を撤去する（CLAUDE.md の書き直しに含める）

## 8. 検証

- [ ] 静的検査（`validate`・`test:hooks`・`lint`・`tests/sandbox`）が緑
- [ ] 停止のケースを `plugin eval` で実走する（design-doc・pr-create・knowledge-capture。課金・承認制。通常のターミナルから実行する）
- [ ] 自作の passthrough（`passthrough_check.py`・`tests/passthrough/`）を削除する
- [ ] 検証用の使い捨て配置先に README の手順でコピーし、スキル・hook の発火・sandbox 下での lint と typecheck を確かめる

## レビュー

- [ ] frontend-code-review の実行（新方式）
- [ ] レビュー指摘の修正（review-result.md を参照）
- [ ] 修正後の差分再レビュー

## 知見保存

刷新の途中では knowledge-capture を回さない（刷新の記録は decisions.md が正本。20261015 ユーザー決定）。

- [ ] 評価でモデルが実際に間違えたところを、`docs/knowledge/` に書く（評価が終わったグループごと）

## デプロイ

- [ ] PR 作成（`pr-create` スキルまたは `gh pr create`）
- [ ] ローカルの静的検査が緑（CI は削除済み）
- [ ] `feature/skillset-renewal` → develop のマージ（その前にアーカイブを済ませる）
- [ ] release ブランチで main へ出す
- PR: none
- CI: none
- Feedback: no

## 福利化

- [ ] compound スキルの実行（パターンをルール・知識に昇格）

## クローズ

- [ ] steering archive モードでアーカイブ（マージ前）
