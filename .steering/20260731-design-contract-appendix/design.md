# 設計: design-contract-appendix

Created: 20260731
Status: **APPROVED**
Approved: 20260731

## 目的

`design.md` が調査・プレモータム・代替案で肥大しても、実装入口・resume が毎回全文を読まないようにする。同一ファイルのまま「契約コア」と「付録」を区切り、読み契約（どのスキルがいつどこまで読むか）とテンプレ境界を動かし、セッションの context 税を減らす。

## スコープ

### 対象

- `design-doc` の `references/templates.md`（節順の入れ替え + 付録境界マーカー）
- `design-doc` / `impl-from-design` / `design-premortem` / `steering` の読み・書き契約（SKILL.md）
- 追加読み手の一文: `impl-review`（コアで足りる）/ `adr`・`impl-tournament`（付録を開く）/ `feature-pipeline`・`debug`・`frontend-code-review`（意図的スキップ明記）
- テンプレに境界マーカーがあることの機械検査（`scripts/validate_skills.py` = `pnpm run validate`）
- 境界無しの既存 `design.md` 向けフォールバック（マーカー欠落時は現行どおり全文扱い）
- `docs/user-guide.md` の resume 行に「契約コアまで」を一行同梱
- `BACKLOG.md` に「アクティブ design の境界追記は任意・強制しない」一行

### 対象外

- SPIKE / 探索実装レーン（BACKLOG の別候補）
- `design.md` の物理分割（`design-appendix.md` 等）
- 既存・アーカイブ済み `design.md` の一括移行・書き換え
- live `design.md` に境界が無いことの lint FAIL（本スライスではテンプレ側のみ機械化）
- 読み契約のフィクスチャ / passthrough による実効検証（BACKLOG の passthrough 拡充へ）
- 契約コアの行数・表サイズ上限ルール
- capture 粒度・ナレッジ鮮度・配置実走・passthrough 拡充
- company / export 追随
- `docs/knowledge/skill-design-patterns.md` の長文追記のみの変更（スキル契約が正本）
- `user-guide.md` の大改訂

## 制約

- 作業ブランチ: `feature/20260731-design-contract-appendix`（base = `integration/20260730-reports`）。親直コミットで機能変更しない
- PR のマージは人間の明示指示があるまでしない
- ADR 20260611（slim-steering: requirements を design に併合）を壊さない — **1 ファイル・承認ゲートは `design.md` 単体**
- 説明文だけ増やす修正は禁止（テンプレ境界・読み手順・機械検査のどれかを動かす）
- 片側修正禁止（テンプレを変えたら読み側スキルを同 PR で直す）
- 対象スキルはすべて**配布可**（starter-kit 最小 / 拡張 3）。master-only 参照を配布可に書かない
- 節名 `## 調査結果` / `## プレモータム所見` 等はスキルが参照するため、付録化しても **見出しレベルと文言は維持**（親見出しの下にネストしない）
- 検証コマンドの正本は **`pnpm run …`**（マスターは pnpm。`mise.toml` で node/pnpm を固定）
- 契約コアの行数上限は設けない（表が長いのはタスク分割の問題。YAGNI）
- Stack: Markdown スキル定義 / Python 検証スクリプト（このリポジトリ）

## 完了条件

- [ ] 新規 `design.md` テンプレで契約コアが連続し、付録境界マーカーの後に付録節が並ぶ
- [ ] `impl-from-design` / `steering` resume の既定読みが契約コアまでに明示され、**操作定義**（下記アプローチ）に従っている
- [ ] `design-doc` Phase 3 に、付録の `影響範囲` と `検討した代替案` を承認前必読とする契約がある
- [ ] `impl-from-design` が実装開始前に `影響範囲` を例外追加読みする（データフローは必要なときのみ）
- [ ] `design-premortem` が全文（コア+付録）を読むこと、および `## プレモータム所見` の作成位置（境界直後 / マーカー無しなら EOF）が明示されている
- [ ] 追加読み手（impl-review / adr / impl-tournament / feature-pipeline / debug / frontend-code-review）の扱いが一文で書かれている
- [ ] 境界マーカー欠落時のフォールバック（全文扱い）が各読み側に書かれている
- [ ] テンプレに境界マーカーが無いと `pnpm run validate`（`validate_skills.py`）が FAIL する
- [ ] `pnpm run validate` PASS。併せて既存の `pnpm run validate:assets` も回帰として PASS（境界検査の正本は前者）
- [ ] `user-guide.md` resume 行と BACKLOG の任意移行一行が同梱されている
- [ ] base = `integration/20260730-reports` の feature PR が作れる状態（マージはしない）

