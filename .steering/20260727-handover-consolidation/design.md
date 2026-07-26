# 設計: 引き継ぎ文書の一元化とバックログの可視化

Status: **APPROVED**
Date: 20260727
Approved: 20260727

## 目的

`export/company` 側から返ってきた FB（`.tmp/master-feedback-20260726.md`）の 5 件のうち、
**会社へ渡す前に必須だった 1 件は 20260726 に解消済み**（引き継ぎプロンプトの手順 9 が手順 3 と
矛盾し、会社側 AI が install 拒否を FAIL 報告する状態だった）。残る 4 件を片付ける。

4 件は 2 系統に分かれる:

**(A) 引き継ぎ文書が 2 版に分かれている問題（FB 指摘 2・3）** — `.tmp/20260726-handover-{spec,prompt}.md`
と同梱の `HANDOVER.md` が別々の内容を持ち、`MIGRATION-GUIDE.md:109` が「**A. `HANDOVER.md` の
本文を貼る（推奨）**」と案内しているため、**実際に貼られるのは修正が入っていない薄い方**になる。
かつ `.tmp` 版は `.gitignore` 対象なので、spec が宣言している「マスターコミット `3202d02` との対応」を
後から再現できない。

**(B) 検証が機械化されていない問題（FB 指摘 4・5）** — 契約突合が export の 3 文書を見ておらず、
前タスクの「`MANIFEST.md` / `HANDOVER.md` の記述と実体の一致を確認 → 齟齬なし」は**手作業**だった。
これは同じセッションで CLAUDE.md に昇格させた「手作業で突合した検証項目は、その場で機械検査に
入れるか『一回限り』と明記する」の適用対象そのもの。またバックログを `archived/` 配下に書くと
`session-start-check.sh` が除外するため次セッションから見えない（20260726 に 2 回続けて起きた）。

## レビュー前に確定した決定（Phase 1.5 の決定インタビュー）

| 決定 | 内容 | 却下した案 |
|---|---|---|
| `.tmp` の 2 文書の扱い | **`HANDOVER.md` に統合して `.tmp` は捨てる。** 貼る版が 1 つになるので「版が 2 つあって内容が違う」問題が構造的に消える。代償は `HANDOVER.md` が 6KB → 9KB 程度に増えること | `export/company/` にコミットして 2 本立てを維持（貼る版と解説版の同期が恒久的な保守コストになる）/ `.tmp` のまま運用（FB 指摘 3 が未解決のまま残る） |
| バックログ注入の粒度 | **件数＋パスの 1 行。** 固定費は数十トークン/セッション。中身は必要になってから開く | 節見出しを列挙（節数に比例して固定費が増える）/ 注入しない（メモリはマシン固有で git に乗らず、他マシン・クローンでは見えない） |

## スコープ

### 対象

- **Phase 1 — `HANDOVER.md` への一元化**: `.tmp` 版だけが持つ 4 項目 + `MANIFEST.md` だけが持つ
  1 項目を `HANDOVER.md` に移し、`.tmp` の 2 文書を削除する
- **Phase 2 — 契約 (i) の追加**: `check_asset_consistency.py` に「export 3 文書のスキル員数・
  hook 名集合 ≡ `export/company/` の実体」を追加する
- **Phase 3 — バックログの注入**: `session-start-check.sh` に `.steering/BACKLOG.md` の
  存在と節数を 1 行注入する分岐を追加する
- **Phase 4 — BACKLOG の更新**: 解消した項目を削除し、残りを整理する

### 対象外

- **`MANIFEST.md` / `MIGRATION-GUIDE.md` の本文の書き換え** — 一次情報としての役割は変えない。
  `MANIFEST` から `HANDOVER` へ移すのは**スモークテスト 1 項目の複製**であって、移設ではない
  （MANIFEST が一次情報である構造を壊さない）
- **手順本文の食い違いの機械検査** — 契約 (i) が見るのは**員数と hook 名の集合**まで。
  FB も「手順本文の食い違いまでは機械化しなくてよい」としている。文章の意味的整合は人が読む
- **rm / mv ポリシーの再設計**（BACKLOG 1 節）— 独立したバックログ項目。本タスクでは触らない
- **前タスクからの持ち越し (b)(c)(d)**（BACKLOG 3 節）— 同上

## 制約

