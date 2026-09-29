#!/bin/bash
# PreToolUse(Bash) guard: 承認ゲート対象パスへの Bash 経由の書き込みを強制確認（ask）に落とす。
#
# GATED_PATHS: CLAUDE.md docs/knowledge/ docs/decisions/ .claude/settings.json .claude/settings.local.json .claude/hooks/
#
# ↑ 対象パスの正本（この 1 行）。末尾 / はディレクトリ配下。permissions.ask の Edit(./...) と対で維持し、
#   check_asset_consistency.py の契約 (s) が突合する。フィクスチャはこの行からケースを自動生成する。
#   guard-gated-delete.sh は意図的に 3 系統（.claude/ を含まない）で、契約 (s) の対象外。
#
# なぜ要るか: permissions のファイルパス ask は Edit(path) のみ（Write ツール呼び出しも Edit 規則が覆う）。
# Bash のリダイレクト先は Claude Code 自体も検査するが、見るのは Edit の allow / deny と作業ディレクトリで
# ask は見ない — acceptEdits では `git show HEAD:a > CLAUDE.md` が ask をすり抜けて上書きされた（20260927 実測）。
# ファイルに触れる全ツール分のルールを揃える（docs/knowledge/claude-code-config.md）規律の Bash 側を担う。
#
# 守る形（ask）: 連鎖（&& || ; | 改行 { } ( )）のすべての部分について
#   - 出力リダイレクト（> >> &> 2> >| 等）の先が対象パス
#   - tee の書き込み先が対象パス
#   - git mv の引数に対象パス（settings.local.json の `Bash(git mv *)` で上書きできるため。-C の値と合成して見る）
#   先頭の代入・ラッパー（env / exec / sudo / timeout 等）は読み飛ばす。照合は大文字小文字を区別しない
#   （macOS の既定 FS は区別せず、`> CLAUDE.MD` でも実ファイルが書き換わる）。
# 守らない形（沈黙）: cd 後の相対パス・変数展開・bash -c / eval の中身・sed -i・任意インタプリタ。
# 脅威モデルは敵対者ではなく「停止契約を滑った善意のエージェント」。**完全な封鎖ではない**。
#
# 判定は tool_input.command の構造抽出（python3 標準ライブラリの json + shlex）。全文検査はしない
# — 入力 JSON には transcript_path（~/.claude/projects/...）が常に入り、.claude/ の判定が恒常的に誤検知する。
# python3 が無い・解析に失敗したときは、下の全文 grep（元の 3 系統）に縮退する（完全な沈黙にはしない）。
# 縮退中は .claude/ 系 3 系統と git mv を守らない（6 系統中 3 系統。python3 前提の防御）。
# 出力は ask の JSON を最大 1 つ（deny は出さない — 誤検知の代償を確認 1 回に抑える）。

payload=$(cat)
[ -z "$payload" ] && exit 0

ask_json() {
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"ask","permissionDecisionReason":"%s"}}\n' "$1"
}

reason='承認制のパス（CLAUDE.md / docs/knowledge/ / docs/decisions/ / .claude/settings*.json / .claude/hooks/）への Bash 経由の書き込み・移動を検出しました（guard-gated-write hook）。knowledge-capture / compound / adr がドラフト提示の停止を越えていないか確認してください。'

# 構造判定。標準出力: ASK / SILENT。それ以外（python3 不在・例外）は縮退へ。
read -r -d '' PYCODE <<'PY'
import json, os, re, shlex, sys

def main():
    hook_path = sys.argv[1]
    m = re.search(r"^# GATED_PATHS:[ \t]*(.+)$", open(hook_path, encoding="utf-8").read(), re.M)
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

    data = json.load(sys.stdin)
    cmd = (data.get("tool_input") or {}).get("command") or ""
    if not cmd:
        print("SILENT")
        return
    cmd = cmd.replace("\r\n", "\n").replace("\r", "\n").replace("\\\n", " ")

    lex = shlex.shlex(cmd.replace("\n", " ; "), posix=True, punctuation_chars=True)
    lex.whitespace_split = True
    toks = list(lex)

    redirs = {">", ">>", "&>", "&>>", ">|", ">&"}
    seps = {";", "&&", "||", "|", "|&", "&", "(", ")", ";;"}
    wrappers = {"timeout", "time", "nice", "nohup", "stdbuf", "command", "builtin", "noglob", "xargs", "env", "exec", "sudo", "{", "!"}
    wrapper_valued = {"-u", "-g"}  # env -u NAME / sudo -u USER -g GROUP: 次の語は値

    segs, cur = [], []
    i = 0
    while i < len(toks):
        t = toks[i]
        if t in redirs:
            nxt = toks[i + 1] if i + 1 < len(toks) else ""
            if not (t == ">&" and nxt.isdigit()) and not nxt.startswith("&") and gated(nxt):
                print("ASK")
                return
            i += 2
            continue
        if t in seps:
            segs.append(cur)
            cur = []
        else:
            cur.append(t)
        i += 1
    segs.append(cur)

    for seg in segs:
        words = [w for w in seg if w not in ("}",)]
        # 先頭の代入・ラッパー（とその数値/オプション引数）を読み飛ばす
        j = 0
        while j < len(words):
            w = words[j]
            if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", w) or w in wrappers:
                j += 1
                while j < len(words) and (words[j].startswith("-") or re.match(r"^[0-9.]+[smhd]?$", words[j])):
                    j += 2 if words[j] in wrapper_valued else 1
                continue
            break
        words = words[j:]
        if not words:
            continue
        head = words[0].rsplit("/", 1)[-1]
        if head == "tee":
            if any(gated(w) for w in words[1:] if not w.startswith("-")):
                print("ASK")
                return
        elif head == "git":
            k, cdir = 1, ""
            while k < len(words) and words[k].startswith("-"):
                if words[k] == "-C" and k + 1 < len(words):
                    cdir = os.path.join(cdir, words[k + 1])
                k += 2 if words[k] in ("-C", "-c") else 1
            if k < len(words) and words[k] == "mv":
                ops = [w for w in words[k + 1:] if not w.startswith("-")]
                if any(gated(w) or (cdir and gated(os.path.normpath(os.path.join(cdir, w)))) for w in ops):
                    print("ASK")
                    return
    print("SILENT")

try:
    main()
except SystemExit:
    raise
except Exception:
    sys.exit(3)
PY

verdict=$(printf '%s' "$payload" | python3 -c "$PYCODE" "$0" 2>/dev/null)
case "$verdict" in
  ASK) ask_json "$reason"; exit 0 ;;
  SILENT) exit 0 ;;
esac

# ---- 縮退: python3 不在・解析失敗。全文 grep（元の 3 系統・リダイレクトと tee のみ）----
# 全文検査なので誤検知はありうる（ask なので代償は確認 1 回）。.claude/ 系は transcript_path と衝突するため見ない。
targets='CLAUDE\.md|docs/knowledge/|docs/decisions/'
if printf '%s' "$payload" | grep -qiE ">>?[[:space:]\\\\\"']*[^|&;]*($targets)"; then
  ask_json "$reason"
  exit 0
fi
if printf '%s' "$payload" | grep -qiE "tee[[:space:]\\\\\"'-]+[^|&;]*($targets)"; then
  ask_json "$reason"
fi

exit 0
