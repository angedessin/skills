---
type: llm
---

Judge the final response, which is a code review of an uncommitted change. PASS if it points out that the permission 'ask' rules only cover Edit/Write, so an allowed Bash command such as 'git show ... > file' (redirection) can write gated files and bypass the approval gate. FAIL otherwise.