- **`export/company` は同一リポジトリの worktree** — 実体は `/Users/kentaro/Desktop/_lab/ai/skills-export-company/`
- **修正の順序は「main で直す → export へ merge → `export/company/` 側の変換分のみ追随」** —
  `HANDOVER.md` は `export/company/` 配下なので **export ブランチでしか直せない**（main には存在しない）。
  Phase 1 は export 側の作業、Phase 2・3・4 は main 側の作業
- **`HANDOVER.md` は配布物**。マスター固有の語（`deploy_skills.py` / `starter-kit.md` / 契約名など）を
  本文に持ち込まない。移す内容は会社側の読み手が解読できる形に一般化する
- **hook は依存ゼロを維持する**（POSIX 標準ユーティリティのみ）。`session-start-check.sh` は
  `.steering/` が無い環境で素通しするフェイルオープンを保つ
- **契約 (i) は対象不在で SKIP に降格する** — 契約 (g) と同じ設計。持ち出し worktree が無い環境で
  `exit 2` を返すと、他の契約の FAIL を握りつぶして呼び出し側の hook が無音になる（20260726 に
  実際に起きた欠陥）
- `.steering/archived/` 配下は履歴のため変更しない

## 完了条件

### 達成条件

- [ ] `HANDOVER.md` が**貼る版として単独で完結**している（`.tmp` 版だけが持っていた 4 項目 +
      `MANIFEST` のスモークテスト 1 項目を含む）
- [ ] `.tmp/20260726-handover-spec.md` と `-prompt.md` が削除されている
- [ ] `HANDOVER.md` に「どちらの版も同じことを言っている」に相当する**虚偽の記述が無い**
      （版が 1 つになったので、そもそも書く必要が無い）
- [ ] `HANDOVER.md` にマスター固有語（`deploy_skills.py` / `starter-kit` / `DEPLOY_PERMISSIONS` /
      契約記号）が**混入していない**
- [ ] `python3 scripts/check_asset_consistency.py` が **9 契約**を表示し、全 PASS
- [ ] 契約 (i) を**故意に壊すと exit 1 で落ちる**ことを実測（員数のズレ / hook 名のズレの両方）
- [ ] 契約 (i) が持ち出し worktree 不在時に **SKIP** になり、他契約の FAIL を握りつぶさない
      ことを実測
- [ ] `session-start-check.sh` が `.steering/BACKLOG.md` の存在時に 1 行注入し、**不在時は
      何も注入しない**ことを実測
- [ ] 同 hook がアクティブタスク・フラグの既存 3 分岐を壊していないことを実測
- [ ] `.steering/BACKLOG.md` の 2 節から解消済み項目が削除されている

### 無回帰条件（着手前から満たされている）

- [ ] `python3 scripts/validate_skills.py` が 29/29 PASS
- [ ] `validate_skills.py <worktree>/export/company/skills` が 10/10 PASS
- [ ] `--portability` が混入 0 件
- [ ] `check_export_stopcontract.py` のサマリが 実質差分 7 / 無害のみ 1 / 差分なし 2 で不変
- [ ] `deploy_skills.py --dry-run` が両経路で exit 0

## 調査結果

### 実在確認（20260727）

```
check_asset_consistency.py  契約関数 a,b,c,d,e,f,h（2-tuple）+ g（3-tuple・SKIP を持つ）
                            contracts リストは :451-458、g は :460 付近で個別に呼ばれる
session-start-check.sh      PROJECT_ROOT 解決 → .steering 不在で exit 0 → フラグ 2 種 →
                            アクティブタスク → msg 組み立て → json_escape → printf
                            依存は find / sed / sort / basename のみ
.steering/BACKLOG.md        `## ` 見出しは 4 節（うち 4 節目は「既知の環境問題（タスクではない）」）
HANDOVER.md                 6248 bytes。手順 9 スモークテストは :62-68（3 項目）
MANIFEST.md                 33923 bytes。スモークテストは :122-。:125 に
                            「`.claude/hooks/` を編集 → settings の ask により確認が出る」