## アプローチ

同一 `design.md` 内で節順を入れ替え、契約コアをファイル先頭に連続配置する。コア末尾（`## 未解決の論点` の直後）に機械検出可能な境界マーカー `<!-- design-doc-boundary: appendix -->` を置き、それ以降を付録とする。読み側スキルに「既定はコアまで / 例外で付録の該当節 / プレモータムは全文 / マーカー無しは全文」を手順として書く。テンプレへのマーカー存在を `pnpm run validate` で機械検査し、説明文のみの変更で終わらせない。

**人間承認（Phase 3）**: 契約コアに加え、付録の `影響範囲` と `検討した代替案` を承認前必読とする（コアへは戻さない）。

**実装入口（impl-from-design）**: 既定はコア。実装開始前に `影響範囲` を例外追加読み。`## テスト方針` は TDD/非コード検証時、`## 調査結果` は追記時、`## データフロー` は必要なときだけ。

**境界の操作定義（プレモータム反映）**: ツールがファイル全文を返しても、既定読みの必須入力は境界コメントより前の見出しに限定する。可能なら `Read` の `limit` で境界行まで取得する。必須入力をコアに限定したあと付録を推論に使ってはならない（例外読みで開いた節だけ追加可）。プレモータムは例外で全文必須。

**`## プレモータム所見` の作成位置（プレモータム反映）**: 節が無ければ **境界マーカーの直後（付録先頭）** に作成する。マーカーが無い旧ファイルでは EOF に追記する。境界より前（コア）へ挿入しない。

## 主要コンポーネント

| コンポーネント | 場所 | 変更後の記述・契約（原本なしで判定できる粒度） |
|---------------|------|------|
| design.md テンプレ | `.claude/skills/design-doc/references/templates.md` | 節順をコア連続に変更。`## 未解決の論点` の直後に `<!-- design-doc-boundary: appendix -->` と短い付録説明（blockquote 1 つ）を挿入。付録側の `##` 見出し名は現状維持 |
| design-doc 本文 | `.claude/skills/design-doc/SKILL.md` | Phase 2 のセクション列挙を新順に合わせる。生成時に境界を必ず入れる。Phase 3 で影響範囲・検討した代替案を承認前必読。セッション継続は既定コアまで。方針転換の追記先（肥大しうる調査・代替は付録側）を一文で明示 |
| impl-from-design | `.claude/skills/impl-from-design/SKILL.md` | 既定コア読み。実装開始前に `影響範囲` を例外追加。テスト方針・調査結果・データフローは上記アプローチどおり。マーカー無しは全文 |
| design-premortem | `.claude/skills/design-premortem/SKILL.md` | subagent / 自走とも **常に全文**。所見は `## プレモータム所見`（無ければ境界直後に作成、マーカー無しなら EOF） |
| steering | `.claude/skills/steering/SKILL.md` | resume の要約用読みを契約コアまでに限定（操作定義どおり）。マーカー無しは全文。構造説明をコア/付録に合わせて更新 |
| impl-review | `.claude/skills/impl-review/SKILL.md` | design 整合は契約コア読みで足りる旨を一文 |
| adr / impl-tournament | 各 SKILL.md | 代替案・テスト方針等の付録節を開く旨を一文 |
| feature-pipeline / debug / frontend-code-review | 各 SKILL.md | 境界読み対象外（Status / 調査結果追記 / 参照のみ）を意図的スキップとして一文 |
| 機械検査 | `scripts/validate_skills.py`（`pnpm run validate`） | テンプレに `design-doc-boundary: appendix` が無いと FAIL。live design.md は対象外 |
| user-guide | `docs/user-guide.md` | resume の説明に「契約コアまで」を一行 |
| BACKLOG | `.steering/BACKLOG.md` | アクティブ design の境界追記は任意・強制しない、を一行（二重契約の収束は強制しない） |

