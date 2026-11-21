#!/usr/bin/env python3
"""スキル frontmatter・構造と、配るものの一覧の機械検証（マスター専用ツール・依存ゼロ）。

検証項目（スキルごと）:
  1. name がディレクトリ名と一致する
  2. description が引用符付き 1 行で 1024 文字以内
  3. ファイル全体が 500 行以内
  4. アストラル面文字（U+10000 以上）を含まない
  5. metadata.version がある
  6. 本文に「When NOT to use」を含む見出しがある（発動境界の明示）
  7. 承認語彙（承認 / APPROVED）が出現するスキルは、本文にハードストップ表現
     （「ここで止ま」または見出しの STOP）を 1 つ以上持つ。否定形（承認不要 等）は
     トリガーから除外。逃し弁として本文に <!-- validator: no-stop-needed --> があればスキップ。

検証項目（既定の走査のときだけ）:
  8. リポジトリの CLAUDE.md が 50 行以内（行動ルールだけにする。独自の目標）
  9. README の依存の一覧が、実際のスキル・agent・hook・settings の雛形と一致する。
     壊した一覧で検査が落ちることも毎回確かめる（self-test）
 10. CLAUDE.md と design-doc の「小さな作業にしない」条件が同じ 3 つ（ファイルごとの目印で見る）。
     どちらかの目印を消すと落ちることも毎回確かめる（self-test）

ポータビリティ（レポートのみ・FAIL にしない）:
  python3 scripts/validate_skills.py --portability   # 配るスキルのマスター内部前提（日付・固有語）

使い方:
  python3 scripts/validate_skills.py                 # .claude/skills/ 全体
  python3 scripts/validate_skills.py <dir>           # 指定ディレクトリ配下の各スキル
  python3 scripts/validate_skills.py --skill <dir>   # 単一スキル（そのディレクトリ自体）のみ
  python3 scripts/validate_skills.py --template      # templates/SKILL.template.md（プレースホルダ許容）
  python3 scripts/validate_skills.py --portability   # ポータビリティレポート
終了コード: 0 = 全 PASS / 1 = FAIL あり / 2 = 使い方の誤り（不明なオプション等）

検査スクリプトの規律（検査を足すときに守る）:
  - フェイルクローズは比較の両側に要る。0 件どうしの比較で緑を出さない
  - 対象が無いときは SKIP にして、FAIL があれば FAIL を優先する
  - 警告は verbose の外に出す
  - 語彙の抽出は語幹で持つ（活用や強調で取りこぼさない）
  - 文書と実体の突き合わせは「記載漏れ」と「死んだ参照」の 2 方向に分ける
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SKILLS = ROOT / ".claude" / "skills"

# 項目7で承認語彙のトリガーから除外する否定形（自律実行境界の引用による誤 FAIL を防ぐ）。
_APPROVAL_NEGATIONS = ["承認不要", "承認なし", "承認は不要", "承認を要さない"]

# マスター専用のスキルの一次情報は README の依存の一覧。項目9 がこの集合との一致を検査する。
MASTER_ONLY = {"skill-test"}
CLAUDE_MD_MAX_LINES = 50

# --portability レポート用。配るスキルの本文・references に「配置先の読み手が解読できない
# マスター内部前提」が混入していないかを検出する（report-only）。
# 検出対象:
#   1. 単独の YYYYMMDD 日付（内部 QA/インシデントの日付付きエピソード。配置先に文脈が無い）。
#      パス（直前が "/"）は除外。
#   2. マスター固有語（配置先に存在しない仕組みを前提にした語）。
PORTABILITY_VOCAB = [
    "還流", "配布セット", "source-commit", "deployments.md",
    "このマスター", "マスターへ", "マスターの git", "（distributable）",
]

DISTRIBUTED = "配る"
MASTER_ONLY_MARK = "マスター専用"
SKILLS_MARKER = "<!-- deps:skills -->"
HOOKS_MARKER = "<!-- deps:hooks -->"
HOOK_PATH_RE = re.compile(r"\.claude/hooks/([\w.-]+)")


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


def portability_selftest() -> list[str]:
    """拾うべき行を拾い、拾ってはいけないもの（パスの中の日付・SKILL.md の外のファイル）を拾わないかを確かめる。
    戻り値は期待どおりにならなかった行。"""
    import tempfile

    want = {"目安は 2026-10 の実測": True, "500 行まで 0.7〜3 ドル": True, "例: （20261026。要点）": True,
            "例: （<YYYYMMDD>。要点）": False, "`.steering/20261026-x/` を読む": False, "差分 1,000 行": False}
    bad = []
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        (d / "cost.md").write_text("| 500 行まで | 0.7〜3 ドル |\n測った時期: 2026-11\n", encoding="utf-8")
        for line, hit in want.items():
            (d / "SKILL.md").write_text(f"---\nname: x\n---\n{line}\n", encoding="utf-8")
            got = portability_hits(d)
            if bool(got) != hit or any(rel != "SKILL.md" for rel, _, _ in got):
                bad.append(line)
    return bad


def portability_hits(skill_dir: Path) -> list[tuple[str, int, str]]:
    """配るスキルの SKILL.md + references/*.md から、配置先で解読できない
    マスター内部前提（日付付きエピソード・マスター固有語）を行単位で拾う。

    戻り値: (相対パス, 行番号, 何を検出したか) のリスト。
    """
    hits: list[tuple[str, int, str]] = []
    files = [skill_dir / "SKILL.md"]
    ref = skill_dir / "references"
    if ref.is_dir():
        files += sorted(ref.glob("*.md"))
    date_re = re.compile(r"(?<![/\w])20\d{6}(?![\w])")
    # 時期で古くなる記述。測った値は本文でなく別ファイル（frontend-code-review/cost.md など）に置く
    month_re = re.compile(r"(?<![/\w-])20\d{2}-(?:0[1-9]|1[0-2])(?![\d])")
    money_re = re.compile(r"\d\s*ドル")
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
            for mm in month_re.finditer(line):
                hits.append((rel, i, f"年月 {mm.group()}（時期で古くなる記述の疑い）"))
            if money_re.search(line):
                hits.append((rel, i, "金額（時期で古くなる記述の疑い。測った値は別ファイルへ）"))
            for v in PORTABILITY_VOCAB:
                if v in line:
                    hits.append((rel, i, f"マスター固有語「{v}」"))
    return hits


def table_rows(readme: str, marker: str) -> list[list[str]]:
    """marker の直後の表の本体を、セルのリストで返す（見出しと区切りの行を除く）。"""
    if marker not in readme:
        return []
    rows: list[list[str]] = []
    started = False
    for line in readme.split(marker, 1)[1].splitlines():
        if not line.startswith("|"):
            if started:
                break
            continue
        started = True
        rows.append([c.strip() for c in line.strip().strip("|").split("|")])
    return rows[2:]


def code_names(cell: str) -> set[str]:
    """セルの中のバッククォートの名前を返す。"""
    return set(re.findall(r"`([^`]+)`", cell))


def mentions(text: str, name: str) -> bool:
    """text が name に言及するか。`.steering/` や `review-bug-x` のような別の語には当たらない。"""
    return re.search(r"(?<![\w.-])" + re.escape(name) + r"(?![\w-])", text) is not None


def two_way(label: str, listed: set[str], actual: set[str]) -> list[str]:
    """一覧と実体を「記載漏れ」と「死んだ参照」の 2 方向で比べる。"""
    out = []
    if actual - listed:
        out.append(f"{label}: 一覧に書かれていない {sorted(actual - listed)}")
    if listed - actual:
        out.append(f"{label}: 一覧にあるが実体が無い {sorted(listed - actual)}")
    return out


def dependency_problems(
    readme: str,
    skills: dict[str, str],
    agents: set[str],
    hooks: set[str],
    template_hooks: set[str],
) -> list[str]:
    """README の依存の一覧を実体と突き合わせる。skills は スキル名 -> SKILL.md の本文。"""
    skill_rows = table_rows(readme, SKILLS_MARKER)
    hook_rows = table_rows(readme, HOOKS_MARKER)
    # 0 件どうしの比較で緑を出さない
    if not skill_rows or not skills:
        return ["スキルの依存の一覧または実体のスキルが 0 件"]
    if not hook_rows or not hooks or not template_hooks:
        return ["hook の一覧・実体の hook・雛形の hook 登録のどれかが 0 件"]

    listed_skills = {name for r in skill_rows for name in code_names(r[0])}
    problems = two_way("スキル", listed_skills, set(skills))

    listed_agents: set[str] = set()
    marked_master: set[str] = set()
    for row in skill_rows:
        if len(row) != 4:
            problems.append(f"スキルの一覧の列数が 4 でない: {row}")
            continue
        names = code_names(row[0])
        name = next(iter(names), "")
        need_agents, see_skills = code_names(row[1]), code_names(row[2])
        listed_agents |= need_agents
        if row[3] == MASTER_ONLY_MARK:
            marked_master.add(name)
        elif row[3] != DISTRIBUTED:
            problems.append(f"{name}: 配るかの欄が「{DISTRIBUTED}」「{MASTER_ONLY_MARK}」のどちらでもない")
        if name not in skills:
            continue
        text = skills[name]
        used_agents = {a for a in agents if mentions(text, a)}
        problems += two_way(f"{name} の agent", need_agents, used_agents)
        used_skills = {s for s in skills if s != name and mentions(text, s)}
        problems += two_way(f"{name} の案内先のスキル", see_skills, used_skills)
        if row[3] == DISTRIBUTED and used_skills & MASTER_ONLY:
            problems.append(f"{name}: 配るのにマスター専用のスキルを参照する {sorted(used_skills & MASTER_ONLY)}")
    problems += two_way("agent", listed_agents, agents)
    if marked_master != MASTER_ONLY:
        problems.append(f"マスター専用の印 {sorted(marked_master)} が MASTER_ONLY {sorted(MASTER_ONLY)} と違う")

    listed_hooks = {name for r in hook_rows for name in code_names(r[0])}
    problems += two_way("hook", listed_hooks, hooks)
    distributed = {name for r in hook_rows if r[-1] == DISTRIBUTED for name in code_names(r[0])}
    problems += two_way("雛形に登録する hook", distributed, template_hooks)
    return problems


def dependency_self_test(
    readme: str,
    skills: dict[str, str],
    agents: set[str],
    hooks: set[str],
    template_hooks: set[str],
) -> list[str]:
    """壊した入力で dependency_problems が落ちることを確かめる。落ちなかった壊し方を返す。"""
    first_agent = sorted(agents)[0]
    first_skill = sorted(skills)[0]
    row_of = next(line for line in readme.splitlines() if line.startswith(f"| `{first_skill}`"))
    cases = {
        "スキルの行を消す": (readme.replace(row_of + "\n", ""), skills, agents, hooks, template_hooks),
        "死んだ行を足す": (readme.replace(row_of, row_of + "\n| `ghost` | - | - | 配る |"), skills, agents, hooks, template_hooks),
        "一覧を丸ごと消す": (readme.replace(SKILLS_MARKER, ""), skills, agents, hooks, template_hooks),
        "hook の一覧を丸ごと消す": (readme.replace(HOOKS_MARKER, ""), skills, agents, hooks, template_hooks),
        "agent を使うのに書かない": (readme, {**skills, first_skill: skills[first_skill] + f"\n`{first_agent}`\n"}, agents, hooks, template_hooks),
        "実体のない agent": (readme, skills, agents - {first_agent}, hooks, template_hooks),
        "実体の hook を足す": (readme, skills, agents, hooks | {"ghost.sh"}, template_hooks),
        "雛形の hook を足す": (readme, skills, agents, hooks, template_hooks | {"ghost.sh"}),
        "配るのにマスター専用を参照": (readme, {**skills, first_skill: skills[first_skill] + "\n" + next(iter(MASTER_ONLY)) + "\n"}, agents, hooks, template_hooks),
    }
    return [label for label, args in cases.items() if not dependency_problems(*args)]


def check_dependencies() -> tuple[list[str], list[str]]:
    """リポジトリの実体を読んで項目9を流す。戻り値は (問題, 落ちなかった self-test)。"""
    readme_path = ROOT / "README.md"
    template_path = ROOT / "templates" / "settings.template.json"
    missing = [str(p.relative_to(ROOT)) for p in (readme_path, template_path) if not p.is_file()]
    if missing:
        return [f"ファイルが無い: {missing}"], []
    readme = readme_path.read_text(encoding="utf-8")
    skills = {
        d.name: (d / "SKILL.md").read_text(encoding="utf-8")
        for d in sorted(DEFAULT_SKILLS.iterdir())
        if (d / "SKILL.md").is_file()
    }
    agents = {p.stem for p in (ROOT / ".claude" / "agents").glob("*.md")}
    hooks_dir = ROOT / ".claude" / "hooks"
    hooks = {p.name for pattern in ("*.sh", "*.py") for p in hooks_dir.glob(pattern)}
    template_hooks = set(HOOK_PATH_RE.findall(template_path.read_text(encoding="utf-8")))
    args = (readme, skills, agents, hooks, template_hooks)
    problems = dependency_problems(*args)
    return problems, ([] if problems else dependency_self_test(*args))


# 項目10: 目印はファイルごとに持つ（CLAUDE.md は「承認制のパス」と書き、design-doc はそのパスを列挙するため）
STAGE_RULES = {
    "CLAUDE.md": ("小さな作業にしない", [("3 ファイル以上",), ("公開している API",), ("承認制のパス",)]),
    ".claude/skills/design-doc/SKILL.md": (
        "小さな作業として扱わない",
        [("3 ファイル以上",), ("公開している API",), ("CLAUDE.md", "docs", ".claude")],
    ),
}


def stage_rule_problems(texts: dict[str, str]) -> list[str]:
    problems = []
    for rel, (lead, markers) in STAGE_RULES.items():
        text = texts.get(rel)
        if text is None:
            problems.append(f"{rel}: ファイルが無い")
            continue
        lines = [line for line in text.splitlines() if lead in line]
        if len(lines) != 1:
            problems.append(f"{rel}: 「{lead}」の行が {len(lines)} 行（1 行のはず）")
            continue
        body = re.split(r"[:：]", lines[0].split(lead, 1)[1], maxsplit=1)
        conds = [c.strip() for c in re.split(r"・", body[-1].split("。")[0]) if c.strip()]
        if len(conds) != len(markers):
            problems.append(f"{rel}: 条件が {len(conds)} つ（{len(markers)} つのはず）: {conds}")
            continue
        for group in markers:
            hit = [c for c in conds if all(m in c for m in group)]
            if len(hit) != 1:
                problems.append(f"{rel}: 目印 {list(group)} に当たる条件が {len(hit)} つ（1 つのはず）")
    return problems


def stage_rule_self_test(texts: dict[str, str]) -> list[str]:
    """目印を 1 つずつ消す・条件を足す・行を消すと落ちることを確かめる。落ちなかった壊し方を返す。"""
    cases: dict[str, dict[str, str]] = {}
    for rel, (lead, markers) in STAGE_RULES.items():
        line = next(x for x in texts[rel].splitlines() if lead in x)
        for group in markers:
            for m in group:
                cases[f"{rel} の「{m}」を消す"] = {**texts, rel: texts[rel].replace(line, line.replace(m, "〇〇"))}
        first = re.split(r"[:：]", line.split(lead, 1)[1], maxsplit=1)[-1]
        cases[f"{rel} に条件を足す"] = {**texts, rel: texts[rel].replace(line, line.replace(first, "テストを消す・" + first.lstrip(), 1))}
        cases[f"{rel} の行を消す"] = {**texts, rel: texts[rel].replace(line, "")}
    return [label for label, broken in cases.items() if not stage_rule_problems(broken)]


def check_stage_rules() -> tuple[list[str], list[str]]:
    """リポジトリの実体を読んで項目10を流す。戻り値は (問題, 落ちなかった self-test)。"""
    texts = {rel: (ROOT / rel).read_text(encoding="utf-8") for rel in STAGE_RULES if (ROOT / rel).is_file()}
    problems = stage_rule_problems(texts)
    return problems, ([] if problems else stage_rule_self_test(texts))


# main() が分岐として受け付けるフラグの全集合。**分岐を足したらここにも足す**
# （片側修正だと、実在するフラグが「不明なオプション」で弾かれる）。
KNOWN_FLAGS = ("--help", "-h", "--skill", "--template", "--portability")


def main() -> None:
    args = sys.argv[1:]
    # --help / -h は使い方を出して正常終了する。これが無いと未知のフラグが
    # 走査ルートとして解釈され、Path("--help").iterdir() が未捕捉例外で落ちる。
    # 全面 argparse 化はしない — PostToolUse hook が --skill で呼んでおり、
    # 引数処理の書き換えは既存の経路すべての回帰リスクになる。
    if args and args[0] in ("--help", "-h"):
        print(__doc__)
        sys.exit(0)
    # 未知のフラグを走査ルートとして解釈しない。`--protability` のような打ち間違いが
    # Path("--protability").iterdir() の生 Traceback になり、原因が読み取れなかった。
    if args and args[0].startswith("-") and args[0] not in KNOWN_FLAGS:
        print(f"エラー: 不明なオプション: {args[0]}", file=sys.stderr)
        print(f"  使えるオプション: {', '.join(KNOWN_FLAGS)}", file=sys.stderr)
        print("  使い方は --help を参照してください。", file=sys.stderr)
        sys.exit(2)
    # ポータビリティレポート（配るスキルにマスター内部前提が無いか・report-only）
    if args and args[0] == "--portability":
        rest = args[1:]
        if rest and rest[0].startswith("-"):
            print(f"エラー: 不明なオプション: {rest[0]}（`--portability` に修飾子は無い）", file=sys.stderr)
            sys.exit(2)
        root = Path(rest[0]) if rest else DEFAULT_SKILLS
        dirs = sorted(
            d for d in root.iterdir() if d.is_dir() and d.name not in MASTER_ONLY
        )
        silent = portability_selftest()
        if silent:
            print(f"FAIL  ポータビリティの self-test — 拾わなかった行: {silent}")
            sys.exit(1)
        print("ポータビリティレポート（配るスキルのマスター内部前提・0 件が目標）")
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
            print("混入なし（配るスキルはクリーン）")
        sys.exit(0)

    # テンプレートモード（templates/SKILL.template.md をプレースホルダ許容で検証）
    if args and args[0] == "--template":
        tpl = Path(args[1]) if len(args) > 1 else ROOT / "templates" / "SKILL.template.md"
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

    root = Path(args[0]) if args else DEFAULT_SKILLS
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

    total = len(dirs)
    # リポジトリ既定の .claude/skills を走査するときだけ、リポジトリ全体の検査を足す
    if root.resolve() == DEFAULT_SKILLS.resolve():
        total += 1
        claude_md = ROOT / "CLAUDE.md"
        n = len(claude_md.read_text(encoding="utf-8").splitlines()) if claude_md.is_file() else None
        if n is None:
            failed += 1
            print("FAIL  CLAUDE.md — ファイルが無い")
        elif n > CLAUDE_MD_MAX_LINES:
            failed += 1
            print(f"FAIL  CLAUDE.md — {n} 行（上限 {CLAUDE_MD_MAX_LINES} 行。知識は docs/knowledge/ へ移す）")
        else:
            print(f"PASS  CLAUDE.md（{n} 行）")

        total += 1
        problems, silent = check_dependencies()
        if problems:
            failed += 1
            print("FAIL  README の依存の一覧")
            for e in problems:
                print(f"      - {e}")
        elif silent:
            failed += 1
            print(f"FAIL  依存の一覧の self-test — 落ちなかった壊し方: {silent}")
        else:
            print("PASS  README の依存の一覧（self-test 込み）")

        total += 1
        problems, silent = check_stage_rules()
        if problems:
            failed += 1
            print("FAIL  小さな作業にしない条件（CLAUDE.md と design-doc）")
            for e in problems:
                print(f"      - {e}")
        elif silent:
            failed += 1
            print(f"FAIL  小さな作業にしない条件の self-test — 落ちなかった壊し方: {silent}")
        else:
            print("PASS  小さな作業にしない条件（CLAUDE.md と design-doc。self-test 込み）")
    print(f"\n{total - failed}/{total} PASS")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