```

### `HANDOVER.md` に移す 5 項目（FB の差分表を実測で確認）

| 項目 | 現在の所在 | `HANDOVER.md` |
|---|---|---|
| session-start / session-stop の対配置警告 | `.tmp` 版 / `MIGRATION-GUIDE` のつまずきどころ | **無し** |
| `ask` を外さない / install deny を緩めない | `.tmp` 版 / `MANIFEST`（ask のみ）/ `MIGRATION-GUIDE`（deny のみ） | **無し** |
| 「保証していないこと」の集約節 | `.tmp` 版のみ（他は散在） | **無し** |
| 手順 9 の開発フロー確認（install 拒否は仕様） | `.tmp` 版のみ | **無し** |
| 手順 9「`.claude/hooks/` 編集 → ask」 | `MANIFEST:125` のみ | **無し** |

## アプローチ

**貼る版を 1 つにする。** 2 版を同期し続ける設計は、片側修正の種を恒久的に残す
（このリポジトリが繰り返し踏んでいる型）。`MIGRATION-GUIDE` が `HANDOVER` を貼るよう案内している
のだから、**内容を `HANDOVER` に集めて `.tmp` を消す**のが構造的な解決になる。
`MANIFEST` は一次情報の役割を保つ（`HANDOVER` は冒頭で「MANIFEST を全文読め・食い違ったら
MANIFEST が正」と指示し続ける）。

**契約 (i) は (c)(d) と同型の集合比較にする。** 文書の本文をパースせず、
「文書全文に現れるスキル名・hook 名の集合」と「実体のディレクトリ / ファイル名」を比べる。
書式非依存で、表に書こうが散文に書こうが拾える。**員数は「実体の数」を正として、
文書が別の数を書いていたら落とす**（`MANIFEST` は既に「一次情報は `ls skills/ | wc -l`」と
宣言しているので、その宣言を機械で裏づける形になる）。

**バックログの注入は「存在と規模」だけにする。** 中身を注入すると節数に比例して毎セッションの
固定費が増える。存在が見えれば「今回の問題（アーカイブ配下で不可視）」は解消する。
**節数は `## ` の総数を出し、「未着手 N 件」とは書かない** — BACKLOG の 4 節目は
「既知の環境問題（タスクではない）」なので、未着手件数として数えると誤報になる。

## 主要コンポーネント

> 以下は**暫定**。実装の最初（tasklist の 0.）で変更対象を表す語で全文検索し、
> 表に挙げ漏れた箇所を潰してから着手する。

### Phase 1 — `HANDOVER.md` への一元化（**export ブランチの作業**）

| ファイル | 変更後の状態 |
|---|---|
| `export/company/HANDOVER.md` | 手順 2 に **session-start / session-stop の対配置警告**を追加（「書く側だけを配るとフラグは毎セッション立つのに拾う主体が居らず、knowledge-capture / compound の自動起動が永久に発火しない」）。手順 3 に **`ask` を外さない / install deny を緩めない**を追加（ask は Edit / Write ツールにしか掛からず Bash のリダイレクトで迂回できるため hook と対で維持する、を含む）。手順 9 に **開発フロー確認**（`npm run test` 等が通ること・**install 拒否は仕様で FAIL ではない**・拒否を不具合として報告したり deny を外して「直す」ことをしない）と **`.claude/hooks/` 編集 → ask** を追加。手順一覧の前に **「保証していないこと」節**を新設（ゲート対象は書き込みのみで削除・移動・`sed -i` は非対象 / PreToolUse は再起動後に確認 / ask の発火は AI から観測できず人間が見る / 非対話モードでは ask が deny に落ちる）。**マスター固有語は書かない**（`deploy_skills.py` / `starter-kit` / 契約記号を出さず、「配布経路が違う」という一般的な表現にする） |
| `.tmp/20260726-handover-spec.md` | **削除** |
| `.tmp/20260726-handover-prompt.md` | **削除** |
| `export/company/MIGRATION-GUIDE.md` `:125`（**洗い出しで追加・20260727**） | 20260726 に追記した「パッケージインストールの全面 deny は…」の一文に **`deploy_skills.py` というマスター固有のスクリプト名**が入っている。配置先の読み手はそのスクリプトを持たないため解読できない。「マスターから新規プロジェクトへ配る**別の配布経路**では」という一般的な表現に直す。**本文の書き換えは対象外としたが、これは自分が前日に混入させたマスター固有語の除去であり、Phase 1 の制約（マスター固有語を持ち込まない）と同じ規律の適用** |

### Phase 2 — 契約 (i) の追加（**main の作業**）

