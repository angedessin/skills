# 設計: spike-lane

Created: 20260801
Status: **APPROVED**
Approved: 20260801

## 目的

`design.md` の Status に探索実装レーン `SPIKE` を追加し、承認ゲートを壊さずに「設計を固めるためのローカル実装」を第一級のパスにする。ゲートが区別できない「悪い勝手実装」と「知らせる探索」を Status で分離し、学びは `decisions.md` に残して本実装は通常の DRAFT→APPROVED に戻す。

## スコープ

### 対象

- `design.md` の Status 語彙に `SPIKE` を追加（既存 `DRAFT` / `APPROVED` は維持）
- 入口: `design-doc`（SPIKE への遷移手順・テンプレ表記）
- 実装入口: `impl-from-design`（`SPIKE` でも起動可。外向き操作の禁止を手順化）
- 外向きゲート: `pr-create`（`SPIKE` なら停止・拒否）
- オーケストレーター: `feature-pipeline`（`SPIKE` は一気通貫に載せない・停止）
- 表示・仕様: `steering` SKILL / `steering/references/spec.md`（Status 3 値の説明）
- ワークフロー図: `README.md` の Status 表記（`feature-pipeline` と同一コミットで改訂する既存ルールに従う）
- 利用者向け一行: `docs/user-guide.md` / `docs/starter-kit.md` の Status・依存表に SPIKE を追記（説明のみにせず契約と揃える）
- BACKLOG 節 4 の「SPIKE レーン」行を着手時に移し、完了時に削除
- 回帰: `tests/passthrough/impl-from-design/` に SPIKE 許可と DRAFT 停止の対、`tests/passthrough/pr-create/` に SPIKE 拒否（必須）

### 対象外

- 承認ゲート全撤廃、会話内承認による Status 代用
- `SPIKE` → `APPROVED` の直昇格
- `impl-tournament` を SPIKE で起動可能にすること（引き続き `APPROVED` のみ）
- worktree / 専用ブランチ必須化、リモート push の許可
- capture 粒度・ナレッジ鮮度・配置実走・passthrough 全スキル拡充（BACKLOG の別候補）
- design.md 境界の任意追記の強制（BACKLOG 残置）
- company / export 追随
- `docs/knowledge/skill-design-patterns.md` への長文追記のみの変更（契約が正本。必要なら compound で後追い）
- live / アーカイブ済み `design.md` の一括 Status 書き換え

## 制約

- 作業ブランチ: `feature/20260801-spike-lane`（base = `integration/20260730-reports`）。親直コミットで機能変更しない
- PR のマージは人間の明示指示があるまでしない
- 説明文だけ増やす修正は禁止（Status 契約・手順・機械検査または passthrough のどれかを動かす）
- 片側修正禁止（Status 語彙を増やしたら読み手・入口スキルを同 PR で直す）
- 対象スキルはすべて**配布可**（starter-kit 最小 / 拡張 2・3 / メタ層）。master-only 参照を配布可に書かない
- company / export は Frozen
- 用語: フルモード＝7エージェント。検証コマンド正本は `pnpm run …`
- Phase 1.5 確定: (1) `Status: SPIKE` (2) ローカル実装のみ・PR/push/マージ禁止・学びは `decisions.md` (3) 出口は破棄 or DRAFT 戻し→通常承認（直昇格禁止）
- Stack: Markdown スキル定義 / passthrough シナリオ（このリポジトリ）

## 完了条件

