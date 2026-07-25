# 福利化ログ: review-followups

## 20260726 — compound 実行

### 昇格したパターン

1. **同送 hook の単一情報源に新しい防御を載せ忘れると、検出側が偽グリーンを出す** → `scripts/deploy_skills.py`（`expected_hooks()`）
   - 根拠: 20260725 に新設した `guard-gated-write.sh` が `expected_hooks()` に入っておらず、配置先に配られないうえ `check_deploy_drift.py` が「不足なし」の緑を出す状態だった。この関数は「両者に同じリストを書くと片側修正で腐る」という理由で単一情報源として作られたのに、**新規 hook がそこに入る経路が無かった**
   - 同送リストに追加し、docstring に「新しい hook を追加したら、載せるか master-only かをその場で決める」を明記
   - master-only の hook（`remind-config-docs.sh` / `validate-skill-edit.sh`）とその理由も docstring に列挙。分類が記録されていないと、次に見た人が漏れなのか意図なのか判断できない

2. **「既存違反の洗い出し」の範囲は現在の作業ツリーだけではない** → `.claude/skills/compound/SKILL.md`（Step 4）
   - 根拠（効果検証）: 20260725 に昇格した「昇格したら既存の違反箇所を洗い出して直す」が、**今回まさに機能しなかった**。「リポジトリ全体から洗い出し」が現在の作業ツリーだけと読まれ、別ブランチの worktree にある配布物が射程外になり、master が High として塞いだ穴が配布物では開いたままだった
   - `git worktree list` で対象を列挙してから grep する手順を追加。「フォークには伝播しない」方針は機能差分の話であって**防御の欠陥には適用しない**ことを明記
   - 配布可スキルなので日付・固有名は入れず一般化して記述

3. **作りたてのタスクに `.capture-needed` を立てない（AND 条件）** → `.claude/hooks/session-stop.sh`
   - 根拠: `skill-issues.md` の起票分。`*.md` の存在だけでは着手の証拠にならない（`design-doc` も `steering init` も着手前に 2 ファイルを作る）。今セッションでも、削除したフラグが毎ターン復活することを実測
   - 条件は **AND**（`design.md` / `tasklist.md` 以外の `*.md` が無い **かつ** tasklist にチェック済みが 0 件）。片方だけに緩めると偽陰性が出る — 今セッションは大量に作業したが `.steering/` に増えた `*.md` はゼロで、「他の `*.md` があるか」単独の指標なら**フラグが立たなかった**
   - 偽陽性（余計な確認 1 回）と偽陰性（知見が失われる）はコストが非対称なので、迷う場合はフラグを立てる側に倒す方針を本文にも記録

### 変更したファイル

- `scripts/deploy_skills.py`（`expected_hooks()` に `guard-gated-write.sh` を追加 + master-only の分類を明記）
- `.claude/skills/compound/SKILL.md`（Step 4 の洗い出し範囲）
- `.claude/hooks/session-stop.sh`（AND 条件）
- `export/company/claude-config/hooks/session-stop.sh`（別 worktree・上記の反映）

### 既存違反の洗い出し（ルール2 の新しい範囲を自分に適用）

- **`validate-skill-edit.sh` が未分類だった** → master-only として docstring に追記（依存する `scripts/validate_skills.py` が配置先に無く、置いても効かないため）
- **export worktree の `session-stop.sh` に同じ偽陽性が残っていた** → master の修正前とバイト一致（フォーク独自の改変なし）を確認したうえで反映
- 実測: 修正版 `session-stop.sh` を 6 ケースのフィクスチャで検証し、master・export とも期待どおり
- 静的検査: master 29/29 PASS・持ち出し 10/10 PASS・portability 混入 0 件・停止契約サマリ 7/1/2 で不変

### 実装中に見つけた不具合（修正済み）

- 最初の AND 条件が効いていなかった。`grep -c` は 0 件のとき「`0` を出力して exit 1」を返すため、`|| echo 0` を付けると値が `0\n0` になり整数比較が壊れる。フィクスチャ検証で発覚（**書いただけでは効いていない**の実例がまた 1 件増えた）

### 昇格しなかったもの

- **CLAUDE.md への行動ルール追加**（防御を変えたら配布物を確認する）— 候補1（機械）と候補2（スキル手順）でカバーされるため。このリポジトリ自身の規律「人の注意ではなく機械で支える」に照らして、CLAUDE.md を太らせる価値が無いと判断
- 「配布物にも同じ防御が要る」「部分文字列は長さ順で適用する」— 同セッションの `knowledge-capture` で `docs/knowledge/` に保存済み（重複）

### 効果検証（20260725 の昇格ルールとの突合）

- 候補2 `remind-config-docs.sh` に付いていた **⚠ 効果は未検証** を解消。発火（両分岐・誤発火なし・セッション 1 回制限）と、注入内容の適用（元ファイルを読まずに要点を適用）を観察した。ただし**対照が無い 1 事例**のため「効いた」とは断定せず観察継続とする
- 候補1「昇格したら既存違反を洗い出す」は**範囲の記述に欠陥があり機能しなかった** → 上記の昇格2 で修正
- 候補3・4・5 に反する再発なし
