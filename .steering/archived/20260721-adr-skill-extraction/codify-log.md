# Codify Log: 20260721-adr-skill-extraction

## 20260721 — compound 実行

### 昇格したパターン

- **Key components 表を検証可能な形にする** → `design-doc` スキル（Phase 2）
  今回、表が 7 ファイルで打ち切られ片側修正になりかけ、「`adr` に変更」としか
  書いていなかったため Constraints 違反にレビューで気づけなかった（design-premortem が検出）。
  「原本を開かずに制約違反を判定できる情報を各行に書く」+「表は暫定・実装前に全文 grep で確定」
  の 2 点を追加。配布可スキルのため汎用形で記述（配布分類という語彙は入れない）

- **固有名は書く時点で実在確認する** → `design-doc` スキル（Phase 2）
  `export/20260714-company/` を 3 重に誤って design.md に記載した失敗から。
  (1) 同日 e037440 でリネーム済み (2) main には無く別ブランチ (3) b08ab67 で
  独立フォーク運用になり skill-harvest 不可。会話の早い段階の grep 結果を裏取りせず転記したのが原因

- **スキル変更時に配布分類を先に確認する** → `CLAUDE.md`（行動ルール 1 行）
  design-doc は配布可のため配布分類という語彙を入れられない。リポジトリ固有の具体は
  CLAUDE.md 側に置く分担にした

### 却下した昇格先

- `docs/knowledge/skill-design-patterns.md` への追記（2 件）
  → 却下。同ファイルは 240 行かつ CLAUDE.md から @参照（毎セッションの固定費）で、
  追記は説明文であって手順ではない。「説明文では守られない」の規律を自らに適用し、
  同じ内容を design-doc の構造（表の書き方）と CLAUDE.md の行動ルールに落とした

### 効果検証

`review-result.md` / `codify-log.md` が今回タスクに無いため突合対象なし。
ただし会話中に「片側修正の禁止」（skill-design-patterns の昇格済みルール）に**反しかけた**
事象が発生した。ルール自体は正しく、欠けていたのは洗い出しの手順。
→ 上記 1 件目でその手順を補った

### 変更したファイル

- `.claude/skills/design-doc/SKILL.md`（v1.6 → v1.7）
- `CLAUDE.md`
