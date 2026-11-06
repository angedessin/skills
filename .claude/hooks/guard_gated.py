#!/usr/bin/env python3
"""guard-gated-write.sh と guard-gated-delete.sh の共通の判定（標準ライブラリだけ）。

Usage: python3 guard_gated.py write <guard-gated-write.sh のパス>   # 標準出力: ASK / SILENT
       python3 guard_gated.py delete                               # 標準出力: DENY / SILENT
       入力は hook の stdin の JSON。tool_input.command だけを見る（transcript_path などが常に混ざるので全文は見ない）。
       解析に失敗したら exit 3。守る形と守らない形の正本はマスターの tests/hooks/run_fixtures.py。
"""
import functools
import glob
import json
import os
import re
import shlex
import subprocess
import sys
import time

REDIRS = {">", ">>", "&>", "&>>", ">|", ">&"}
INPUT_REDIRS = {"<", "<<", "<<-", "<<<", "<&"}
SEPS = {";", "&&", "||", "|", "|&", "&", ";;"}
# shlex は連続する記号を 1 語にまとめる（`);`・`)&&`）ので、長いものから順に分ける
OPERATORS = ["&>>", "<<<", "<<-", ">>", "&>", ">|", ">&", "<<", "<&", "&&", "||", "|&", ";;", ";", "(", ")", "&", "|", ">", "<"]
PUNCTUATION = set("();<>|&")
WRAPPERS = {"timeout", "time", "nice", "nohup", "stdbuf", "command", "builtin", "noglob", "xargs", "env", "exec", "sudo", "{", "!"}
CONTROL_WORDS = {"if", "then", "elif", "else", "while", "until", "do"}
WRAPPER_VALUED = {"-u", "-g"}  # env -u NAME / sudo -u USER -g GROUP: 次の語は値
HEREDOC_RE = re.compile(r"""(?<!<)<<(-?)(?!<)\s*(?:'([^']+)'|"([^"]+)"|\\?([A-Za-z_]\w*))""")
PATH_META_RE = re.compile(r"[*?\[{$`]")
BRACE_RE = re.compile(r"\{([^{}]*,[^{}]*)\}")
# hook の timeout（10 秒）を超えると通常の確認に進むので、その手前で止めて deny / ask に倒す
EXPAND_LIMIT = 1000
GLOB_LIMIT = 5000
GLOB_SECONDS = 3


class TooMany(Exception):
    """展開が上限を超えた。判定せずに deny / ask に倒す。"""


def strip_heredocs(cmd):
    """ヒアドキュメントの本文を落とす。本文はコマンドではなく、アポストロフィで shlex も失敗する。

    終わりの行が無ければヒアドキュメントではないと見て残す（`echo "a << b"` などの誤認で後ろを落とさない）。
    """
    lines = cmd.split("\n")
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        out.append(line)
        i += 1
        for m in HEREDOC_RE.finditer(line):
            delimiter = m.group(2) or m.group(3) or m.group(4)
            for j in range(i, len(lines)):
                if (lines[j].lstrip("\t") if m.group(1) else lines[j]) == delimiter:
                    i = j + 1
                    break
    return "\n".join(out)


def strip_comments(cmd):
    """行末までのコメントを落とす。引用の中の `#` と語の途中の `#`（`$#`・`x/#a`）はコメントではない。

    shlex に任せると、改行を畳んだ後なので後ろの行まで全部消える。
    """
    out = []
    quote = None
    i = 0
    while i < len(cmd):
        c = cmd[i]
        if quote:
            out.append(c)
            if c == "\\" and quote == '"' and i + 1 < len(cmd):
                out.append(cmd[i + 1])
                i += 1
            elif c == quote:
                quote = None
        elif c == "\\" and i + 1 < len(cmd):
            out.append(c + cmd[i + 1])
            i += 1
        elif c in "\"'":
            quote = c
            out.append(c)
        elif c == "#" and (i == 0 or cmd[i - 1] in " \t\n;&|()"):
            while i < len(cmd) and cmd[i] != "\n":
                i += 1
            continue
        else:
            out.append(c)
        i += 1
    return "".join(out)


def split_operators(tok):
    """`);` のような記号の連なりを演算子に分ける。記号以外を含む語はそのまま返す。"""
    if not tok or not set(tok) <= PUNCTUATION:
        return [tok]
    out = []
    while tok:
        op = next((o for o in OPERATORS if tok.startswith(o)), tok[0])
        out.append(op)
        tok = tok[len(op):]
    return out


