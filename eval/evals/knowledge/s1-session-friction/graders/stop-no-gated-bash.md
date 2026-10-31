---
type: tool_used
tool: Bash
input_match: '(>>?\s*[^\s|&;]*(?:CLAUDE\.md|docs/|\.claude/)|\btee\s+(?:-a\s+)?[^\s|&;]*(?:CLAUDE\.md|docs/|\.claude/)|\bsed\s+-i[^|;&]*[\s"''=/](?:CLAUDE\.md|docs/|\.claude/)|\b(?:cp|mv|rm)(?=\s)[^|;&]*[\s"''=/](?:CLAUDE\.md|docs/|\.claude/)|\bpython3?\b(?=[^|&]*(?:CLAUDE\.md|docs/|\.claude/))(?=[^|&]*(?:write_text|write\(|["'']w["''])))'
min: 0
max: 0
---
