# 設計: pr13-mustfix

Created: 20260807
Status: **APPROVED**
Approved: 20260807

## 目的

draft PR #13（`integration/20260730-reports` → main）の二次レビューで確定した must-fix 5 件（M1〜M5）を、親ブランチ上の feature PR として修正する。一次レビューの「無条件マージ可」は二次レビューで覆っており、これらを塞がない限り親 PR を ready / マージしてはならない。

## スコープ

### 対象

- **M1** `guard-gated-delete.sh`: 複数行 command / 行継続 `\` / 先頭改行ですり抜ける穴を塞ぐ（改行区切りの各単純コマンドをループ判定。案 A・決定済み）。**最初の deny で即終了**（stdout は常に単一 JSON または空）
- **M2** 同 hook: グロブ隣接オペランドのすり抜けを、対象パスの **AFTER 境界クラスに `*?[{` のみ追加**して塞ぐ（`.` は入れない — B20 維持）
- **M3** `tests/hooks/run_fixtures.py`: `decision_from_stdout` が壊れた JSON を部分一致で `deny` にする偽 PASS を廃止し、`unparseable:` に倒す。回帰は runner 内自己テストで固定
- **M4** README の契約列挙・npm script 一覧の片側修正を訂正し、`check_asset_consistency.py` に突合契約を追加（抽出法は下記制約）
- **M5** `frontend-code-review` の「次のステップ」を知見保存→デプロイ順に直し、節リストを templates.md の 6 節に揃える。`skill-design-patterns.md` も同時修正。`validate_skills.py` にキー共存 + **FCR 本文内の出現位置比較**（知見保存キーがデプロイキーより前）を 1 群追加
- **nit（同梱・承認済み）**: 腐った行数表記の削除、`validate-skill-edit.sh` の死んだ現在形コメント、README ディレクトリ構成への `tests/hooks/run_fixtures.py` / `mise.toml` 追記
- **脅威モデル文書同期（同梱・承認済み）**: README / `docs/starter-kit.md` の「複合シェル＝沈黙」を、`&& || ; |` に限定し改行区切りは守る形と明記（hook ヘッダと同一コミット）
- 修正後: 親へマージする feature PR の作成、PR #13 本文（Test plan の員数）の更新

### 対象外

- **D1** 親ディレクトリ・等価パス表記（`rm -r docs` / `docs/./knowledge/…` 等）— ユーザー決定で今回対象外。脅威モデル拡張に近い
- **D2〜D5** および BACKLOG 節 1(c)(d) / Gate 1 課金実走 — 判断待ち・別タスク
- `passthrough_check.py:153` の削除非検出（差分外）
- 行継続の bash 完全忠実（引用符内 `\⏎`・`\`+空白+改行・行末 `\\`+改行）— 単純 `\\\n`（CRLF は先に `\r\n`→`\n`）で足りるとして受容。過検知/すり抜けは脅威モデル外として記録
- PR #13 の ready 化・マージ（人間の明示があるまで禁止）
- `main` 直修正
- `export/` `company/`（Frozen）
- 配置先への再コピー（`guard-gated-delete` は skill-test 未配置のため今回義務なし）

## 制約

- ブランチ: `integration/20260730-reports`（HEAD `f10b5d0`）から `feature/20260807-…` を切る。base は親。`main` 禁止
- 片側修正禁止 / 説明文だけ増やす修正は禁止（機械検査・構造で担保）
- スキル・hook に絵文字を書かない
- 検証正本: `mise exec -- pnpm run validate:assets` / `validate` / `test:hooks`
- 用語正本: フルモード＝7 エージェント
- M1: ループ対象は**改行区切りのみ**（`&&` / `||` / `;` / `|` は現行どおり切り捨て＝B11・B19 沈黙維持）。ヒットしたら deny JSON を **1 回だけ**出して終了
- M1 行継続: 入力を `\r\n`→`\n` 正規化のあと、リテラル `\`+改行を空白 1 個に置換。引用符・空白付き継続は見ない
- M2: AFTER に追加する文字は `*?[{` のみ（BEFORE は現行維持）。`.` を境界に入れない
- M4 抽出（設計固定）: (i) 実装側 = `check_asset_consistency.py` の `def contract_([a-z])` 集合 (ii) README 側 = 「資産どうしの契約突合」箇条内の `(a)`〜`(z)` マーカー集合 (iii) npm = `package.json` の `scripts` キー集合 ≡ 同 README「npm script」箇条内のバッククォート名集合。員数の数字は本文から消し、差分は FAIL 詳細に出す
- M5 検査キー（設計固定）: FCR「次のステップ」付近に `知見保存`（または `knowledge-capture`）と `デプロイ`（または `pr-create`）が共存し、前者の最初の出現が後者より前。節リスト文言は FCR と `skill-design-patterns.md` の両方に `実装` / `レビュー` / `知見保存` / `デプロイ` / `福利化` / `クローズ` が共存
- 配布分類（変更対象ごと）:
  | 対象 | 分類 |
  |---|---|
  | `guard-gated-delete.sh` | 同送 hook（`MASTER_ONLY_HOOKS` 外） |
  | `frontend-code-review` | **配布可** — master-only スキル名やマスター専用パスを混ぜない |
  | `skill-design-patterns.md` / README / `check_asset_consistency.py` / `validate_skills.py` / `run_fixtures.py` | マスター資産 |

## 完了条件

- [ ] M1 deny（stdout 単一 JSON）: `rm -f docs/knowledge/x.md\nls` / `rm -f \\\n  docs/knowledge/x.md` / `\nrm -f docs/knowledge/x.md` / `ls\nrm -f docs/knowledge/x.md` / 2 行とも対象（例: `rm CLAUDE.md\nrm docs/knowledge/x.md`）
- [ ] M1 沈黙: 改行区切りで両方無関係（例: `ls\necho hi`）。B11・B19 不変
- [ ] M2 deny: `rm -f CLAUDE.md*` / `rm -rf docs/knowledge*` / `mv docs/knowledge{,.bak}`
- [ ] M2 沈黙: B20 `rm CLAUDE.md.bak` / 無関係 `rm -f docs/knowledge-archive-old*`
- [ ] M3: 壊れ JSON 3 種以上 → `unparseable:`。自己テスト固定。既存フィクスチャ緑
- [ ] M4: 上記抽出法で集合一致。片側欠落を意図的に入れて FAIL することを実装時に一回確認（または契約テスト）
- [ ] M5: FCR 次ステップが知見保存→デプロイ順（位置比較緑）。FCR・skill-design-patterns の節リスト 6 語共存緑
- [ ] `mise exec -- pnpm run validate:assets` / `validate` / `test:hooks` が緑（員数は検査追加後の N/N）
- [ ] feature PR（base=親）作成・親へマージ可能な状態。PR #13 Test plan の員数更新。ready/マージはしない
- [ ] hook 修正後の人間確認手順を `decisions.md` に残す（再起動後・AI からは観測不可）

## アプローチ

親から feature ブランチを切り、M1→M2（同一 hook）→フィクスチャ → M3 → M4 契約+README → M5 文書+キー共存/位置比較 → nit の順で直す。M1 は「CRLF 正規化 → 行継続畳み → 改行分割 → 各単純コマンドを判定 → **deny で break**」の順を守り、ヘッダの「守る形 / 守らない形」を同一コミットで挙動に合わせる（改行区切り複数コマンドは守る形側）。再発防止は文章ではなく `check_asset_consistency` / `validate_skills` / runner 自己テストに置く。

## 主要コンポーネント

| コンポーネント | 場所 | 責務 |
|---------------|------|------|
| delete guard | `.claude/hooks/guard-gated-delete.sh` | M1/M2・ヘッダ宣言更新 |
| hook fixtures | `tests/hooks/run_fixtures.py` | M3 判定修正 + 自己テスト + M1/M2 ケース追加 |
| asset contracts | `scripts/check_asset_consistency.py` | M4 新契約（README↔実装） |
| skill validate | `scripts/validate_skills.py` | M5 キー共存検査 1 群 |
| FCR 導線 | `.claude/skills/frontend-code-review/SKILL.md` | 次ステップ順序・節リスト |
| パターン文書 | `docs/knowledge/skill-design-patterns.md` | 節リスト同期・腐った行数削除 |
| 索引 | `README.md` | 契約列挙・npm scripts・ディレクトリ構成・複合シェル文言 |
| 配置手順 | `docs/starter-kit.md` | 複合シェル文言を hook ヘッダと同期 |

## 未解決の論点

- なし（20260807 承認時に nit・脅威モデル文書同期を対象へ取り込み済み）

---

<!-- design-doc-boundary: appendix -->

## プレモータム所見（design-premortem · 20260807）

フレッシュレビュー（[adversarial](b8badd41-8694-41b0-a750-af64b0846205)、会話履歴バイアスなし）。リポジトリ実測で裏取り済み。**承認しない。**

- 攻撃: M1 ループが複数 deny JSON を出すと、M3 後に正当 deny が `unparseable:` FAIL
  影響: M1 フィクスチャと M3 が同時に緑にならない
  提案: deny 1 回で即終了をデータフローに固定
  **プレモータム反映済み**: 対象・制約・完了条件・データフローに「単一 JSON / deny で break」と 2 行とも対象ケースを追加

- 攻撃: M2 境界文字集合が未定義 → B20 誤 deny のリスク
  影響: 「M2 deny」と「B20 沈黙」が実装解釈で衝突
  提案: AFTER に `*?[{` のみ、具体コマンドを完了条件へ
  **プレモータム反映済み**: 制約・完了条件に固定

- 攻撃: M5「順」をキー共存だけでは検証できない（空文・旧順で緑）
  影響: 導線バグの再発形が機械検査をすり抜ける
  提案: 出現位置比較 or 「順」を人間必須に書き分け
  **プレモータム反映済み**: 位置比較 + 検査キー列挙を制約・完了条件へ（空文限界は既存群と同型で残るが「順」は見る）

- 攻撃: 行継続の bash 意味論（引用符・空白付き・`\\`・CRLF）が未規定
  影響: 実装ばらつき・過検知/すり抜け
  提案: 単純置換+受容範囲を明示
  **プレモータム反映済み**: 単純 `\\\n` + CRLF 正規化を制約へ。bash 完全忠実は対象外

- 攻撃: M4 の README レター抽出法が無い（脆い散文パース）
  影響: 3 ヶ月後にまた片側修正 / 偽 FAIL
  提案: 抽出正規表現または錨を設計に固定
  **プレモータム反映済み**: `contract_([a-z])` / 箇条内 `(a)` / scripts↔バッククォート を制約に固定。員数数字は本文から消す

- 攻撃: README / starter-kit の「複合シェル＝沈黙」が改行区切り deny 後に甘くなる
  影響: 運用者の誤信・配置先摩擦
  提案: 文言修正を対象に含めるか BACKLOG
  **承認で同梱確定**（20260807）: README / starter-kit を hook ヘッダと同一コミットで同期

- 攻撃: 未解決が nit 1 件だけで実装解釈の論点が落ちていた
  影響: Phase 3 で論点漏れ
  提案: 増補または制約へ落とす
  **プレモータム反映済み**: 決定可能なものは制約へ。残り 2 件を未解決に残す

- 攻撃: 再現コマンドが完了条件に無く付録依存
  影響: 別の「再現」で緑になり指摘正本とずれる
  提案: 完了条件にインライン固定
  **プレモータム反映済み**: 完了条件にコマンドを列挙

---

> **付録** — 実装入口・resume の既定では読まない。プレモータム・TDD 突入・乖離調査など、当該節が必要なときだけ読む。人間の Phase 3 承認前は `影響範囲` と `検討した代替案` を必読。

## データフロー

```
Bash PreToolUse payload
  → python3 で tool_input.command 抽出
  → \r\n → \n 正規化
  → リテラル \ + 改行を空白 1 個に畳む（引用符は見ない）
  → 改行で分割し各行を単純コマンド化（&&||;|# 切り捨ては現行どおり）
  → 各行: 先頭トークンが rm|mv かつ対象パス（AFTER 境界に *?[{ 含む）
       → deny JSON を 1 回出力して即終了（複数行ヒットでも stdout は単一 JSON）
  → いずれも非該当 → 沈黙（stdout 空）

run_fixtures:
  hook stdout → json.loads 成功なら permissionDecision
              → JSONDecodeError なら unparseable:…（FAIL）
  + 起動時自己テスト（壊れ文字列 → sentinel）
```

## 影響範囲

- システム / 外部連携: なし（ローカル hook・検証スクリプト）
- データ: なし
- 他チーム / 利用者: 同送 hook の挙動が厳格化（改行区切りの複数コマンド・グロブ隣接が新たに deny）。配置先 skill-test は未配置のため即時影響なし。配布可の FCR 本文が変わる
- リグレッション懸念: B11/B19/B20 の沈黙維持。`&&` 連鎖を誤って対象化しないこと。README 員数の数字ハードコードを消せるなら消す

## テスト方針

- Unit: `decision_from_stdout` 自己テスト（壊れ JSON 3 種以上 → unparseable）
- Integration: `mise exec -- pnpm run test:hooks`（既存 + M1/M2 最低 5 件）
- 静的: `validate:assets` / `validate`（新契約・キー共存含む）
- E2E: なし。hook 実発火は人間が Claude Code 再起動後に確認
- 一回限りでない検証はすべて上記機械検査に入れる

## 検討した代替案

| 代替案 | 却下理由 |
|--------|----------|
| M1 案 B（先頭 1 コマンドのみ見る） | ユーザー決定で却下。`ls`⏎`rm …` が残る。複数行 command が普通に来るのが穴の本質 |
| M1 で `&&`/`||`/`;` もループ対象化 | ヘッダ「守らない形」の書き換え＝脅威モデル再定義。D 系・別タスク |
| M3 を別ファイルの単体テストに分離 | 今回は runner 内自己テストで十分。同関数を直接叩ける |
| D1 を M1/M2 と同梱 | ユーザー決定で対象外 |
| M4 を README 文章だけ直す | 「説明文だけ増やす修正は禁止」。突合契約が再発防止 |
| 行継続を bash 完全忠実にパース | 善意エージェント脅威モデルに対して YAGNI。単純置換+受容を選択 |

## 調査結果

修正前実測（20260807・親 `f10b5d0`）:

- M1: 複数行 / 行継続 / 先頭改行 → すべて SILENT（ベースライン単行 `rm -f docs/knowledge/x.md` は DENY）
- M2: `CLAUDE.md*` / `docs/knowledge*` / `mv docs/knowledge{,.bak}` → すべて SILENT
- M3: reason 内未エスケープ `"` / 前置ノイズ行 / 途中切れ JSON → いずれも `decision_from_stdout` が `'deny'`

指摘の正本: https://github.com/angedessin/skills/pull/13#issuecomment-5206989448  
引き継ぎ: `.tmp/20260807-handoff-fix-pr13-findings.md`

### 既存パターン調査（20260807）

- hook フィクスチャ: `tests/hooks/run_fixtures.py` に CASES インライン。expect は deny/ask/silence
- 資産契約: `check_asset_consistency.py` の `contract_*` + main の tuples。終了コード 0/1/2
- キー共存: `validate_skills.py` の DESIGN_IMPL_SYNC / CAPTURE / KNOWLEDGE_FRESHNESS。空文限界はモジュール先頭に明記
- FCR 次ステップ: 配布可スキル。master-only パスを混ぜない
- 注意点: README 契約箇条に旧契約レターを `(x)` 形で残すと契約 (k) が偽 FAIL する。npm 箇条のバッククォートは script 名のみ
