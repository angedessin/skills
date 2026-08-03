# 設計: capture-granularity

Created: 20260803
Status: **APPROVED**
Approved: 20260803

## 目的

`.capture-needed` に潰れている「セッションに知見がありうる催促」と「タスク完了時の capture 義務」を意味分離し、途中タスクでの確認ノイズを下げつつ、偽陰性（知見喪失）を増やさない。

## スコープ

### 対象
- セッション催促の確認 UX を「今 / 後で / スキップ」に変更し、各選択の操作定義を読み手に書く
- `steering` archive 直前を完了ゲートの唯一の硬い発火点にし、knowledge-capture 未了なら停止する
- 上記に必要な hooks・CLAUDE.md・steering / knowledge-capture・starter-kit 等の契約・手順・機械検査の同期

### 対象外
- capture を「完了時のみ」に単純化（偽陰性増・レポート明示のやらなくてよい縮退）
- フラグ 2 種への分割（決定インタビューで却下）
- `capture_done` 生涯フラグの廃止（途中 capture は現行どおり `capture_done` を立て、archive ゲートを満たす）
- **途中「今」後の再催促** — `capture_done` 後は Stop が立て直さない既存トレードオフを維持（偽陰性許容。本タスクでは触らない）
- `feature-pipeline` 本文 — archive ハードストップは `steering` に委譲。パイプラインは Phase 5 で steering を呼ぶだけ（復帰文言を pipeline に複製しない）
- ナレッジ鮮度の機械化・配置実走・passthrough 拡充・design.md 境界の任意追記（BACKLOG 節 4 の別項）
- company / export 追随

## 制約

- 親ブランチ: `integration/20260730-reports`。本変更は `feature/20260803-capture-granularity` から親への PR（base = 親）。**PR マージは人間の明示指示があるまでしない**
- 説明文だけ増やす修正は禁止（契約・手順・機械検査のどれかを動かす）
- 片側修正禁止: 確認文言・スキップ操作・archive ゲートは、書く側（hook）と読む側（CLAUDE.md / skills / starter-kit / user-guide）を同一コミットで揃える
- 偽陰性を増やさない（Stop 側）: `session-stop.sh` の現行フェイルセーフ（作りたてスキップの AND、`capture_done` 未了なら立てる）は維持。**スキップ後の再立ては意図どおり**（スキップ≠永久免除）
- 既知の残トレードオフ: 途中「今」→`capture_done` 後はセッション催促が止まる（偽陰性許容・対象外）
- 新ランタイムフラグを増やさない（`.gitignore` の 3 種のまま）
- 検証の正本は `pnpm run …`
- company / export は Frozen

## 完了条件

- [ ] SessionStart 注入文と CLAUDE.md / starter-kit / user-guide の確認が「今 / 後で / スキップ」で一致する
- [ ] **スキップの実行主体**: SessionStart 確認でのスキップは **hook 注入文の操作定義に従い** `.capture-needed` を `rm` する（knowledge-capture 未起動でよい。CLAUDE.md 再掲は任意）。スキル内三択はフラグ起点起動時の同契約再掲
- [ ] 「スキップ」は `.capture-needed` のみ削除し `capture_done` を立てない。**効果範囲＝次の Stop まで**（Stop フェイルセーフが再立てする。跨セッションの永久スキップではない）
- [ ] 「後で」はフラグ残置のみ（何も消さない）。compact/resume 再注入で再確認してよい（フラグが残っている限り）
- [ ] 「今」は `knowledge-capture` 起動。完了時は現行どおり `capture_done` を立てる
- [ ] `steering` archive は `capture_done` または「知見なしでアーカイブ」が無いとき **停止**する。汎用「省略してアーカイブ」および tasklist `[x]` 単独では非充足
- [ ] 複数 `.capture-needed` は**タスク単位**で三択（一括スキップ禁止）
- [ ] 三択は `.codify-needed` 確認より**先**。スキップしても compound 確認は別フラグとして残す
- [ ] `session-stop.sh` の立て方無回帰をフィクスチャで確認: (1) 作りたてスキップ (2) `capture_done` 時スキップ (3) **スキップ後（フラグ無し・`capture_done` 無し）に再立て**
- [ ] 変更対象の全文検索洗い出しが tasklist 先頭手順どおり完了し、漏れが主要コンポーネント表に反映済み
- [ ] `pnpm run validate`（capture-granularity キー共存検査を含む）が通る
- [ ] BACKLOG 節 4 の「capture 粒度」行が削除済み（本 design に移済み）