| ファイル | 変更後の状態 |
|---|---|
| `scripts/check_asset_consistency.py` | `contract_i(require_export: bool) -> tuple[str, list[str], list[str]]` を追加（契約 (g) と同じ 3-tuple・SKIP を返せる形）。検査内容: 持ち出しセットの 3 文書（`HANDOVER.md` / `MANIFEST.md` / `MIGRATION-GUIDE.md`）**全文**から抽出したスキル名集合が `export/*/skills/` の実体と一致し、hook 名集合（`*.sh`）が `claude-config/hooks/` の実体と一致すること。**員数の記述**（「10 スキル」「5 本」等の数値）が実体の数と一致すること。対象不在は **SKIP**（`--require-export` で FAIL に昇格）。`contracts` リストではなく `contract_g` と同じ扱いで `main()` から呼ぶ |
| `scripts/check_asset_consistency.py` docstring | 契約一覧に (i) を追記。終了コードの節は変更しない |
| `README.md` | インフラ節の「7 契約」→「9 契約」に更新し、(h)(i) の説明を追加（前回 (h) を足したときに README を更新したが、その形式に (i) を足す） |

> **員数の抽出方法**: 文書から `(\d+)\s*(スキル|本)` のような数値表現を全部拾うと、無関係な数値
> （「3 点で記録する」等）を巻き込む。**スキル名・hook 名の集合比較を主とし、員数は
> 「`skills/` の実体数」と「文書が主張する数」の照合に限る**（`MANIFEST` の一次情報宣言に対応する
> 形にする）。誤検知が出るなら員数照合は落として集合比較だけ残す — **偽 FAIL より偽 PASS が危険**
> なので、集合比較（取りこぼしが致命的）を優先する

### Phase 3 — バックログの注入（**main の作業**）

| ファイル | 変更後の状態 |
|---|---|
| `.claude/hooks/session-start-check.sh` | `STEERING_DIR/BACKLOG.md` が存在する場合、`## ` の行数を数えて `msg` に 1 行追加する分岐を追加（アクティブタスク分岐の後）。文言は「【バックログ】`.steering/BACKLOG.md`（N 節）— 着手前の候補。次のタスクを選ぶときに読む」。**不在なら何も足さない**（既存のフェイルオープンを維持）。依存は増やさない（`grep -c` で数える） |
| `README.md` | SessionStart Hook の説明に「BACKLOG.md の存在と節数も注入する」を追記 |

### Phase 4 — BACKLOG の更新（**main の作業**）

| ファイル | 変更後の状態 |
|---|---|
| `.steering/BACKLOG.md` | 2 節から 2-1 / 2-2 / 2-3 / 2-4 を削除し、「2026-07-27 に `20260727-handover-consolidation` で解消」と記録して節自体を畳む（1 節 rm/mv・3 節 持ち越し・4 節 環境問題は残す）。**節を消すと `## ` の総数が変わる**ので、Phase 3 の注入が正しい数を出すことを確認する |

## データフロー

**契約 (i) の突合**

```
export/*/skills/           ─┐ 実体（正）
export/*/claude-config/hooks/ ─┤
                            ├→ contract_i → PASS / FAIL(exit 1) / SKIP（worktree 不在）
HANDOVER.md                ─┤
MANIFEST.md                ─┤ 文書が主張する集合・員数
MIGRATION-GUIDE.md         ─┘

起動主体: npm run validate:assets / validate-skill-edit.sh の assets モード
         （既に配線済み。契約を足すだけで両方に乗る）
```

**バックログの可視化**

```
.steering/BACKLOG.md（固定パス・タスクディレクトリではない）
  → session-start-check.sh が存在と節数を検出
  → SessionStart で 1 行注入（数十トークン）
  → アクティブタスク一覧は汚さない（archived と同様に別枠）
```

## 影響範囲

- **`HANDOVER.md` が 6KB → 9KB 程度に増える** — 会社側 AI が読む量が増える。ただし
  `MANIFEST.md`（34KB）を全文読ませる設計なので、相対的な増分は小さい
- **`.tmp` の 2 文書を削除する** — 20260726 に指摘 1 を直した内容が入っているので、
  **削除前に `HANDOVER.md` へ移し終えていることを確認する**（順序を守る。消してから移すと失われる）
- **契約 (i) が既存の違反を新たに検出する可能性がある** — 3 文書は 20260726 に本数記述を
  実体と突合済み（手作業）なので PASS する見込みだが、**Phase 1 で `HANDOVER.md` を書き換えた
  直後は特に確認する**（新しい記述が実体とズレる可能性）
