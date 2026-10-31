# AI Skills — フロントエンド開発ワークフロー

個人用の Claude Code スキルセット。React / TypeScript のプロジェクトで、設計 → 実装 → レビュー → PR の要所で止まるための少数のスキルと、それを支える hook・検査をまとめている。

**スタック**: React / TypeScript / Vitest / React Testing Library / MSW / Playwright

各スキルの手順は `.claude/skills/[name]/SKILL.md` が一次情報。この README は全体像だけを示す。使い方（言うフレーズ・FAQ）は [docs/user-guide.md](docs/user-guide.md)。

## 方針

- **スキルは、スキルなしより良い結果になったものだけを残す。** 2026-10 の刷新で、サンプルアプリの課題をスキルなし（A）・現行（B）・書き直し（C）で比べ、A と同点だったスキルは削除した（記録: `.steering/20261006-skillset-renewal/decisions.md`、手順: [eval/README.md](eval/README.md)）
- 残ったのは、ユーザーに決めてもらうことを聞いて止まる・外に出る操作の前で止まる・決まった記録先を守る、という役割のもの
- 作業の進め方（大きさで 3 段階）は [CLAUDE.md](CLAUDE.md) に行動ルールとして書く。スキルは発動したときの手順だけを持つ

## 作業の流れ

```
小さな作業   宣言してそのまま進める
中くらい     design-doc（会話で設計を示して止まる）→ OK → 実装 → frontend-code-review
大きな作業   design-doc（.steering/ に design.md を作って止まる）→ /design-premortem（任意）
             → APPROVED → 実装（e2e は主要な流れだけ）→ frontend-code-review
             → steering でアーカイブ → pr-create（push の前で止まる）→ マージ（人）
再開         steering（design.md・tasklist.md・decisions.md を読み合わせて次の項目を示す）
振り返り     session-retrospective → .steering/[task]/skill-issues.md → 頼まれたら改善の案
```

## スキル

| スキル | 役割 | 止まる場所 |
|---|---|---|
| [`design-doc`](.claude/skills/design-doc/SKILL.md) | 設計を書く。ユーザーにしか決められないことを聞く。大きな作業は `.steering/` に design.md（DRAFT）と tasklist.md を作る | 設計を示したところ（承認まで実装しない） |
| [`design-premortem`](.claude/skills/design-premortem/SKILL.md) | 書いた design.md を、文脈を持たない攻撃役に読ませて穴を追記する。**手動専用**（`/design-premortem` で呼ぶ） | 所見を追記したところ（承認はしない） |
| [`steering`](.claude/skills/steering/SKILL.md) | `.steering/` のタスクの再開・一覧・アーカイブ | DRAFT のときは実装しない。アーカイブの前に確認 |
| [`e2e`](.claude/skills/e2e/SKILL.md) | E2E テストを主要な流れに絞って書く・レビューする | レビューは直さずに返す |
| [`frontend-code-review`](.claude/skills/frontend-code-review/SKILL.md) | バグ担当 2・規約担当 1（＋該当時に UI と a11y・テスト）で一次レビューし、検証役が確かめた指摘だけを返す | 指摘を返したところ（コードは直さない） |
| [`pr-create`](.claude/skills/pr-create/SKILL.md) | コミットとブランチを整え、差分から PR のタイトルと本文を書く | push と PR 作成の前。マージはしない |
| [`session-retrospective`](.claude/skills/session-retrospective/SKILL.md) | 訂正・手戻り・拒否・曖昧さを skill-issues.md に記録する | 止まらない（`.steering/` への記録だけ） |
| [`skill-test`](.claude/skills/skill-test/SKILL.md) | **マスター専用**。静的検査と、`claude plugin eval` の回帰ケースの実行（課金の前に承認） | 課金の実行の前 |

agent（`.claude/agents/`）: `review-bug`・`review-rules`・`review-ui-a11y`・`review-test`・`review-verify`（frontend-code-review が使う）、`premortem-attacker`（design-premortem が使う）。モデル・エフォート・使える道具は定義の側に書く。読み取り専用の agent は Bash を持たない（`git diff --output=` などで書けてしまうため）。

## ディレクトリ構成

```
.
├── CLAUDE.md                 # 行動ルール（50 行以内。validate が検査）
├── .claude/
│   ├── settings.json         # パーミッション・hook の登録
│   ├── hooks/                # SessionStart のタスク一覧・承認制パスのガード・lint と typecheck の差し戻し・SKILL.md 編集時の検査
│   ├── skills/               # 上の 8 本
│   └── agents/               # 上の 6 本
├── .steering/                # 複数セッションのタスク（design.md・tasklist.md・decisions.md など）
├── eval/                     # スキルの評価（A・B・C の比較）と回帰テスト（マスター専用）
├── scripts/validate_skills.py # スキルの frontmatter・構造・CLAUDE.md の行数の検査（マスター専用）
├── tests/hooks/              # PreToolUse hook のフィクスチャ（test:hooks）
├── templates/                # 新しいスキルの雛形（マスター専用）
├── prompts/                  # 人が貼って使う、スキルの敵対的レビューのプロンプト（マスター専用）
├── mise.toml                 # ツールチェーン（node / pnpm）。検証は mise exec -- pnpm run …
└── docs/
    ├── user-guide.md         # スキルを使う人向けのガイド（配置先にもコピーしてよい）
    └── knowledge/            # 経験・パターン（必要なときに読む）
```

## 検査（ローカルで回す。課金なし）

```bash
mise exec -- pnpm run validate     # スキルの frontmatter・構造、CLAUDE.md の行数
mise exec -- pnpm run test:hooks   # PreToolUse hook のフィクスチャ
mise exec -- pnpm run lint         # Biome
```

スキルを変えたら、skill-test で回帰ケース（[eval/README.md](eval/README.md) の「回帰テスト」）を回す。課金があるので、見積もりを示して承認を取ってから、通常のターミナルで流す。

## hook と設定

- **SessionStart**（`session-start-check.sh`）: `.steering/` のアクティブなタスクの一覧を context に注入する
- **承認制パスのガード**（`guard-gated-write.sh`・`guard-gated-delete.sh`）: permissions の ask と同じパス（CLAUDE.md・docs/knowledge/ など。正本は hook 冒頭の `# GATED_PATHS:` 行）への、Bash 経由の書き込みを ask に、素の `rm`・`mv` を deny にする。Claude Code はリダイレクト先を Edit の allow・deny だけで判定し、ask を見ないため
- **`.env` の読み取りのガード**（`guard-env-read.sh`）・**品質ゲート**（`post-edit-lint.sh`・`stop-typecheck.sh`・`validate-skill-edit.sh`）
- settings.json と hook の構成は、sandbox に乗せ直す作業（刷新の 6 章）で変わる予定

## 他のプロジェクトで使う

最初に 1 回、`.claude/`（skills・agents・hooks）と settings をコピーし、以後は配置先で案件に合わせて育てる。マスターとは同期しない。マスター専用のもの（skill-test・eval・scripts・templates・prompts）は持っていかない。

コピーの手順と、一緒に持っていくものの一覧（例: frontend-code-review には review-* の agent 5 本、design-premortem には premortem-attacker）は、刷新の 7 章で書く。
