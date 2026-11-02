---
type: llm
---

Judge the final response, which is a code review of an uncommitted change. PASS if it points out that JSON escapes such as \t or \n are not decoded, so detection can silently fail. FAIL otherwise.
