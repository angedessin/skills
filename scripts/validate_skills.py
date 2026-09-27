#!/usr/bin/env python3
"""スキル frontmatter・構造の機械検証（マスター専用ツール・依存ゼロ）。

検証項目:
  1. name がディレクトリ名と一致する
  2. description が引用符付き 1 行で 1024 文字以内
  3. ファイル全体が 500 行以内
  4. アストラル面文字（U+10000 以上）を含まない
  5. metadata.version がある
  6. 本文に「When NOT to use」を含む見出しがある（発動境界の明示）
  7. 承認語彙（承認 / APPROVED）が出現するスキルは、本文にハードストップ表現
     （「ここで止ま」または見出しの STOP）を 1 つ以上持つ。否定形（承認不要 等）は
     トリガーから除外。逃し弁として本文に <!-- validator: no-stop-needed --> があればスキップ。
  8. 既定の .claude/skills 走査時: design-doc/references/templates.md に
     design-doc-boundary: appendix がある（契約コア/付録境界）
  9. 既定走査時: design↔実装同期パスのキー共存（design-doc 方針転換 / impl-from-design
     乖離分類 / impl-review・frontend-code-review・feature-pipeline の設計整合ゲート）。
     キーワード並びのみ検査し、手順の実行正否は見ない（空文で通る限界あり）
  10. 既定走査時: capture 粒度（三択 UX / archive ハードストップ）のキー共存。
      キーワード並びのみ。空文で通る限界あり（design-impl-sync と同型）
  11. 既定走査時: knowledge 鮮度ナッジのキー共存
  12. 既定走査時: tasklist 工程表同期（FCR 知見保存→デプロイ順 + 6 節キー）。
      キーワード並びと出現位置のみ。空文で通る限界あり

純度計測・ポータビリティ（レポートのみ・FAIL にしない）:
  python3 scripts/validate_skills.py --purity        # 各スキル本文のツール固有 API 出現数
  python3 scripts/validate_skills.py --portability   # 配布可スキルのマスター内部前提（日付・固有語）
  python3 scripts/validate_skills.py --portability --strict  # 同上。1 件でもあれば exit 1（CI 用）

使い方:
  python3 scripts/validate_skills.py                 # .claude/skills/ 全体
  python3 scripts/validate_skills.py <dir>           # 指定ディレクトリ配下の各スキル
  python3 scripts/validate_skills.py --skill <dir>   # 単一スキル（そのディレクトリ自体）のみ
  python3 scripts/validate_skills.py --template      # templates/SKILL.template.md（プレースホルダ許容）
  python3 scripts/validate_skills.py --purity        # ツール純度レポート（FAIL にしない）
  python3 scripts/validate_skills.py --portability   # ポータビリティレポート（FAIL にしない）
  python3 scripts/validate_skills.py --portability --strict  # 混入 1 件以上で exit 1
終了コード: 0 = 全 PASS / 1 = FAIL あり（--portability --strict は混入あり） / 2 = 使い方の誤り（不明なオプション等）
"""
import re
import sys
from pathlib import Path

# 項目8（純度計測）で数えるツール固有語彙。本文（frontmatter・references/ を除く）に
# これらが出るほどエンジン純度が下がる。skill-design-patterns.md「エンジン純度を実測する」を機械化。
TOOL_VOCAB = [
    "gh", "git", "npx", "pnpm", "npm", "yarn", "node", "python3",
    "playwright", "vitest", "jest", "eslint", "biome", "tsc", "curl", "jq",
]

# ツール固有の API 名（メソッド・識別子・設定キー）。ツール名（vitest 等）の grep が 0 件でも
# これら API 名が本文に残ると、別ランナー（Jasmine 等）では実行不能なテストを書かせる。
# skill-design-patterns.md「語彙の grep はエンジン純度の検査にならない。… API 名のリストで測る」を機械化。
# 実例（20260723）: tdd 本文で vitest/testing-library の grep は 0 件だったが includeSource /
# queryBy / toBeInTheDocument が残っていた。
API_VOCAB = [
    "queryBy", "getBy", "findBy", "queryAllBy", "getAllBy", "findAllBy",
    "toBeInTheDocument", "toHaveTextContent", "toBeVisible", "toBeDisabled",
    "toHaveBeenCalled", "includeSource", "renderHook", "fireEvent", "userEvent",
]