## アプローチ

フラグは `.capture-needed` 1 種のままにする。セッション側は確認を三択にして意味を分離し、完了側は `steering` archive を唯一の硬いゲートにする。途中の knowledge-capture は現行どおり `capture_done` を立てて archive を満たす。「スキップ」は**いま出ている催促の解除**だけに閉じ（次 Stop でフェイルセーフが再立て）、完了義務の免除には使わない。SessionStart の操作定義は **`session-start-check.sh` の注入文**（CLAUDE.md 再掲は任意）。archive 充足は `capture_done` または「知見なしでアーカイブ」のみ。

## 主要コンポーネント

| コンポーネント | 場所 | 変更後の記述・契約（原本なしで判定できる粒度） |
|---------------|------|------|
| SessionStart hook | `.claude/hooks/session-start-check.sh` | `.capture-needed` 検出時の注入文を「今 / 後で / スキップ」三択確認に変更。**SessionStart の操作定義はこの注入文**。文言に三択が含まれる。複数タスクは列挙し、単位はタスクごと |
| セッション開始ルール | `CLAUDE.md` | 三択確認の**任意再掲**（配置先で CLAUDE.md が無くても hook だけで足りる）。タスク単位。スキップ＝対象の `.capture-needed` を `rm`（`capture_done` 非作成）／後で＝残置／今＝knowledge-capture。スキップ効果＝次 Stop まで |
| knowledge-capture | `.claude/skills/knowledge-capture/SKILL.md` | フラグ起点時は三択を `.codify-needed` より先に。スキップは `.capture-needed` のみ削除。SessionStart の操作定義は hook 注入文と同一契約 |
| steering archive | `.claude/skills/steering/SKILL.md` | knowledge-capture **ハードストップ**。充足: `capture_done` または「知見なしでアーカイブ」。汎用省略・`[x]` 単独は非充足 |
| steering spec | `.claude/skills/steering/references/spec.md` | フラグ意味・セッション確認・archive 前チェックを SKILL と同一契約に更新 |
| starter-kit | `docs/starter-kit.md` | SessionStart 時の確認文言を三択に同期 |
| user-guide | `docs/user-guide.md` | フラグ／セッション開始確認を三択・スキップ寿命に同期 |
| README | `README.md` | Stop/SessionStart を三択・archive ゲート・スキップ＝次 Stop までに合わせて現行形へ |
| BACKLOG | `.steering/BACKLOG.md` | 節 4「capture 粒度」行を削除（本タスクへ移したため） |
| 機械検査 | `scripts/validate_skills.py` | 三択文言と archive ハードストップ目印の書く側・読む側共存。空文限界はコメント明記 |

## 未解決の論点

（承認時に推奨で確定。実装の正本は完了条件・主要コンポーネント）

- [x] 知見専用省略句 = 「知見なしでアーカイブ」
- [x] archive 充足 = (A) `capture_done` または専用句のみ（`[x]` 単独不可）
- [x] 複数フラグ = タスク単位。一括スキップ禁止
- [x] validate キー共存 = 入れる
- [x] 三択と `.codify-needed` = 三択を先。スキップしても compound 確認は残す

---

<!-- design-doc-boundary: appendix -->

## プレモータム所見（design-premortem）

