# 設計: design-impl-sync

Created: 20260802
Status: **APPROVED**
Approved: 20260803

<!-- Status は DRAFT / SPIKE / APPROVED の 3 値。既定は DRAFT。
     SPIKE（探索・破棄前提・外向き禁止）の表記例: Status: **SPIKE**
     読み取り: Status 行の最初の語彙トークン ∈ {DRAFT,SPIKE,APPROVED}、以外は停止。
     実装可否の正本: DRAFT のみ実装禁止。SPIKE/APPROVED は実装可（SPIKE は外向き不可）。 -->

## 目的

APPROVED 後の実装中に design↔実装がずれたとき、契約コア変更は再承認・APPROVED 追認のみは APPROVED 維持、という第一級の同期パスをスキル契約として明確にする。あわせてレビューで設計整合をゲート入力として強制突合し、「承認済みを守るだけ／起動条件が曖昧」だった摩擦（personal-friction 指摘 4）を解消する。ゲート全撤廃はしない。

## スコープ

### 対象
- `design-doc` の「方針転換」節: 起動条件（契約コア vs APPROVED 追認）・分類表・Status 遷移（コア変更時は DRAFT 戻し）。**Status / 契約コアの書き込みはこの節のみ**（impl-from-design は提案と停止に限定）。DRAFT 戻し時は既存 `review-result.md` を破棄（SPIKE 出口と同型）。作業ツリーは**残置前提**を明記する（SPIKE 並の破棄ゲートは設けない）
- 契約コア集合の正本: design-doc の契約コア全見出し（目的・スコープ・制約・完了条件・アプローチ・主要コンポーネント・未解決の論点）。書き手・読み手・Axis 1 で部分集合を別定義しない
- `impl-from-design` の「乖離」節: 停止後に短い固定テンプレで分類提案（コア変更 → design-doc 方針転換を提案 / APPROVED 追認 → APPROVED 維持更新を提案）。勝手に Status・コアを変更しない
- `impl-review` Axis 1: 契約コア突合を必須化。**Status が APPROVED のときのみ**不一致をゲート級 **High**（High 尺度に「設計契約コア不一致」を明示追加）。DRAFT/SPIKE は Info またはスキップ。design 無しはスキップ。単独起動時も「design 同期が先」を次ステップに書く
- `frontend-code-review`: 設計整合 High をゲート入力として明示（OPEN のままマージ前提にしない）。Gate 3 で設計整合残存を DEFERRED するとき**必須警告**。`.steering/*/design.md` があるタスクで契約成果物（SKILL.md 等）が変わる場合は**軽量でも Axis 1 をスキップしない**
- `feature-pipeline`: 乖離待機を**両分岐**で書く（コア→DRAFT なら Step 0 再判定で Gate 1／APPROVED 追認なら Phase 2 継続）。DRAFT 戻し時の review-result 破棄と整合
- BACKLOG 節 4 の当該行を完了扱いに更新（実装完了・マージ後）
- 検証: **`pnpm run validate` のキーワード共存検査を主**（空文で通る限界はコメントで明記）。分類提案テンプレ／手順キー欠落で fail

### 対象外
- 承認ゲートの全撤廃・「APPROVED のまま任意にコア書き換え」パス
- SPIKE レーンの出口契約の再設計（既存の破棄 / DRAFT 戻しをそのまま使う。用語・手順とも SPIKE 出口節へ委譲し、本タスクの「APPROVED 追認」と混線させない）
- capture 粒度・ナレッジ鮮度・配置1件・passthrough **全体**拡充（別 BACKLOG。本タスクで passthrough を必須にはしない）
- live design.md への境界マーカー一括追記
- company / export 追随
- 親 `integration/20260730-reports` → `main` の PR

## 制約

- Stack: 本リポジトリはスキル／ドキュメント成果物（React アプリ実装ではない）。検証は `pnpm run …`
- 説明文だけ増やす修正は禁止（契約・手順・機械検査のどれかを動かす）
- 片側修正禁止（書き手と読み手を同じコミットで揃える。Status 遷移を増やすなら Phase メッセージも分岐）
- 配布分類: 変更対象スキルはいずれも**配布可**。master-only 名を本文に書かない
- 用語正本: フルモード＝7エージェント
- PR マージは人間の明示指示まで禁止。base = `integration/20260730-reports`
- SPIKE / DRAFT / APPROVED の既存読み取り規則・実装可否正本は壊さない

## 完了条件