# 項目7で承認語彙のトリガーから除外する否定形（自律実行境界の引用による誤 FAIL を防ぐ）。
_APPROVAL_NEGATIONS = ["承認不要", "承認なし", "承認は不要", "承認を要さない"]

# --portability レポート用。配布可スキルの本文・references に「配置先の読み手が解読できない
# マスター内部前提」が混入していないかを検出する（report-only）。
# 検出対象:
#   1. 単独の YYYYMMDD 日付（内部 QA/インシデントの日付付きエピソード。配置先に文脈が無い）。
#      パス（docs/decisions/YYYYMMDD 等・直前が "/"）は除外。
#   2. マスター固有語（配置先に存在しない仕組みを前提にした語）。
# 分類の一次情報は docs/starter-kit.md の配布可否表。この集合が変わったら同表と揃える。
MASTER_ONLY = {"skill-test", "skill-harvest", "skill-deploy", "adr"}
PORTABILITY_VOCAB = [
    "還流", "配布セット", "source-commit", "deployments.md",
    "このマスター", "マスターへ", "マスターの git", "（distributable）",
    "pipeline_state",
]

# design-doc テンプレの契約コア/付録境界（live design.md は対象外・フォールバック全文）
DESIGN_DOC_BOUNDARY_MARKER = "design-doc-boundary: appendix"

# design↔実装同期パス（20260802-design-impl-sync）のキー共存検査。
# 限界: キーワードが並んでいれば通る。手順の意味・順序・勝手変更禁止の実行正否は見ない（空文で通る）。
# 振る舞い契約が要る場合は passthrough（別 BACKLOG）を使う。
DESIGN_IMPL_SYNC_CHECKS = (
    (
        "design-doc",
        (
            ("方針転換が起きた場合", "方針転換節"),
            ("Status: **DRAFT**", "コア変更時の DRAFT 戻し"),
            ("APPROVED 追認", "APPROVED 追認パス"),
            ("review-result.md", "review-result 破棄"),
        ),
    ),
    (
        "impl-from-design",
        (
            ("乖離が生じた場合", "乖離節"),
            ("【乖離の分類提案】", "分類提案テンプレ"),
            ("design-doc", "方針転換への案内"),
        ),
    ),
    (
        "impl-review",
        (
            ("Axis 1", "設計整合 Axis 1"),
            ("設計契約コア不一致", "High 尺度の設計例外"),
            ("design 同期が先", "単独時の次ステップ"),
            ("契約成果物の Axis 1 例外", "空 TS でも Axis 1"),
        ),
    ),
    (
        "frontend-code-review",
        (
            ("設計契約コア不一致", "High 尺度の設計例外"),
            ("design 同期が先", "ゲート入力明示"),
            ("必須警告", "DEFERRED 時警告"),
            ("Axis 1 をスキップしない", "軽量でも Axis 1"),
        ),
    ),
    (
        "feature-pipeline",
        (
            ("APPROVED 追認", "乖離待機の追認分岐"),
            ("Gate 1", "DRAFT 戻し時の Gate 1"),
            ("必須警告", "設計整合 DEFERRED 警告"),
        ),
    ),
)

