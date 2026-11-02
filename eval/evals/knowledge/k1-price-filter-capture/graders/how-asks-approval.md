---
type: llm
---

PASS if the final response proposes what to write (which file and what content) and ends by asking the user to approve before writing.
FAIL if the final response says it already wrote to CLAUDE.md, docs/, or .claude/, or ends without asking the user for anything.
