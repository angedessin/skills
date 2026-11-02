---
type: llm
---

Judge the final response, which is a code review of an uncommitted change. PASS if it points out that grepping the whole command line wrongly denies commands like 'rm /tmp/a && ls docs/knowledge/' where the gated path is not being deleted. FAIL otherwise.
