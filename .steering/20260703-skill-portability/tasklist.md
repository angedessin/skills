# Tasklist: skill-portability

Last updated: 20260703

## Implementation

- [x] `scripts/validate_skills.py` 新設（5 項目検証・終了コード・依存ゼロ・対象ディレクトリ指定可）
- [x] 全 19 スキルの frontmatter に `metadata.version: "1.0"` を一括付与
- [x] validate で全 19 スキル PASS を確認（付与前 0/19 → 付与後 19/19）
- [x] `docs/starter-kit.md` 新設（構成表 4 セット・配置 5 手順・CLAUDE.md 雛形・ドリフト確認手順）
- [x] README 横展開節: 段階基準表 + starter-kit.md リンク + 配置前チェックコマンド
- [x] `rule-audit/SKILL.md` Step 4 改訂（validate_skills.py → skills-ref → 手動の優先順）

## Verification

- [x] validate_skills.py の FAIL 検出確認（scratchpad で name 不一致・アストラル面絵文字・引用符なし description・metadata 欠落の 4 種を検出）
- [x] metadata 付与前後の git diff 目視（19 ファイル・挿入は metadata 2 行のみ — 非破壊確認）
- [x] 構造検証: 新規/改訂ファイルのアストラル面絵文字なし
- [ ] starter-kit 手順の実地検証は初回配置時に繰り越し

## Deploy

- [x] コミット（main 直コミット運用）

## Compound

- [x] compound スキルの実行（昇格候補ゼロ — 核心判断は design.md / starter-kit.md に記録済み。効果検証: 絵文字禁止ルールが validate で機械化）

## Knowledge

- [x] knowledge-capture スキルの実行（新規保存なし — starter-kit.md 自体が知識成果物）
- [x] steering archive モードでアーカイブ

---

Archived: 20260703
繰り越し（配置時作業）: starter-kit 手順の実地検証は初回配置時に行う
