#!/usr/bin/env python3
"""guard-gated-write.sh と guard-gated-delete.sh の共通の判定（標準ライブラリだけ）。

Usage: python3 guard_gated.py write <guard-gated-write.sh のパス>   # 標準出力: ASK / SILENT
       python3 guard_gated.py delete                               # 標準出力: DENY / SILENT
       入力は hook の stdin の JSON。tool_input.command だけを見る（transcript_path などが常に混ざるので全文は見ない）。
       解析に失敗したら exit 3。何を守らないかは各 hook の冒頭コメントに書く。
"""
import json
import os
import re
import shlex
import subprocess
import sys

REDIRS = {">", ">>", "&>", "&>>", ">|", ">&"}
INPUT_REDIRS = {"<", "<<", "<<-", "<<<", "<&"}
SEPS = {";", "&&", "||", "|", "|&", "&", ";;"}
# shlex は連続する記号を 1 語にまとめる（`);`・`)&&`）ので、長いものから順に分ける
OPERATORS = ["&>>", "<<<", "<<-", ">>", "&>", ">|", ">&", "<<", "<&", "&&", "||", "|&", ";;", ";", "(", ")", "&", "|", ">", "<"]
PUNCTUATION = set("();<>|&")
WRAPPERS = {"timeout", "time", "nice", "nohup", "stdbuf", "command", "builtin", "noglob", "xargs", "env", "exec", "sudo", "{", "!"}
CONTROL_WORDS = {"if", "then", "elif", "else", "while", "until", "do"}
WRAPPER_VALUED = {"-u", "-g"}  # env -u NAME / sudo -u USER -g GROUP: 次の語は値
HEREDOC_RE = re.compile(r"""(?<!<)<<-?(?!<)\s*(?:'([^']+)'|"([^"]+)"|\\?([A-Za-z_]\w*))""")
PATH_META_RE = re.compile(r"[*?\[{$`]")


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
        m = HEREDOC_RE.search(line)
        if not m:
            continue
        delimiter = m.group(1) or m.group(2) or m.group(3)
        for j in range(i, len(lines)):
            if lines[j].strip() == delimiter:
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


def project_relative(path, cwd, root):
    """プロジェクトのルートからの小文字の相対パスを返す。外か、解決できなければ None。

    親だけを実パスに解決する。rm / mv が操作するのはリンクそのもので、リンク先ではない。
    大文字小文字は区別しない（macOS の既定の FS は区別しない）。
    """
    path = os.path.expanduser(path)
    if not os.path.isabs(path):
        if cwd is None:
            return None
        path = os.path.join(cwd, path)
    parent, name = os.path.split(os.path.normpath(path))
    rel = os.path.relpath(os.path.join(os.path.realpath(parent), name), root).lower()
    return None if rel == ".." or rel.startswith("../") else rel


def under_docs(rel):
    return rel == "docs" or rel.startswith("docs/")


def is_claude_md(rel):
    return os.path.basename(rel) == "claude.md"


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


def project_roots(start):
    """判定するルートの一覧。worktree に入ると CLAUDE_PROJECT_DIR は開始時の場所のままで、cwd だけが移る（公式）。

    cwd が同じリポジトリの worktree なら、そのルートも足す。別のリポジトリなら足さない。
    """
    root = os.path.realpath(os.environ.get("CLAUDE_PROJECT_DIR") or start)
    here, there = git_location(start), git_location(root)
    if here and there and here[1] == there[1] and here[0] != root:
        return [root, here[0]]
    return [root]


def is_recursive(words):
    return any(w == "--recursive" or re.match(r"^-[A-Za-z]*[rR]", w) for w in words)


def removes_project_root(tok, cwd, roots):
    """対象がプロジェクトのルートかその親か（`.`・`..`・`../proj`）、ルートの直下をまるごと指す形（`*`・`./*`）か。"""
    base = re.sub(r"(^|/)\*$", r"\1", tok)
    if PATH_META_RE.search(base):
        return False
    path = os.path.expanduser(base or ".")
    if not os.path.isabs(path):
        if cwd is None:
            return False
        path = os.path.join(cwd, path)
    real = os.path.realpath(path)
    return any(r == real or r.startswith(real.rstrip(os.sep) + os.sep) for r in roots)


def delete_target_is_gated(tok, cwd, roots):
    return any(target_is_gated_in(tok, cwd, root) for root in roots)


def target_is_gated_in(tok, cwd, root):
    """プロジェクトの中の CLAUDE.md（どの階層でも）か、ルートの docs/ の下か。外のパスは当たらない。"""
    meta = PATH_META_RE.search(tok)
    if not meta:
        rel = project_relative(tok, cwd, root)
        return rel is not None and (is_claude_md(rel) or under_docs(rel))

    # グロブ・ブレース・変数の手前までは確定している（`docs/$f`・`docs*`・`CLAUDE.md*`）
    prefix = tok[: meta.start()]
    rel = project_relative(prefix or ".", cwd, root)
    if rel is None:
        return False
    if under_docs(rel) or (prefix and is_claude_md(rel)):
        return True
    # 名前が書かれていて、手前にグロブがあるだけの形（`*/CLAUDE.md`）。変数は行き先が分からないので見ない
    if "$" in tok or "`" in tok:
        return False
    return tok.rsplit("/", 1)[-1].lower() == "claude.md"


def delete_decision(data):
    cmd = (data.get("tool_input") or {}).get("command") or ""
    if not cmd:
        return "SILENT"
    start = data.get("cwd") or os.getcwd()
    roots = None  # git を呼ぶので、rm / mv があったときだけ求める
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
            roots = roots or project_roots(start)
            ops = operands(words[1:])
            if any(delete_target_is_gated(w, cwd, roots) for w in ops):
                return "DENY"
            if head == "rm" and is_recursive(words[1:]) and any(removes_project_root(w, cwd, roots) for w in ops):
                return "DENY"
    return "SILENT"


def main():
    data = json.load(sys.stdin)
    if sys.argv[1] == "write":
        print(write_decision(data, sys.argv[2]))
    else:
        print(delete_decision(data))


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        sys.exit(3)
