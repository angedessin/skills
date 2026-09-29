#!/usr/bin/env python3
"""セットアップ資産どうしの契約突合（マスター専用ツール・依存ゼロ）。

このリポジトリは「同じ情報が複数箇所にある」構造を繰り返し壊してきた。実例:

  20260723 `27c19ab` 「契約ズレ・片側修正 13 件を修正」というコミットが、
           session-start-check.sh を expected_hooks() に足しながら
           HOOK_REGISTRATIONS への登録を忘れ、配置を KeyError で全滅させた
  20260726 `b9b6a91` 「同送 hook の漏れ」をルールとして昇格させたコミットが、
           guard-gated-write.sh で **同じ漏れを 1 階層下で再発**させた

どちらも注意力の問題ではない。expected_hooks() は「単一情報源」として作られたのに、
実際には expected_hooks() の返り値と HOOK_REGISTRATIONS のキーという **2 つのリスト**が
あり、両者を突合するものが存在しなかった。ドキュメント（README・starter-kit）に至っては
実体との機械的な繋がりが一切なかった。

このスクリプトはその突合を機械化する。**人が「直したつもり」でも、片側だけ直したら落ちる。**

検査する契約:
  (a) expected_hooks() の全可能出力 ⊆ HOOK_REGISTRATIONS のキー、かつ
      HOOK_REGISTRATIONS に実ファイルの無い死んだ登録が無い（双方向）
  (b) expected_hooks() の全可能出力 ∪ MASTER_ONLY_HOOKS ≡ .claude/hooks/ の実ファイル
      → hook を 1 本足してどちらにも分類しなければ落ちる（分類漏れの検出）
  (c) README 全文の *.sh 言及集合 ≡ .claude/hooks/ の実ファイル
  (d) expected_hooks() の全可能出力 ⊆ docs/starter-kit.md 全文の *.sh 言及集合
  (e) マスター settings.json の各 permission ルールが DEPLOY_PERMISSIONS か
      MASTER_ONLY_PERMISSIONS に分類済み。逆方向（配布側にあってマスターに無い / マスターから
      消えたのに分類に残る）と 2 集合の重複も検査する
  (f) **マスター settings.json の hooks 登録 ≡ .claude/hooks/ の実ファイル**
      → hooks/ に置いて expected_hooks() にも README にも入れたが、settings.json への
        登録を忘れる = マスターで一度も発火しない、という片側修正を検出する
  (h) deploy_skills.MASTER_ONLY ≡ validate_skills.MASTER_ONLY
      → 配布分類が 2 ファイルに独立定義されている。片方への足し忘れは
        「配布してはいけないスキルが配布可能になる」に直結する
  (j) マスター settings / DEPLOY / MASTER_ONLY に Write|NotebookEdit|MultiEdit の
      **パス付き**規則が無い（Claude Code は Edit(path)/Read(path) のみ参照。死んだ規則は
      起動時警告になる。ツール名のみの Write は対象外）
  (k) README の契約レター集合 ≡ 本スクリプトの contract_*、かつ
      package.json の scripts キー集合 ≡ README「npm script」箇条のバッククォート名
      → 員数や列挙の片側修正を検出する（抽出は下記正規表現に固定）
  (l) feature-pipeline の Phase / Step 見出しに出るスキル名 ⊆ README「メインワークフロー」図
      → CLAUDE.md の「ワークフロー図と feature-pipeline は同一コミットで改訂する」を機械化する。
        フェーズを足してオーケストレーターだけ直し、図を放置した片側修正を検出する
  (m) feature-pipeline の判定表の行 ID 列（順序つき）≡ scripts/pipeline_state.py の ROW_ORDER、
      かつ各行の現在地語（Phase / Gate / 即停止）が一致する
      → 表と関数のどちらかだけ直した片側修正、および行順の入れ替え（Phase 3.7 到達不能型）を検出する。
        意味（条件・到達可能性・優先順位）は tests/state が関数側で検査する
  (n) steering/references/spec.md の tasklist テンプレの節見出し列（順序つき）と
      デプロイ節の `PR:` / `CI:` / `Feedback:` キー ≡ design-doc/references/templates.md（正本）
      → 写しが正本から工程順ごとずれる片側修正を検出する
  (o) スキル本文が名指しする agent 名（`.claude/agents/<名>.md` のパス表記と、frontend-code-review の
      ディスパッチ表の「役割名」列）⊆ `.claude/agents/` の定義名、かつ全定義がいずれかから参照されている
      → 存在しない agent への死んだ参照と、どのスキルからも呼ばれない孤児定義を検出する（双方向）
  (p) `.claude/agents/*.md` の frontmatter: 必須キー・既知キーのみ・name = ファイル名・model / effort の値・
      preload する skills の実在・読み取り専用の定義に書き込み系ツールが混ざらないこと
      （書き込みを許す定義は WRITABLE_AGENTS に明示列挙する）。読み取り専用の定義に許すツールは
      Read / Grep / Glob だけのホワイトリスト（Bash は `git diff --output=<path>` で書き込めるため許さない）
  (r) capture フラグ（capture_done / pr_capture_done）の producer（knowledge-capture が touch する）と
      consumer（feature-pipeline・steering・hook・.gitignore・deploy_skills・状態機械）が名前で一致し、
      リポジトリ内で使われるフラグ名が既知の 2 つだけ
      → producer と consumer のどちらかだけを直す片側修正（Critical 2 と同型）を検出する
  (s) guard-gated-write.sh の `# GATED_PATHS:` 行 ≡ マスター settings の permissions.ask にある
      Edit(./...)（ディレクトリの */**/**/* は 1 つに畳む・~/ 起点は除外）
      → Edit の ask だけ足して Bash 経由の書き込みが素通りする（またはその逆の）片側修正を検出する
  (t) マスター settings と DEPLOY_PERMISSIONS の allow に `Bash(git ...)` のルールが無い
      → 組み込みの読み取り専用判定を前置一致の allow で上書きし、--output / difftool -x を開けるのを防ぐ
  (q) remind-config-docs.sh が注入する要約 ⇄ その正本（docs/knowledge/）: 要約の各項目の見出し語が
      要約と正本の両方に存在し、要約の項目数が突合表と一致する
      → 正本の言い換え・削除で要約だけが古くなる（注入される「要点」が正本と食い違う）ドリフトを検出する

  会社向け持ち出しセット用の契約 (g)(i) は 20260730 Frozen handoff で除去済み。

契約 (c)(d) が「集合比較」なのは書式非依存にするため。README のツリーを構文解析すると
書式変更で壊れる。全文から *.sh を拾って集合で比べれば、ツリーに書こうが散文に書こうが拾える。
(d) だけ包含（⊆）なのは、starter-kit の *.sh 言及が手順 6 以外にも存在するため
（節境界のパースを避ける。等価にすると節の挿入で偽 PASS を生む）。

(l) も包含（⊆）。README の図は debug / tdd / e2e / rule-audit などパイプラインが編成しない
スキルも描くため、等価にすると常に落ちる。**(l) はフェーズの順序を見ない** — 図では
knowledge-capture が [5.5]（PR 前）と [7]（残り）の 2 箇所に出るなど、同じスキルが複数の
位置に現れるため順序比較は書式変更で壊れやすい。図の順序のドリフトは人のレビューで見る。
一方、判定表の行順は (m) が、tasklist テンプレの節順は (n) が機械検査する。

**終了コードの優先順位**: FAIL が 1 件でもあれば 1。2 を返すのは走査の前提そのものが崩れている場合だけ。

使い方:
  python3 scripts/check_asset_consistency.py            # 全契約を検査
  python3 scripts/check_asset_consistency.py --verbose  # PASS の内訳も表示
終了コード: 0 = 全 PASS / 1 = 契約違反あり / 2 = 走査の前提が崩れている
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

MASTER_ROOT = Path(__file__).resolve().parent.parent
HOOKS_DIR = MASTER_ROOT / ".claude" / "hooks"
SETTINGS = MASTER_ROOT / ".claude" / "settings.json"
README = MASTER_ROOT / "README.md"
STARTER_KIT = MASTER_ROOT / "docs" / "starter-kit.md"

sys.path.insert(0, str(MASTER_ROOT / "scripts"))
try:
    from deploy_skills import (  # noqa: E402
        DEPLOY_PERMISSIONS,
        HOOK_REGISTRATIONS,
        MASTER_ONLY_HOOKS,
        MASTER_ONLY_PERMISSIONS,
        expected_hooks,
    )
    from deploy_skills import MASTER_ONLY as DEPLOY_MASTER_ONLY  # noqa: E402
except ImportError as e:  # pragma: no cover - 実行環境の異常のみ
    print(f"ERROR: deploy_skills.py を読み込めない: {e}", file=sys.stderr)
    sys.exit(2)

SH_RE = re.compile(r"[A-Za-z0-9_-]+\.sh")
CONTRACT_DEF_RE = re.compile(r"^def contract_([a-z])\(", re.M)
# 箇条内の「(a) 説明」形のみ。`(g)(i) は` のように直前が ) の連続マーカーは除外する
CONTRACT_LETTER_RE = re.compile(r"(?<!\))\(([a-z])\)\s")
NPM_SCRIPT_TICK_RE = re.compile(r"`([a-z][a-z0-9:_-]*)`")

PASS, FAIL, SKIP = "PASS", "FAIL", "SKIP"


def die(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(2)


def all_possible_sends() -> set[str]:
    """expected_hooks() が返しうる hook の**全体**。

    条件分岐（knowledge-capture の有無・.steering 系スキルの有無）を素通りせず、
    全スキルを渡した場合の最大集合を取る。ここを「代表的なセット 1 つ」で代用すると、
    条件分岐の片方だけ壊れたときに検出できない。
    """
    skills_dir = MASTER_ROOT / ".claude" / "skills"
    all_skills = [p.name for p in skills_dir.iterdir() if p.is_dir()] if skills_dir.is_dir() else []
    return set(expected_hooks(all_skills))


def actual_hooks() -> set[str]:
    return {p.name for p in HOOKS_DIR.glob("*.sh")}


def sh_mentions(path: Path) -> set[str]:
    return set(SH_RE.findall(path.read_text(encoding="utf-8")))


def registered_hooks(settings_path: Path) -> set[str]:
    """settings.json（または settings.example.json）が登録している hook 名。

    「何を配ると宣言しているか」「何を発火させると宣言しているか」の機械可読な一次情報。
    """
    if not settings_path.is_file():
        return set()
    try:
        cfg = json.loads(settings_path.read_text(encoding="utf-8")).get("hooks", {})
    except json.JSONDecodeError:
        return set()
    names: set[str] = set()
    for entries in cfg.values():
        for entry in entries:
            for h in entry.get("hooks", []):
                names.update(SH_RE.findall(h.get("command", "")))
    return names


def master_permissions() -> dict:
    if not SETTINGS.exists():
        die(f"settings.json が無い: {SETTINGS}")
    try:
        cfg = json.loads(SETTINGS.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        die(f"settings.json が JSON として読めない: {e}")
    if "permissions" not in cfg:
        die("settings.json に permissions セクションが無い（走査の前提が崩れている）")
    return cfg["permissions"]


# ---- 契約 ----------------------------------------------------------------


def contract_a() -> tuple[str, list[str]]:
    sends = all_possible_sends()
    missing = sorted(sends - set(HOOK_REGISTRATIONS))
    dead = sorted(set(HOOK_REGISTRATIONS) - actual_hooks())
    details = []
    if missing:
        details.append(f"同送するのに HOOK_REGISTRATIONS に登録が無い: {', '.join(missing)}")
        details.append("→ deploy_guardrails() が KeyError で落ちる（配置が全滅する）")
    if dead:
        details.append(f"HOOK_REGISTRATIONS にあるが実ファイルが無い（死んだ登録）: {', '.join(dead)}")
    return (FAIL, details) if details else (PASS, [f"同送 {len(sends)} 本すべて登録済み・死んだ登録なし"])


def contract_b() -> tuple[str, list[str]]:
    classified = all_possible_sends() | set(MASTER_ONLY_HOOKS)
    actual = actual_hooks()
    details = []
    if actual - classified:
        details.append(f"分類されていない hook: {', '.join(sorted(actual - classified))}")
        details.append("→ expected_hooks() に足すか MASTER_ONLY_HOOKS に入れるかを決める")
    if classified - actual:
        details.append(f"分類にあるが実ファイルが無い: {', '.join(sorted(classified - actual))}")
    if details:
        return FAIL, details
    return PASS, [
        f"実ファイル {len(actual)} 本すべて分類済み"
        f"（同送 {len(all_possible_sends())} / master-only {len(MASTER_ONLY_HOOKS)}）"
    ]


def contract_c() -> tuple[str, list[str]]:
    if not README.exists():
        die(f"README が無い: {README}")
    mentioned = sh_mentions(README)
    actual = actual_hooks()
    details = []
    if actual - mentioned:
        details.append(f"README に載っていない hook: {', '.join(sorted(actual - mentioned))}")
    if mentioned - actual:
        details.append(f"README にあるが実在しない hook: {', '.join(sorted(mentioned - actual))}")
    return (FAIL, details) if details else (PASS, [f"README の記述 {len(mentioned)} 件が実ファイルと一致"])


def contract_d() -> tuple[str, list[str]]:
    if not STARTER_KIT.exists():
        die(f"starter-kit が無い: {STARTER_KIT}")
    missing = sorted(all_possible_sends() - sh_mentions(STARTER_KIT))
    if missing:
        return FAIL, [
            f"配置手順に載っていない同送 hook: {', '.join(missing)}",
            "→ 手動配置する人がこの hook を配らない（deploy_skills.py は配るので手順とズレる）",
        ]
    return PASS, [f"同送 {len(all_possible_sends())} 本すべて配置手順に記載あり"]


def contract_e() -> tuple[str, list[str]]:
    master = master_permissions()
    details = []
    for key in ("allow", "ask", "deny"):
        m = set(master.get(key, []))
        dep = set(DEPLOY_PERMISSIONS.get(key, []))
        mo = set(MASTER_ONLY_PERMISSIONS.get(key, []))
        if m - dep - mo:
            details.append(f"[{key}] マスターにあるが未分類: {', '.join(sorted(m - dep - mo))}")
            details.append("  → DEPLOY_PERMISSIONS か MASTER_ONLY_PERMISSIONS に入れる")
        if dep - m:
            details.append(f"[{key}] 配布側にあるがマスターに無い（ドリフト）: {', '.join(sorted(dep - m))}")
        if mo - m:
            details.append(f"[{key}] master-only 分類に残っているがマスターに無い（死んだ分類）: {', '.join(sorted(mo - m))}")
        if dep & mo:
            details.append(f"[{key}] 配布と master-only の両方に入っている: {', '.join(sorted(dep & mo))}")
    if details:
        return FAIL, details
    total = sum(len(master.get(k, [])) for k in ("allow", "ask", "deny"))
    return PASS, [f"マスターの {total} ルールすべて分類済み・ドリフト/死んだ分類/重複なし"]


def contract_f() -> tuple[str, list[str]]:
    """マスター settings.json の hooks 登録 ≡ .claude/hooks/ の実ファイル。

    hooks/ に置いて expected_hooks() にも README にも入れたが settings.json への登録を
    忘れる = マスターで一度も発火しない、という片側修正を塞ぐ。20260726 のレビューで
    「この経路が無検査だった」と指摘されて追加した（手作業で 1 回確認しただけで
    契約として encode していなかった）。

    同一 event で同じ matcher のエントリが複数あると、Claude Code が後段を落とす実測が
    ある（20260807: PreToolUse Bash を 3 分割 → /hooks に delete が出ず deny 沈黙）。
    """
    reg = registered_hooks(SETTINGS)
    actual = actual_hooks()
    details = []
    if reg - actual:
        details.append(f"settings.json に登録があるのにファイルが無い: {', '.join(sorted(reg - actual))}")
    if actual - reg:
        details.append(f"ファイルがあるのに settings.json に登録が無い: {', '.join(sorted(actual - reg))}")
        details.append("→ マスターで一度も発火しない（置いただけで効いていない）")

    try:
        cfg = json.loads(SETTINGS.read_text(encoding="utf-8")).get("hooks", {})
    except json.JSONDecodeError:
        cfg = {}
    for event, entries in cfg.items():
        seen: dict[object, int] = {}
        for entry in entries:
            key = entry.get("matcher")
            seen[key] = seen.get(key, 0) + 1
        for matcher, n in sorted(seen.items(), key=lambda x: str(x[0])):
            if n > 1:
                label = matcher if matcher is not None else "(matcher なし)"
                details.append(
                    f"{event}: matcher={label!r} が {n} エントリに分割されている"
                )
                details.append(
                    "→ 同一 event+matcher は 1 エントリに hooks を並べる（後段が /hooks から落ちる）"
                )

    return (FAIL, details) if details else (PASS, [f"hooks 登録 {len(reg)} 件が実ファイルと一致"])


def contract_h() -> tuple[str, list[str]]:
    """master-only スキルの分類が 2 ファイルで一致しているか。

    `MASTER_ONLY` は deploy_skills.py（誤配置の防止）と validate_skills.py（--portability の
    走査除外）に**独立して定義**されている。用途が違うので統合はしないが、片方に新しい
    master-only スキルを足し忘れると「配布してはいけないスキルが配布可能になる」か
    「portability 検査が誤った対象を走査する」。値の集合の片側修正は grep でも静的検査でも
    検出されないため（どちらも自分の中では整合している）、突合をここに置く。

    import による単一化はしない: validate_skills.py は PostToolUse hook が --skill で呼ぶ
    最も頻繁に走る経路で、そこに deploy_skills への import 依存を足すと片方の破損がもう片方を
    巻き込む。「スクリプトは依存ゼロ」の規約にも反する。
    """
    try:
        import validate_skills  # noqa: PLC0415 - 突合のためだけに読む
    except ImportError as e:
        return FAIL, [f"validate_skills.py を読み込めない: {e}"]
    d_only = set(DEPLOY_MASTER_ONLY)
    v_only = set(validate_skills.MASTER_ONLY)
    if d_only != v_only:
        details = []
        if d_only - v_only:
            details.append(f"deploy_skills.py にのみある: {', '.join(sorted(d_only - v_only))}")
        if v_only - d_only:
            details.append(f"validate_skills.py にのみある: {', '.join(sorted(v_only - d_only))}")
        details.append("→ 分類の一次情報は docs/starter-kit.md の選定表。両方を揃える")
        return FAIL, details
    return PASS, [f"master-only スキル {len(d_only)} 件が両ファイルで一致"]


DEAD_FILE_PATH_PERM_RE = re.compile(r"^(Write|NotebookEdit|MultiEdit)\(.+\)$")


def contract_j() -> tuple[str, list[str]]:
    """パス付き Write/NotebookEdit/MultiEdit は Claude Code が参照せず起動時警告になる。"""
    details: list[str] = []
    sources = [
        ("settings.json", master_permissions()),
        ("DEPLOY_PERMISSIONS", DEPLOY_PERMISSIONS),
        ("MASTER_ONLY_PERMISSIONS", MASTER_ONLY_PERMISSIONS),
    ]
    for label, perms in sources:
        for key in ("allow", "ask", "deny"):
            dead = sorted(r for r in perms.get(key, []) if DEAD_FILE_PATH_PERM_RE.match(r))
            if dead:
                details.append(f"[{label}/{key}] 死んだパス規則: {', '.join(dead)}")
                details.append("  → Edit(path) に置き換える（Edit が編集系ツールを覆う）")
    if details:
        return FAIL, details
    return PASS, ["settings / DEPLOY / MASTER_ONLY に死んだ Write|NotebookEdit|MultiEdit(path) なし"]


GATED_MARKER_RE = re.compile(r"^# GATED_PATHS:[ \t]*(.+)$", re.M)
EDIT_PROJECT_RE = re.compile(r"^Edit\(\./(.+)\)$")
GLOB_SUFFIX_RE = re.compile(r"/(\*\*/\*|\*\*|\*)$")


def contract_s() -> tuple[str, list[str]]:
    """書き込み hook の GATED_PATHS ≡ permissions.ask の Edit(./...)（ディレクトリの 3 形式は 1 つに畳む）。

    ゲートしたいパスは到達できる全ツール分を塞ぐ（Edit は permissions、Bash は hook）。
    片方にだけ足すと、もう片方の経路が開いたまま残る。~/ 起点の規則はプロジェクト外なので対象外。
    guard-gated-delete.sh は意図的に 3 系統で、この突合に入れない。
    """
    hook = HOOKS_DIR / "guard-gated-write.sh"
    if not hook.is_file():
        return FAIL, [f"{hook.name} が無い"]
    m = GATED_MARKER_RE.search(hook.read_text(encoding="utf-8"))
    if not m:
        return FAIL, [f"{hook.name} に '# GATED_PATHS:' 行が無い（対象パスの正本）"]
    hook_set = set(m.group(1).split())
    ask_set: set[str] = set()
    for rule in master_permissions().get("ask", []):
        e = EDIT_PROJECT_RE.match(rule)
        if not e:
            continue
        path = e.group(1)
        g = GLOB_SUFFIX_RE.search(path)
        ask_set.add(path[: g.start()] + "/" if g else path)
    details: list[str] = []
    if hook_set - ask_set:
        details.append(f"hook にだけある（Edit の ask が無い）: {', '.join(sorted(hook_set - ask_set))}")
    if ask_set - hook_set:
        details.append(f"ask にだけある（Bash 経由の書き込みが素通り）: {', '.join(sorted(ask_set - hook_set))}")
    if details:
        details.append("  → guard-gated-write.sh の GATED_PATHS と settings.json の Edit(./...) ask を揃える")
        return FAIL, details
    return PASS, [f"GATED_PATHS ≡ Edit(./...) ask（{len(hook_set)} 系統）"]


GIT_ALLOW_RE = re.compile(r"^Bash\(\s*git\b")


def contract_t() -> tuple[str, list[str]]:
    """allow に git のルールを置かない（マスター settings と DEPLOY_PERMISSIONS）。

    Claude Code 組み込みの読み取り専用判定は git の読み取り形をプロンプトなしで通し、
    --output / difftool -x / 作業ツリー外のパスは止める。前置一致の allow（`Bash(git diff*)` 等）は
    その判定を上書きして危険な形まで許す（20260927 headless 実測）。
    """
    details: list[str] = []
    for label, perms in (("settings.json", master_permissions()), ("DEPLOY_PERMISSIONS", DEPLOY_PERMISSIONS)):
        bad = sorted(r for r in perms.get("allow", []) if GIT_ALLOW_RE.match(r))
        if bad:
            details.append(f"[{label}/allow] git のルール: {', '.join(bad)}")
    if details:
        details.append("  → 削除する（git の読み取りは組み込みの判定に任せる。allow は危険な形まで許す）")
        return FAIL, details
    return PASS, ["settings / DEPLOY の allow に git のルールなし"]


def _readme_bullet_after(heading_substr: str) -> str:
    """README の '- **…**' 箇条のうち、見出し部分文字列を含む最初の 1 箇条本文を返す。"""
    text = README.read_text(encoding="utf-8")
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.startswith("- **") and heading_substr in line:
            start = i
            break
    if start is None:
        return ""
    chunk = [lines[start]]
    for line in lines[start + 1 :]:
        if line.startswith("- **") or line.startswith("## "):
            break
        chunk.append(line)
    return "\n".join(chunk)


def contract_k() -> tuple[str, list[str]]:
    """README の契約レター・npm script 一覧が実装と一致するか。"""
    details: list[str] = []
    self_src = Path(__file__).read_text(encoding="utf-8")
    impl_letters = set(CONTRACT_DEF_RE.findall(self_src))

    asset_bullet = _readme_bullet_after("資産どうしの契約突合")
    if not asset_bullet:
        return FAIL, ["README に「資産どうしの契約突合」箇条が無い"]
    readme_letters = set(CONTRACT_LETTER_RE.findall(asset_bullet))
    if impl_letters != readme_letters:
        only_impl = sorted(impl_letters - readme_letters)
        only_readme = sorted(readme_letters - impl_letters)
        if only_impl:
            details.append(f"実装のみ: {', '.join(f'({x})' for x in only_impl)}")
        if only_readme:
            details.append(f"README のみ: {', '.join(f'({x})' for x in only_readme)}")

    pkg_path = MASTER_ROOT / "package.json"
    try:
        pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        details.append(f"package.json を読めない: {e}")
        details.append("→ 員数ハードコードではなく集合一致。直すときは両側を同じコミットで")
        return FAIL, details
    pkg_scripts = set((pkg.get("scripts") or {}).keys())

    npm_bullet = _readme_bullet_after("npm script")
    if not npm_bullet:
        details.append("README に「npm script」箇条が無い")
    else:
        readme_scripts = set(NPM_SCRIPT_TICK_RE.findall(npm_bullet))
        if pkg_scripts != readme_scripts:
            only_pkg = sorted(pkg_scripts - readme_scripts)
            only_rm = sorted(readme_scripts - pkg_scripts)
            if only_pkg:
                details.append(f"package.json scripts のみ: {', '.join(only_pkg)}")
            if only_rm:
                details.append(f"README npm script のみ: {', '.join(only_rm)}")

    if details:
        details.append("→ 員数ハードコードではなく集合一致。直すときは両側を同じコミットで")
        return FAIL, details
    return PASS, [
        f"契約レター {len(impl_letters)} 件と npm scripts {len(pkg_scripts)} 件が README と一致"
    ]


MAIN_WORKFLOW_RE = re.compile(r"^## メインワークフロー\s*\n+```\n(.*?)\n```", re.M | re.S)
# feature-pipeline の Phase / Step 見出し（`## Phase 1 — 計画（design-doc）` 等）。
# Gate 見出しはスキル名を持たないので拾わなくてよい。
FP_PHASE_HEAD_RE = re.compile(r"^#{2,3} .*?(?:Phase|Step)\s*[\d.]+[a-z]?\b.*$", re.M)

FEATURE_PIPELINE = MASTER_ROOT / ".claude" / "skills" / "feature-pipeline" / "SKILL.md"
TASKLIST_TEMPLATE = MASTER_ROOT / ".claude" / "skills" / "design-doc" / "references" / "templates.md"
STEERING_SPEC = MASTER_ROOT / ".claude" / "skills" / "steering" / "references" / "spec.md"

# 判定表の行 `| `P37` | 条件 | **Phase 3.7**（…） |`。先頭セルの行 ID だけを契約キーとして拾う。
PHASE_ROW_RE = re.compile(r"^\|\s*`([A-Z][0-9A-Za-z]*)`\s*\|")
# 現在地の語。表は `**Phase 3.7**`・関数側は `Phase 3.7（…）` と装飾が違うので語だけ比べる。
PHASE_WORD_RE = re.compile(r"(Phase\s*[\d.]+|Gate\s*\d+|即停止)")
TASKLIST_BLOCK_RE = re.compile(r"```markdown\n(# タスクリスト:.*?)\n```", re.S)
DEPLOY_KEY_RE = re.compile(r"^- (PR|CI|Feedback):", re.M)


def _named_skills(text: str) -> set[str]:
    """テキスト中に語として出現するスキル名の集合。

    語幹一致を避けるため前後の境界を明示する（`impl-review` が `impl-reviewer` に
    誤ヒットしない・`review-ui` が `review-ui-x` を拾わない）。
    """
    skills_dir = MASTER_ROOT / ".claude" / "skills"
    if not skills_dir.is_dir():
        die(f"skills ディレクトリが無い: {skills_dir}")
    found = set()
    for p in skills_dir.iterdir():
        if p.is_dir() and re.search(rf"(?<![\w-]){re.escape(p.name)}(?![\w-])", text):
            found.add(p.name)
    return found


def contract_l() -> tuple[str, list[str]]:
    """README のワークフロー図と feature-pipeline のフェーズ構成のドリフト検出。

    フェイルクローズ: 図が見つからない・パイプラインが実在しないのに README が案内している、
    はいずれも FAIL。「片方が消えたから比較不要」で黙って PASS にすると、
    死んだ案内が README に残ったまま気づけない。
    """
    if not README.exists():
        die(f"README が無い: {README}")
    readme_text = README.read_text(encoding="utf-8")
    m = MAIN_WORKFLOW_RE.search(readme_text)
    if not m:
        return FAIL, [
            "README に「## メインワークフロー」直後のコードブロックが無い",
            "→ 図の見出し・書式を変えたなら MAIN_WORKFLOW_RE も同じコミットで直す",
        ]
    in_diagram = _named_skills(m.group(1))

    if not FEATURE_PIPELINE.is_file():
        if "feature-pipeline" in in_diagram:
            return FAIL, [
                "README の図が feature-pipeline を案内しているが SKILL.md が実在しない",
            ]
        return PASS, ["feature-pipeline が無く README も案内していない（比較対象なし）"]

    fp_text = FEATURE_PIPELINE.read_text(encoding="utf-8")
    phase_heads = "\n".join(FP_PHASE_HEAD_RE.findall(fp_text))
    if not phase_heads:
        return FAIL, [
            "feature-pipeline に Phase / Step 見出しが 1 つも無い",
            "→ 見出し書式を変えたなら FP_PHASE_HEAD_RE も同じコミットで直す",
        ]
    in_pipeline = _named_skills(phase_heads)

    missing = sorted(in_pipeline - in_diagram)
    if missing:
        return FAIL, [
            f"feature-pipeline が編成するのに README の図に無い: {', '.join(missing)}",
            "→ 図とオーケストレーターは同一コミットで改訂する（CLAUDE.md のスキル管理ルール）",
        ]
    return PASS, [
        f"パイプラインが編成する {len(in_pipeline)} スキルすべてが図に存在"
        f"（図は {len(in_diagram)} スキルを描画）"
    ]


def _phase_word(text: str) -> str:
    m = PHASE_WORD_RE.search(text)
    return re.sub(r"\s+", "", m.group(1)) if m else ""


def contract_m() -> tuple[str, list[str]]:
    """判定表（SKILL.md）と pipeline_state.py の行 ID 列・現在地語の突合。

    フェイルクローズ: 表が 0 行・関数を読めない、はいずれも FAIL。0 行を「差分なし」で
    PASS にすると、表の書式を変えた瞬間に検査が黙って無効化される。
    """
    try:
        from pipeline_state import PHASE_BY_ROW, ROW_ORDER  # noqa: E402
    except ImportError as e:
        return FAIL, [f"scripts/pipeline_state.py を読み込めない: {e}"]
    if not FEATURE_PIPELINE.is_file():
        return FAIL, [f"feature-pipeline/SKILL.md が無い: {FEATURE_PIPELINE}"]

    table_ids: list[str] = []
    table_words: dict[str, str] = {}
    for line in FEATURE_PIPELINE.read_text(encoding="utf-8").splitlines():
        m = PHASE_ROW_RE.match(line)
        if not m:
            continue
        table_ids.append(m.group(1))
        table_words[m.group(1)] = _phase_word(line.rstrip().rstrip("|").rsplit("|", 1)[-1])

    if not table_ids:
        return FAIL, [
            "feature-pipeline の判定表に行 ID 付きの行が 1 つも無い",
            "→ 表の書式を変えたなら PHASE_ROW_RE も同じコミットで直す",
        ]

    details: list[str] = []
    dupes = sorted({i for i in table_ids if table_ids.count(i) > 1})
    if dupes:
        details.append(f"表に重複した行 ID: {', '.join(dupes)}")
    only_table = [i for i in table_ids if i not in ROW_ORDER]
    only_func = [i for i in ROW_ORDER if i not in table_ids]
    if only_table:
        details.append(f"表のみ（pipeline_state.py に無い）: {', '.join(only_table)}")
    if only_func:
        details.append(f"pipeline_state.py のみ（表に無い）: {', '.join(only_func)}")
    if not (only_table or only_func or dupes) and table_ids != ROW_ORDER:
        details.append(f"行順が違う — 表: {' > '.join(table_ids)}")
        details.append(f"              関数: {' > '.join(ROW_ORDER)}")
        details.append("行順は判定の優先順位そのもの。入れ替えると到達不能な行が生まれる")
    for row_id in ROW_ORDER:
        if row_id in table_words and table_words[row_id] != _phase_word(PHASE_BY_ROW[row_id]):
            details.append(
                f"{row_id} の現在地語が違う — 表: {table_words[row_id] or '(なし)'}"
                f" / 関数: {_phase_word(PHASE_BY_ROW[row_id]) or '(なし)'}"
            )
    if details:
        details.append("→ 表（SKILL.md）と関数（pipeline_state.py）は同一コミットで直す。意味は tests/state が検査する")
        return FAIL, details
    return PASS, [f"判定表 {len(table_ids)} 行の ID・順序・現在地語が pipeline_state.py と一致"]


def _tasklist_template(path: Path) -> tuple[list[str], list[str], list[str]] | None:
    """tasklist テンプレの (節見出し列, デプロイ節キー列, チェックボックス項目列)。テンプレが見つからなければ None。"""
    if not path.is_file():
        return None
    m = TASKLIST_BLOCK_RE.search(path.read_text(encoding="utf-8"))
    if not m:
        return None
    block = m.group(1)
    return re.findall(r"^## .+$", block, re.M), DEPLOY_KEY_RE.findall(block), re.findall(r"^- \[ \] .+$", block, re.M)


def contract_n() -> tuple[str, list[str]]:
    """steering の tasklist テンプレ（写し）が design-doc の正本と同じ工程順か。"""
    canonical = _tasklist_template(TASKLIST_TEMPLATE)
    copy = _tasklist_template(STEERING_SPEC)
    if canonical is None:
        return FAIL, [f"正本に tasklist テンプレが無い: {TASKLIST_TEMPLATE}"]
    if copy is None:
        return FAIL, [f"写しに tasklist テンプレが無い: {STEERING_SPEC}"]
    if not canonical[0]:
        return FAIL, ["正本の tasklist テンプレに `## ` 見出しが 1 つも無い"]
    if not canonical[1] or not canonical[2]:
        return FAIL, [
            "正本の tasklist テンプレからデプロイ節のキー（`- PR:` 等）またはチェックボックス項目が 1 つも抽出できない",
            "→ 書式を変えたなら DEPLOY_KEY_RE 等も同じコミットで直す（0 件どうしの一致を PASS にしない）",
        ]

    details: list[str] = []
    if canonical[0] != copy[0]:
        details.append("節見出し列（順序つき）が違う")
        details.append(f"  正本 templates.md: {' > '.join(h[3:] for h in canonical[0])}")
        details.append(f"  写し spec.md     : {' > '.join(h[3:] for h in copy[0])}")
    if canonical[1] != copy[1]:
        details.append(
            f"デプロイ節のキーが違う — 正本: {canonical[1] or '(なし)'} / 写し: {copy[1] or '(なし)'}"
        )
    if canonical[2] != copy[2]:
        only_canon = [i for i in canonical[2] if i not in copy[2]]
        only_copy = [i for i in copy[2] if i not in canonical[2]]
        details.append(f"チェックボックス項目（順序つき）が違う — 正本のみ: {only_canon or '(なし)'} / 写しのみ: {only_copy or '(なし)'}")
    if details:
        details.append("→ 正本は design-doc/references/templates.md。写しを正本に合わせて直す")
        return FAIL, details
    return PASS, [
        f"節見出し {len(canonical[0])} 件・デプロイ節キー {len(canonical[1])} 件・"
        f"チェックボックス項目 {len(canonical[2])} 件が正本と一致"
    ]


AGENTS_DIR = MASTER_ROOT / ".claude" / "agents"
SKILLS_DIR = MASTER_ROOT / ".claude" / "skills"
FRONTEND_CODE_REVIEW = SKILLS_DIR / "frontend-code-review" / "SKILL.md"

# 本文が agent を名指す 2 つの書式だけを契約として拾う（スキル名と語が重なるため語一致では区別できない）:
#   1. `.claude/agents/<名>.md` のパス表記
#   2. frontend-code-review のディスパッチ表 `| test-agent | `review-test` | ... |` の役割名列
AGENT_PATH_RE = re.compile(r"\.claude/agents/([a-z][a-z0-9-]*)\.md")
DISPATCH_ROW_RE = re.compile(r"^\|\s*[a-z0-9-]+-agent\s*\|\s*`([a-z][a-z0-9-]*)`\s*\|", re.M)

# 書き込み系ツールを持ってよい定義。ここに無い定義は読み取り専用でなければならない。
WRITABLE_AGENTS = {"tournament-variant"}
AGENT_REQUIRED_KEYS = ("name", "description", "tools", "model")
# 公式 docs（Create custom subagents）が定義するキー。打ち間違いが黙って無視されるのを防ぐ。
AGENT_KNOWN_KEYS = {
    "name", "description", "tools", "disallowedTools", "model", "effort", "skills", "permissionMode",
    "maxTurns", "mcpServers", "hooks", "memory", "background", "omitClaudeMd", "isolation", "color",
    "initialPrompt", "experimental",
}
AGENT_MODELS = {"sonnet", "opus", "haiku", "fable", "inherit"}
AGENT_EFFORTS = {"low", "medium", "high", "xhigh", "max"}
# 読み取り専用の定義に許すツール（ホワイトリスト）。Bash は `Bash(git diff *)` のように絞っても
# `--output=<path>` でファイルが書け、`git symbolic-ref` は ref を書き換えられるため、Bash ごと許さない。
# 黒名簿方式（Edit / Write を禁止）だと、引用符付き・`Agent`・`mcp__*`・`WebFetch` などが抜ける。
READONLY_TOOLS = {"Read", "Grep", "Glob"}


def _agent_frontmatter(text: str) -> dict[str, object] | None:
    """agent 定義の frontmatter を `キー: 値` と `- 要素` の限られた書式で読む（標準ライブラリのみ）。"""
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return None
    result: dict[str, object] = {}
    key = None
    for line in m.group(1).splitlines():
        item = re.match(r"^\s+-\s+(.*)$", line)
        if item and key is not None:
            if not isinstance(result.get(key), list):
                result[key] = []
            result[key].append(item.group(1).strip())  # type: ignore[union-attr]
            continue
        kv = re.match(r"^([A-Za-z][A-Za-z0-9]*):\s*(.*)$", line)
        if kv:
            key = kv.group(1)
            result[key] = kv.group(2).strip() if kv.group(2).strip() else []
    return result


def _agent_names() -> list[str] | None:
    if not AGENTS_DIR.is_dir():
        return None
    return sorted(p.stem for p in AGENTS_DIR.glob("*.md"))


def contract_o() -> tuple[str, list[str]]:
    """スキル本文の agent 参照 ⇄ `.claude/agents/` の定義（死んだ参照と孤児定義の双方向）。"""
    defs = _agent_names()
    if not defs:
        return FAIL, [f".claude/agents/ に定義が 1 つも無い: {AGENTS_DIR}"]
    if not FRONTEND_CODE_REVIEW.is_file():
        return FAIL, [f"frontend-code-review/SKILL.md が無い: {FRONTEND_CODE_REVIEW}"]

    dispatch_roles = set(DISPATCH_ROW_RE.findall(FRONTEND_CODE_REVIEW.read_text(encoding="utf-8")))
    if not dispatch_roles:
        return FAIL, [
            "frontend-code-review にディスパッチ表（`| xxx-agent | `役割名` | ... |`）の行が 1 つも無い",
            "→ 表の書式を変えたなら DISPATCH_ROW_RE も同じコミットで直す",
        ]
    path_refs: set[str] = set()
    for f in sorted(SKILLS_DIR.glob("*/SKILL.md")) + sorted(SKILLS_DIR.glob("*/references/*.md")):
        path_refs |= set(AGENT_PATH_RE.findall(f.read_text(encoding="utf-8")))

    refs = dispatch_roles | path_refs
    dangling = sorted(refs - set(defs))
    orphans = sorted(set(defs) - refs)
    details: list[str] = []
    if dangling:
        details.append(f"定義の無い agent を名指ししている: {', '.join(dangling)}")
    if orphans:
        details.append(f"どのスキルからも参照されない定義: {', '.join(orphans)}")
    if details:
        details.append("→ スキル本文の参照と .claude/agents/ の定義は同一コミットで直す")
        return FAIL, details
    return PASS, [f"agent 定義 {len(defs)} 本すべてが参照され、参照はすべて定義に解決する"]


def _unquote(item: str) -> str:
    return item.strip().strip("\"'")


def _agent_list(value: object) -> list[str] | None:
    """frontmatter の複数値（`- a` の列 / `a, b`）を要素のリストにする。インライン配列 `[a, b]` は None。"""
    if isinstance(value, list):
        return [_unquote(v) for v in value]
    text = str(value or "").strip()
    if text.startswith("["):
        return None
    return [_unquote(t) for t in text.split(",") if t.strip()]


def contract_p() -> tuple[str, list[str]]:
    """`.claude/agents/*.md` の frontmatter 検査（必須キー・値・実在・読み取り専用）。"""
    names = _agent_names()
    if not names:
        return FAIL, [f".claude/agents/ に定義が 1 つも無い: {AGENTS_DIR}"]
    skill_names = {p.name for p in SKILLS_DIR.iterdir() if p.is_dir()} if SKILLS_DIR.is_dir() else set()

    details: list[str] = []
    for name in names:
        fm = _agent_frontmatter((AGENTS_DIR / f"{name}.md").read_text(encoding="utf-8"))
        if fm is None:
            details.append(f"{name}: frontmatter（`---` で囲んだ先頭ブロック）が読めない")
            continue
        for key in AGENT_REQUIRED_KEYS:
            if not fm.get(key):
                details.append(f"{name}: 必須キー `{key}` が無い（または空）")
        unknown = sorted(set(fm) - AGENT_KNOWN_KEYS)
        if unknown:
            details.append(f"{name}: 未知のキー {', '.join(unknown)}（打ち間違いは黙って無視される）")
        if fm.get("name") and fm["name"] != name:
            details.append(f"{name}: name（{fm['name']}）がファイル名と違う")
        model = fm.get("model")
        if isinstance(model, str) and model not in AGENT_MODELS and not model.startswith("claude-"):
            details.append(f"{name}: model `{model}` は既知の値ではない（{', '.join(sorted(AGENT_MODELS))} か claude-*）")
        effort = fm.get("effort")
        if effort is not None and effort not in AGENT_EFFORTS:
            details.append(f"{name}: effort `{effort}` は既知の値ではない（{', '.join(sorted(AGENT_EFFORTS))}）")

        skills = _agent_list(fm.get("skills") or [])
        if skills is None:
            details.append(f"{name}: skills のインライン配列 `[...]` は読めない（`- name` の列で書く）")
        else:
            for skill in skills:
                if skill not in skill_names:
                    details.append(f"{name}: preload する skills `{skill}` が .claude/skills/ に無い")

        tool_list = _agent_list(fm.get("tools"))
        if tool_list is None:
            details.append(f"{name}: tools のインライン配列 `[...]` は読めない（`- Read` の列かカンマ区切りで書く）")
        elif name not in WRITABLE_AGENTS:
            for tool in tool_list:
                if tool not in READONLY_TOOLS:
                    details.append(
                        f"{name}: 読み取り専用のはずが `{tool}` を持つ"
                        f"（許可は {', '.join(sorted(READONLY_TOOLS))} のみ。Bash は git の --output などで書き込めるため持たせない）"
                    )
    stale = sorted(WRITABLE_AGENTS - set(names))
    if stale:
        details.append(f"WRITABLE_AGENTS に定義の無い名前: {', '.join(stale)}")
    if details:
        details.append("→ 書き込みを許す定義は WRITABLE_AGENTS に明示列挙する。読み取り専用の定義に足すなら意図を確認する")
        return FAIL, details
    return PASS, [
        f"agent 定義 {len(names)} 本の frontmatter が契約どおり"
        f"（書き込み可は {', '.join(sorted(WRITABLE_AGENTS))} のみ・他は {', '.join(sorted(READONLY_TOOLS))} だけ）"
    ]


# capture フラグ（capture_done / pr_capture_done）の producer / consumer。フラグ名は文字列で
# 散らばっているため、片側だけ直す（Critical 2 と同型）と検査が黙って通る。名前で突合する。
FLAG_PRODUCER = SKILLS_DIR / "knowledge-capture" / "SKILL.md"
FLAG_CONSUMERS = {
    # フラグ名: そのフラグを読む / 除外する / 案内する場所（producer 以外）
    "pr_capture_done": (
        ".claude/skills/feature-pipeline/SKILL.md",
        ".claude/skills/steering/SKILL.md",
        ".claude/skills/steering/references/spec.md",
        ".gitignore",
        "scripts/deploy_skills.py",
        "scripts/pipeline_state.py",
    ),
    "capture_done": (
        ".claude/skills/feature-pipeline/SKILL.md",
        ".claude/skills/steering/SKILL.md",
        ".claude/skills/steering/references/spec.md",
        ".claude/hooks/session-stop.sh",
        ".gitignore",
        "scripts/deploy_skills.py",
        "scripts/pipeline_state.py",
    ),
}
FLAG_TOKEN_RE = re.compile(r"[A-Za-z0-9_]*capture_done[A-Za-z0-9_]*")
FLAG_SCAN_GLOBS = (
    ".claude/skills/*/SKILL.md", ".claude/skills/*/references/*.md", ".claude/hooks/*.sh",
    "scripts/*.py", "tests/state/*.py", ".gitignore", "README.md", "docs/user-guide.md",
)


def contract_r() -> tuple[str, list[str]]:
    """capture フラグの producer（knowledge-capture）と consumer の名前突合。

    - producer が各フラグを `touch` している
    - 各 consumer がそのフラグ名を含む（`capture_done` の検査は `pr_capture_done` を数えない）
    - リポジトリ全体で使われているフラグ名が既知の 2 つだけ（`post_capture_done` 等の打ち間違い・新設の検出）
    フェイルクローズ: producer / consumer のファイルが読めなければ FAIL。
    """
    if not FLAG_PRODUCER.is_file():
        return FAIL, [f"producer が無い: {FLAG_PRODUCER}"]
    producer_text = FLAG_PRODUCER.read_text(encoding="utf-8")

    details: list[str] = []
    for flag, consumers in FLAG_CONSUMERS.items():
        if not re.search(rf"touch \.steering/\[task\]/{flag}\b", producer_text):
            details.append(f"{flag}: producer（knowledge-capture/SKILL.md）に `touch .steering/[task]/{flag}` が無い")
        token = re.compile(rf"(?<![A-Za-z0-9_]){flag}\b")
        for rel in consumers:
            path = MASTER_ROOT / rel
            if not path.is_file():
                details.append(f"{flag}: consumer が読めない: {rel}")
            elif not token.search(path.read_text(encoding="utf-8")):
                details.append(f"{flag}: consumer {rel} がこのフラグ名を含まない（片側修正の可能性）")

    seen: dict[str, set[str]] = {}
    for pattern in FLAG_SCAN_GLOBS:
        for path in sorted(MASTER_ROOT.glob(pattern)):
            if path == Path(__file__).resolve():
                continue  # この検査自身の説明文・メッセージは走査しない
            for tok in set(FLAG_TOKEN_RE.findall(path.read_text(encoding="utf-8"))):
                seen.setdefault(tok, set()).add(str(path.relative_to(MASTER_ROOT)))
    for tok in sorted(set(seen) - set(FLAG_CONSUMERS)):
        details.append(f"未知のフラグ名 `{tok}`（{', '.join(sorted(seen[tok]))}）— 打ち間違いか、新設なら FLAG_CONSUMERS に足す")
    if details:
        details.append("→ フラグの producer と consumer は同一コミットで直す（意味は tests/state が検査する）")
        return FAIL, details
    return PASS, [f"フラグ {len(FLAG_CONSUMERS)} 種の producer と consumer {sum(len(c) for c in FLAG_CONSUMERS.values())} 箇所が名前で一致"]


REMIND_HOOK = HOOKS_DIR / "remind-config-docs.sh"
# hook が注入する要約の各項目 `(N) ...` を代表する見出し語。**要約と正本の両方に存在すること**。
# 要約の項目を足したら、ここにも見出し語を足す（項目数の一致も検査する）。
REMIND_SUMMARIES = {
    "config": (
        "docs/knowledge/claude-code-config.md",
        ("Write(path)", "glob は形式を列挙する", "イベント種別"),
    ),
    "skills": (
        "docs/knowledge/skill-design-patterns.md",
        ("ハードストップ", "片側修正", "責務境界", "日付付き"),
    ),
}
REMIND_EMIT_RE = re.compile(r'^\s*emit "([a-z]+)" "(.*)"\s*$', re.M)
REMIND_ITEM_RE = re.compile(r"\(\d\)")


def contract_q() -> tuple[str, list[str]]:
    """remind-config-docs.sh の注入要約 ⇄ 正本（docs/knowledge/）のドリフト検査。

    フェイルクローズ: hook・正本・emit 行のどれかが読めないときは FAIL（比較対象なしで PASS にしない）。
    """
    if not REMIND_HOOK.is_file():
        return FAIL, [f"hook が無い: {REMIND_HOOK}"]
    emitted = dict(REMIND_EMIT_RE.findall(REMIND_HOOK.read_text(encoding="utf-8")))

    details: list[str] = []
    for category, (doc_rel, anchors) in REMIND_SUMMARIES.items():
        summary = emitted.get(category)
        if summary is None:
            details.append(f"{category}: hook に emit \"{category}\" の行が無い（書式を変えたなら REMIND_EMIT_RE も直す）")
            continue
        doc = MASTER_ROOT / doc_rel
        if not doc.is_file():
            details.append(f"{category}: 正本が無い: {doc_rel}")
            continue
        doc_text = doc.read_text(encoding="utf-8")
        item_count = len(REMIND_ITEM_RE.findall(summary))
        if item_count != len(anchors):
            details.append(
                f"{category}: 要約の項目数（{item_count}）が突合表の見出し語の数（{len(anchors)}）と違う"
                " — 項目を足した・消したなら REMIND_SUMMARIES も同じコミットで直す"
            )
        for anchor in anchors:
            if anchor not in summary:
                details.append(f"{category}: 見出し語「{anchor}」が hook の要約に無い（要約を言い換えたなら突合表を直す）")
            if anchor not in doc_text:
                details.append(f"{category}: 見出し語「{anchor}」が正本 {doc_rel} に無い（正本が変わって要約だけが古い可能性）")
    if details:
        details.append("→ 要約は正本の要点。正本を直したら要約も、要約を直したら正本との整合も確認する")
        return FAIL, details
    total = sum(len(a) for _, a in REMIND_SUMMARIES.values())
    return PASS, [f"注入要約 {len(REMIND_SUMMARIES)} 系統・見出し語 {total} 件が要約と正本の両方に存在"]


def main() -> None:
    ap = argparse.ArgumentParser(
        description="セットアップ資産どうしの契約突合（マスター専用）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="終了コード: 0 = 全 PASS / 1 = 契約違反あり / 2 = 走査の前提が崩れている",
    )
    ap.add_argument("--verbose", action="store_true", help="PASS の契約も内訳を表示する")
    args = ap.parse_args()

    if not HOOKS_DIR.is_dir():
        die(f"hooks ディレクトリが無い: {HOOKS_DIR}")

    contracts = [
        ("(a) 同送 hook が HOOK_REGISTRATIONS に登録済み", contract_a),
        ("(b) .claude/hooks/ の全ファイルが分類済み", contract_b),
        ("(c) README の hook 記述が実体と一致", contract_c),
        ("(d) 同送 hook が配置手順に記載済み", contract_d),
        ("(e) permissions が配布/マスター専用に分類済み", contract_e),
        ("(f) settings.json の hooks 登録が実体と一致", contract_f),
        ("(h) master-only スキルの分類が 2 ファイルで一致", contract_h),
        ("(j) 死んだ Write|NotebookEdit|MultiEdit(path) が無い", contract_j),
        ("(k) README の契約レター・npm scripts が実装と一致", contract_k),
        ("(l) ワークフロー図と feature-pipeline のフェーズが一致", contract_l),
        ("(m) 判定表の行 ID・順序が pipeline_state.py と一致", contract_m),
        ("(n) tasklist テンプレの写しが正本と同じ工程順", contract_n),
        ("(o) スキル本文の agent 参照が .claude/agents/ の定義と一致", contract_o),
        ("(p) agent 定義の frontmatter が契約どおり（読み取り専用を含む）", contract_p),
        ("(q) hook の注入要約が正本（docs/knowledge/）と食い違っていない", contract_q),
        ("(r) capture フラグの producer と consumer が名前で一致", contract_r),
        ("(s) 書き込み hook の対象パスが permissions.ask と一致", contract_s),
        ("(t) allow に git のルールが無い", contract_t),
    ]

    failed = 0
    for label, fn in contracts:
        status, details = fn()
        print(f"{status}  {label}")
        if status == FAIL:
            failed += 1
        if status == FAIL or args.verbose:
            for d in details:
                print(f"      {d}")

    total = len(contracts)
    print()
    if failed:
        print(f"{total - failed}/{total} PASS — {failed} 件の契約違反")
        sys.exit(1)
    print(f"{total}/{total} PASS")


if __name__ == "__main__":
    main()