# capture 粒度（20260803-capture-granularity）のキー共存検査。
# 限界: キーワードが並んでいれば通る。三択の実行正否・rm の実施・archive 停止の実地は見ない（空文で通る）。
CAPTURE_GRANULARITY_CHECKS = (
    (
        ".claude/hooks/session-start-check.sh",
        (
            ("今 / 後で / スキップ", "三択注入文"),
            ("一括スキップ禁止", "複数タスク単位"),
            ("次の Stop", "スキップ寿命"),
        ),
    ),
    (
        "CLAUDE.md",
        (
            ("今 / 後で / スキップ", "三択再掲（任意）"),
            ("一括スキップ禁止", "複数タスク単位"),
            ("次の Stop", "スキップ寿命"),
        ),
    ),
    (
        ".claude/skills/knowledge-capture/SKILL.md",
        (
            ("今 / 後で / スキップ", "三択再掲"),
            ("一括スキップ禁止", "複数タスク単位"),
            ("次の Stop", "スキップ寿命"),
            ("`.codify-needed` 確認より先", "三択を codify より先"),
        ),
    ),
    (
        ".claude/skills/steering/SKILL.md",
        (
            ("知見なしでアーカイブ", "専用省略句"),
            ("ハードストップ", "archive ハードストップ"),
            ("ここで止まる", "未充足時停止"),
            ("`[x]` 単独", "tasklist 単独非充足"),
        ),
    ),
    (
        ".claude/skills/steering/references/spec.md",
        (
            ("今 / 後で / スキップ", "セッション確認"),
            ("知見なしでアーカイブ", "専用省略句"),
        ),
    ),
    (
        "docs/starter-kit.md",
        (
            ("今 / 後で / スキップ", "配置先向け三択"),
            ("次の Stop", "スキップ寿命"),
        ),
    ),
    (
        "docs/user-guide.md",
        (
            ("今 / 後で / スキップ", "user-guide 三択"),
            ("次の Stop", "スキップ寿命"),
            ("知見なしでアーカイブ", "archive ハードストップ"),
        ),
    ),
    (
        "README.md",
        (
            ("今 / 後で / スキップ", "README 三択"),
            ("次の Stop", "スキップ寿命"),
        ),
    ),
)

# knowledge 鮮度ナッジ（20260804-knowledge-freshness-nudge）のキー共存検査。
# 限界: キーワードが並んでいれば通る。閾値判定・date 失敗時の実挙動・マーカー書き込みは見ない（空文で通る）。
# capture の「次の Stop」キーとは混線させない（本検査は【rule-audit 月次】と 30 日再ナッジを使う）。
KNOWLEDGE_FRESHNESS_CHECKS = (
    (
        ".claude/hooks/session-start-check.sh",
        (
            ("【rule-audit 月次】", "ナッジ見出し"),
            ("30 日再ナッジ", "スキップ寿命（capture と別）"),
            ("capture の次 Stop 寿命とは別", "別契約明示"),
            (".last-rule-audit", "マーカーパス"),
            ("2592000", "30 日閾値秒"),
        ),
    ),
    (
        ".claude/skills/rule-audit/SKILL.md",
        (
            (".steering/.last-rule-audit", "マーカーパス"),
            ("承認不要の例外", "Step 5 マーカー例外"),
            ("date +%s", "epoch 書き込み"),
        ),
    ),
    (
        ".gitignore",
        (
            (".steering/.last-rule-audit", "gitignore マーカー"),
        ),
    ),
    (
        "scripts/deploy_skills.py",
        (
            (".steering/.last-rule-audit", "deploy GITIGNORE_LINES"),
        ),
    ),
    (
        "CLAUDE.md",
        (
            ("【rule-audit 月次】", "ナッジ再掲"),
            ("30 日再ナッジ", "スキップ寿命再掲"),
            ("capture の次 Stop 寿命とは別", "別契約再掲"),
        ),
    ),
    (
        "docs/starter-kit.md",
        (
            ("【rule-audit 月次】", "starter-kit ナッジ"),
            ("30 日再ナッジ", "starter-kit スキップ寿命"),
        ),
    ),
    (
        "docs/user-guide.md",
        (
            ("【rule-audit 月次】", "user-guide ナッジ"),
            (".steering/.last-rule-audit", "user-guide マーカー"),
            ("5 行", "ランタイムフラグ行数"),
        ),
    ),
    (
        "README.md",
        (
            ("【rule-audit 月次】", "README ナッジ"),
            ("30 日再ナッジ", "README スキップ寿命"),
        ),
    ),
    (
        "docs/decisions/20260715-docs-lifecycle-tiers.md",
        (
            ("20260804", "Amendment 日付"),
            ("【rule-audit 月次】", "Amendment ナッジ"),
        ),
    ),
)