- [x] Status 正規表記が `Status: **DRAFT — …**` / `Status: **SPIKE**` / `Status: **APPROVED**` に固定され、読み取り規則「Status 行の最初の語彙トークン ∈ {DRAFT,SPIKE,APPROVED}、以外は停止」が design-doc / impl-from-design / pr-create / feature-pipeline / steering に同文である
- [x] steering / spec の旧二値文（「APPROVED になるまで実装禁止」「DRAFT → APPROVED」のみ）が残り、SPIKE と矛盾しないこと。正本は「**DRAFT のみ実装禁止。SPIKE/APPROVED は実装可（SPIKE は外向き不可）**」
- [x] `impl-from-design` が `SPIKE` で実装に入れる一方、`DRAFT` と未知 Status では停止する（DRAFT 停止 passthrough 維持）
- [x] `design-doc` Phase 4 が `SPIKE` のまま「承認」と言われても `APPROVED` にせず、DRAFT 戻しを要求して停止する
- [x] `feature-pipeline` 判定表の **DRAFT 行の直後（APPROVED 行より上）** に `SPIKE → 即停止（パイプライン外）` があり、未知 Status も fail-closed。Phase 2 の APPROVED 再確認が SPIKE を明示拒否する
- [x] `pr-create` が対象タスクの `design.md` を Status で見て `SPIKE` なら拒否。複数アクティブ時はブランチ/差分と `.steering/[task]` の対応が取れない、または差分に SPIKE タスク成果が含まれる場合 fail-closed
- [x] DRAFT 戻し出口に「作業ツリー差分を残すか捨てるか」の明示ゲートがある。残す場合は「再実装ではなく差分を設計に追認する」経路を別契約として書く（黙ったまま APPROVED→実装で SPIKE 成果を本流化するのを禁止）
- [x] 破棄および DRAFT 戻しの前に `decisions.md` へ最低 1 エントリ（試したこと / 捨てた・残す理由）が無いと出口手順が進まない
- [x] SPIKE 中に作った `review-result.md` があれば DRAFT 戻し/破棄時に破棄するか残置禁止とする手順がある（pipeline 汚染防止）
- [x] `README.md` ワークフロー図と `feature-pipeline` が同一コミットで SPIKE を反映している
- [x] `pnpm run validate` PASS
- [x] passthrough: `impl-from-design` の DRAFT 停止維持 + SPIKE 続行（外向き禁止の言及あり）+ `pr-create` の SPIKE 拒否（任意にしない）
- [ ] base = `integration/20260730-reports` の feature PR が作れる状態（マージはしない）
- [x] `.steering/BACKLOG.md` 節 4 から SPIKE 行が削除されている

## アプローチ

既存の Status ゲートを拡張する。`design.md` に第三状態 `SPIKE` を足す。正規表記は `Status: **SPIKE**`（DRAFT/APPROVED も既存太字慣行に揃える）。読み取りは全入口で「Status 行の最初の語彙トークン ∈ {DRAFT,SPIKE,APPROVED}、以外は停止」。

`impl-from-design` は `APPROVED | SPIKE` 続行 / `DRAFT`・未知で停止。`SPIKE` 時は実装開始時にローカルのみ・外向き禁止・学びは decisions を明示する。`pr-create` は対象タスクの Status を読み `SPIKE` なら拒否（複数タスク時は対応不能・SPIKE 差分混入で fail-closed）。

`feature-pipeline` は判定表で **DRAFT の直後・APPROVED より上** に `SPIKE → 即停止` を置き、未知 Status も fail-closed（未マッチで下位行へ落とさない）。Phase 2 の APPROVED 再確認でも SPIKE を拒否。

`design-doc` Phase 4 は現 Status が `SPIKE` なら「承認」でも `APPROVED` にせず、DRAFT 戻しを要求して停止（直昇格のハードストップ）。

出口: (a) 破棄 — decisions 必須エントリ → 差分片付けは確認後のみ → review-result 等の副作用成果を片付け → タスク整理。(b) 本実装へ — decisions 必須 → **作業ツリーを捨てるか残すかの明示ゲート** → 契約コア更新 → `DRAFT` → 通常承認。残す場合は「追認経路」（再実装前提にしない）を別契約として書く。入口はユーザー明示のみ。

正本の実装可否: **DRAFT のみ実装禁止。SPIKE/APPROVED は実装可（SPIKE は外向き不可）**。旧「APPROVED まで実装禁止」文は残さない。

## 主要コンポーネント

| コンポーネント | 場所 | 変更後の記述・契約（原本なしで判定できる粒度） |
|---------------|------|------|
| Status 語彙 | `design-doc/references/templates.md` + `steering/references/spec.md` | 3 値と正規表記。SPIKE の意味・出口・読み取り規則（未知は停止）。テンプレ既定は DRAFT。SPIKE 例を別ブロック。旧二値「APPROVED まで実装禁止」を正本文に置換 |
| design-doc | `.claude/skills/design-doc/SKILL.md` | SPIKE 遷移（明示のみ）。出口（破棄 / DRAFT 戻し＋ツリーゲート＋decisions 必須＋review-result 片付け）。Phase 4: SPIKE 中の承認発話では APPROVED にせず停止 |
| impl-from-design | `.claude/skills/impl-from-design/SKILL.md` | `APPROVED\|SPIKE` 続行、`DRAFT`・未知停止。SPIKE 時外向き禁止注意・decisions 促し。description を実態に合わせる |
| pr-create | `.claude/skills/pr-create/SKILL.md` | 対象 task の design が SPIKE なら停止。複数アクティブ時の対応規則と SPIKE 差分混入の fail-closed |
| feature-pipeline | `.claude/skills/feature-pipeline/SKILL.md` | 判定表で DRAFT 直後に SPIKE 即停止。未知 Status fail-closed。Phase 2 再確認で SPIKE 拒否。README と同一コミット |
| steering | `.claude/skills/steering/SKILL.md` + spec | status/resume で SPIKE 表示。実装可否の正本文に置換（片側の旧文を残さない） |
| README 図 | `README.md` | SPIKE 分岐（探索・外向き禁止・DRAFT 戻し）を短く反映 |
| 利用者文書 | `docs/user-guide.md` / `docs/starter-kit.md` | Status 3 値と SPIKE 許可を契約と揃える |
| passthrough | `tests/passthrough/impl-from-design/` + `pr-create/` | DRAFT 停止維持。SPIKE 続行。pr-create SPIKE 拒否（必須） |
| BACKLOG | `.steering/BACKLOG.md` | 節 4 の SPIKE 行を完了時削除 |

