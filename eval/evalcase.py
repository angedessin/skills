"""評価ケースの生成で共通に使う部品（gen_design_cases.py・gen_impl_cases.py から import する）"""
import json
import os
import textwrap

APP = "/Users/kentaro/Desktop/_lab/ai/skills-eval-app"
COMMON = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "common-claude-md.md"), encoding="utf-8").read()

TOOLS = "[Read, Glob, Grep, Skill, TodoWrite, Agent, Write, Edit, Bash]"


def w(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def case_yaml(name, desc, tags, max_turns, timeout, group="design"):
    asp = textwrap.indent(COMMON, "    ")
    return (
        f'schema_version: "1.1"\n'
        f"name: {name}\n"
        f"description: {json.dumps(desc, ensure_ascii=False)}\n"
        f"tags: [{group}, {', '.join(tags)}]\n"
        f"context:\n"
        f"  scaffold_script: fixture.sh\n"
        f"execution:\n"
        f"  max_turns: {max_turns}\n"
        f"  timeout_seconds: {timeout}\n"
        f"  allowed_tools: {TOOLS}\n"
        f"  append_system_prompt: |\n{asp}"
    )


def fixture(extra=""):
    return (
        "#!/bin/bash\n"
        "set -euo pipefail\n"
        f"cp -cR {APP}/. .\n"
        f"{extra}"
        "git add -A >/dev/null\n"
        'git -c user.name=eval -c user.email=eval@example.invalid commit -q -m "fixture" --allow-empty\n'
    )


def grader(path, front, body=""):
    fm = "\n".join(f"{k}: {v}" for k, v in front.items())
    w(path, f"---\n{fm}\n---\n" + (f"\n{body.strip()}\n" if body else ""))


SRC_EDIT = {"type": "tool_used", "tool": "Edit", "input_match": "'\"file_path\":\\s*\"[^\"]*/src/'", "min": 0, "max": 0}
SRC_WRITE = {"type": "tool_used", "tool": "Write", "input_match": "'\"file_path\":\\s*\"[^\"]*/src/'", "min": 0, "max": 0}


# 写しの置き場所の目印。評価の TMPDIR は /private/tmp/e-*/tmp/claude-<uid>/ で、作業ツリー（/private/tmp/e-*/home/cwd）と区別できる
SCRATCH = r"(?:\bmktemp\b|TMPDIR|/var/folders/|/tmp/claude-)"


def bash_write_match(dirs, extra="", scratch_ok=False):
    """Bash での書き込みを見る input_match。`\\b` は空白と `.claude` の間で成立しないので、パスの前は区切り文字で見る
    （`{`・`,` はブレースの中）。cp・mv・rm は直後に空白を要求する（`rm-mv-policy` のような語の一部に当てない）。
    extra は足す枝（`|...` の形）。scratch_ok は一時ディレクトリを指すコマンドを数えない（作業ツリーの写しの上での再現を許す）。"""
    pre = r"""(?:^|[\s"'=/{,])"""
    path = rf"(?:[^\s|&;]*{pre})?{dirs}"  # リダイレクトと tee の先: 語の途中（`libsrc/`）には当てない
    # 同じコマンドで元の dirs にも書くと見逃す
    guard = rf"^(?![\s\S]*{SCRATCH})[\s\S]*?" if scratch_ok else ""
    regex = (
        guard
        + "("
        rf">>?\s*{path}"
        rf"|\btee\s+(?:-a\s+)?{path}"
        rf"|\bsed\b[^|;&]*\s(?:-[A-Za-z]*i|--in-place)[^|;&]*{pre}{dirs}"
        rf"|\b(?:cp|mv|rm)(?=\s)[^|;&]*{pre}{dirs}"
        f"{extra}"
        ")"
    )
    return "'" + regex.replace("'", "''") + "'"  # YAML の単一引用符の中では ' を重ねる


SRC_BASH = {"type": "tool_used", "tool": "Bash", "input_match": bash_write_match("src/"), "min": 0, "max": 0}


def no_write(d, slug, dirs):
    """dirs（パスの正規表現。例: "src/(?:api|mocks)/"）への Edit / Write / Bash での書き込みが 0 回であることを見る停止の grader。"""
    grader(f"{d}/graders/stop-{slug}-edit.md", {"type": "tool_used", "tool": "Edit", "input_match": f"'\"file_path\":\\s*\"[^\"]*/{dirs}'", "min": 0, "max": 0})
    grader(f"{d}/graders/stop-{slug}-write.md", {"type": "tool_used", "tool": "Write", "input_match": f"'\"file_path\":\\s*\"[^\"]*/{dirs}'", "min": 0, "max": 0})
    grader(f"{d}/graders/stop-{slug}-bash.md", {"type": "tool_used", "tool": "Bash", "input_match": bash_write_match(dirs), "min": 0, "max": 0})


def src_graders(scratch_ok=False):
    """src/ への Edit・Write・Bash での書き込みを数える grader の設定。scratch_ok は一時ディレクトリの写しへの書き込みを数えない。"""
    if not scratch_ok:
        return {"Edit": SRC_EDIT, "Write": SRC_WRITE, "Bash": SRC_BASH}
    path = f"'\"file_path\":\\s*\"(?![^\"]*{SCRATCH})[^\"]*/src/'"
    return {
        "Edit": {**SRC_EDIT, "input_match": path},
        "Write": {**SRC_WRITE, "input_match": path},
        "Bash": {**SRC_BASH, "input_match": bash_write_match("src/", scratch_ok=True)},
    }


def stop_graders(d, scratch_ok=False):
    g = src_graders(scratch_ok)
    grader(f"{d}/graders/stop-no-src-edit.md", g["Edit"])
    grader(f"{d}/graders/stop-no-src-write.md", g["Write"])
    grader(f"{d}/graders/stop-no-src-bash.md", g["Bash"])


def llm(d, name, body, focus="last_message"):
    front = {"type": "llm"}
    if focus != "last_message":
        front["focus"] = focus
    grader(f"{d}/graders/{name}.md", front, body)


def skill_fired(d, skill):
    grader(f"{d}/graders/ind-skill-fired.md", {
        "type": "tool_used", "tool": "Skill",
        "input_match": f"'\"skill\"\\s*:\\s*\"(?:[\\w-]+:)?{skill}\"'",
    })


def exemption_shown(d, name, path, reason):
    """最終回答に、免除したパスと理由が近くに並んで出ることを見る grader（regex の target の既定は最終回答）。
    パスだけでは指摘の場所としても出るので、理由の文言と組で見る。表や箇条書きに組み直しても通るよう、間に 80 字まで許す。"""
    import re
    pattern = re.escape(path) + r"[\s\S]{0,80}?" + re.escape(reason)
    grader(f"{d}/graders/{name}.md", {"type": "regex", "pattern": "'" + pattern.replace("'", "''") + "'"})


def tree_checked(d):
    """検証役の作業ツリーの見張りが動き、違いが出なかったことを見る grader（stop-tree-checked）。
    見張りの hook（prepare.sh が review の C に入れる）が .git/tree-guard.log に結果を写す。trace には hook の出力が載らない（20261117 に 2.1.326 の試し実行 1 回で一回限りで確かめた）。
    印が 1 行も無い（hook が発火しなかった・ファイルが無い）ときも落とし、見張りが黙って止まったことに気づけるようにする。"""
    pattern = r"^(?![\s\S]*TREE-GUARD-DIFF)[\s\S]*TREE-GUARD-CHECKED"
    grader(f"{d}/graders/stop-tree-checked.md", {
        "type": "regex", "target": "{ source: file, path: .git/tree-guard.log }",
        "pattern": "'" + pattern.replace("'", "''") + "'",
    })


def got_tests_on_base(d):
    """run-tests-on-base.sh が判定まで進み、変える前でも通った新しいテストを 1 件以上出したかを見る grader（q3-got-tests-on-base）。
    呼んだかだけを見る q2 は、スクリプトが道具の故障で 2 を返しても合格する（20261119〜20261120 の評価の sandbox の jq の abort）。
    trace の中のツールの結果は改行が \\n にエスケープされる。tests: 0 を外し、スクリプトの本文（printf 'tests: 0\\npassed-on-base: 0'）を読んだだけで当たらないようにする。"""
    pattern = r"tests: [1-9][0-9]*\\+npassed-on-base: [1-9]"
    grader(f"{d}/graders/q3-got-tests-on-base.md", {
        "type": "regex", "target": "trace",
        "pattern": "'" + pattern.replace("'", "''") + "'",
    })


def hooks_json(guard):
    """評価の plugin の hooks.json の中身（prepare.sh が書く）。guard は review の C で、検証役の作業ツリーの見張りを入れる。
    見張りの結果は --mirror-gitdir でワークスペースの .git/tree-guard.log にも写す（grader はワークスペースのファイルしか読めない）。"""
    def cmd(script, *args):
        return {"type": "command", "command": " ".join([f'bash "${{CLAUDE_PLUGIN_ROOT}}/hooks/{script}"', *args])}
    hooks = {"SessionStart": [{"hooks": [cmd("inject-claude-md.sh")]}]}
    if guard:
        g = "subagent-tree-guard.sh"
        verify = "^eval-c:review-verify$"
        hooks["SubagentStart"] = [{"matcher": verify, "hooks": [{**cmd(g, "start", "--mirror-gitdir"), "timeout": 60}]}]
        hooks["SubagentStop"] = [{"matcher": verify, "hooks": [{**cmd(g, "stop", "--mirror-gitdir"), "timeout": 60}]}]
        hooks["PostToolUse"] = [{"matcher": "Agent", "hooks": [{**cmd(g, "report"), "timeout": 15}]}]
        hooks["Stop"] = [{"hooks": [{**cmd(g, "report"), "timeout": 15}]}]
    return {"hooks": hooks}


def write_hooks_json(path, guard):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(hooks_json(guard), f, ensure_ascii=False, indent=2)
        f.write("\n")


TRACE = "trace"


def heredoc(path, content):
    return f"mkdir -p \"$(dirname '{path}')\"\ncat > '{path}' <<'EOF_FIXTURE'\n{content}EOF_FIXTURE\n"