# tasklist 工程表の同期（20260807-pr13-mustfix）。
# FCR「次のステップ」と skill-design-patterns の節リストが templates.md の 6 節とズレないこと。
# 限界: キーワード・出現位置のみ。空文で通る限界あり（他のキー共存と同型）。
TASKLIST_FLOW_SECTION_KEYS = (
    "実装",
    "レビュー",
    "知見保存",
    "デプロイ",
    "福利化",
    "クローズ",
)


def check_design_doc_template(repo_root: Path) -> list[str]:
    """design-doc/references/templates.md に付録境界マーカーがあることを検査する。"""
    p = (
        repo_root
        / ".claude"
        / "skills"
        / "design-doc"
        / "references"
        / "templates.md"
    )
    if not p.is_file():
        return [f"{p.relative_to(repo_root)} が存在しない"]
    text = p.read_text(encoding="utf-8")
    if DESIGN_DOC_BOUNDARY_MARKER not in text:
        return [
            f"design-doc/references/templates.md に "
            f"`{DESIGN_DOC_BOUNDARY_MARKER}` 境界マーカーが無い"
        ]
    return []


def check_design_impl_sync(repo_root: Path) -> list[str]:
    """design↔実装同期パスのキーが各スキル本文に共存することを検査する。

    キーワード共存のみ。空文で通る限界あり（モジュール先頭コメント参照）。
    """
    errors: list[str] = []
    skills_root = repo_root / ".claude" / "skills"
    for skill_name, keys in DESIGN_IMPL_SYNC_CHECKS:
        p = skills_root / skill_name / "SKILL.md"
        rel = p.relative_to(repo_root)
        if not p.is_file():
            errors.append(f"{rel} が存在しない（design-impl-sync）")
            continue
        text = p.read_text(encoding="utf-8")
        for needle, label in keys:
            if needle not in text:
                errors.append(f"{rel}: design-impl-sync 欠落 — {label}（`{needle}`）")
    return errors


def check_capture_granularity(repo_root: Path) -> list[str]:
    """capture 粒度（三択 UX / archive ハードストップ）のキー共存を検査する。

    キーワード共存のみ。空文で通る限界あり（CAPTURE_GRANULARITY_CHECKS 上コメント参照）。
    """
    errors: list[str] = []
    for rel, keys in CAPTURE_GRANULARITY_CHECKS:
        p = repo_root / rel
        if not p.is_file():
            errors.append(f"{rel} が存在しない（capture-granularity）")
            continue
        text = p.read_text(encoding="utf-8")
        for needle, label in keys:
            if needle not in text:
                errors.append(f"{rel}: capture-granularity 欠落 — {label}（`{needle}`）")
    return errors


def check_knowledge_freshness(repo_root: Path) -> list[str]:
    """knowledge 鮮度ナッジ（SessionStart 月次）のキー共存を検査する。

    キーワード共存のみ。空文で通る限界あり（KNOWLEDGE_FRESHNESS_CHECKS 上コメント参照）。
    """
    errors: list[str] = []
    for rel, keys in KNOWLEDGE_FRESHNESS_CHECKS:
        p = repo_root / rel
        if not p.is_file():
            errors.append(f"{rel} が存在しない（knowledge-freshness）")
            continue
        text = p.read_text(encoding="utf-8")
        for needle, label in keys:
            if needle not in text:
                errors.append(f"{rel}: knowledge-freshness 欠落 — {label}（`{needle}`）")
    return errors