## 未解決の論点

（20260801 承認時に推奨案で確定。詳細は `decisions.md`）

- [x] 入口: 生成時選択と既存 DRAFT からの明示遷移の両方
- [x] 破棄: 差分提示→確認後のみ戻す（黙って `git reset --hard` しない）
- [x] `impl-tournament` に SPIKE 不可を一文
- [x] 外向き防衛: **B**（横断契約）
- [x] DRAFT 戻しで差分残置: 追認経路を本スライスに含め、黙った残置は禁止
- [x] tdd 直呼び等: 対象外に明示（一本化しない）
- [x] 滞在上限: 受容＋短い探索の一文

---

<!-- design-doc-boundary: appendix -->

## プレモータム所見

### 反映済み（設計本文を修正）

- 攻撃: feature-pipeline 判定表で SPIKE が DRAFT/APPROVED に未マッチし下位行へフォールスルーする
  影響: 探索がレビュー/PR フェーズに吸い込まれる
  提案: DRAFT 直後に SPIKE 即停止 + 未知 Status fail-closed → **反映済み**（完了条件・アプローチ・主要コンポーネント）

- 攻撃: SPIKE 成果を残したまま DRAFT→APPROVED すると直昇格のゴム印になる
  影響: 動かしたコードが設計承認の代用になる
  提案: DRAFT 戻し時のツリー明示ゲートと追認経路の別契約 → **反映済み**（アプローチ・完了条件。追認を本スライスに含めるかは未解決に残置）

- 攻撃: design-doc Phase 4 が SPIKE 中の「承認」で APPROVED に書き換えうる
  影響: 直昇格が入口より安く起きる
  提案: Phase 4 ハードストップ → **反映済み**

- 攻撃: decisions 追記が促しだけで出口を機械的に落とせない / review-result が pipeline を汚染する / Status 正規表記と未知値 / steering 旧二値文の矛盾 / pr-create の複数タスク曖昧 / passthrough の任意化
  影響: ゲート非決定・学び揮発・外向き混入
  提案: 各完了条件・コンポーネントに固定 → **反映済み**（pr-create シナリオは必須化）

### 人間の判断に委ねる

- 攻撃: 外向き防衛が pr-create 単点。生 push / gh 直はスキル外
  影響: 「ローカルのみ」が手続き上破れやすい
  提案: (A) pr-create までに留め対象外明記 / (B) 横断契約
  反論: 生 git までスキルで塞ぐのは配置先・権限モデルがバラバラで過剰になりうる
  判断: 未解決「外向き防衛の範囲」— 推奨 B

- 攻撃: tdd 直呼び等 Status 非参照経路は素通りしうる
  影響: Status 分離の意味が崩れる
  提案: 一本化 or 対象外明示
  反論: 全実装入口の網羅は本スライスを爆発させる（既存も DRAFT 中の tdd 直は同様）
  判断: 未解決 — 推奨は対象外明示

- 攻撃: SPIKE 滞在上限が無くレビュー回避ルート化する
  影響: DRAFT 形骸化・巨大差分の常態承認
  提案: 上限契約 or 文化依存で受容
  判断: 未解決 — 推奨は受容＋短い探索の一文

---

> **付録** — 実装入口・resume の既定では読まない。プレモータム・TDD 突入・乖離調査など、当該節が必要なときだけ読む。人間の Phase 3 承認前は `影響範囲` と `検討した代替案` を必読。

## データフロー

