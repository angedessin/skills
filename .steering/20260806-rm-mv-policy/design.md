# 設計: rm-mv-policy

Created: 20260806
Status: **APPROVED**
Approved: 20260806

## 目的

承認ゲート対象パス（`CLAUDE.md` / `docs/knowledge/` / `docs/decisions/`）への削除・移動が、書き込みゲートを迂回して素通しになる穴を塞ぐ。`rm` / `mv` を **deny** し、善意のエージェントがゲートを壊さないようにする。

## スコープ

### 対象
- 対象パスへの **素の `rm` / `mv`**（flag 付き含む）を PreToolUse hook で `tool_input.command` から構造抽出し **deny**
- 新 hook `guard-gated-delete.sh` の settings 登録・`deploy_skills.py`（`expected_hooks` / `HOOK_REGISTRATIONS`）・consistency 契約 (a)(b)(c)(d)(e)(f)(j)・README / starter-kit / `claude-code-config.md` の記述更新
- 発火／沈黙フィクスチャ一式と `pnpm` から呼べる runner（`tests/hooks/…` + script。新規）
- 完了後に `.steering/BACKLOG.md` 節 1 を削除し、export 文書ドリフトを「既知・今回非対応」と一文残す（追従タスクは今切らない）

### 対象外
- `sed -i` / 任意インタプリタ経由の削除（脅威モデル外）
- シェル複合（例: `cd docs/knowledge && rm x.md`、`bash -c '…'`、変数展開のみ）— 守らない（完全封鎖ではない）
- `git rm` / `/bin/rm` 等の別名 — **対象外**（承認時確定）
- company / export / MANIFEST 追随（Frozen）。マスター文書だけ実態に合わせる
- `guard-gated-write.sh` の改変・リネーム
- 配置先 skill-test への再配置実走
- C.6 / C.7
- permissions の変更・flag 追加補完 — **現行維持＋文書のみ**（承認時: 案 C）。`DEPLOY_PERMISSIONS` も触らない

## 制約

- Stack: Bash hooks（依存ゼロ・POSIX） / `settings.json` permissions / `scripts/deploy_skills.py`（`DEPLOY_PERMISSIONS` 含む） / `scripts/check_asset_consistency.py`
- 判定は **deny**（ask に統一しない）
- PreToolUse は permissions より先。hook 沈黙は deny を救済しない → permissions deny はプロジェクト内に誤爆しない形に限る
- パス判定は **`tool_input.command` の構造抽出のみ**（全文検査禁止）
- **抽出失敗・非対象形は沈黙（フェイルオープン）** — deny に倒すと通常 Bash が広く死ぬ。塞ぐのは「パース可能な素の rm/mv + 対象パス」に限る
- 対象パス文字列の正本は `guard-gated-write.sh` と同じ 3 系統（`CLAUDE.md` / `docs/knowledge/` / `docs/decisions/`）。新 hook 先頭コメントに write hook・`Edit(…)` ask との**手同期**を明記（機械突合は必須にしない）
- 片側修正禁止（hook 実体・settings の PreToolUse 登録・`expected_hooks` / `HOOK_REGISTRATIONS`・README / starter-kit / claude-code-config）。本タスクでは permissions / `DEPLOY_PERMISSIONS` は変更しない
- 検証の正本は `pnpm run …`
- 親ブランチは `integration/20260730-reports`。feature PR の base は親。マージは人間の明示後のみ

## 完了条件

### hook（本命）
- [ ] 守る形の表（下記アプローチ）に列挙した `rm` / `mv` × 対象パスが deny（フィクスチャで発火を機械確認）
- [ ] 沈黙コーパス（対象外パス・対象外コマンド形・`transcript_path` 混入ペイロード）で誤 deny 0
- [ ] `rm -R` / `rm --recursive` / `rm -f -r` など flag 付きでも、素の `rm` としてパースでき対象パスなら deny
- [ ] command 抽出の契約テスト（正常抽出 / 抽出失敗→沈黙）がある
- [ ] `guard-gated-write.sh` の書き込み ask を**同じ runner**で再録し、発火・誤検知が現状維持
- [ ] フィクスチャ置き場と runner が `pnpm run` から呼べ、一回限りの手動確認だけで「ゼロ」と書かない