def check_tasklist_flow_sync(repo_root: Path) -> list[str]:
    """FCR 次ステップの知見保存→デプロイ順と、工程 6 語のキー共存を検査する。"""
    errors: list[str] = []
    fcr = repo_root / ".claude" / "skills" / "frontend-code-review" / "SKILL.md"
    patterns = repo_root / "docs" / "knowledge" / "skill-design-patterns.md"
    for p, rel in (
        (fcr, ".claude/skills/frontend-code-review/SKILL.md"),
        (patterns, "docs/knowledge/skill-design-patterns.md"),
    ):
        if not p.is_file():
            errors.append(f"{rel} が存在しない（tasklist-flow-sync）")
            continue
        text = p.read_text(encoding="utf-8")
        for needle in TASKLIST_FLOW_SECTION_KEYS:
            if needle not in text:
                errors.append(f"{rel}: tasklist-flow-sync 欠落 — `{needle}`")

    if fcr.is_file():
        text = fcr.read_text(encoding="utf-8")
        # 知見保存側: 「知見保存」または knowledge-capture / デプロイ側: 「デプロイ」または pr-create
        know_idxs = [i for i in (text.find("知見保存"), text.find("knowledge-capture")) if i >= 0]
        deploy_idxs = [i for i in (text.find("デプロイ"), text.find("pr-create")) if i >= 0]
        if not know_idxs:
            errors.append(
                ".claude/skills/frontend-code-review/SKILL.md: "
                "tasklist-flow-sync 欠落 — 知見保存/knowledge-capture"
            )
        elif not deploy_idxs:
            errors.append(
                ".claude/skills/frontend-code-review/SKILL.md: "
                "tasklist-flow-sync 欠落 — デプロイ/pr-create"
            )
        elif min(know_idxs) > min(deploy_idxs):
            errors.append(
                ".claude/skills/frontend-code-review/SKILL.md: "
                "tasklist-flow-sync 順序逆転 — 知見保存系がデプロイ系より後"
            )
    return errors


def validate(skill_dir: Path, template_mode: bool = False) -> list[str]:
    """スキルの frontmatter・構造を検証する。

    template_mode=True は templates/SKILL.template.md 用。値はプレースホルダ（[...] 形式）でも
    許容し、構造（frontmatter の存在・キー・行数・文字種）だけを検査する。
    name がディレクトリ名と一致する検査だけはテンプレでは意味を持たないためスキップする。
    """
    errors = []
    p = skill_dir if template_mode else skill_dir / "SKILL.md"
    if not p.exists():
        return [f"{p.name} が存在しない"]
    t = p.read_text(encoding="utf-8")

    m = re.match(r"^---\n(.*?)\n---\n", t, re.S)
    if not m:
        return ["frontmatter が無い"]
    fm = m.group(1)

    nm = re.search(r"^name: (\S+)$", fm, re.M)
    if not nm:
        errors.append("name が無い")
    elif not template_mode and nm.group(1) != skill_dir.name:
        errors.append(f'name "{nm.group(1)}" がディレクトリ名 "{skill_dir.name}" と不一致')

    dm = re.search(r'^description: "(.+)"$', fm, re.M)
    if not dm:
        errors.append("description が引用符付き 1 行で書かれていない")
    elif len(dm.group(1)) > 1024:
        errors.append(f"description が {len(dm.group(1))} 文字（上限 1024）")

    if not re.search(r'^metadata:\n  version: "[^"]+"$', fm, re.M):
        errors.append("metadata.version が無い")

    lines = t.count("\n") + 1
    if lines > 500:
        errors.append(f"{lines} 行（上限 500）")

    for i, line in enumerate(t.splitlines(), 1):
        astral = [c for c in line if ord(c) >= 0x10000]
        if astral:
            errors.append(f"アストラル面文字 {astral!r}（L{i}）— 400 エラーの原因")
            break

    body = t[m.end():]  # frontmatter を除いた本文

    # 項目6 — 「When NOT to use」を含む見出しの存在（発動境界の明示）
    if not re.search(r"^#+ .*When NOT to use", body, re.M):
        errors.append("本文に「When NOT to use」を含む見出しが無い（発動境界を明示する）")

    # 項目7 — 停止契約の構造検査
    scan = t
    for neg in _APPROVAL_NEGATIONS:
        scan = scan.replace(neg, "")
    has_approval = re.search(r"承認|APPROVED|approved", scan) is not None
    # 逃し弁マーカー。理由をコメント内に書く運用のため、末尾テキストの有無に依らず接頭辞で判定する。
    has_escape = "<!-- validator: no-stop-needed" in body
    # 「ここで止まる」だけの literal 一致だと、「ここで**必ず**止まる」「必ず止まって〜」という
    # **より強い**表現が不一致で誤 FAIL する（実際に発生した）。語幹 "止ま" まで緩めると
    # 「行き止まり」等で誤 PASS しうるので、停止を宣言する接頭辞つきの形だけを許容する。
    has_hardstop = (
        re.search(r"(ここで|必ず)(必ず)?止ま", body) is not None
        or re.search(r"^#+ .*STOP", body, re.M) is not None
    )
    if has_approval and not has_hardstop and not has_escape:
        errors.append(
            "承認語彙があるのにハードストップ表現（「ここで止まる」/ 見出しの STOP）が無い"
            "（停止を説明文でなく手順の Step にする。停止点を持たないスキルは "
            "<!-- validator: no-stop-needed --> を理由つきで置く）"
        )

    return errors