- [x] `design-doc`「方針転換」に: 起動条件・**分類表（コア例/APPROVED 追認例/迷ったらコア）**・コア変更時の `Status: **DRAFT**` 戻し→再承認・APPROVED 追認パス・「Status/コア書き込みはこの節のみ」・SPIKE は出口節へ委譲・review-result 破棄・作業ツリー残置前提、が書いてある
- [x] `impl-from-design`「乖離」が停止＋短い固定テンプレの分類提案になり、Status/コアを自ら書き換えず design-doc 方針転換を案内する
- [x] `impl-review` Axis 1 が契約コア全見出しと突合し、APPROVED 時のみ不一致を High（尺度に設計例外を明記）、DRAFT/SPIKE は Info/スキップ、design 無しはスキップ。単独起動時も「design 同期が先」を次ステップに書く
- [x] `frontend-code-review` が設計整合 High をゲート入力にし、design あり＋契約成果物変更では軽量でも Axis 1 をスキップせず、Gate 3 の設計整合 DEFERRED に必須警告、OPEN のままマージ前提にしない旨を明示する
- [x] `feature-pipeline` の乖離待機が両分岐（DRAFT→Gate1 / APPROVED 追認→Phase2）で、review-result 破棄と矛盾しない
- [x] `validate_skills.py` が方針転換/乖離分類/Axis 1 High のキー共存を検査し、欠落で fail（空文限界をコメント明記）
- [x] `pnpm run validate` が通る
- [x] BACKLOG 節 4 の「design↔実装の同期パス明確化」を完了行にする（マージ直前で可）

## アプローチ

契約の骨格は Phase 1.5＋承認時の推奨一括確定: **契約コア（design-doc 正本の全見出し）の変更は DRAFT 戻し→再承認。文言整理・tasklist 追従・付録のみは APPROVED 追認（APPROVED 維持＋decisions 1 行）。迷ったらコア。** Status / 契約コアの書き込みは `design-doc` 方針転換のみ。`impl-from-design` は停止と短い分類提案に限定する。SPIKE 中は既存 SPIKE 出口のみ。レビューは High 尺度に設計契約コア不一致を明示追加し、APPROVED 時のみゲート級、design あり＋契約成果物変更では軽量でも Axis 1 必須、Gate 3 の設計整合 DEFERRED に警告必須。機械検査は validate キーワード共存を主とする。

### 分類表（方針転換・乖離分類の正本）

| 区分 | 例 | 結果 |
|------|-----|------|
| 契約コア変更 | 目的の書き換え、スコープ対象/対象外の追加削除、制約の追加、完了条件の追加/削除/意味変更、アプローチの技術選択変更、主要コンポーネント行の追加削除・責務変更、未解決の論点の実質追加 | `Status: **DRAFT**` → Phase 3 再承認。APPROVED のままコアを書かない。既存 review-result は破棄。作業ツリーは残置前提 |
| APPROVED 追認 | 誤字・表現の整理、tasklist のチェック/順序の実態追従、付録のみの追記、主要コンポーネントの「場所」パスの表記ゆれ修正（責務不変） | APPROVED 維持。design/tasklist 更新＋`decisions.md` に 1 エントリ |
| 迷ったら | どちらとも言える変更 | **コア変更扱い**（再承認側に倒す） |

用語: SPIKE 出口の「残差分を設計に吸収して DRAFT へ」は **SPIKE 吸収** と呼ぶ。本表の「APPROVED 追認」とは別語。

## 主要コンポーネント

| コンポーネント | 場所 | 責務（変更後に原本なしで判定できる記述） |
|---------------|------|------|
| 方針転換契約 | `.claude/skills/design-doc/SKILL.md` | 「方針転換が起きた場合」を上記分類表＋DRAFT 戻し／APPROVED 追認／単一ライター／SPIKE 委譲／review-result 破棄／作業ツリー残置前提で書き換え。Phase メッセージが Status 遷移と矛盾しないこと |
| 乖離時分類 | `.claude/skills/impl-from-design/SKILL.md` | 乖離時: 停止 → 固定テンプレ（区分・根拠1行・次アクション1行）で分類提案 → コアなら design-doc 方針転換を案内 / APPROVED 追認なら更新案を提示 → ユーザー判断待ち。Status・コアは書かない |
| 設計整合 | `.claude/skills/impl-review/SKILL.md` | Axis 1: design.md があるとき契約コア全見出しと突合。APPROVED 時のみ不一致 High（尺度に設計例外）。DRAFT/SPIKE は Info/スキップ。design 無しはスキップ。単独時も「design 同期が先」を次ステップに含める |
| レビューゲート入力 | `.claude/skills/frontend-code-review/SKILL.md` | High 尺度に設計契約コア不一致を追加。設計整合 High をゲート入力化。design あり＋契約成果物変更では軽量でも Axis 1 必須。Gate 3 の設計整合 DEFERRED に必須警告。「OPEN のままマージ前提にしない」を明示 |
| パイプライン待機 | `.claude/skills/feature-pipeline/SKILL.md` | 乖離待機を両分岐で更新。DRAFT 戻し時の review-result 破棄と整合 |
| 機械検査 | `scripts/validate_skills.py` | 方針転換/乖離分類/Axis 1 High のキー共存検査。欠落で fail。空文で通る限界をコメント明記 |
| BACKLOG | `.steering/BACKLOG.md` | 節 4 の同期パス行を完了 |