実施: 20260803。会話経緯バイアスなし。リポジトリ裏取り済み（`session-stop.sh` / `session-start-check.sh` / `steering` archive / `knowledge-capture` Step1・6 / `feature-pipeline` Phase4–5 / `CLAUDE.md` セッション開始）。

- 攻撃: [1][2] 「スキップ」の寿命が契約に無い。`session-stop.sh` はフラグも `capture_done` も無いと再 `touch` する
  影響: 「スキップしたのにまた出てくる」がバグに見える。跨セッションの永久スキップと誤解される
  提案: 効果範囲＝次 Stop までを完了条件・CLAUDE.md に固定
  **プレモータム反映済み**: 完了条件・アプローチ・制約・CLAUDE.md 行に「次 Stop まで」を明記

- 攻撃: [1][4] スキップ実行主体が CLAUDE.md と knowledge-capture で二重
  影響: 口頭スキップでファイル残留、または手順食い違い
  提案: SessionStart 経路の正本を CLAUDE.md（`rm` まで）に単一化
  **プレモータム反映済み**: 完了条件・主要コンポーネント表で正本を CLAUDE.md に固定（PR #9 で hook 注入文へ変更 — decisions 参照）

- 攻撃: [2][5] archive 充足に tasklist `[x]` 単独が残り、ハードゲートが形骸化しうる
  影響: 汎用省略を塞いでも手動チェックで抜けられる
  提案: (A)/(B)/(C) を未解決論点化
  **プレモータム反映済み（論点化）**: 未解決の論点へ移動。充足条件の最終形は承認待ち

- 攻撃: [4][1] `feature-pipeline` Phase 5 が表にも対象外にも無い
  影響: パイプライン中の archive 停止で旧省略癖またはクローズ不能
  提案: 対象に復帰段落を入れるか、対象外に「steering 委譲」を明示
  **プレモータム反映済み**: 対象外に「pipeline 本文不触・steering 委譲」を明示

- 攻撃: [3] 完了条件の機械検証が弱い。session-stop「意味不変」に差分定義が無い
  影響: 文言差し替えだけで完了した気になれる
  提案: stop フィクスチャ 3 ケースを完了条件に必須化
  **プレモータム反映済み**: 完了条件に作りたて / `capture_done` / スキップ後再立てを必須化

- 攻撃: [5][2] 途中「今」→`capture_done` 生涯沈黙の偽陰性が名指し不足
  影響: 長期タスク後半の知見喪失が再燃
  提案: 既知トレードオフとして制約／対象外へ昇格
  **プレモータム反映済み**: 対象外・制約に「途中 capture 後は再催促しない（偽陰性許容）」を明記

- 攻撃: [1][6] 複数 `.capture-needed` 時の三択単位が未定義
  影響: 一括削除／一括起動に倒れる
  提案: 未解決論点に追加（推奨: タスク単位・一括スキップ禁止）
  （人間判断）未解決の論点へ追加済み

- 攻撃: [6][1] compact 再注入×「後で」、および `.codify-needed` 併存時の三択順序
  影響: compact のたびノイズ／福利化順序破壊
  提案: 「後で」+compact は再確認可と完了条件化。codify 順序は未解決へ
  **一部反映済み**: 「後で」+compact 再確認可を完了条件へ。codify 順序は未解決の論点

- 攻撃: [4] user-guide 等が表から落ち、片側修正ドリフト
  影響: 文言同期漏れ
  提案: 表に user-guide / README を必須行化
  **プレモータム反映済み**: 主要コンポーネント表に `docs/user-guide.md` と `README.md` を追加

---

> **付録** — 実装入口・resume の既定では読まない。プレモータム・TDD 突入・乖離調査など、当該節が必要なときだけ読む。人間の Phase 3 承認前は `影響範囲` と `検討した代替案` を必読。

---

> **付録** — 実装入口・resume の既定では読まない。プレモータム・TDD 突入・乖離調査など、当該節が必要なときだけ読む。人間の Phase 3 承認前は `影響範囲` と `検討した代替案` を必読。

