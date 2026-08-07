# 保守メモ — 会社向け持ち出しセット（`export/company/`）

**読み手: このリポジトリ（マスター）の保守者。** 会社へは持ち出さない（持ち出すのは `export/company/` 配下だけ）。

会社側が読む文書は `export/company/` の 3 点（MANIFEST / HANDOVER / MIGRATION-GUIDE）。
そちらには**配置手順と現状だけ**を書き、マスター前提の手順（ここに書いてあること）は混ぜない
— 配置する Claude が「マスターの `.claude/skills/` をコピーする」を実行しようとして詰まるため。

---

## 育成方針: 原則は独立フォーク。ただし停止契約はマスターを上流として同期する

（2026-08-07 決定。それ以前は「完全独立フォーク・再エクスポートしない」だった）

| 対象 | 正本 | 運用 |
|---|---|---|
| 同梱スキルの選定（10 本の顔ぶれ）・除外判断 | このセット | 会社の事情で独立に決める。マスターに合わせない |
| スタック語彙（Angular / Jasmine）・MR 運用・非同梱名の言い換え | このセット | 下の変換レシピとして維持し、再同期のたびに再適用する |
| **停止契約・手順・スキル本文** | **マスター（`.claude/skills/`）** | 必要時にマスターから本文を再同期する。会社側で先に強化しない |
| hooks・settings の防御 | マスター | 同梱 6 本についてマスターの修正を追随する |

- **なぜ本文だけ上流に置くか**: 停止契約はスキルの防御そのもので、素通り事例をマスター側で何度も潰した蓄積がある。会社側で独立に育てると、その蓄積が届かないまま古い防御で運用することになる（2026-08-07 の再同期は、まさに docs / hooks だけ新しく本文が 2 世代古い状態を解消したもの）。一方、同梱の顔ぶれやスタック語彙は会社の事情で決まるもので、マスターに従う理由がない
- **`source-commit` は同期の基準**として使う（出所の履歴ではない）。次の再同期では `git diff <source-commit> HEAD -- .claude/skills/<name>` でマスター側の変更を確認してから取り込む
- **再同期のたびに変換レシピを全部適用し、検査コマンドを通す**。「前回やったから大丈夫」は使わない
- **「フォークには同期・伝播しない」を防御の欠陥に適用しない。** マスター側で hook・権限・停止契約の穴を塞いだら、このセットにも同じ穴が開いていないかを必ず見る（独立フォーク方針は機能差分とスタック適応のための取り決めであって、防御を古いまま放置してよいという意味ではない）

---

## 変換レシピ（マスター → このセット）

再同期のたびに適用する。**人の記憶に頼らず、この節を手順書として使う。**

### 手順

1. マスターの `.claude/skills/<name>/` 配下を `export/company/skills/<name>/` へコピーする（**ディレクトリ丸ごとの機械上書きはしない** — 下の「禁止ファイル」が再流入する）
2. 禁止ファイルを除外する
3. 禁止語彙・禁止参照を置換する
4. `metadata.source-commit` を同期に使ったマスターの hash に更新する。`metadata.modified` は原則残さない（下の「会社パッチの扱い」）
5. hooks を同梱 6 本だけ追随し、理由文から非同梱スキル名を除去する
6. `export/company/` の 3 文書を実態に合わせる（hook 本数・依存・Status の値域など）
7. 検査を回す（下の「検査コマンド」）

### 禁止ファイル（コピーしない・完了時に存在してはならない）

| ファイル | 理由 |
|---|---|
| `tdd/references/patterns.md` | 中身が React / Vitest / RTL / MSW / pnpm 前提で、Jasmine の本文と矛盾する。誤ったスタックのコード例を持ち込む害が雛形としての価値を上回る |

### 禁止語彙（個人スタック → 会社スタック）

| マスター | このセット |
|---|---|
| `React / TypeScript / Vitest / React Testing Library / MSW / Playwright` | `Angular / TypeScript / Jasmine` |
| `vitest` / `Vitest`（テストランナー） | `Jasmine` |
| `MSW ハンドラー` | `HTTP モックの方針（HttpTestingController 等）` |
| `Playwright シナリオ` | 削除（E2E は非運用） |
| `In-source テスト` / `includeSource` / `§hook` | 削除（Vitest / React Hooks 専用で Angular に対応物が無い） |
| `PR` / `gh pr create` / `GitHub Actions` / `CI グリーン` | `MR` / `MR（マージリクエスト）の作成` / `パイプライングリーン` |
| `pnpm` / `npx` | 使わない（`npx` は settings で deny） |

### 禁止参照（非同梱スキル名 — 本文・references・hook 理由文のすべてで 0 件にする）

`adr` / `e2e` / `empirical-prompt-tuning` / `feature-pipeline` / `frontend-code-review` / `impl-review` / `impl-tournament` / `pr-create` / `pr-feedback` / `review-a11y` / `review-correctness` / `review-performance` / `review-security` / `review-ui` / `security-audit` / `skill-deploy` / `skill-harvest` / `skill-test` / `test-review`

置換の型:

| マスターの記述 | このセット |
|---|---|
| `→ frontend-code-review の担当` | `→ 本スキルの対象外（コードレビューは別途用意された手段で行う）` |
| `review-result.md（frontend-code-review が生成）` | `review-result.md（任意 — 生成元は問わない）` |
| `feature-pipeline 等のオーケストレーター` | `複数フェーズをまとめて進めるオーケストレーター` |
| `+ empirical-prompt-tuning の実行提案` | `（修正後、同じ状況を再現させて挙動が直ったかを実地で確認する）` |
| `compound / skill-harvest の回収経路` | `compound の回収経路` |
| `security-audit があちらの担当` | 「本スキルは危険性を見ない」と担当範囲だけ書く |
| Related skills の非同梱スキル行 | 行ごと削除 |

