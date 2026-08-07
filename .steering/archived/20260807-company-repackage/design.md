# 設計: company-repackage

Created: 20260807
Status: **APPROVED**

## 目的

`main` 最新を正として、会社向け持ち出しセット `export/company/` を再パッケージする。同梱 10 スキルの本文・hooks / settings・説明文書を揃え、会社が持ち込んで使える状態にする。

## スコープ

### 対象
- `export/company` ブランチでの作業。`main` の取り込み（merge。既に `e05d020` 済みなら残り作業のみ）
- **同名 10 スキル本文を main から同期**（停止契約・手順の正本は main）
- 同期はディレクトリ丸ごと上書きにしない。手順:
  1. main の `.claude/skills/<name>/` をベースにする
  2. **`tdd/references/patterns.md` はコピーしない**（main にあっても持ち込み禁止）
  3. Angular / Jasmine 語彙へ再適用
  4. 非同梱スキル名を除去（理由文の `adr` 等も含む）
  5. 会社側 `metadata.modified` 由来の停止契約強化がある場合は、捨てる／残すをスキルごとに明示して三点マージ（黙って消さない）
- 変換レシピ（禁止語彙・禁止参照スキル名・禁止ファイル・残す会社パッチの扱い）を MANIFEST に残す
- hooks / settings: **同梱は次の 6 本に固定** — `session-start-check` / `session-stop` / `guard-env-read` / `guard-gated-write` / `guard-gated-delete` / `post-edit-lint`。`stop-typecheck` / `validate-skill-edit` / `remind-config-docs` は同梱しない
- hooks 追随: 上記 6 本について main の重要修正を取り込む。理由文から非同梱スキル名を除去
- 会社方針維持: `npx` 全面 deny、パッケージ install 全面 deny
- `MANIFEST.md` / `HANDOVER.md` / `MIGRATION-GUIDE.md` を再パッケージ後の実態に更新（死んだ検査参照の除去、hook 本数・python3 依存、独立フォーク方針と今回の例外同期の関係）

### 対象外
- tdd `references/patterns.md` の新規作成・main からのコピー（禁止）
- pr-create / pr-feedback の同梱（後続判断。MR 向けはカートリッジ差し替えで可）
- レビュー系 8 / feature-pipeline / e2e / adr / master-only の同梱
- `stop-typecheck` / `validate-skill-edit` / `remind-config-docs` の同梱
- 会社実プロジェクトへの配置（HANDOVER 実行は別セッション）
- main への `check_export_stopcontract` 復帰
- passthrough シナリオの課金実走（任意）。ただし文書から死んだ検査参照を消すこと、既存 `export/company/tests/` の更新要否判定は対象

## 制約

- worktree: `/Users/kentaro/Desktop/_lab/ai/skills-export-company`、ブランチ `export/company`
- `main` は merge で取り込む（rebase しない）
- 配布正本: `export/company/skills/` と `export/company/claude-config/`
- `metadata.source-commit` は同期に使った main 側 hash
- `guard-gated-delete` は python3 依存。欠如・抽出失敗時はフェイルオープン（沈黙）→ HANDOVER / MANIFEST に明記。settings `_comment` の「POSIX のみ・追加インストール不要・5 本」は更新必須
- commit / push / 会社配置はユーザー明示承認後のみ

## 完了条件

- [ ] `main` が `export/company` に取り込まれている
- [ ] 同梱 10 スキルについて、許可差分を除き main との停止契約差分が空
  - **許可差分のみ**: Angular/Jasmine 語彙、非同梱スキル名の除去、三点マージで残すと明示した会社 `modified` パッチ、`patterns.md` 不在
  - 「実質一致」という曖昧判定は使わない。差分は `diff` + 禁止語 grep で示す
- [ ] `export/company/skills/tdd/references/patterns.md` が存在しない
- [ ] 同梱 10 本文・同梱 hooks 理由文に非同梱スキル名が残っていない
- [ ] React / Vitest / pnpm 等の個人スタック語彙が意図せず戻っていない（許可箇所以外 grep ゼロ）
- [ ] hooks 実体が上記 6 本のみ。`guard-gated-delete` が settings の PreToolUse(Bash) に登録
- [ ] settings の `_comment` / 3 文書が hook 本数・python3 依存・削除ゲートと一致
- [ ] `npx` / install の会社 deny が settings から消えていない
- [ ] 3 文書に `check_export_stopcontract` 等の死んだ検査参照が無い
- [x] 変換レシピと「原則独立＋停止契約は上流同期」方針が文書化されている（**保守文書 `export/COMPANY-MAINTENANCE.md` に配置**。当初は MANIFEST を指定していたが、配置作業をする Claude にとってマスター前提の手順がノイズ／誤実行のもとになるため移した。20260807 ユーザー承認）
- [ ] `ls export/company/skills | wc -l` が 10 で文書と一致
- [ ] `export/company/tests/` の更新要否を判定し、不要ならその旨を decisions に1行、要なら scenario を現状に合わせる

## アプローチ

`main` merge を土台にする。10 スキルは main をベースにコピーするが `patterns.md` は持ち込まない。Angular / 非同梱名除去のあと、会社 `modified` パッチは三点マージで扱いを明示する。hooks は 6 本固定で main 追随し、会社 deny を残す。3 文書と settings コメントは同期後の実態だけを書く。検証は許可差分を除いた diff と禁止語 grep に落とす。

## 主要コンポーネント