def parse(cmd):
    """連鎖を分けて、(単純コマンドの語のリストのリスト, リダイレクトの書き込み先のリスト) を返す。

    サブシェルの境界は ["("]・[")"] の要素として返す。`$(...)` も同じ形になる。
    """
    cmd = cmd.replace("\r\n", "\n").replace("\r", "\n").replace("\\\n", " ")
    cmd = strip_comments(strip_heredocs(cmd))
    lex = shlex.shlex(cmd.replace("\n", " ; "), posix=True, punctuation_chars=True)
    lex.whitespace_split = True
    lex.commenters = ""
    toks = [t for raw in lex for t in split_operators(raw)]

    segs, cur, targets = [], [], []
    i = 0
    while i < len(toks):
        t = toks[i]
        if (t in REDIRS or t in INPUT_REDIRS) and cur and cur[-1].isdigit():
            cur.pop()  # `2>`・`1>&2` の番号（shlex は `2` と `>` を分ける）
        if t in REDIRS:
            nxt = toks[i + 1] if i + 1 < len(toks) else ""
            if not (t == ">&" and nxt.isdigit()) and not nxt.startswith("&"):
                targets.append(nxt)
            i += 2
            continue
        if t in INPUT_REDIRS:
            i += 2
            continue
        if t in SEPS or t in ("(", ")"):
            segs.append(cur)
            cur = []
            if t in ("(", ")"):
                segs.append([t])
        else:
            cur.append(t)
        i += 1
    segs.append(cur)
    return segs, targets


def command_words(seg):
    """先頭の代入・ラッパー・制御語（とその数値やオプションの引数）を読み飛ばした語のリストを返す。"""
    words = [w for w in seg if w != "}"]
    j = 0
    while j < len(words):
        w = words[j]
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", w) or w in WRAPPERS or w in CONTROL_WORDS:
            j += 1
            while w in WRAPPERS and j < len(words) and (words[j].startswith("-") or re.match(r"^[0-9.]+[smhd]?$", words[j])):
                j += 2 if words[j] in WRAPPER_VALUED else 1
            continue
        break
    return words[j:]


def command_name(words):
    return words[0].rsplit("/", 1)[-1]


def operands(words):
    """オプションを除いた引数。単独の `-`（`cd -`）は引数として残す。"""
    return [w for w in words if not w.startswith("-") or w == "-"]


def write_decision(data, hook_path):
    with open(hook_path, encoding="utf-8") as f:
        m = re.search(r"^# GATED_PATHS:[ \t]*(.+)$", f.read(), re.M)
    if not m:
        sys.exit(3)
    pats = []
    for g in m.group(1).split():
        if g.endswith("/"):
            pats.append(re.compile(r"(^|/)" + re.escape(g.rstrip("/")) + r"(/|$)", re.I))
        else:
            pats.append(re.compile(r"(^|/)" + re.escape(g) + r"$", re.I))

    def gated(tok):
        return any(p.search(tok) for p in pats)

    cwd = data.get("cwd") or os.getcwd()

    def expand(words):
        """ブレースとグロブを展開する（シェルと同じく語の順を保つ）。当たらないグロブと変数は字面のまま残す。"""
        out = []
        for w in words:
            for x in expand_braces(w):
                hits = []
                if PATH_META_RE.search(x) and "$" not in x and "`" not in x:
                    absolute = os.path.isabs(os.path.expanduser(x))
                    hits = sorted(h if absolute else os.path.relpath(h, cwd) for h in glob_hits(x, cwd))
                out += hits or [x]
        return out

    cmd = (data.get("tool_input") or {}).get("command") or ""
    if not cmd:
        return "SILENT"
    segs, targets = parse(cmd)
    if any(gated(t) for t in targets):
        return "ASK"
    for seg in segs:
        words = command_words(seg)
        if not words:
            continue
        head = command_name(words)
        if head == "tee":
            if any(gated(w) for w in words[1:] if not w.startswith("-")):
                return "ASK"
        elif head == "cp":
            into = []
            for k, w in enumerate(words[1:], 1):
                nxt = words[k + 1 : k + 2]
                if w.startswith("--target-directory="):
                    into.append(w.split("=", 1)[1])
                elif w == "--target-directory":
                    into += nxt
                elif re.match(r"^-[A-Za-z]*t", w):  # -t DIR・-tDIR・-rt DIR
                    rest = w[w.index("t") + 1 :]
                    into += [rest] if rest else nxt
            if any(gated(w) for w in expand(into) + expand(operands(words[1:]))[-1:]):
                return "ASK"
        elif head == "sed":
            if any(w == "--in-place" or w.startswith("--in-place=") or re.match(r"^-[A-Za-z]*[iI]", w) for w in words[1:]):
                if any(gated(w) for w in expand(operands(words[1:]))):
                    return "ASK"
        elif head == "git":
            k, cdir = 1, ""
            while k < len(words) and words[k].startswith("-"):
                if words[k] == "-C" and k + 1 < len(words):
                    cdir = os.path.join(cdir, words[k + 1])
                k += 2 if words[k] in ("-C", "-c") else 1
            if k < len(words) and words[k] == "mv":
                ops = [w for w in words[k + 1:] if not w.startswith("-")]
                if any(gated(w) or (cdir and gated(os.path.normpath(os.path.join(cdir, w)))) for w in ops):
                    return "ASK"
    return "SILENT"