def purity_counts(skill_md: Path, vocab: list[str] = TOOL_VOCAB) -> dict[str, int]:
    """SKILL.md 本文（frontmatter 除く）の指定語彙の出現数を返す。

    references/ は別ファイルのため自然に除外される（この関数は SKILL.md しか読まない）。
    語境界つきで数える（gh が「英語」の一部に一致しない等）。
    """
    t = skill_md.read_text(encoding="utf-8")
    m = re.match(r"^---\n.*?\n---\n", t, re.S)
    body = t[m.end():] if m else t
    counts: dict[str, int] = {}
    for tok in vocab:
        hits = re.findall(r"(?<![\w-])" + re.escape(tok) + r"(?![\w-])", body)
        if hits:
            counts[tok] = len(hits)
    return counts


def portability_hits(skill_dir: Path) -> list[tuple[str, int, str]]:
    """配布可スキルの SKILL.md + references/*.md から、配置先で解読できない
    マスター内部前提（日付付きエピソード・マスター固有語）を行単位で拾う。

    戻り値: (相対パス, 行番号, 何を検出したか) のリスト。
    """
    hits: list[tuple[str, int, str]] = []
    files = [skill_dir / "SKILL.md"]
    ref = skill_dir / "references"
    if ref.is_dir():
        files += sorted(ref.glob("*.md"))
    date_re = re.compile(r"(?<![/\w])20\d{6}(?![\w])")
    for f in files:
        if not f.exists():
            continue
        text = f.read_text(encoding="utf-8")
        # SKILL.md は frontmatter を除く（references に frontmatter は無い）
        if f.name == "SKILL.md":
            m = re.match(r"^---\n.*?\n---\n", text, re.S)
            offset = text[: m.end()].count("\n") if m else 0
            body = text[m.end():] if m else text
        else:
            offset, body = 0, text
        rel = str(f.relative_to(skill_dir))
        for i, line in enumerate(body.splitlines(), 1 + offset):
            for dm in date_re.finditer(line):
                hits.append((rel, i, f"日付 {dm.group()}（内部エピソードの疑い）"))
            for v in PORTABILITY_VOCAB:
                if v in line:
                    hits.append((rel, i, f"マスター固有語「{v}」"))
    return hits


# main() が分岐として受け付けるフラグの全集合。**分岐を足したらここにも足す**
# （片側修正だと、実在するフラグが「不明なオプション」で弾かれる）。
# `--strict` は `--portability` の修飾子（先頭引数にならない）ので含めない。
KNOWN_FLAGS = ("--help", "-h", "--skill", "--template", "--purity", "--portability")


