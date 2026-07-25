# 福利化ログ: skillset-hardening

## 20260725 — compound 実行

### 昇格したパターン

1. **昇格したら既存の違反箇所を洗い出して直す** → `compound/SKILL.md`（Step 4 に手順追加）
   - 根拠（効果検証）: 「@参照は毎セッション展開される」を 20260702 に昇格したが、`CLAUDE.md` の実物は外されず、20260721 に固定費として再認識されてもなお残り、20260725 の 8 軸評価で 3 度目に検出されて初めて修正された。昇格の完了条件に「既存違反ゼロ」が無かったのが原因
2. **「必要時に読む」ドキュメントの要点を作業の瞬間に注入する** → `.claude/hooks/remind-config-docs.sh`（新規）+ PostToolUse 登録
   - ポインタではなく**本文**を注入する形にした。同一セッションで、@参照で全文ロードされていた `skill-design-patterns.md` のルールは守れ、ポインタだけの `claude-code-config.md` は 3 ルール違反した — 差は「内容が context にあったか否か」だけだった
   - カテゴリごとにセッション 1 回だけ発火（毎回注入すると新しい固定費になる）
   - **⚠ 効果は未検証**: hook の発火は実測したが、「注入された内容を実際に守るか」は次タスクで観察する
3. **`git add -A` / `git commit` の前にステージ内容を確認する** → `CLAUDE.md`（自律実行の境界）
   - 根拠: サブエージェントが「変更するな」の指示に反して作成した検証ゴミ 28KB を、確認せずコミットした
4. **ハードストップ検出を強化形にも当てる** → `scripts/validate_skills.py`（項目7）
   - 根拠: `ここで必ず止まる` という**より強い**表現が literal 不一致で誤 FAIL した。`(ここで|必ず)止ま` に緩めた（語幹 `止ま` までは緩めない — 「行き止まり」等で誤 PASS するため）
5. **自己レビューで代替した場合は成果物に明記し Status を確定しない** → `frontend-code-review/SKILL.md`
   - 根拠: 自己レビュー High 1 件に対し、フレッシュ 3 体が 3 件追加検出。うち 2 件は本人が書いたスクリプトの中核ロジック

### 変更したファイル

- `.claude/skills/compound/SKILL.md`
- `.claude/skills/frontend-code-review/SKILL.md`
- `.claude/hooks/remind-config-docs.sh`（新規）
- `.claude/settings.json`（PostToolUse に登録・PreToolUse の構造変更）
- `CLAUDE.md`
- `scripts/validate_skills.py`
- `docs/knowledge/claude-code-config.md`（hook のイベント種別による挙動差を訂正・追記）

### 既存違反の洗い出し（新ルール1 の適用）

- 候補4: validator 全件 — master 29/29・持ち出し 10/10・template PASS（誤 FAIL / 誤 PASS なし）
- 候補5: 既存の `review-result.md` は Status DEFERRED で準拠済み
- 候補3: 追跡下に検証ゴミの残存なし

### 昇格しなかったもの

- `knowledge-capture` で docs へ保存済みの知見（停止契約の型・自己レビューの限界・検出ツールの3規律）— 重複のため