| コンポーネント | 場所 | 責務（変更後） |
|---------------|------|----------------|
| merge | `export/company` ← `main` | 取り込み済み。残り衝突なし |
| スキル同期 | `export/company/skills/`（10） | main ベース。patterns.md 非コピー。Angular / 非同梱名除去。modified は三点マージ。source-commit 更新 |
| 変換レシピ | `export/company/MANIFEST.md` | 禁止語彙・禁止参照・禁止ファイル・会社パッチの扱い |
| hooks（6） | `claude-config/hooks/` | 名单固定。delete 含む。非同梱 hook を入れない |
| settings | `claude-config/settings.example.json` | delete 登録 + npx/install deny + コメント実態一致 |
| 3 文書 | `MANIFEST` / `HANDOVER` / `MIGRATION-GUIDE` | 実態一致。死んだ検査参照なし。例外同期を明記 |

## 未解決の論点

- [x] 会社 `modified` の停止契約強化 → **全て捨てて main 正に揃える**（20260807 決定）。`modified` 6 件を全文突合した結果、main に無い会社独自の停止契約テキストはゼロ。debug・rule-audit は main のほうが強い。`modified` 行を削除し `source-commit` のみ更新する
- [x] MANIFEST の独立フォーク方針 → **「原則独立フォーク＋停止契約は上流同期」**（20260807 決定）。機能構成・スタック語彙は会社側で独立して育てる。停止契約・手順の正本は master にあり、必要時に本文を再同期する
- [x] knowledge-capture の `@docs/knowledge/` 参照 → **プレーンパス表記へ main 追随**（20260807 決定）

---

<!-- design-doc-boundary: appendix -->

## プレモータム所見

（20260807・design-premortem。フレッシュ subagent 攻撃）

- 攻撃: main 全文同期＋Angular/非同梱名だけの再適用だと、会社 `modified` の停止契約強化が消える
  影響: 素通り対策が退行する
  提案 → **プレモータム反映済み**: 三点マージと「捨てる/残すを明示」を対象・完了条件・未解決に追加
  反論: main 正なら会社独自停止は捨ててよい、という判断もありうる → 未解決で人間が選ぶ

- 攻撃: ディレクトリ丸ごと同期で main の `tdd/references/patterns.md` が再流入する
  影響: Jasmine 本文と矛盾する React/Vitest 例が戻る。スキル数 10 では検知不能
  提案 → **プレモータム反映済み**: コピー禁止・不在を完了条件化

- 攻撃: 「hooks の main 追随」が許可リスト無し（除外 hook の再同梱 / 必要修正の取りこぼし）
  影響: settings・MANIFEST・実体の不一致
  提案 → **プレモータム反映済み**: 同梱 6 本固定、除外 3 本を対象外に明記

- 攻撃: 「実質一致」が機械検証不能。`check_export_stopcontract` は死んでいる
  影響: 目視で完了を詐称できる
  提案 → **プレモータム反映済み**: 許可差分を除いた diff + 禁止語 grep に分解。死んだ検査参照の除去を完了条件化

- 攻撃: 独立フォーク方針と本文同期が文書上矛盾。未解決が「なし」
  影響: 次セッションがどちらを正とするか割れる
  提案 → **プレモータム反映済み**: 方針書き換えを未解決に戻した

- 攻撃: 変換手順が人の記憶依存
  影響: 再同期で漏れが再発
  提案 → **プレモータム反映済み**: 変換レシピを MANIFEST に残すことを対象化

- 攻撃: delete hook の python3 フェイルオープンと settings「POSIX のみ・5本」が整合しない
  影響: ゲート無効に気づけない
  提案 → **プレモータム反映済み**: コメント更新・依存明記・欠如時挙動を完了条件化

- 攻撃: `export/company/tests/` と死んだ検査参照がスコープ外のまま
  影響: 文書の検証経路と完了定義が分岐
  提案 → **プレモータム反映済み**: 死んだ参照除去は必須、tests 更新要否判定は対象（実走は任意）

## データフロー

```
承認
  → main merge（未なら）
  → 10 スキル同期（patterns.md 除外）→ Angular / 非同梱名 → modified 三点マージ
  → hooks 6 本 / settings
  → 3 文書 + 変換レシピ + 例外同期方針
  → 許可差分除外の diff / 禁止語 grep
  → 承認後 commit / push
  → 会社配置は HANDOVER 別セッション
```

## 影響範囲

- システム / 外部連携: なし
- データ: なし
- 他チーム / 利用者: 会社が次に持ち込むスキルの停止契約・手順が main 相当（＋明示残した会社パッチ）になる
- リグレッション懸念: Angular 再適用漏れ、非同梱名残留、会社 deny 誤削除、会社 modified の黙殺、patterns.md 再流入、python3 欠如時の削除ゲート無効

## テスト方針

- Unit / Integration / E2E: 対象外
- 手動・機械: 許可差分を除いた main との diff、禁止語・非同梱名 grep、`patterns.md` 不在、hooks 6 本 ≡ 文書 ≡ settings、npx/install deny 残存、死んだスクリプト名 grep ゼロ
- passthrough 課金実走: 任意。scenario 更新要否は判定必須

## 検討した代替案

| 代替案 | 却下理由 |
|--------|----------|
| スキル本文は同期せず docs/hooks のみ | 会社に渡る振る舞いが古いまま。目的と矛盾 |
| 本文同期を会社デプロイ後に回す | 持ち込み前に揃えるのが本筋。却下 |
| ディレクトリ丸ごと機械上書き | patterns.md 再流入・会社 modified 黙殺。却下 |
| レビュー系・pr 系も同時同梱 | 会社プラグイン / MR カートリッジが別判断 |
| hooks を main 全本同梱 | stop-typecheck 等は会社方針で除外済み |

## 調査結果

- 現状: `export/company` に `main` merge `e05d020` 済み。working tree clean（プレモータム開始時）
- hooks は 5 本（delete 未同梱）
- 同梱 10: design-doc / design-premortem / steering / impl-from-design / tdd / knowledge-capture / compound / session-retrospective / rule-audit / debug