実装前の確定手順: 変更対象語で全文検索し、表の漏れと「同 PR で直す / 意図的スキップ」を潰す — `design.md` を読む / `## 調査結果` / `## 未解決の論点` / `templates.md` / `プレモータム所見` / `主要コンポーネント` / `検討した代替案`。

## 未解決の論点

（承認時にすべて確定。残なし）

- [x] 承認ゲート: 付録のまま、Phase 3 で影響範囲・検討した代替案を必読
- [x] impl-from-design: 実装開始前に影響範囲を例外追加（データフローは都度）
- [x] 追加読み手: 一文パッチ（上記主要コンポーネント）
- [x] 二重契約: フォールバック維持 + BACKLOG 一行
- [x] コア上限: YAGNI（制約に明記）
- [x] 機械検査: `validate_skills.py` / `pnpm run validate`
- [x] user-guide: 一行同梱
- [x] 実効検証: 本スライス対象外（手順＋テンプレ検査で完了）

---

<!-- design-doc-boundary: appendix -->

> **付録** — 実装入口・resume の既定では読まない。プレモータム・TDD 突入・乖離調査など、当該節が必要なときだけ読む。

## データフロー

```
design-doc Phase 2
  → templates.md から design.md 生成（コア連続 + 境界 + 付録節）
  → 人間レビュー（コア + 承認前必読: 影響範囲・検討した代替案）
  → APPROVED

impl-from-design / steering resume
  → 境界まで読む（マーカー無しなら全文）
  → 実装開始前に影響範囲を例外追加。他の付録は都度

design-premortem
  → 常に全文 → ## プレモータム所見 に追記（付録）
```

## 影響範囲

- システム / 外部連携: なし
- データ: 新規 `.steering/*/design.md` の節順が変わる。既存ファイルは未移行のまま（フォールバック）
- 他チーム / 利用者: 配置先へ再コピー後、配布可スキルの読み方が変わる。配置済みプロジェクトは harvest/再コピーまで旧挙動
- リグレッション懸念: コアから付録へ移した節を既定で読まなくなり、テスト方針やデータフローを見落として実装がずれる — 例外読みの列挙漏れが主なリスク。プレモータムがコアのみになると攻撃が浅くなる — 全文契約で防ぐ

## テスト方針

- Unit: なし（アプリコード無し）
- Integration: `pnpm run validate`（`validate_skills.py`）でテンプレ境界マーカー欠落を検出できること（マーカー削除の一時改変またはフィクスチャで確認し、戻す）
- E2E: なし。手確認は「一回限り」と明記: 新規 design.md 生成イメージがコア→境界→付録の順であること
- リポジトリ検査: `pnpm run validate` PASS。回帰として `pnpm run validate:assets` も PASS（境界の正本検査ではない）

## 検討した代替案

| 代替案 | 却下理由 |
|--------|----------|
| B: `design.md` + `design-appendix.md` 物理分割 | ADR 20260611 の 1 ファイル承認ゲートと衝突。参照の手間が戻る（slim-steering の再発） |
| C: テンプレ変更なしで「節を選べ」と書くだけ | 契約・機械が動かず、説明文増のみ禁止に抵触。肥大そのものは残る |
| 契約コアから主要コンポーネントを外す | `impl-from-design` が実装スコープ表を毎回付録読みすることになり税が戻る |
| テスト方針を契約コアに含める | コアが再び厚くなる。TDD 突入時の例外読みで足りる |
| SPIKE レーンを同梱 | 別のゲート例外。レビュー軸が広がる。BACKLOG で分離済み |
| live design.md に境界必須の lint | 既存アクティブ/アーカイブを一括改修するか FAIL だらけになる。本スライスの最小から外す |

## 調査結果

