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

純度計測・ポータビリティ（レポートのみ・FAIL にしない）:
  python3 scripts/validate_skills.py --purity        # 各スキル本文のツール固有 API 出現数
  python3 scripts/validate_skills.py --portability   # 配布可スキルのマスター内部前提（日付・固有語）

使い方:
  python3 scripts/validate_skills.py                 # .claude/skills/ 全体
  python3 scripts/validate_skills.py <dir>           # 指定ディレクトリ配下の各スキル
  python3 scripts/validate_skills.py --skill <dir>   # 単一スキル（そのディレクトリ自体）のみ
  python3 scripts/validate_skills.py --template      # templates/SKILL.template.md（プレースホルダ許容）
  python3 scripts/validate_skills.py --purity        # ツール純度レポート（FAIL にしない）
  python3 scripts/validate_skills.py --portability   # ポータビリティレポート（FAIL にしない）
終了コード: 0 = 全 PASS / 1 = FAIL あり / 2 = 使い方の誤り（不明なオプション等）
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
]

# design-doc テンプレの契約コア/付録境界（live design.md は対象外・フォールバック全文）
DESIGN_DOC_BOUNDARY_MARKER = "design-doc-boundary: appendix"


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
        root = Path(args[1]) if len(args) > 1 else (
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
        sys.exit(0)
    # 純度レポートモード（項目8・FAIL にしない・レポートのみ）
    if args and args[0] == "--purity":
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

    total = len(dirs) + (
        1 if root.resolve() == default_skills.resolve() else 0
    )
    print(f"\n{total - failed}/{total} PASS")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
