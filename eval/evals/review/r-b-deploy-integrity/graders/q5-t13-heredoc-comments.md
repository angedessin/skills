---
type: llm
---

Judge the final response, which is a code review of an uncommitted change. PASS if it points out that dropping lines starting with '#' also removes lines inside heredocs (and that the shebang is not compared). FAIL otherwise.
