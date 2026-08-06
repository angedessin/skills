# 設計: first-deployment-run

Created: 20260805
Status: **APPROVED**
Approved: 20260806

## 目的

マスターの配布機構を、tmpdir ではなく生きた配置先で一度通す。`deployments.md` の有効行を 1 にし、`skill-harvest` / `check_deploy_drift.py` が実パスを巡回できる状態にする（company / export は Frozen・カウントしない）。

## スコープ

### 対象
- 配置先 `/Users/kentaro/Desktop/_lab/ai/skill-test`（検証用サンドボックス・**長期の実運用最小配置先として registry に残置**）への **最小セット** 配置
- `skill-deploy` → `scripts/deploy_skills.py`（dry-run 承認後の本実行）
- `deployments.md` への有効行 1 件登録（ローカル限定・gitignore 済み）。検証後の登録解除はしない
- 最低限スモーク: スキル一覧 + `design-doc` **明示指定**での承認停止
- マスター側: `.steering/BACKLOG.md` 節 4 の「配置1件実走」行の削除、実走で出た摩擦の修正（あれば同一 feature PR）

### 対象外
- company / export の有効行化・追随・パリティ
- レビュー厚み / 統合・運用 / メタ層 / session-retrospective の併配
- 本番アプリ並みのスモーク（依存インストール阻害チェック等 — 空フォルダでは実質不可）
- CLAUDE.md 発動ポリシー・references 再生成を完了条件にすること（残タスク案内に留める。references は**縮退受容**）
- 検証完了後の `skill-test` 登録解除・ディレクトリ破棄（残置方針。パスを消すならそのとき `deployments.md` からも行削除）
- 親 `integration/20260730-reports` → `main` の PR
- passthrough 拡充・design.md 境界任意追記（BACKLOG 節 4 の別項）

## 制約

- 作業ブランチ: `feature/20260805-first-deployment-run`（base = `integration/20260730-reports`）。親直コミットで機能変更しない
- **PR のマージは人間の明示指示があるまでしない**
- 配置先への書き込みはリポジトリ外操作 → `skill-deploy` Step 2 の明示承認が必須（依頼文のパスは承認の代用にしない）
- master-only（skill-test / skill-harvest / skill-deploy / adr）は配置しない
- Frozen: company / export。受け入れ条件にパリティを入れない
- 検証コマンド正本: `pnpm run …`（マスター側）。配置前は `python3 scripts/validate_skills.py` 全 PASS
- 説明文だけ増やす修正は禁止（契約・手順・機械検査のどれかを動かす）

## 完了条件

- [ ] 配置**前**ゲート: `git -C /Users/kentaro/Desktop/_lab/ai/skill-test rev-parse --is-inside-work-tree` が成功（失敗なら当セッションで `git init` → 再検査。スクリプトは git を見ないのでこのゲートを省略しない）
- [ ] `validate_skills.py` 全 PASS のうえで最小セットを `deploy_skills.py` により配置成功
- [ ] `deployments.md` の**正規化済み**有効パスがちょうど 1（`read_registry()` 相当: `#` 以降除去・strip・expanduser。対象は `/Users/kentaro/Desktop/_lab/ai/skill-test`。重複行・`path # note` 混在で 2 件扱いしない）
- [ ] `python3 scripts/check_deploy_drift.py`（引数なし・レジストリモード）が **exit 0**（ドリフトなし）。出力に当該パスが含まれる。exit 1（ドリフト）・exit 2（レジストリ/パス異常）は失敗
- [ ] スモーク: 配置先でスキル一覧が取れること。`design-doc` は**スキルを明示指定**した依頼で承認待ち停止すること（CLAUDE.md 発動ポリシー無しでの自動発動は対象外・非ブロッカー）
- [ ] `.steering/BACKLOG.md` 節 4 から「配置1件実走」行を削除
- [ ] マージ前に本タスクをアーカイブ（worktree/ブランチ上タスクの契約）

## アプローチ

配置先は検証用サンドボックスなので、先に `git init`（未初期化時）→ `rev-parse` 再検査してから配置に入る。マスターから `skill-deploy` で最小セットを選び、dry-run → 明示承認 → 本実行の順で進める。完了の正本は正規化済み有効行 1・`check_deploy_drift.py` exit 0・明示指定スモーク。`skill-test` は一回限りの検証後に解除せず、**registry に残置**して有効行 1 を維持する（パス消失時だけ行削除が対になる運用）。tdd / test-review の references は空サンドボックスでは再生成せず**縮退動作を受容**（削除は任意・必須にしない。ミニテストプロジェクト追加はしない）。CLAUDE.md 発動ポリシーは残タスク（自動発動検証はしない）。マスター側の追跡差分は BACKLOG 更新と、実走で見つかった不具合修正に限定する。

## 主要コンポーネント

| コンポーネント | 場所 | 責務（変更後の状態が原本なしで判定できること） |
|---------------|------|------|
| 配置先リポジトリ初期化 | `/Users/kentaro/Desktop/_lab/ai/skill-test` | `rev-parse --is-inside-work-tree` 成功・空ツリー。アプリコードなし |
| skill-deploy 実行 | マスターセッション | 最小 8 スキル + 同送 hooks/settings。.gitignore フラグ行・source-commit 打刻・レジストリ登録 |
| deployments.md | マスタールート（gitignore） | 正規化後ユニーク有効パス 1: `/Users/kentaro/Desktop/_lab/ai/skill-test`。Frozen コメントは維持。登録後に drift スクリプト exit 0 |
| BACKLOG 節 4 | `.steering/BACKLOG.md` | 「配置1件実走」箇条を削除（完了後）。他の残り項は残す |
| 摩擦修正（条件付き） | 配置スクリプト・starter-kit・skill-deploy 等 | 実走で壊れた契約・手順・機械検査だけ同一 PR で直す。説明文のみの追記はしない |

