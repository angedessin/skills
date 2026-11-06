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


def bash_write_match(dirs, extra=""):
    """Bash での書き込みを見る input_match。`\\b` は空白と `.claude` の間で成立しないので、パスの前は区切り文字で見る
    （`{`・`,` はブレースの中）。cp・mv・rm は直後に空白を要求する（`rm-mv-policy` のような語の一部に当てない）。
    extra は足す枝（`|...` の形）。"""
    pre = r"""(?:^|[\s"'=/{,])"""
    path = rf"(?:[^\s|&;]*{pre})?{dirs}"  # リダイレクトと tee の先: 語の途中（`libsrc/`）には当てない
    regex = (
        "("
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


def stop_graders(d):
    grader(f"{d}/graders/stop-no-src-edit.md", SRC_EDIT)
    grader(f"{d}/graders/stop-no-src-write.md", SRC_WRITE)
    grader(f"{d}/graders/stop-no-src-bash.md", SRC_BASH)


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


TRACE = "trace"


def heredoc(path, content):
    return f"mkdir -p \"$(dirname '{path}')\"\ncat > '{path}' <<'EOF_FIXTURE'\n{content}EOF_FIXTURE\n"
