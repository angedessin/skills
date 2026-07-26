# バックログ（固定パス・タスクディレクトリではない）

**なぜこのファイルがあるか**: 着手前のバックログをアーカイブ済みタスクの `decisions.md` に書くと、
`session-start-check.sh` が `archived/` を除外するため**次セッションから構造的に見えない**
（20260726 に 2 回続けて起きた）。アクティブタスクとして `.steering/[task]/` に置くと毎セッションの
コンテキスト固定費になるため、その中間としてこの 1 枚を置く。

**運用**: 着手するときは `design-doc` で `.steering/[YYYYMMDD]-[task]/` を作り、ここから該当節を移す。
完了したら該当節を削除する。**このファイル自体はアクティブタスク一覧に出ない。**

---

## 1. rm / mv ポリシーの再設計

**起票**: 2026-07-26（`20260726-deploy-integrity` から切り出し・ユーザー判断）
**一次情報**: `.steering/archived/20260726-deploy-integrity/design.md` の「対象外 — rm / mv ポリシーの再設計」節
**優先度**: 中（実害は出ていないが、承認ゲートに整合性の穴がある）

### 目的

承認ゲート（`CLAUDE.md` / `docs/knowledge/` / `docs/decisions/`）は**書き込みだけを塞ぎ、削除・移動は素通し**。
`rm -f docs/knowledge/x.md` が実測で素通りした。かつ permissions の前置一致には flag の網羅漏れがある
（`rm -R` / `rm --recursive` / `rm -f -r` がどのルールにも当たらない）。

### 確定済みのユーザー決定

| 論点 | 決定 |
|---|---|
| 判定を deny か ask か | **`deny` を使う**（プレモータムが提案した「ask に統一」は採らない） |
| 判定精度の問題 | このタスク側で扱う |
| 位置づけ | 配置機構の修復とは独立。混ぜると配布のブロッカーが増える |

### 必ず持ち越す技術的制約（公式 docs で裏取り済み・**再調査しない**）

1. **PreToolUse hook は permissions より先に評価される。** hook が沈黙すると通常の permission flow に
   進むため、**hook は permissions の deny を救済できない**（`permissionDecision: "allow"` を返さない限り）。
   したがって permissions に置く deny は「守りたい範囲の外にだけ当たる形」でなければならない —
   **`Bash(rm -rf /*)` は前置一致で `rm -rf /Users/<...>/<project>/.tmp` にも当たるので使えない**
2. **入力 JSON には `transcript_path`・`cwd`・`tool_input.description` が必ず含まれる**ため、
   **全文検査でパス判定はできない**（プロジェクト外の絶対パスが恒常的に入っている）。
   `tool_input.command` の構造抽出が必須（`remind-config-docs.sh:31` の `grep -o` + `sed` で `jq` 非依存にできる）
3. `permissionDecision` に指定できる値: `allow` / `deny` / `ask` / `defer`
4. **非対話モード（`claude -p`）では hook の `ask` は deny に落ちる**（`docs/knowledge/claude-code-config.md`）。
   `guard-gated-write.sh` は全配置先に無条件同送されるため、配置先の CI で誤検知すると原因の遠い障害になる
5. 20260726 の実測では現行の全文検査 hook は `transcript_path` に巻き込まれていない（発火 13/13・誤検知 0）。
   ただしこれは「`.env` を含むか」「リダイレクト先が対象パスか」を見ているからで、
   **パス判定を足した瞬間に成立しなくなる**

### 併せて塞ぐべき穴

- **`mv` は削除と等価にゲートを破る**（`mv docs/knowledge/x.md /tmp/`）
- `sed -i` / 任意インタプリタ経由は脅威モデル外（敵対者ではなく滑った善意のエージェント）

### 波及

- `guard-gated-write.sh` のリネーム是非（書き込み以外も見るなら名前がずれる）。20260726 時点では
  **リネームしない**と決めた（rm / mv を切り出したので名前と実態が一致した）。このタスクで再検討する
- 配布物側の同名 hook にも同じ変更が要る。**契約 (g) が差分を検出するので片側修正は落ちる**
- 配布物の `MANIFEST.md` に「対象は書き込みのみ・削除は非対象」と明記済み。変更したらここも直す
  （契約は文書の本文までは見ない）

---

## 2. 引き継ぎ文書とその検査の積み残し（company 側 FB の 4 件）

**起票**: 2026-07-26
**一次情報**: `.tmp/master-feedback-20260726.md`（main / export worktree の両方に同内容）
**優先度**: 高（配布運用に直結）。ただし**会社へ渡す前に必須の 1 件（FB の指摘 1）は 20260726 に解消済み**

