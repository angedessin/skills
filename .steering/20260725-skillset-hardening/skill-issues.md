# スキルの問題点

## 20260725 — validator のハードストップ検出が literal 一致で、より強い表現を FAIL にする

**事象**: `session-retrospective` の停止を `### 承認が要る場合 — ここで必ず止まる` と書いたところ、`validate_skills.py` の項目7が FAIL した。パターンが literal `"ここで止ま" in body` のため、**「必ず」を挟んだより強い表現が一致しない**（`scripts/validate_skills.py:123`）。

**期待**: `ここで必ず止ま` のような強化形も検出する。少なくとも FAIL メッセージに「literal 一致である」ことを書く（現状のメッセージは「ここで止まる / 見出しの STOP」とだけ示すため、強い表現を書いた側は理由が分からない）。

**該当**: `scripts/validate_skills.py`（項目7 の `has_hardstop`）

**回避策**: 既存スキルの慣習に合わせ、見出しは `ここで止まる`・本文で `ここで必ず止まる` と強める形にした（`knowledge-capture` の Step 4 が同じ形）。既存資産が全て PASS しているのは、どこかに literal 形が残っているため。

**影響**: 検出漏れではなく誤 FAIL なので安全側。ただし新規に停止を書く人が理由の分からない FAIL に当たる。

---

## 20260725 — 停止契約の差分ガードが、片側修正をその場で検出した（良い挙動の記録）

**事象**: `session-retrospective` の停止を master と export の両方に適用した際、master 側で回収スキル名を落とし export 側では `compound` を残したため、`check_export_stopcontract.py` が実質差分として報告した。編集直後に食い違いが分かり、その場で揃えられた。

**期待**: この挙動を維持する（問題ではなく、意図した設計が効いた記録）。

**該当**: `scripts/check_export_stopcontract.py`

**含意**: 「両側を同一コミットで直す」規律は、人の注意ではなく機械のガードで支えられる。同種のガードを他の producer/consumer 対にも置ける可能性がある（`compound` / `rule-audit` の福利化時に検討）。

---

## 20260725 — 「必要時に読む」プレーンパス参照は、その作業中でも読まれない（compound 昇格候補）

**事象**: CLAUDE.md に「settings.json・hooks 作業時: `docs/knowledge/claude-code-config.md` を読む」という導線があり、このタスクで settings.json と hooks を繰り返し編集したにもかかわらず**一度も読まず、同ファイルに記録済みのルールを 3 つ破った**（ツール網羅・glob の形式列挙・hook の有効化タイミング）。うち 2 つは欠陥として出荷され、フレッシュエージェントのレビューで初めて検出された。

**対照**: 同じセッションで `skill-design-patterns.md` のルール（停止契約の構造・片側修正の禁止・境界の相互明記）は一貫して守れていた。差は **CLAUDE.md の `@` 参照でセッション開始時に全文がロードされていたか否か**だけ。導線の文言は両方とも CLAUDE.md にあった。

**期待**: 「@ を外して必要時に読む導線にする」判断（コンテキスト固定費の削減）は維持しつつ、**作業の瞬間に読ませるトリガー**が要る。

**含意（重要）**: このタスクの Phase 3 で `skill-design-patterns.md` の `@` を外した。今回の実測は、**次セッション以降のスキル作業で同じ失敗が再現しうる**ことを示している。`@` を戻すのは固定費の観点で割に合わないため、別の仕組みが要る。

**昇格候補の案**（compound で検討）:
- `.claude/settings.json` / `.claude/hooks/**` の編集を検知する PreToolUse hook を置き、`claude-code-config.md` を読むよう `additionalContext` で促す（`post-edit-lint.sh` が診断行を AI に返すのと同じ型）
- 同様に `.claude/skills/**/SKILL.md` の編集で `skill-design-patterns.md` を促す
- あるいは CLAUDE.md の導線を「読む」から「**読んでから編集する**」という順序の命令形に変え、該当スキル（`compound` / `rule-audit` 等）の手順にも組み込む

**該当**: CLAUDE.md のドキュメント参照節 / hooks の構成