### 配線・文書
- [ ] `pnpm run` 経由の asset consistency（特に契約 (e)(f) 含む）/ 関連 validate が PASS
- [ ] README / starter-kit / `claude-code-config.md` が「削除・移動は非対象」から実態（書き込み=ask・削除移動=deny・守る形／守らない形）に更新
- [ ] BACKLOG 節 1 が削除され、export 文書ドリフト「既知・今回非対応（追従タスクなし）」が一文残っている

### 人間確認
- [ ] セッション再起動後、対象パスへの `rm` 1 ケースで deny が人間観測できる（PreToolUse は再起動後確認が既知制約。フィクスチャ緑だけでは完了にしない）

## アプローチ

`guard-gated-delete.sh` を PreToolUse(Bash) に追加する。stdin JSON から `tool_input.command` だけを取り、**先頭トークンが `rm` または `mv`**（`/bin/rm`・`git rm` は対象外）で、オペランドに対象パス断片が含まれるとき deny。抽出できない・複合シェルは沈黙。

**守る形（必須）**

| 形 | 例 |
|---|---|
| 素の rm + 対象パス | `rm -f docs/knowledge/x.md` |
| flag 穴相当 | `rm -R docs/knowledge/x` / `rm --recursive …` / `rm -f -r …` |
| 素の mv（ソースまたはデストに対象パス） | `mv docs/knowledge/x.md /tmp/` / `mv a.md docs/knowledge/a.md` |

**守らない形（明示・沈黙）** — `cd … && rm`、`bash -c`、`eval`、`git rm`、`/bin/rm`、説明文にパスが含まれるだけのコマンド、対象外パスのみ。

permissions は現行の粗いネットを維持し、**本タスクでは変更しない**。

## 主要コンポーネント

| コンポーネント | 場所 | 責務 |
|---------------|------|------|
| 新 hook | `.claude/hooks/guard-gated-delete.sh` | `tool_input.command` 構造抽出。対象形なら deny。失敗は沈黙。パス正本は write と手同期 |
| settings | `.claude/settings.json` | PreToolUse に新 hook 登録のみ（permissions は不変） |
| 配布配線 | `scripts/deploy_skills.py` | `expected_hooks` + `HOOK_REGISTRATIONS` 対追加（無条件同送） |
| 一貫性検査 | `scripts/check_asset_consistency.py` | 契約 (a)(b)(c)(d)(e)(f)(j) が PASS（ロジック原則不変・分類追随） |
| フィクスチャ / runner | `tests/hooks/guard-gated-delete/` + `pnpm` script | 発火・沈黙・抽出失敗・write 回帰を機械実行 |
| 文書 | `claude-code-config.md` / `README.md` / `docs/starter-kit.md` | 守る形／守らない形・ask vs deny・再起動確認を明記 |
| バックログ | `.steering/BACKLOG.md` | 節 1 削除 + export ドリフト既知の一文（追従タスクなし） |

## 未解決の論点

なし（20260806 承認時にプレモータム未解決 4 件を推奨セットで確定。詳細は `decisions.md`）

---

<!-- design-doc-boundary: appendix -->

## プレモータム所見（design-premortem · 20260806）

- 攻撃: command 抽出失敗時方針・エスケープ／複合形が未定義。deny 用だけ別パーサになる
  影響: フェイルオープンだと穴、フェイルクローズだと通常 Bash が死ぬ。後で全文検査に戻すと transcript 誤 deny
  提案: 沈黙（フェイルオープン）と守る形を固定し、抽出契約テストを完了条件へ
  **プレモータム反映済み** — 制約・アプローチ・完了条件に反映

- 攻撃: `cd && rm` / 絶対パス / `git rm` / `/bin/rm` / `bash -c` 等が沈黙しうる
  影響: 常用形でゲート再素通し
  提案: 守る／守らない表。別名は人間判断
  **プレモータム反映済み**（表・対象外）。`git rm` 等は未解決に残置

- 攻撃: 誤検知コーパス未定義。「既存フィクスチャ」前提は虚偽に近い。deny 誤爆は ask より重い
  影響: 一回限り確認で回帰なし
  提案: フィクスチャ集合・runner・write 同じ runner 再録
  **プレモータム反映済み**

- 攻撃: `DEPLOY_PERMISSIONS` / 契約 (e)(f) が片側修正リストから欠落
  影響: マスターだけ更新・配置 payload ドリフト
  提案: コンポーネントと制約に明記
  **プレモータム反映済み**

- 攻撃: 対象パスが write regex・新 hook・Edit ask の三重管理
  影響: パス追加時に片側遅れ
  提案: 正本＝write と同じ 3 系統、手同期をコメントで明示（機械突合は必須にしない）
  **プレモータム反映済み**