> 解消済み: FB 指摘 1「引き継ぎプロンプトのスモークテストが手順 3 と矛盾する」
> — `.tmp/20260726-handover-prompt.md` の手順 9 を「`npm run test` 等が通ること。
> **install 系が拒否されるのは仕様であり FAIL ではない**」に差し替え、
> `-spec.md` に「`docs/starter-kit.md` 手順 8 とは経路が違う」の注意書きを追加した。

### 2-1. 貼る版を 1 つに決めて差分を移す（FB 指摘 2）

`MIGRATION-GUIDE.md:109` は「**A. `HANDOVER.md` の本文を貼る（推奨）**」と案内しているため、
**実際に貼られるのは同梱の `HANDOVER.md`**。しかし `.tmp` 版だけが持っている内容がある:

| 項目 | `.tmp` 版 | `HANDOVER.md` | MANIFEST | MIGRATION-GUIDE |
|---|---|---|---|---|
| session-start/stop の対配置警告 | あり | **無し** | 無し | つまずきどころにあり |
| ask を外さない / install deny を緩めない | あり | **無し** | ask のみ | deny のみ |
| 「保証していないこと」の集約節 | あり | **無し** | 散在 | 散在 |
| 手順 9 の開発フロー確認 | あり | **無し** | **無し** | **無し** |
| 手順 9「`.claude/hooks/` 編集 → ask」 | **無し** | 無し | あり | 無し |

**やること**: 貼る版を `HANDOVER.md` に寄せて差分を移す。`.tmp` 版は「人が読む解説」に役割を限定し、
手順の重複を持たせない。**「どちらの版も同じことを言っている」という記述は虚偽なので消す**。

### 2-2. 引き継ぎの一次資料が `.gitignore` 対象（FB 指摘 3）

`.tmp/20260726-handover-{spec,prompt}.md` は追跡外（`.gitignore` に `.tmp/`）。
spec は「マスターコミット `3202d02`」と対応を宣言しているのに、**その対応を後から再現できない**。

**やること**: 2-1 の一元化を前提に、差分を `HANDOVER.md` / `MANIFEST.md` に統合して `.tmp` を捨てるか、
`export/company/` 配下にコミットするかを決める。

### 2-3. 契約が export の 3 文書を見ていない（FB 指摘 4）

`scripts/check_asset_consistency.py` に `MANIFEST` / `HANDOVER` の言及は **0 件**。
契約 (c)(d) の対象は `README.md` と `docs/starter-kit.md` だけ。

`20260726-deploy-integrity` の tasklist `:130`「`MANIFEST.md` / `HANDOVER.md` の記述と実体の一致を確認
→ スキル 10 / hook 5 で齟齬なし」は**手作業の突合**で、同セッションで CLAUDE.md に昇格させた
「手作業で突合した検証項目は、その場で機械検査に入れるか『一回限り』と明記する」の適用対象そのもの。
**上の 2-1 で見つけた食い違いも、現在の契約では検出できない。**

**やること**: 契約 (i)「export 3 文書のスキル員数・hook 名集合 ≡ `export/company/` の実体」を追加する
（(c)(d) と同型なので安い）。手順本文の食い違いまでは機械化しなくてよいが、**員数と名前は毎回自動で見る**。

### 2-4. バックログの可視化（FB 指摘 5）

**このファイル（`.steering/BACKLOG.md`）の新設で半分は解消した。** 残りは:

**やること**: `.claude/hooks/session-start-check.sh` の注入対象にこのファイルを加える
（存在すれば「未着手のバックログが N 件あります」と 1 行注入する程度で足りる。
タスクディレクトリではないのでアクティブタスク一覧は汚さない）。
`.steering/` が無い環境では素通しするフェイルオープンを維持すること。

---

## 3. 前タスクからの持ち越し（`20260725-skillset-hardening` 由来）

**一次情報**: `.steering/archived/20260725-skillset-hardening/decisions.md` のバックログ節

- **(b) 配布機構の初回実走** — 外部プロジェクトへの実配置。20260726 に tmpdir への実配置で
  機構の動作は実証したが、**実際の配置先はまだ 0 件**（`deployments.md` の有効行 0）
- **(c) 構造改善** — `docs/knowledge/skill-design-patterns.md` が **45KB** に増えており剪定対象
  （`rule-audit` の担当）。依存表の網羅・README のセットアップ節新設も含む
- **(d) `passthrough_check.py` のハーネス拡張** — `## setup` 節・サンドボックスでの `git init`。
  `feature-pipeline` の Gate 3.5 のような「外向き操作が副作用」の停止契約を判定可能にする

## 4. 既知の環境問題（タスクではない）

- **`pnpm` のバイナリが壊れており実行できない**（`pnpm --version` も同じエラー）。
  npm script の実行は `npm run <script>` で代替する（npm 11.9.0 は動作）。
  リポジトリの作業とは無関係な環境問題
