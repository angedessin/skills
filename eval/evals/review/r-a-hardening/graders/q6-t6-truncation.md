---
type: llm
---

Judge the final response, which is a code review of an uncommitted change. PASS if it points out that the report truncates text with [:120], so a difference located later in the line (for example around character 192) is not visible. FAIL otherwise.