**同梱 10 スキル同士の相互参照（`debug` / `tdd` / `compound` 等）は残す。** 消すのは非同梱名だけ。

### 会社パッチの扱い

- **原則、会社独自パッチは持たない。** 停止契約・手順の正本はマスターにあり、再同期のたびにマスター本文で置き換える
- 例外的に残すパッチを作った場合は `metadata.modified: "YYYY-MM-DD 変更概要"` に記録し、**この節の表に行を足す**（記録が無いパッチは次の再同期で黙って消える）
- 2026-08-07 時点で残しているパッチ: **なし**

### マスターに存在しない前提への縮退

このセットには `templates/` / `docs/knowledge/` / `scripts/` を同梱していない。マスター本文がそれらを前提にしている箇所は「**あれば使う、無ければこうする**」の縮退形に書き換える（例: `templates/SKILL.template.md` をコピーして書き始める → 雛形があればコピー、無ければ既存スキルの書式に倣う）。

---

## 検査

**完了判定は下の機械検査で行う。目視の「実質一致」を判定に使わない。**

### 静的検査（無課金・毎回）

```bash
cd export/company

# 1. 非同梱スキル名がゼロ
for n in adr e2e empirical-prompt-tuning feature-pipeline frontend-code-review \
         impl-review impl-tournament pr-create pr-feedback review-a11y \
         review-correctness review-performance review-security review-ui \
         security-audit skill-deploy skill-harvest skill-test test-review; do
  grep -rn "\b$n\b" skills/ claude-config/hooks/
done

# 2. 個人スタック語彙がゼロ
grep -rnE '(React|Vitest|React Testing Library|\bMSW\b|Playwright|pnpm|npx|vitest)' skills/ claude-config/hooks/

# 3. 禁止ファイルが不在
test ! -e skills/tdd/references/patterns.md && echo OK

# 4. 会社パッチの記録漏れがない（記録の無い modified は残さない）
grep -rn '^  modified:' skills/

# 5. スキル数と hook 本数が文書と一致
ls skills/ | wc -l                # → 10
ls claude-config/hooks/ | wc -l   # → 6

# 6. settings が壊れていない・hook 登録が実体と一致・会社 deny が残っている
python3 - <<'PY'
import json, pathlib
d = json.load(open('claude-config/settings.example.json'))
reg = sorted({h["command"].split("/")[-1] for g in d["hooks"].values() for grp in g for h in grp["hooks"]})
act = sorted(p.name for p in pathlib.Path('claude-config/hooks').iterdir())
print("hook 登録 == 実体:", reg == act)
print("npx deny:", [x for x in d["permissions"]["deny"] if "npx" in x or "npm exec" in x])
PY
```

### 素通り検査（課金・任意）

シナリオは `export/company/tests/<skill>/scenario.md`。

- **`--all` を使わない。** `--all` の走査対象は `tests/passthrough/` 固定で、このセット専用のシナリオを**永久に拾わない**。さらにこのブランチには master 側の `.claude/skills/` と `tests/passthrough/` もそのまま存在するため、`--all` は**master のスキルを検査して PASS を返す**。持ち出しセットを 1 本も見ていないのに「検査済み」に見える
- **明示指定で回す**: `python3 scripts/passthrough_check.py export/company/tests/<skill>/scenario.md --runs 4`（承認ゲート系は 4 回以上）
- **実行はこのブランチ（worktree）側の `scripts/` から**。スクリプトはルートを実行ファイルの位置から決めるため、main 側の `scripts/` を使うと `export/company/` を解決できない
- **バックグラウンド実行に載せない**（フォアグラウンド直列）。過去に早期完了誤報で二重課金した事例がある
- **回す対象の選び方**: 再同期で**本文が変わったスキルだけ**でよい。`git diff HEAD -- export/company/skills/<name>/SKILL.md` が frontmatter だけなら、前回の検証結果がそのまま引き継げる

### 実行履歴

| 日付 | 対象 | 結果 |
|---|---|---|
| 2026-08-07 | knowledge-capture（`--runs 4`） | **4/4 PASS**（本文を `e02a95d` へ再同期した状態） |
| 2026-08-07 | session-retrospective | 未実行（本文が前回検証時と**完全一致**のため引き継ぎ。差分 3 行はすべて frontmatter） |

---

## 会社側の 3 文書の役割分担（ドリフト防止）

配置手順の一次情報は **MANIFEST の「配置先（会社）でやること」だけ**。他の 2 文書は同じ手順を再掲せず、そこを指す。

| 文書 | 読み手 | 持つ内容 |
|---|---|---|
| `MANIFEST.md` | 配置エンジニア / 配置代行の Claude | 一次情報。中身・除外理由・設定・配置手順の全ステップ |
| `HANDOVER.md` | 配置作業を代行する Claude | そのまま貼る導入プロンプト。手順の詳細は MANIFEST を指す |
| `MIGRATION-GUIDE.md` | 導入判断者 | 入れる価値・課題との対応・コスト。手順は持たず MANIFEST を指す |

**hook の本数・依存・スキル数を変えたら、3 文書と `settings.example.json` の `_comment` を同一コミットで直す。**