- 攻撃: permissions flag 補完と hook 本命が同一完了条件に混在
  影響: 「最小」の終わり条件が曖昧 → 軍拡 or 過少
  提案: 完了条件から切り離し (A)(B)(C) を人間判断 — 推奨 C
  **プレモータム反映済み**（切り離し）。採否は未解決

- 攻撃: Frozen で export 文書が旧記述のまま。系統間ドリフト
  影響: 「マスターでは塞いだ」と配布物語の矛盾
  提案: 既知ドリフトとして完了条件／対象外に固定。追従タスク起票は人間判断
  **プレモータム反映済み**（既知ドリフト明記）。起票可否は未解決

- 攻撃: 未解決が名前・flag・置き場に偏り、再起動後人間確認が完了条件に無い
  影響: フィクスチャ緑だけで効いていると誤認
  提案: 人間確認 1 ケースを完了条件へ
  **プレモータム反映済み**

> **付録** — 実装入口・resume の既定では読まない。プレモータム・TDD 突入・乖離調査など、当該節が必要なときだけ読む。人間の Phase 3 承認前は `影響範囲` と `検討した代替案` を必読。

## データフロー

```
Bash tool call
  → PreToolUse: guard-env-read / guard-gated-write / guard-gated-delete
      delete: tool_input.command のみ抽出
        → 素の rm|mv かつオペランドに gated path → deny
        → 抽出失敗・非対象形 → 沈黙
  → permissions ask/deny（粗いネット・現行維持）
  → 実行 or 拒否
```

## 影響範囲

- システム / 外部連携: Claude Code PreToolUse / permissions。個人配置の同送 hook が増える
- データ: なし
- 他チーム / 利用者: マスターで対象形の rm/mv が deny。export 文書は意図的に旧記述のまま（ドリフト既知）
- リグレッション懸念: 部分一致による誤 deny／配線片側修正／write hook 回帰／「効いている」誤認（再起動未確認）

## テスト方針

- Unit: `tests/hooks/…` に公式 docs 形式 JSON。発火・沈黙・抽出失敗・write 回帰を同一 runner で assert
- Integration: `check_asset_consistency`（(e)(f) 含む）と deploy dry-run
- E2E: なし。代わりにセッション再起動後の人間 deny 観測 1 ケースを完了条件に含む

## 検討した代替案

| 代替案 | 却下理由 |
|--------|----------|
| permissions deny 拡充のみ | flag 順列・パス判定不可 |
| hook のみで permissions 粗いネット削除 | 壊滅的パターンの防波堤喪失 |
| write hook に deny 混在 / リネーム | ask と deny の代償が違う |
| パス範囲拡大 | 誤 deny・コスト増 |
| ask に統一 | 20260726 決定で却下 |
| 抽出失敗を deny | 通常 Bash が広く死ぬ（プレモータム後に却下） |
| 複合シェルまで封鎖 | 軍拡・脅威モデル超過。完全封鎖しない前提 |

## 調査結果

一次情報は再調査しない（BACKLOG 節 1 / `archived/20260726-deploy-integrity`）:

1. PreToolUse は permissions より先。hook は deny を救済できない
2. 全文パス判定不可 → command 構造抽出必須
3. 非対話で ask は deny に落ちる
4. 実測: `rm -f docs/knowledge/x.md` 素通り。flag 穴あり
5. リポジトリに永続 hook runner は無し（20260726 は decisions に発火表を手記録）。本タスクで runner を新設する

### 既存パターン調査（20260806）

- **ask 系 hook**（`guard-gated-write.sh` / `guard-env-read.sh`）: stdin 全文 grep。deny ではないので transcript 誤検知の代償が小さい。本タスクの構造抽出とは意図的に別設計
- **配布**: `expected_hooks` 無条件同送リスト + `HOOK_REGISTRATIONS` 対登録。新 hook は write と同様常時同送
- **検証先例**: `archived/20260804-knowledge-freshness-nudge/verification.md` は一時フィクスチャ表。永続 runner は無し → `tests/hooks/` + `pnpm` script を新設
- **Vitest カートリッジは非適用**（Bash hook）。観察可能結果は hook stdout の `permissionDecision` 有無と値
- 注意点: permissions / `DEPLOY_PERMISSIONS` は触らない。片側は hook・settings PreToolUse・expected_hooks・HOOK_REGISTRATIONS・文書