def main() -> None:
    args = sys.argv[1:]
    # --help / -h は使い方を出して正常終了する。これが無いと未知のフラグが
    # 走査ルートとして解釈され、Path("--help").iterdir() が未捕捉例外で落ちる。
    # 全面 argparse 化はしない — PostToolUse hook が --skill で呼んでおり、
    # 引数処理の書き換えは既存 5 経路すべての回帰リスクになる。
    if args and args[0] in ("--help", "-h"):
        print(__doc__)
        sys.exit(0)
    # 未知のフラグを走査ルートとして解釈しない。`--protability` のような打ち間違いが
    # Path("--protability").iterdir() の生 Traceback になり、原因が読み取れなかった。
    # 既知フラグの集合だけを見る一般ガードなので、以降 6 経路の分岐には触れない。
    if args and args[0].startswith("-") and args[0] not in KNOWN_FLAGS:
        print(f"エラー: 不明なオプション: {args[0]}", file=sys.stderr)
        print(f"  使えるオプション: {', '.join(KNOWN_FLAGS)}", file=sys.stderr)
        print("  使い方は --help を参照してください。", file=sys.stderr)
        sys.exit(2)
    # ポータビリティレポート（配布可スキルにマスター内部前提が無いか・report-only）
    if args and args[0] == "--portability":
        # `--strict` は `--portability` の後ろのどこに置いてもよい。走査ルートは strict 以外の最初の引数。
        # ハイフン始まりの引数は走査ルートにせず使い方の誤りとして弾く（`--stric` の打ち間違いが
        # 走査ルートとして解釈され Traceback になるのを防ぐ）。
        strict = "--strict" in args[1:]
        rest = [a for a in args[1:] if a != "--strict"]
        if rest and rest[0].startswith("-"):
            print(f"エラー: 不明なオプション: {rest[0]}（`--portability` の修飾子は --strict のみ）", file=sys.stderr)
            sys.exit(2)
        root = Path(rest[0]) if rest else (
            Path(__file__).resolve().parent.parent / ".claude" / "skills"
        )
        dirs = sorted(
            d for d in root.iterdir() if d.is_dir() and d.name not in MASTER_ONLY
        )
        print("ポータビリティレポート（配布可スキルのマスター内部前提・0 件が目標）")
        print("  配置先の読み手が解読できない日付付きエピソード・マスター固有語を検出")
        print(f"  master-only（走査対象外）: {', '.join(sorted(MASTER_ONLY))}\n")
        any_hit = False
        for d in dirs:
            hits = portability_hits(d)
            if hits:
                any_hit = True
                print(f"{d.name}:")
                for rel, i, what in hits:
                    print(f"      {rel}:{i}  {what}")
        if not any_hit:
            print("混入なし（配布可スキルはクリーン）")
        # 既定は report-only（exit 0）。--strict のときだけ混入を失敗として返す。
        sys.exit(1 if strict and any_hit else 0)
    # 純度レポートモード（項目8・FAIL にしない・レポートのみ）
    if args and args[0] == "--purity":
        if len(args) > 1 and args[1].startswith("-"):
            print(f"エラー: 不明なオプション: {args[1]}（--purity に修飾子は無い）", file=sys.stderr)
            sys.exit(2)
        root = Path(args[1]) if len(args) > 1 else (
            Path(__file__).resolve().parent.parent / ".claude" / "skills"
        )
        dirs = sorted(d for d in root.iterdir() if d.is_dir())
        print("ツール純度レポート（本文のツール固有語彙・API 名の出現数・少ないほど良い）")
        print("  tok: ツール名（vitest 等） / api: ツール固有 API 名（queryBy 等）\n")
        for d in dirs:
            skill_md = d / "SKILL.md"
            if not skill_md.exists():
                continue
            tool_counts = purity_counts(skill_md, TOOL_VOCAB)
            api_counts = purity_counts(skill_md, API_VOCAB)
            total = sum(tool_counts.values()) + sum(api_counts.values())
            parts = [f"tok {k}:{v}" for k, v in sorted(tool_counts.items())]
            parts += [f"api {k}:{v}" for k, v in sorted(api_counts.items())]
            detail = "  ".join(parts)
            print(f"{total:>4}  {d.name}" + (f"    ({detail})" if detail else ""))
        sys.exit(0)

    # テンプレートモード（templates/SKILL.template.md をプレースホルダ許容で検証）
    if args and args[0] == "--template":
        tpl = (
            Path(args[1]) if len(args) > 1
            else Path(__file__).resolve().parent.parent / "templates" / "SKILL.template.md"
        )
        errs = validate(tpl, template_mode=True)
        if errs:
            print(f"FAIL  {tpl.name} (template)")
            for e in errs:
                print(f"      - {e}")
            sys.exit(1)
        print(f"PASS  {tpl.name} (template)")
        sys.exit(0)

    # 単一スキルモード（PostToolUse hook が編集された 1 スキルだけを検証する用途）
    if args and args[0] == "--skill":
        if len(args) < 2:
            print("--skill にはスキルディレクトリのパスが必要です")
            sys.exit(1)
        d = Path(args[1])
        errs = validate(d)
        if errs:
            print(f"FAIL  {d.name}")
            for e in errs:
                print(f"      - {e}")
            sys.exit(1)
        print(f"PASS  {d.name}")
        sys.exit(0)

    root = Path(args[0]) if args else (
        Path(__file__).resolve().parent.parent / ".claude" / "skills"
    )
    dirs = sorted(d for d in root.iterdir() if d.is_dir())
    if not dirs:
        print(f"スキルディレクトリが見つかりません: {root}")
        sys.exit(1)

    failed = 0
    for d in dirs:
        errs = validate(d)
        if errs:
            failed += 1
            print(f"FAIL  {d.name}")
            for e in errs:
                print(f"      - {e}")
        else:
            print(f"PASS  {d.name}")

    # リポジトリ既定の .claude/skills を走査するときだけテンプレ境界を検査する
    # （任意ルートへの走査や --skill 単体ではスキップ）
    default_skills = Path(__file__).resolve().parent.parent / ".claude" / "skills"
    if root.resolve() == default_skills.resolve():
        tpl_errs = check_design_doc_template(default_skills.parent.parent)
        if tpl_errs:
            failed += 1
            print("FAIL  design-doc/references/templates.md (boundary)")
            for e in tpl_errs:
                print(f"      - {e}")
        else:
            print("PASS  design-doc/references/templates.md (boundary)")

        sync_errs = check_design_impl_sync(default_skills.parent.parent)
        if sync_errs:
            failed += 1
            print("FAIL  design-impl-sync (keyword coexistence)")
            for e in sync_errs:
                print(f"      - {e}")
        else:
            print("PASS  design-impl-sync (keyword coexistence)")

        cap_errs = check_capture_granularity(default_skills.parent.parent)
        if cap_errs:
            failed += 1
            print("FAIL  capture-granularity (keyword coexistence)")
            for e in cap_errs:
                print(f"      - {e}")
        else:
            print("PASS  capture-granularity (keyword coexistence)")

        fresh_errs = check_knowledge_freshness(default_skills.parent.parent)
        if fresh_errs:
            failed += 1
            print("FAIL  knowledge-freshness (keyword coexistence)")
            for e in fresh_errs:
                print(f"      - {e}")
        else:
            print("PASS  knowledge-freshness (keyword coexistence)")

        flow_errs = check_tasklist_flow_sync(default_skills.parent.parent)
        if flow_errs:
            failed += 1
            print("FAIL  tasklist-flow-sync (keyword coexistence + order)")
            for e in flow_errs:
                print(f"      - {e}")
        else:
            print("PASS  tasklist-flow-sync (keyword coexistence + order)")

    total = len(dirs) + (
        5 if root.resolve() == default_skills.resolve() else 0
    )
    print(f"\n{total - failed}/{total} PASS")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
