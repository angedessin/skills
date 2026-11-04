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
import sys

REDIRS = {">", ">>", "&>", "&>>", ">|", ">&"}
SEPS = {";", "&&", "||", "|", "|&", "&", "(", ")", ";;"}
WRAPPERS = {"timeout", "time", "nice", "nohup", "stdbuf", "command", "builtin", "noglob", "xargs", "env", "exec", "sudo", "{", "!"}
WRAPPER_VALUED = {"-u", "-g"}  # env -u NAME / sudo -u USER -g GROUP: 次の語は値
HEREDOC_RE = re.compile(r"""(?<!<)<<-?(?!<)\s*(?:'([^']+)'|"([^"]+)"|\\?([A-Za-z_]\w*))""")


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


def parse(cmd):
    """連鎖を分けて、(単純コマンドの語のリストのリスト, リダイレクトの書き込み先のリスト) を返す。"""
    cmd = cmd.replace("\r\n", "\n").replace("\r", "\n").replace("\\\n", " ")
    cmd = strip_heredocs(cmd)
    lex = shlex.shlex(cmd.replace("\n", " ; "), posix=True, punctuation_chars=True)
    lex.whitespace_split = True
    toks = list(lex)

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
        if t in SEPS:
            segs.append(cur)
            cur = []
        else:
            cur.append(t)
        i += 1
    segs.append(cur)
    return segs, targets


def command_words(seg):
    """先頭の代入・ラッパー（とその数値やオプションの引数）を読み飛ばした語のリストを返す。"""
    words = [w for w in seg if w != "}"]
    j = 0
    while j < len(words):
        w = words[j]
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", w) or w in WRAPPERS:
            j += 1
            while j < len(words) and (words[j].startswith("-") or re.match(r"^[0-9.]+[smhd]?$", words[j])):
                j += 2 if words[j] in WRAPPER_VALUED else 1
            continue
        break
    return words[j:]


def command_name(words):
    return words[0].rsplit("/", 1)[-1]


def operands(words):
    """オプションを除いた引数（`--` の後ろは全部引数）。"""
    out, only_operands = [], False
    for w in words:
        if only_operands or not w.startswith("-"):
            out.append(w)
        elif w == "--":
            only_operands = True
    return out


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


def delete_target_is_gated(tok, cwd, root):
    """プロジェクトの中の CLAUDE.md（どの階層でも）か、ルートの docs/ の下か。

    外のパス（`/tmp/x/docs/y`）は当たらない。大文字小文字は区別しない（macOS の既定の FS は区別しない）。
    """
    if "$" in tok or "`" in tok:
        return False
    tok = re.split(r"[*?\[{]", tok, maxsplit=1)[0]  # グロブとブレースの手前まで（`CLAUDE.md*`・`docs/x{,.bak}`）
    if not tok:
        return False
    tok = os.path.expanduser(tok)
    if not os.path.isabs(tok):
        if cwd is None:
            return False
        tok = os.path.join(cwd, tok)
    rel = os.path.relpath(os.path.realpath(tok), root).lower()
    if rel == ".." or rel.startswith("../"):
        return False
    return os.path.basename(rel) == "claude.md" or rel == "docs" or rel.startswith("docs/")


def delete_decision(data):
    cmd = (data.get("tool_input") or {}).get("command") or ""
    if not cmd:
        return "SILENT"
    start = data.get("cwd") or os.getcwd()
    root = os.path.realpath(os.environ.get("CLAUDE_PROJECT_DIR") or start)
    cwd = start
    segs, _ = parse(cmd)
    for seg in segs:
        words = command_words(seg)
        if not words:
            continue
        head = command_name(words)
        if head == "cd":
            # `cd` の後の相対パスを正しく解決する。解決できない形（`cd -`・変数）の後の相対パスは見ない
            ops = operands(words[1:])
            target = os.path.expanduser(ops[0] if ops else "~")
            if target == "-" or "$" in target or "`" in target or cwd is None and not os.path.isabs(target):
                cwd = None
            else:
                cwd = os.path.normpath(os.path.join(cwd or "", target))
        elif head in ("rm", "mv") and any(delete_target_is_gated(w, cwd, root) for w in operands(words[1:])):
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
