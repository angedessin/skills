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
             → pr-create（push の前で止まる）→ steering でアーカイブ → マージ（人）
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

frontend-code-review の限界: テスト担当はテストファイルが変わったときだけ動くので、実装だけを変えた差分のテストの抜けは見ない。

## ディレクトリ構成

```
.
├── CLAUDE.md                 # 行動ルール（50 行以内。validate が検査）
├── .claude/
│   ├── settings.json         # パーミッション・sandbox・hook の登録
│   ├── hooks/                # SessionStart のタスク一覧・承認制パスのガード・lint と typecheck の差し戻し・SKILL.md 編集時の検査
│   ├── skills/               # 上の 8 本
│   └── agents/               # 上の 6 本
├── .steering/                # 複数セッションのタスク（design.md・tasklist.md・decisions.md など）
├── eval/                     # スキルの評価（A・B・C の比較）と回帰テスト（マスター専用）
├── scripts/validate_skills.py # スキルの frontmatter・構造・CLAUDE.md の行数・依存の一覧の検査（マスター専用）
├── tests/hooks/              # PreToolUse hook のフィクスチャ（test:hooks）
├── tests/sandbox/            # settings.json と sandbox の検査（test:sandbox・test:sandbox:probe）
├── templates/                # 新しいスキルの雛形（マスター専用）と、配置先の settings の雛形
├── prompts/                  # 人が貼って使う、スキルの敵対的レビューのプロンプト（マスター専用）
├── mise.toml                 # ツールチェーン（node / pnpm）。検証は mise exec -- pnpm run …
└── docs/
    ├── user-guide.md         # スキルを使う人向けのガイド（配置先にもコピーしてよい）
    └── knowledge/            # 経験・パターン（必要なときに読む）
```

## 検査（ローカルで回す。課金なし）

```bash
mise exec -- pnpm run validate     # スキルの frontmatter・構造、CLAUDE.md の行数、依存の一覧
mise exec -- pnpm run test:hooks   # PreToolUse hook のフィクスチャ
mise exec -- pnpm run test:sandbox # settings.json の形（sandbox の中での確認は tests/sandbox/README.md）
mise exec -- pnpm run lint         # Biome
```

スキルを変えたら、skill-test で回帰ケース（[eval/README.md](eval/README.md) の「回帰テスト」）を回す。課金があるので、見積もりを示して承認を取ってから、通常のターミナルで流す。

## hook と設定

- **SessionStart**（`session-start-check.sh`）: `.steering/` のアクティブなタスクの一覧を context に注入する
- **承認制パスのガード**（`guard-gated-write.sh`・`guard-gated-delete.sh`）: permissions の ask と同じパス（CLAUDE.md・docs/・.claude/。正本は hook 冒頭の `# GATED_PATHS:` 行）への、Bash 経由の書き込みを ask にする。プロジェクトの中の CLAUDE.md・docs/ への `rm`・`mv` は deny にする（`.claude/` の素の `rm`・`mv` は sandbox が止める）。sandbox には「承認すれば進む」が無く、作業ディレクトリの CLAUDE.md・docs/ も守らないため
- **品質ゲート**（`post-edit-lint.sh`・`stop-typecheck.sh`・`validate-skill-edit.sh`）
- **sandbox**（`.claude/settings.json`）: Bash の秘密の読み取り・通信先・書き込み範囲を OS のレベルで制限する。`.env` の読み取りも止める。`autoAllowBashIfSandboxed: false` で、sandbox の中の Bash も通常の確認に乗せる（hook が見ない `sed -i` などの書き込みを確認なしで通さないため）。hook は sandbox の外で動く

## 他のプロジェクトで使う

最初に 1 回コピーし、以後は配置先で案件に合わせて育てる。マスターとは同期しない。plugin にしないのは、配置先でスキルを書き換えたいため（plugin のスキルは更新で上書きされ、1 本だけオフにもできない）。

### コピーの手順

通常のターミナルで、マスターのルートから流す（sandbox を有効にした Claude Code の中からは、作業ディレクトリの外に書けない）。

```bash
DEST=/path/to/project
mkdir -p "$DEST/.claude/skills" "$DEST/.claude/agents" "$DEST/.claude/hooks"

# スキルと agent: 下の依存の一覧から選ぶ（例は設計・再開・レビュー・PR）
cp -R .claude/skills/{design-doc,steering,frontend-code-review,pr-create} "$DEST/.claude/skills/"
cp .claude/agents/review-*.md "$DEST/.claude/agents/"

# hook: 配る 5 本と、guard hook の共通の部品
cp .claude/hooks/{guard-gated-delete,guard-gated-write,post-edit-lint,session-start-check,stop-typecheck}.sh .claude/hooks/guard_gated.py "$DEST/.claude/hooks/"

# 知識: frontend-code-review の規約担当が読む
mkdir -p "$DEST/docs"
cp -R docs/knowledge "$DEST/docs/"

# settings: 既にあれば上書きしない。そのときは手で合わせる
cp -n templates/settings.template.json "$DEST/.claude/settings.json"
```

コピーした後に配置先で確かめる:

