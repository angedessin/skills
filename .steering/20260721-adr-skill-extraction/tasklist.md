# Tasklist: 20260721-adr-skill-extraction

## Pre-implementation

- [x] `ADR` / `docs/decisions` / `knowledge-capture` の 3 語で全文 grep し、Key components 表を確定させる
      （4 件の洗い残しを検出: compound :64 / rule-audit :19 / steering references :143 / user-guide :43）
- [x] `skill-deploy` に master-only 除外リストの実体があるか確認（Open questions 5）
      → `scripts/deploy_skills.py:45` の `MASTER_ONLY` と `skill-deploy/SKILL.md:51` の 2 箇所に実体あり

## Implementation

- [ ] `templates/SKILL.template.md` をコピーして `.claude/skills/adr/SKILL.md` を作成
  - [ ] frontmatter: master-only を description に明記（skill-harvest / skill-test の書式に合わせる）
  - [ ] description に When NOT to use（既存 ADR の閲覧・decisions.md への記録では発動しない）
  - [ ] Step: 起票判定（却下した代替案があるか。無ければ ADR にしないと案内して終わる）
  - [ ] Step: 近縁 ADR 検出（ファイル名 + `# Decision:` 見出し行のみ。本文全文は読まない）
  - [ ] Step: **ハードストップ** — ドラフト提示 → 明示承認を待つ。書き込みはその後
  - [ ] Step: 書き込み後、`.steering/[task]/decisions.md` に ADR へのリンク行を追記
  - [ ] Step: Superseded / Amended の印付けと相互リンク（既存 7 本への遡及適用は行わない）
- [ ] `knowledge-capture` 改修（配布可）
  - [ ] Step 2 決定木: ADR 枝を削除。「却下した代替案がある決定」は decisions.md に記録し、
        「チームの決定記録に上げるか検討してください」と添えて終わる（ADR 形式は与えない）
  - [ ] `.steering/` のタスクディレクトリが無い場合は会話で提示して終わる旨を同ステップに明記
  - [ ] 「ADR 形式のドラフトを提示しない」の禁止句を明示ステップとして書く
  - [ ] Step 5: `docs/decisions/` 書き込み節と Superseded 段落を削除
  - [ ] glossary: 決定木の枝と Step 5 の節を削除
  - [ ] 本文・frontmatter から `ADR` / `Nygard` / `docs/decisions` の語を一掃
  - [ ] **`adr` というスキル名を書かない**（配布可のため）
  - [ ] metadata.version を上げる
- [ ] `compound` 改修（配布可・**4 箇所**）
  - [ ] :17 When NOT to use / :21 境界 / :64 昇格候補 4 / :228 Related skills から「ADR・語彙」を削除
  - [ ] `adr` の名は書かない
  - [ ] metadata.version を上げる
- [ ] `rule-audit`（配布可・**2 箇所**）: :19 から ADR を削除 / :60 の「knowledge-capture の担当」を削除
      （どちらも `adr` に置き換えない）
- [ ] `session-retrospective`（配布可）: :16 から `docs/decisions/` を削除
- [ ] `feature-pipeline`（配布可）: :240 の知見保存フェーズから `docs/decisions/` を削除
- [ ] `steering/references/spec.md`（配布可）: :143 の ADR 参照を削除
- [ ] `CLAUDE.md`: 「ナレッジ保存先のルール」表の ADR 行を `adr` スキル経由と明記
- [ ] `README.md` 必須 3 箇所 + スキル一覧
  - [ ] :46 ディレクトリツリー / :158 knowledge-capture 説明（glossary 含む）/ :177 データフロー図
  - [ ] スキル一覧に `adr` を追加
  - [ ] :73 / :92 のワークフロー図に `adr` を足すか判断（推奨: 足さない。足すなら feature-pipeline と同一コミット）
- [ ] `docs/user-guide.md` :43 のスキル分類。`adr` を**手動起動**側に追加
- [ ] `docs/starter-kit.md` :31 の master-only 行に `adr` を追加
      （:4 / :15 の ADR 参照は ADR そのものを指すため変更しない）
- [ ] `scripts/deploy_skills.py` :45 の `MASTER_ONLY` に `"adr"` を追加
- [ ] `.claude/skills/skill-deploy/SKILL.md` :51 の master-only 列挙に `adr` を追加
      （deploy_skills.py と同一コミット — 片側修正の禁止）

## Verification

- [ ] `python3 scripts/validate_skills.py` が全スキル PASS（`adr` の停止契約検査を含む）
- [ ] `python3 scripts/validate_skills.py --purity` で `adr` のツール語彙出現数を確認
- [ ] `knowledge-capture/SKILL.md` に `ADR` `Nygard` `docs/decisions` が 0 件
- [ ] `compound` / `rule-audit` / `session-retrospective` / `feature-pipeline` に `adr` が 0 件
- [ ] `knowledge-capture` / `compound` に `glossary` `語彙` が 0 件
- [ ] `adr` が `skill-deploy` の配布対象に含まれない（または starter-kit に手動除外の注記）
- [ ] Open questions の結論を design.md に反映

## Deploy

- [ ] コミット 1: glossary 分岐の削除（掃除・挙動不変）
- [ ] コミット 2: ADR の master-only 切り出し（挙動変更）
- [ ] main へ直接コミット

## Compound

- [x] `compound` スキルの実行（昇格 3 件: design-doc に 2 件・CLAUDE.md に 1 件。
      skill-design-patterns への追記 2 件は「説明文であって手順ではない」として却下。詳細は codify-log.md）
- [x] `knowledge-capture` スキルの実行（`docs/knowledge/review-workflow.md` に
      design-premortem の費用対効果を追記。あわせて design-premortem v1.1 で
      「渡す情報の切り分け」を明文化 — 遮断するのは会話履歴でありリポジトリ参照は許可する）
- [ ] `steering` スキルの archive モードでアーカイブ