## 未解決の論点

承認時（20260803）に推奨案で一括確定済み。残なし。

| 論点 | 確定 |
|------|------|
| 設計不一致の重要度 | High 尺度に「設計契約コア不一致」を明示追加。Gate 3 で設計整合 DEFERRED 時は必須警告 |
| 軽量・md 中心 diff | design.md があるタスクで契約成果物が変わる場合は軽量でも Axis 1 をスキップしない |
| 機械検査の主 | validate キーワード共存＋限界をコメント明記（passthrough 必須にはしない） |
| DRAFT 戻し時の副次状態 | review-result 破棄。作業ツリーは残置前提を明記 |
| Axis 1 の Status ガード | APPROVED のときのみゲート級 High。DRAFT/SPIKE は Info またはスキップ |
| design が無いタスク | 設計整合スキップ維持 |

---

<!-- design-doc-boundary: appendix -->

> **付録** — 実装入口・resume の既定では読まない。プレモータム・TDD 突入・乖離調査など、当該節が必要なときだけ読む。人間の Phase 3 承認前は `影響範囲` と `検討した代替案` を必読。

## プレモータム所見

（design-premortem / 20260802。設計承認ではない。会話履歴なし・リポジトリ突合あり）

### プレモータム反映済み（契約コアを修正）

- 契約コア集合の揺れ → 正本を design-doc 契約コア全見出しに一本化。Axis 1 も同じ集合
- 分類表欠落 → アプローチ直下にコア/APPROVED 追認/迷ったらコアの表を追加。完了条件・主要コンポーネントに分類表を必須化
- Status 単一ライター未定義 → design-doc 方針転換のみ書き込み、impl-from-design は提案と停止、をスコープ／アプローチ／主要コンポーネントに明記
- feature-pipeline「一文」曖昧 → 両分岐（DRAFT→Gate1 / APPROVED 追認→Phase2）に変更
- SPIKE「追認」と同語異義 → 「SPIKE 吸収」vs「APPROVED 追認」に用語分離。SPIKE は出口節へ委譲
- 未解決の網羅不足 → High 尺度・軽量/md・機械検査・review-result/作業ツリー・Status ガード・design 無しを未解決に昇格（推奨付き）

### 人間の判断に委ねる（未解決の論点へ移動済み）

- 攻撃: frontend-code-review の High＝実害尺度に設計不一致を載せる衝突
  影響: Gate 3 で過剰停止か習慣的 DEFERRED
  提案: 未解決「重要度ラベル」で A/B/C を選ぶ（推奨 A＋DEFERRED 時警告）
  反論: Medium だけだと「マージ前提にしない」が弱く指摘 4 が残る。別ラベルは学習コスト増

- 攻撃: md 中心 diff で軽量に落ち Axis 1 がスキップされうる
  影響: このリポジトリの主戦場でゲート不発
  提案: 未解決「軽量・md」で例外の採否（推奨 A: design あり＋契約成果物変更ではスキップしない）

- 攻撃: validate キーフレーズは空文で通る
  影響: 検査緑のまま実行時回帰
  提案: 未解決「機械検査の主」（推奨 A: validate 最小＋限界明記。余裕があれば C）

- 攻撃: DRAFT 戻し後に古い OPEN review-result / 作業ツリー残置
  影響: Gate 3 再燃や同期漏れ
  提案: 未解決「副次状態」（推奨: review-result 破棄、ツリーは残置前提を明記）

- 攻撃: DRAFT/SPIKE 中の Axis 1 ゲート級指摘がノイズ or 穴
  影響: 未承認設計との不一致 High、またはスキップ穴
  提案: 未解決「Status ガード」（推奨 A: APPROVED のみゲート級）

### 参考（本文修正なし・リスク受容または Info）

- 正本階層（Status=ゲート、コア=内容、decisions=追認ログ、review-result=指摘キャッシュ）はデータフロー／影響範囲の運用メモとして足りる。追加節は YAGNI
- company/export 対象外は配布可変更として妥当。配置ドリフトは skill-harvest 既知コスト
- 分類提案が厚くなると旧挙動へ回帰しうる → 固定テンプレ短文化を完了条件・主要コンポーネントに既に反映