```
[ユーザー: 探索が必要]
        │
        ▼
 design-doc: Status → SPIKE（明示のみ）
        │
        ▼
 impl-from-design（SPIKE 可）──► ローカル実装・検証
        │                         │
        │                         ├─ pr-create → 拒否して停止
        │                         └─ feature-pipeline → 停止
        ▼
 学びを decisions.md へ
        │
        ├─ 破棄: decisions 必須 → 差分片付け（確認後）→ 副作用成果片付け → タスク整理
        └─ 本実装へ: decisions 必須 → ツリー残置/破棄ゲート
                         │
                         ├─ 破棄してから契約コア更新 → Status DRAFT
                         └─ 残す場合は追認経路（別契約）→ Status DRAFT
                         │
                         ▼
              通常承認 → APPROVED → impl-from-design / pipeline
              （SPIKE のまま「承認」→ Phase 4 が拒否）
```

## 影響範囲

- システム / 外部連携: なし（リポジトリ内スキル契約のみ）
- データ: 新規・既存 `.steering/*/design.md` の Status 語彙。既存 DRAFT/APPROVED ファイルの自動移行はしない
- 他チーム / 利用者: 配布先で design-doc / impl-from-design / pr-create / feature-pipeline / steering を使う人。SPIKE を知らないと「DRAFT なのに実装できた」と誤認しうる → 文書と停止メッセージで Status 名を明示する
- リグレッション懸念:
  - `impl-from-design` の description/前提が緩く読め、DRAFT 素通りが増える → DRAFT 停止シナリオを維持し SPIKE と対で書く
  - `feature-pipeline` が SPIKE 未マッチで下位フェーズへ落ちる → 判定表で DRAFT 直後に即停止 + 未知 fail-closed
  - SPIKE 成果の残置＋承認で直昇格相当 → DRAFT 戻し時のツリーゲート
  - README と pipeline のドリフト → 同一コミット改訂ルールを守る
  - Status 非参照の実装入口（tdd 直等）は本スライスで塞がない場合、DRAFT/SPIKE 中も従来どおり素通りしうる（未解決で明示）

## テスト方針

- Unit: `pnpm run validate`（既存の境界・ハードストップ検査の回帰）
- Integration: なし（アプリコード変更なし）
- E2E / passthrough: `impl-from-design` の DRAFT 停止維持 + SPIKE 続行。`pr-create` の SPIKE 拒否（必須）。承認ゲート系は実行時 `--runs 4`（コスト明示のうえ任意実行だが、シナリオ資産自体は必須）

## 検討した代替案

| 代替案 | 却下理由 |
|--------|----------|
| 専用スキル `spike-from-design`（Status は DRAFT/APPROVED のまま） | 起動経路が増え「いつどっちか」が曖昧。レポートが Status: SPIKE を明示。Phase 1.5 で A 不採択 |
| 会話フラグ / tasklist メモだけで探索許可 | 成果物に残らず次セッションから見えない。Phase 1.5 で C 不採択 |
| worktree / 専用ブランチ必須（範囲 B） | SPIKE の軽さが消える。Phase 1.5 で範囲 A を採択 |
| SPIKE → APPROVED 直昇格 | 動かしたコードが設計承認の代用になる。出口 A（DRAFT 経由）を採択 |
| 承認ゲート全撤廃 | レポートのやらなくてよい縮退。固定制約 |

## 調査結果

- 一次根拠: `.tmp/reports/20260730-personal-friction-report.md` 指摘 5 / 体感優先度 4
- 引き継ぎ: `.tmp/20260731-handoff-after-p2.md`（SPIKE を推奨・次）
- P2（契約/付録）は完了済み・別タスク。本タスクは Status レーンのみ
- 現行: `impl-from-design` / `feature-pipeline` / `impl-tournament` は APPROVED 前提。DRAFT は停止。SPIKE 語彙は未導入

### 既存パターン調査（20260801）

- Status ゲート: `impl-from-design` Step 1・`feature-pipeline` 判定表（上から順・最初マッチ）・`design-doc` Phase 4・`steering` resume/status 表示が Status 語彙の主読み手
- passthrough: `tests/passthrough/*/scenario.md` を `--all` で列挙。追加シナリオは別ディレクトリ名（`impl-from-design-spike` / `pr-create-spike`）
- 検証: `mise exec -- pnpm run validate`（壊れた `~/Library/pnpm` を避ける）
- 注意点: feature-pipeline は SPIKE を DRAFT/APPROVED の間に置き、未知は fail-closed（下位行フォールスルー防止）
