# SPIKE レーンの手順（探索実装）

`SKILL.md` の「SPIKE レーン」節から参照される手順の詳細。入口・制約・出口を扱う。
**出口（破棄 / DRAFT 戻し）に進む前に必ず全文を読む。** 停止条件（`decisions.md` に最低 1 エントリ）は SKILL.md 本文にも書いてある。

### 入口

- **新規**: Phase 2 でユーザーが探索を選んだら `Status: **SPIKE**` で生成してよい（既定は DRAFT）
- **既存 DRAFT**: ユーザー明示で `Status: **SPIKE**` に更新してよい

### SPIKE 中の制約

- ローカル実装可（`impl-from-design` が扱う）
- **外向き禁止**: push / remote 操作 / PR 作成をしない
- 破棄前提の短い探索（滞在上限の機械ルールは設けない）

### 出口（どちらも `decisions.md` に最低 1 エントリ必須。無ければ出口に進まない）

**(a) 破棄**
1. 試したこと・捨てる理由を `decisions.md` に書く
2. 作業ツリー差分を提示し、ユーザー確認後にのみ戻す（黙って `git reset --hard` しない）
3. SPIKE 中に作った `review-result.md` があれば破棄する（残置禁止）
4. タスク整理（アーカイブ等はユーザー判断）

**(b) 本実装へ（DRAFT 戻し）**
1. 試したこと・残す/捨てる理由を `decisions.md` に書く
2. **作業ツリーを捨てるか残すかの明示ゲート**（黙った残置は禁止）
   - 捨てる: 確認後に差分を戻してから契約コアを更新し `Status: **DRAFT**`
   - 残す: 「再実装ではなく、残差分を設計に**SPIKE 吸収**する」経路であることを明示し、契約コアを実態に合わせて更新してから `Status: **DRAFT**`（APPROVED 維持の「APPROVED 追認」とは別語）
3. SPIKE 中の `review-result.md` があれば破棄する（pipeline 汚染防止）
4. 通常の Phase 3（人間レビュー）→ APPROVED へ。SPIKE のまま承認して APPROVED にはしない