def project_relative(path, cwd, roots):
    """パスを含むルートのうち最も深いものからの、小文字の相対パスを返す。外か、解決できなければ None。

    最も深いルートで見るのは、プロジェクト自身が親リポジトリの docs/ の下にあるときに全部を docs/ と誤認しないため。
    親だけを実パスに解決する。rm / mv が操作するのはリンクそのもので、リンク先ではない。
    大文字小文字は区別しない（macOS の既定の FS は区別しない）。
    """
    path = os.path.expanduser(path)
    if not os.path.isabs(path):
        if cwd is None:
            return None
        path = os.path.join(cwd, path)
    parent, name = os.path.split(os.path.normpath(path))
    resolved = os.path.join(os.path.realpath(parent), name)
    for root in sorted(roots, key=len, reverse=True):
        rel = os.path.relpath(resolved, root).lower()
        if rel != ".." and not rel.startswith("../"):
            return rel
    return None


def relative_locations(path, cwd, roots):
    """判定するプロジェクトからの相対パスの一覧。外か、解決できなければ空。

    末尾の `/` はリンクをたどる（`rm -rf link/` はリンクを残してリンク先の中身を消す。macOS で確認）ので、リンク先も見る。
    """
    rels = [project_relative(path, cwd, roots)]
    if path.endswith("/") and (cwd is not None or os.path.isabs(os.path.expanduser(path))):
        rels.append(project_relative(os.path.realpath(os.path.join(cwd or "", os.path.expanduser(path))), cwd, roots))
    return [r for r in rels if r is not None]


def under_docs(rel):
    return rel == "docs" or rel.startswith("docs/")


def is_claude_md(rel):
    return os.path.basename(rel) == "claude.md"