- 一次根拠: `.tmp/20260730-personal-friction-report.md` 指摘 3（design 肥大 → context 税）。体感優先度で SPIKE より上
- ADR `docs/decisions/20260611-slim-steering-artifacts.md`: requirements 分離は参照手間が増えるだけとして併合。本設計は物理再分離せず読み契約で税を下げる
- 現行テンプレ節順（`templates.md`）: 目的→スコープ→制約→完了条件→アプローチ→主要コンポーネント→データフロー→影響範囲→テスト方針→未解決の論点→検討した代替案→調査結果。**未解決の論点が付録候補の後ろにあり、コア連続化には並べ替えが必須**
- `impl-from-design` は Status・主要コンポーネント・調査結果追記・テスト方針（非コード時）に依存
- `design-premortem` は design.md を subagent に渡して攻撃し `## プレモータム所見` に追記
- 配布分類（starter-kit）: design-doc / impl-from-design / steering / design-premortem はすべて配布可
- `package.json`: `validate` = `validate_skills.py`、`validate:assets` = `check_asset_consistency.py`（別物。プレモータムで完了条件の取り違えを検出）

### 既存パターン調査（20260731）

- スキル契約変更: SKILL.md + 必要なら references。version を上げる慣例あり
- 機械検査: `validate_skills.py` の `validate()` と `main()` の既定走査にチェックを足すのが既存パターン（asset 契約とは分離）
- 注意点: 配布可スキル本文にマスター日付エピソードを増やさない。境界マーカー文字列はテンプレと validator で同一リテラル

## プレモータム所見

Status: RESOLVED（2026-07-31・承認時に未解決論点を確定）

- 攻撃: 承認が「主にコア」だと影響範囲・代替案がゲートから落ちる
  影響: APPROVED の密度低下。形だけの 1 ファイル承認
  提案: 影響範囲/代替をコアへ戻すか、承認前必読契約にする → **未解決の論点へ。推奨は承認前必読**
  反論: コアに全部戻すと肥大対策が空洞化する

- 攻撃: impl-from-design 例外読みがテスト方針/調査結果のみで、データフロー・影響範囲の見落としを自ら警告しているのに契約化していない
  影響: スコープ表だけ合って流れがズレる
  提案: 例外追加またはコア復帰 → **未解決の論点へ**

- 攻撃: HTML コメント境界だけでは Read が全文をコンテキストに載せ、税削減が幻想になりうる
  影響: 手順分岐だけ増え目的未達
  提案: 操作定義（limit / 必須入力の限定）を書く → **プレモータム反映済み**（アプローチに操作定義を追記）

- 攻撃: 完了条件の `validate:assets` と検査置き場 `validate_skills.py` が別コマンド
  影響: 境界チェックを足しても完了条件コマンドでは検知されない
  提案: 正コマンドを一致 → **プレモータム反映済み**（完了条件・テスト方針・機械検査行を `pnpm run validate` に統一。承認時に npm→pnpm も確定）

- 攻撃: 更新対象スキル表が狭く、impl-review / impl-tournament / adr 等が片側修正になりうる
  影響: 配布後の沈黙リグレッション
  提案: 検索ヒットの必修正/スキップを未解決に → **プレモータム反映済み**（検索候補列挙＋未解決論点）

- 攻撃: 境界無し live design を永久全文扱いにすると二系統契約が残る
  影響: 3ヶ月後に分岐コストが税削減を上回る
  提案: 収束策を BACKLOG か受け入れ文に → **未解決の論点へ**

- 攻撃: `## プレモータム所見` の作成位置が未定義で、コア側に挿入されうる
  影響: 境界契約の自己破壊・コア再肥大
  提案: 境界直後 / マーカー無し EOF に固定 → **プレモータム反映済み**

- 攻撃: 完了条件が「SKILL に書いてある」止まりで読み打切りの実効を検証しない
  影響: 説明追加だけで目的未達のままマージ可能
  提案: フィクスチャ検証か目的の引き下げ → **未解決の論点へ**（本スライスは手順＋テンプレ検査を推奨）

- 攻撃: 主要コンポーネント表に上限がなくコアが再肥大する
  影響: 付録化の効果が薄れ、再設計議論が再燃する
  提案: 上限ルールか YAGNI 受け入れ → **未解決の論点へ**