- `mise.toml` のあるプロジェクトは、Claude Code を起動する前に通常のターミナルで `mise trust` を流す。sandbox の中では信頼の記録を書けず、`mise exec` が失敗する
- Claude Code を再起動する。sandbox を有効にする前から動いていたプロセスでは、通信先の制限が効かなかった（`/clear` では直らない）
- 雛形の `allowedDomains` は GitHub と npm だけ。案件で要る通信先を足す。これは絶対の上限ではない。auto モードでは、Claude がコマンドごとに通信先を足し、自動の判定が認めれば確認なしで届く（公式の per-command allowed domains）。manual と acceptEdits では確認が出て、許可すれば届く。必ず止めたいなら、ユーザー設定か `--settings` で `network.strictAllowlist` を入れる（リポジトリの settings では効かない）
- hook を減らしたら、settings の登録も消す
- **sandbox の設定はチェックアウト中のブランチに従う。** 設定の無いブランチへ切り替えると、sandbox も guard hook も何の表示もなく外れる。設定を入れたコミットを統合ブランチに入れてからブランチを切り直し、古いブランチへ切り替えたら `/sandbox` で確かめる
- `allowLocalBinding: true` で、E2E の開発サーバーがローカルのポートを listen できる。macOS では、sandbox の中のコマンドが localhost の他のサービスにも届くので、認証の無いサービスを動かしている案件では外すか、E2E を通常のターミナルで動かす。Vite の起動までは確かめた。Playwright のブラウザの起動は確かめていない
- `permissions.allow` を足すと守りが薄くなる。`excludedCommands` のコマンドは sandbox の外で動き、`git rebase --exec` のように任意の処理も動かせる。今は通常の確認（auto モードでは自動の判定）だけが守っている
- `gh` は `gh pr`・`gh api`・`gh repo view` だけを sandbox の外に出す。ほかのサブコマンドが要るなら `excludedCommands` に足す。除外が効くのは呼び出し全体が一致するときだけで、パイプ・`cd`・リダイレクトを付けると sandbox の中に残り、TLS や SSH の検証で失敗する。単独で呼び、本文は `--body-file` で渡す
- `.env` の読み取り禁止は Bash から動かす開発ツールにも効く。Vite の `loadEnv` はエラーを出さずにそのファイルを飛ばすので、値が黙って入らない。追跡している `.env.example` などでは、`git status`・`git add` がエラーを表示したまま rc=0 で終わる。`.env` を使う案件では `sandbox.filesystem.denyRead` を案件に合わせて絞るか、その開発ツールを通常のターミナルで動かす

### 依存の一覧

`mise exec -- pnpm run validate` が、この 2 つの表と実際のスキル・agent・hook・雛形を突き合わせる。

- **agent:** 無いと、スキルは汎用の subagent に指示を渡す代替に落ちる。一緒に持っていく
- **案内先のスキル:** 本文で名前を出すだけで、無くても動く

<!-- deps:skills -->
| スキル | agent | 案内先のスキル | 配るか |
|---|---|---|---|
| `design-doc` | - | `design-premortem`・`steering` | 配る |
| `design-premortem` | `premortem-attacker` | `design-doc` | 配る |
| `steering` | - | `design-doc` | 配る |
| `e2e` | - | `frontend-code-review` | 配る |
| `frontend-code-review` | `review-bug`・`review-rules`・`review-ui-a11y`・`review-test`・`review-verify` | `e2e` | 配る |
| `pr-create` | - | - | 配る |
| `session-retrospective` | - | - | 配る |
| `skill-test` | - | - | マスター専用 |

<!-- deps:hooks -->
| hook | 要るもの（無ければ素通し） | 配るか |
|---|---|---|
| `session-start-check.sh` | - | 配る |
| `guard-gated-write.sh` | python3（無ければ全文 grep に縮退） | 配る |
| `guard-gated-delete.sh` | python3 | 配る |
| `guard_gated.py` | guard hook 2 本が呼ぶ部品 | 配る（部品） |
| `post-edit-lint.sh` | Biome か ESLint か Stylelint の設定 | 配る |
| `stop-typecheck.sh` | jq・tsconfig.json・tsc | 配る |
| `validate-skill-edit.sh` | `scripts/validate_skills.py` | マスター専用 |

持っていかないもの: `eval/`・`eval-pilot/`・`scripts/`・`tests/`・`prompts/`・`templates/`（雛形のコピーを除く）。`docs/user-guide.md` は持っていってもよい。

### 配置先の CLAUDE.md

スキルは CLAUDE.md が無くても動くが、評価は `.steering/` の行動ルールを含む CLAUDE.md（`eval/common-claude-md.md`）がある状態で比べた。同じ結果を期待するなら、マスターの CLAUDE.md の「作業の進め方」と「自律実行の境界」を配置先の CLAUDE.md に写し、案件に合わせて直す。「スキル管理」「環境」はマスターの事情なので写さない。

### settings の雛形

`templates/settings.template.json` は、マスターの `.claude/settings.json` とマスター専用の `validate-skill-edit.sh` を登録しないことだけが違う（`test:sandbox` が検査する）。

`sandbox.failIfUnavailable` は `true` で、sandbox の使えない環境では起動時に止まる。`.env` の Bash からの読み取りを止めているのが sandbox なので、黙って守りが消えないようにする。そうした環境で使うなら `false` にするが、`.env` などの Bash からの読み取りを OS のレベルでは止められなくなる。どのコマンドが確認なしで読めるかは確かめていないので、`Bash(cat .env*)` などの deny を足す。

**`permissions.allow` に git の読み取り系（`Bash(git diff*)` など）を書かない。** 読み取りの形は書かなくても確認なしで動く。allow のパターンは書き込みの形にも一致する（公式の例: `Bash(git log * main)` は `git log --output=<file> main` に一致する）。20261103 に公式の permissions で確認した。