## データフロー

```
session end
  session-stop.sh
    （作りたてスキップ AND 維持 / capture_done なければ）
    → touch .capture-needed

session start
  session-start-check.sh
    → 注入: 三択確認（今 / 後で / スキップ）
  ユーザー選択
    今 → knowledge-capture → rm .capture-needed + touch capture_done
    後で → 何もしない（フラグ残置）
    スキップ → rm .capture-needed のみ（capture_done なし）
             ※ 次の session-stop でフェイルセーフが再 touch（永久スキップではない）

task complete
  steering archive
    capture_done or 「知見なしでアーカイブ」?
      YES → アーカイブ実行
      NO  → ハードストップ（ここで止まる）
            → knowledge-capture 実行 / または「知見なしでアーカイブ」
            → 汎用「省略してアーカイブ」・tasklist [x] 単独では非充足
```

## 影響範囲

- システム / 外部連携: なし（hooks とスキル契約のみ）
- データ: 新フラグなし。既存 `.capture-needed` / `capture_done` の意味付けが分かれる（スキップ≠完了）
- 他チーム / 利用者: 個人マスター利用者。配置先は再コピー後に効く（knowledge-capture / hooks / steering は配布対象になりうる）
- リグレッション懸念:
  - スキップは次 Stop まで — 「跨セッションで催促が消える」期待は満たさない（意図的・フェイルセーフ優先）
  - 途中 capture 後は再催促しない（`capture_done` 維持）— 偽陰性許容（対象外）
  - archive を汎用省略だけで通していた運用は、capture に関して通らなくなる（意図的）
  - feature-pipeline は steering に委譲（本文不触）。Phase 4 で `capture_done` が立つハッピーパスは現行どおり

## テスト方針

- Unit: 該当なし。hook は `bash -n`
- Integration / フィクスチャ（必須）: 一時 `.steering/` で session-stop (1) 作りたてスキップ (2) `capture_done` 時スキップ (3) スキップ後再立て
- validate: キー共存を必須化した場合はその検査。空文限界はコメント
- エージェント枝（三択・archive ハードストップ）: 機械検査に入らない分は tasklist に「一回限り」と明記

## 検討した代替案

| 代替案 | 却下理由 |
|--------|----------|
| フラグ 2 種（セッション用 / 完了用） | gitignore・hooks・deploy・文書面が増える。決定インタビューで B を採択 |
| capture「完了時のみ」単純化 | 偽陰性増。レポート明示のやらなくてよい縮退 |
| `capture_done` 生涯廃止（毎セッション再催促） | 「完了」と「セッション」は分離されない。ノイズ増のリスク |
| 完了ゲートを tasklist 全チェック時に発火 | 全チェック＝知見確定ではない |
| ユーザー明示の「タスク完了」新コマンド | 新発動語が増え、忘れやすく機械保証が弱い |

## 調査結果

- 一次根拠: `.tmp/reports/20260730-personal-friction-report.md` 指摘1（1ビット潰し）。向き先例は「完了時 capture とセッション末メモの分離 / 確認文を今・後で・スキップに」
- 現行 `session-stop.sh` はフェイルセーフ明示（偽陽性＝確認1回、偽陰性＝知見喪失）
- 現行 `steering` archive は knowledge-capture をチェックリスト＋「明示的に省略」＋汎用「省略してアーカイブ」で満たせ、硬いゲートではない
- 確認文言の旧形: `session-start-check.sh` / `CLAUDE.md` / `docs/starter-kit.md`（実装時再検索で確定）。周辺: `docs/user-guide.md`（フラグ説明）、`steering/references/spec.md:190`（旧「促す」）、`README.md`
- プレモータムで確定した契約: スキップ寿命＝次 Stop まで / SessionStart 操作定義＝hook 注入文（CLAUDE.md 再掲は任意・PR #9 追認） / pipeline は steering 委譲