@functools.lru_cache(maxsize=None)
def git_location(directory):
    """(worktree のルート, 共通の .git) を返す。git の外や失敗のときは None。"""
    try:
        p = subprocess.run(
            ["git", "-C", directory, "rev-parse", "--path-format=absolute", "--show-toplevel", "--git-common-dir"],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    lines = p.stdout.splitlines()
    if p.returncode != 0 or len(lines) != 2:
        return None
    return os.path.realpath(lines[0]), os.path.realpath(lines[1])


def project_roots(start, cwd):
    """判定するルートの一覧。worktree に入ると CLAUDE_PROJECT_DIR は開始時の場所のままで、cwd だけが移る（公式）。

    開始時の場所か今の場所（同じ呼び出しの `cd` の後）が同じリポジトリの中なら、その worktree のルートも足す。
    別のリポジトリなら足さない。プロジェクトがリポジトリの一部なら、リポジトリのルートも足される。
    """
    project = os.environ.get("CLAUDE_PROJECT_DIR")
    started_in = git_location(os.path.realpath(start))
    root = os.path.realpath(project) if project else (started_in[0] if started_in else os.path.realpath(start))
    roots = [root]
    there = git_location(root)
    if there:
        for directory in (start, cwd):
            here = git_location(directory) if directory else None
            if here and here[1] == there[1] and here[0] not in roots:
                roots.append(here[0])
    return roots


def is_recursive(words):
    return any(w == "--recursive" or re.match(r"^-[A-Za-z]*[rR]", w) for w in words)


def removes_project_root(tok, cwd, roots):
    """対象がプロジェクトのルートかその親か（`.`・`..`・`../proj`）、ルートの直下をまるごと指す形（`*`・`./*`・`*/`・`**`）か。

    末尾が名前ならリンク自体を消すだけなので親だけを解決する。`.`・`..`・末尾の `/`・グロブはリンクをたどる。
    """
    base = re.sub(r"(^|/)\*+/?$", r"\1", tok)
    if PATH_META_RE.search(base):
        return False
    path = os.path.expanduser(base or ".")
    if not os.path.isabs(path):
        if cwd is None:
            return False
        path = os.path.join(cwd, path)
    parent, name = os.path.split(path)
    real = os.path.realpath(path) if name in ("", ".", "..") else os.path.join(os.path.realpath(parent), name)
    return any(r == real or r.startswith(real.rstrip(os.sep) + os.sep) for r in roots)


def expand_braces(tok):
    """`{a,b}` を語の順を保って展開する。`{}`・`{1..3}` は展開しない。上限を超えたら TooMany。"""
    words = [tok]
    while True:
        out, changed = [], False
        for t in words:
            m = BRACE_RE.search(t)
            if m:
                changed = True
                out += [t[: m.start()] + alt + t[m.end() :] for alt in m.group(1).split(",")]
            else:
                out.append(t)
            if len(out) > EXPAND_LIMIT:
                raise TooMany(tok)
        if not changed:
            return out
        words = out


def glob_hits(tok, cwd):
    """今あるファイルに対してグロブを展開する。`**` は zsh と同じく再帰する（bash の既定より広く見る）。

    当たりを 1 件ずつ返すので、呼び出し側は最初に当たった時点で止められる。上限の件数か時間を超えたら TooMany。
    """
    path = os.path.expanduser(tok)
    if not os.path.isabs(path):
        if cwd is None:
            return
        path = os.path.join(glob.escape(cwd), path)
    deadline = time.monotonic() + GLOB_SECONDS
    for n, hit in enumerate(glob.iglob(path, recursive=True)):
        if n >= GLOB_LIMIT or time.monotonic() > deadline:
            raise TooMany(tok)
        yield hit


def path_is_gated(path, cwd, roots):
    return any(is_claude_md(rel) or under_docs(rel) for rel in relative_locations(path, cwd, roots))


def delete_target_is_gated(tok, cwd, roots):
    """プロジェクトの中の CLAUDE.md（どの階層でも）か、ルートの docs/ の下か。外のパスは当たらない。"""
    meta = PATH_META_RE.search(tok)
    if not meta:
        return path_is_gated(tok, cwd, roots)

    # グロブ・変数の手前までは確定している（`docs/$f`・`docs*`・`CLAUDE.md*`）
    prefix = tok[: meta.start()]
    rels = relative_locations(prefix or ".", cwd, roots)
    if not rels:
        return False
    if any(under_docs(rel) or (prefix and is_claude_md(rel)) for rel in rels):
        return True
    # 変数は行き先が分からないので見ない
    if "$" in tok or "`" in tok:
        return False
    # 名前が書かれている形（`*/CLAUDE.md`）は、今ファイルが無くても止める
    if tok.rsplit("/", 1)[-1].lower() == "claude.md":
        return True
    return any(path_is_gated(hit, cwd, roots) for hit in glob_hits(tok, cwd))


def delete_decision(data):
    cmd = (data.get("tool_input") or {}).get("command") or ""
    if not cmd:
        return "SILENT"
    start = data.get("cwd") or os.getcwd()
    cwd = start
    subshells = []
    segs, _ = parse(cmd)
    for seg in segs:
        if seg == ["("]:
            subshells.append(cwd)
            continue
        if seg == [")"]:
            if subshells:
                cwd = subshells.pop()
            continue
        words = command_words(seg)
        if not words:
            continue
        head = command_name(words)
        if head == "cd":
            # `cd` の後の相対パスを正しく解決する。解決できない形（`cd -`・変数）の後の相対パスは見ない
            ops = operands(words[1:])
            target = os.path.expanduser(ops[0] if ops else "~")
            if target == "-" or "$" in target or "`" in target or (cwd is None and not os.path.isabs(target)):
                cwd = None
            else:
                cwd = os.path.normpath(os.path.join(cwd or "", target))
        elif head in ("rm", "mv"):
            roots = project_roots(start, cwd)  # git を呼ぶので、rm / mv があったときだけ求める
            ops = [t for w in operands(words[1:]) for t in expand_braces(w)]
            if any(delete_target_is_gated(w, cwd, roots) for w in ops):
                return "DENY"
            if head == "rm" and is_recursive(words[1:]) and any(removes_project_root(w, cwd, roots) for w in ops):
                return "DENY"
    return "SILENT"


def main():
    data = json.load(sys.stdin)
    write = sys.argv[1] == "write"
    try:
        verdict = write_decision(data, sys.argv[2]) if write else delete_decision(data)
    except TooMany:
        verdict = "ASK" if write else "DENY"
    print(verdict)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        sys.exit(3)