- **`session-start-check.sh` は配布対象の hook** — 変更は配置先にも波及する。`.steering/BACKLOG.md`
  が無い配置先では何も注入しないので無害だが、**契約 (g) が master と export の hook 差分を
  検出する**ため、export 側の同名ファイルにも同じ変更が要る（片側修正になると落ちる）
- **Phase 4 で BACKLOG の節数が変わる** — Phase 3 の注入が出す数値が変わるので、
  最後に整合を確認する
- **課金なし** — 素通り検査を回さない（スキル本文を変更しないため）

## テスト方針

- **静的（無回帰）**: 各 Phase 完了時に `validate_skills.py`（29/29）+ export セット（10/10）+
  `--portability`（0 件）+ `check_export_stopcontract.py`（7/1/2）+ `check_asset_consistency.py`
  + `bash -n` 全 hook + JSON 妥当性
- **契約 (i) の実効性**: **故意に壊して落ちることを実測する**。(1) `HANDOVER.md` のスキル名を 1 つ
  消す → FAIL、(2) hook 名を実在しないものに書き換える → FAIL、(3) 員数を 10 → 9 に書き換える → FAIL、
  (4) 持ち出し worktree 不在 → **SKIP**（かつ他契約の FAIL があれば exit 1 になること）
- **`session-start-check.sh` のフィクスチャ検証**: (1) BACKLOG あり → 1 行注入、(2) BACKLOG なし →
  注入なし、(3) `.steering/` なし → exit 0、(4) 既存 3 分岐（`.capture-needed` / `.codify-needed` /
  アクティブタスク）が壊れていない、(5) 注入 JSON が妥当（`json_escape` を通っている）
- **`HANDOVER.md` の配布可性**: マスター固有語の混入を grep で確認（`deploy_skills` / `starter-kit` /
  `DEPLOY_PERMISSIONS` / `契約 (` / `check_asset_consistency`）
- **契約 (g) の維持**: `session-start-check.sh` を master と export の両方で直し、
  契約 (g) が PASS することを確認（片側修正なら落ちる）

## 未解決の論点

**着手前に必要な論点は Phase 1.5 で解決済み。** 実装中に判断が要る可能性があるもの:

1. **員数照合の誤検知** — 文書から数値表現を拾うと無関係な数値を巻き込む恐れがある。
   実装して誤検知が出たら**員数照合は落として集合比較だけ残す**（アプローチ節に方針を明記済み）。
   偽 FAIL は「無関係な編集がブロックされる」形で警報疲れを招くため、集合比較の確実性を優先する
2. **`HANDOVER.md` の分量** — 5 項目を移して 9KB を大きく超える場合、「保証していないこと」節を
   `MANIFEST` への参照に置き換える選択肢がある。ただし FB 指摘 2 の趣旨は「貼る版が薄いこと」なので、
   参照に逃げると元の問題に戻る。**分量が問題になったら報告して判断を仰ぐ**

## 検討した代替案

- **`.tmp` の 2 文書を `export/company/` にコミットして 2 本立てを維持** — 却下（Phase 1.5 の決定）。
  貼る版と解説版の同期が恒久的な保守コストになり、契約 (i) は本文の意味的整合を見ないので
  片側修正の種が残る
- **`.tmp` のまま運用し、引き継ぎのたびに作り直す** — 却下。FB 指摘 3（一次資料が追跡外）が
  未解決のまま残り、「マスターコミットとの対応」を後から再現できない
- **契約 (i) で手順本文の意味的整合も検査する** — 却下。文章の意味は機械化に向かない。
  FB も「員数と名前は毎回自動で見るべき、手順本文までは機械化しなくてよい」としている
- **バックログの節見出しを注入する** — 却下（Phase 1.5 の決定）。節数に比例して毎セッションの
  固定費が増える。存在が見えれば今回の問題は解消する
- **バックログを注入せずメモリだけに任せる** — 却下。メモリはマシン固有で git に乗らないため、
  他マシン・クローンでは見えない。FB 指摘 5 の根本原因（リポジトリ内の機構で見えない）が残る
- **`MANIFEST.md` の内容を `HANDOVER.md` に統合して 1 文書にする** — 却下。`MANIFEST` は
  34KB の一次情報で、貼る版に統合すると「まず全文読め」の構造が崩れる。役割分担は維持する