（このプレモータムは設計を承認しない。design-doc の Phase 3 STOP に戻る）

## データフロー

```
実装中に乖離検知
  └─ impl-from-design: 停止 → 短い分類テンプレ（コア / APPROVED 追認 / 迷ったらコア）
        ├─ ユーザー: コア変更 → design-doc 方針転換のみが Status/コアを書く → DRAFT
        │     ├─ review-result 破棄 / 作業ツリー残置
        │     └─ Step 0 再判定 → Gate 1（再承認）→ APPROVED → 実装再開
        └─ ユーザー: APPROVED 追認 → design/tasklist 更新（APPROVED 維持）+ decisions → Phase 2 継続

レビュー
  └─ impl-review Axis 1（契約コア全見出し。APPROVED のみゲート級 High）
        └─ frontend-code-review: 設計整合 High をゲート入力
              （design あり＋契約成果物変更では軽量でも Axis 1 必須）
              → review-result 明示 → 人間トリアージ
              → 設計整合 DEFERRED 時は必須警告
```

## 影響範囲

- システム / 外部連携: なし（スキル本文・検証スクリプトのみ）
- データ: `.steering/[task]/design.md` の Status が実装中に DRAFT へ戻りうる。decisions.md 追記が増える。review-result は DRAFT 戻し時に破棄
- 他チーム / 利用者: 配布先で該当スキルを使う人。APPROVED 中のコア変更が再承認必須になるため「止まって戻る」頻度が上がりうる（意図どおり）。配置先に旧方針転換が残る期間は skill-harvest で回収
- リグレッション懸念: (1) 誤分類 → 分類表＋迷ったらコア (2) design 無しで過剰ゲート → スキップ維持 (3) SPIKE 出口と APPROVED 追認の混線 → 用語分離 (4) High インフレ → DEFERRED 必須警告 (5) md のみ diff で Axis 1 不発 → 契約成果物変更時は軽量でも Axis 1 必須

## テスト方針

- Unit: なし（アプリコードなし）
- Integration / 静的: `pnpm run validate`（方針転換/乖離分類/Axis 1 High のキー共存。空文限界はコメント）
- 実行層: 本タスクでは必須にしない（別 BACKLOG の passthrough 拡充）
- 手作業（一回限りと明記する場合のみ）: 変更後 SKILL の該当節を分類表と突合

## 検討した代替案

| 代替案 | 却下理由 |
|--------|----------|
| どんな変更も APPROVED のまま続行（再承認なし） | 承認ゲートが形骸化する。handoff「ゲート全撤廃はしない」に反する |
| どんな変更も必ず DRAFT 戻し | アジャイルな APPROVED 追認（tasklist・文言）まで再承認になり摩擦が過大 |
| レビューは触らず実装中パスだけ強化 | personal-friction / BACKLOG が求める「レビュー突合」が残る |
| 設計不一致で frontend-code-review 自体をハードストップ | `.steering` 無し・軽量変更で過剰停止。報告＋ゲート入力で人間トリアージする方が安全 |
| SPIKE 中も同じ「APPROVED 向け同期パス」を適用 | SPIKE は既に破棄/DRAFT 戻し出口がある。重ねると Status 意味が崩れる |
| 契約コア集合を Axis 1 用に部分集合化 | 書き手と読み手で判定が割れる（プレモータムで却下相当→正本一本化） |

## 調査結果

### 現状（20260802）
- `impl-from-design`: 乖離時は停止 → 未解決追記 → ユーザー待ち。分類・DRAFT 戻し提案なし
- `design-doc`「方針転換」: 大きく変わったら design/tasklist を更新、とあるが起動条件と Status 遷移が無い
- `impl-review` Axis 1: 設計整合はあるが重要度が「要確認」止まり
- `frontend-code-review`: High は実害定義。impl-agent に設計整合を委託するが設計をゲート入力としては扱っていない。`*.md` はモード判定に影響しない
- 一次根拠: `.tmp/reports/20260730-personal-friction-report.md` 指摘 4 / BACKLOG 節 4 / SPIKE PR #7 decisions（後続起票）

### 既存パターン調査（20260803）
- validate 拡張: `check_design_doc_template` と同型で既定 `.claude/skills` 走査時に追加検査（キーワード共存）
- バージョン: 契約変更スキルは metadata.version をバンプ（design-doc 1.11 / impl-from-design 1.7 / impl-review 1.4 / frontend-code-review 1.5 / feature-pipeline 1.6）
- 注意点: SPIKE 出口の旧「追認」語は「SPIKE 吸収」に置換して APPROVED 追認と分離