### 最小セット（配置スキル一覧）

`design-doc` / `steering` / `impl-from-design` / `tdd` / `frontend-code-review` / `impl-review` / `test-review` / `knowledge-capture`  
（フルモード用 review-* 5 は入れない → FCR は未配置分スキップの縮退でよい）

## 未解決の論点

- [ ] なし（プレモータム由来の残置 / references 縮退は 20260806 決定で閉じた）

---

<!-- design-doc-boundary: appendix -->

> **付録** — 実装入口・resume の既定では読まない。プレモータム・TDD 突入・乖離調査など、当該節が必要なときだけ読む。人間の Phase 3 承認前は `影響範囲` と `検討した代替案` を必読。

## プレモータム所見

（20260805・design-premortem。サブエージェント攻撃。設計は未承認）

- 攻撃: 配置先が git 未初期化でも `deploy_skills.py` / skill-deploy Step 0 は通る。完了条件の `git init` が後追い確認になりうる
  影響: 非リポジトリを有効配置先として登録できる
  提案 → 反映済み: 配置前に `rev-parse --is-inside-work-tree` 必須ゲートを完了条件・アプローチ・主要コンポーネントへ明記

- 攻撃: `register_deployment` は行完全一致、`read_registry` は `#` 除去後に読む。表記ゆれで有効パスが二重になりうる
  影響: 「ちょうど 1」と巡回件数が乖離し harvest が二重巡回する
  提案 → 反映済み: 完了条件を正規化済みユニーク 1 に変更（今回の空レジストリでは実害は小さいが検証定義を揃える）

- 攻撃: drift 完了条件が「見える」だけで exit 0 を要求していない
  影響: 配置直後ドリフトや hook 不備を成功扱いにできる
  提案 → 反映済み: レジストリモード **exit 0** を必須化

- 攻撃: CLAUDE.md 発動ポリシー無しで design-doc 自動発動スモークを想定している
  影響: モデル差で再現不能。「壊れた」と「発動しない」を区別できない
  提案 → 反映済み: スモークを明示指定の承認停止に限定。自動発動は対象外

- 攻撃: 空配置先で tdd/test-review の references 再生成を残タスクにしつつ実用性は未検証
  影響: pnpm 前提 examples が誤誘導しうる
  提案 → 反映済み（20260806 決定）: 縮退受容で確定。ミニプロジェクト追加は対象外。references 削除は任意・非必須

- 攻撃: 検証用 `skill-test` を registry に残すか破棄するか未決定。`deployments.md` はローカル限定で別端末再現も未定義
  影響: パス消失で registry モードが恒常的に exit 2
  提案 → 反映済み（20260806 決定）: **残置**。目的が有効行 1 のため解除しない。パスを消すときは `deployments.md` 行削除を対にする（対象外に明記）

## データフロー

```
ユーザー承認 (skill-deploy Step 2)
  → deploy_skills.py
      → 配置先 .claude/skills/* コピー + source-commit
      → hooks / settings.json 同送
      → .gitignore フラグ行追記
      → deployments.md に絶対パス 1 行
  → check_deploy_drift.py（レジストリ）exit 0
  → 配置先でスモーク (design-doc 明示指定 → 承認停止)
  → マスター BACKLOG 更新 → feature PR → integration
```

## 影響範囲

- システム / 外部連携: 配置先ディレクトリへのファイル書き込み（リポジトリ外）。リモート push は配置先・マスターとも本タスクの必須ではない
- データ: `deployments.md`（ローカルのみ）。git 追跡されないため証跡は `decisions.md` / アーカイブに残す
- 他チーム / 利用者: なし（個人検証用パス）
- リグレッション懸念: 配置スクリプトや同送 hooks を直す場合、既存の tmpdir 検証・他シナリオに影響しうる。修正時は `validate_skills.py` と関連 dry-run で確認

## テスト方針

- Unit / Integration / E2E（アプリ）: 対象外（アプリコードを作らない）
- 配置前: `python3 scripts/validate_skills.py` 全 PASS
- 配置検証: dry-run ログの書き込み一覧確認 → 本実行後に配置先スキル員数・source-commit・gitignore・レジストリ有効行を確認
- スモーク: 配置先セッションでスキル一覧 + design-doc **明示指定**での承認停止（自動発動は検証しない）

## 検討した代替案

| 代替案 | 却下理由 |
|--------|----------|
| 完了条件をレジストリ 1 行のみ | 「使える」確認が残らず、tmpdir 検証と差が薄い |
| 本番アプリ並みスモーク必須 | 空フォルダでは依存インストール等を検証できない |
| 最小 + レビュー厚み | 完了条件のスモークに不要。検証用に厚すぎる |
| company を有効行に載せる | Frozen。カウントしない契約 |
| tmpdir 再実行で代替 | 既に 20260726 で機構実証済み。今回の目的は実レジストリ 1 件 |
| 検証後に registry から解除 | 目的の「有効行 1」が再び 0 に戻る。残置を採る |
| ミニテストプロジェクトを足して references 再生成 | 空サンドボックス実走のスコープ膨張。縮退受容で足りる |
