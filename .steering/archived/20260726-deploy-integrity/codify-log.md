# 福利化ログ: deploy-integrity

## 20260726 — compound 実行

### 効果検証（20260725-review-followups の昇格ルールとの突合）

**昇格ルール 1「同送 hook の単一情報源に新しい防御を載せ忘れると、検出側が偽グリーンを出す」は不完全だった。**

そのルールは `expected_hooks()` だけを名指しし、**対になる `HOOK_REGISTRATIONS` に触れていなかった**。結果、ルールを昇格させたコミット自身（`b9b6a91`）が `guard-gated-write.sh` を `expected_hooks()` に足しながら `HOOK_REGISTRATIONS` に登録せず、**同じクラスの障害を 1 階層下で再発**させた（配置が全構成で KeyError）。

「単一情報源」という言葉が、実際には 2 つあるリストの片方だけを指していた。**ルールの対象が「対」なら、対の両方を名指ししないと守られない。**

→ 本タスク内で解消済み: `expected_hooks()` の docstring に「返り値に入れた hook は `HOOK_REGISTRATIONS` にも登録すること」を追加し、契約 (a) で機械化（故意に壊して落ちることを実測）。

その他の昇格ルールに反する再発はなし（昇格 2「洗い出し範囲は現在の作業ツリーだけではない」は本タスクで `git worktree list` を実行して遵守。昇格 3「作りたてタスクに `.capture-needed` を立てない」はフィクスチャ 3 ケースで期待どおり動作）。

### 昇格したパターン

1. **配布分類の値の集合が 2 ファイルに独立定義されていた** → `scripts/check_asset_consistency.py`（契約 (h)）
   - `MASTER_ONLY` が `deploy_skills.py:45`（誤配置の防止）と `validate_skills.py:60`（`--portability` の走査除外）に独立定義。値は一致していたので実害は未発生だが、片方への足し忘れは「**配布してはいけないスキルが配布可能になる**」に直結する
   - **import による単一化はしない**: `validate_skills.py` は PostToolUse hook が `--skill` で呼ぶ最も頻繁に走る経路で、`deploy_skills` への import 依存を足すと片方の破損がもう片方を巻き込む。「スクリプトは依存ゼロ」の規約にも反する。突合の機械化なら両者を独立に保てる
   - 実測: `validate` 側に 1 件足す / `adr` を落とす の両方向で FAIL、元に戻すと PASS

2. **`REGISTRY` も 2 ファイルに独立定義されていた**（洗い出しで追加検出） → `scripts/check_deploy_drift.py` を import に変更
   - こちらは `check_deploy_drift.py` が**既に** `deploy_skills` を import していたため、契約を足すより **producer 側から取る**のが正しい（新しい結合を作らずに済む）
   - 無回帰: 既存 2 経路（引数なし / 配置先パス直指定）と `--help` を実測

3. **手作業の突合を「機械化した」と扱わない** → `CLAUDE.md`（自律実行の境界）
   - 根拠: 出荷前検証で `settings.json` の hook 登録を手作業で突合し「なし ✓」と報告したが契約化せず、レビューで High として指摘された（`review-result.md` の H3）
   - 1 行に絞って追記。詳細な背景は `skill-issues.md` と `review-result.md` に残す
   - **混同 2（「単体で効く」≠「全体で効く」）は CLAUDE.md に上げなかった** — 直前の knowledge-capture で `skill-design-patterns.md` の検出ツールの規律 #6 #7 として書き込んだ内容と重複し、片側修正の種になるため

### 変更したファイル

- `scripts/check_asset_consistency.py`（契約 (h) 追加・docstring 更新）
- `scripts/check_deploy_drift.py`（`REGISTRY` を import に変更）
- `CLAUDE.md`（自律実行の境界に 1 行）

### 既存違反の洗い出し（昇格したルールを自分に適用）

`scripts/*.py` の大文字定数を機械的に走査し、複数ファイルに同名定義がある対を列挙した:

| 定数 | 判定 |
|---|---|
| `MASTER_ONLY`（2 ファイル） | **違反** → 契約 (h) で機械化 |
| `REGISTRY`（2 ファイル） | **違反** → import で単一化 |
| `MASTER_ROOT`（5 ファイル） | 違反ではない。各スクリプトが `Path(__file__)` から自分の位置を解決する規約であって、値の契約ではない |

`git worktree list` で別ブランチ（`export/company`）も確認。同じ 2 箇所が存在するが、merge で伝播するファイルであり、契約 (h) はどちらの worktree から実行してもローカルのスクリプトを読むため両ブランチで効く。

**残った違反: 0 件。**

### 昇格しなかったもの

- 「単体で効くことは全体で効くことを意味しない」の CLAUDE.md 行動ルール化 — knowledge の規律 #6 #7 と重複（上記）
- `check_export_stopcontract.py` / `check_deploy_drift.py` の `exit 2` — 単一契約のツールで他契約の検出を殺さず、hook にも繋がっていないため規律 #6 の違反ではない。将来 hook に繋ぐ場合は再確認が必要
