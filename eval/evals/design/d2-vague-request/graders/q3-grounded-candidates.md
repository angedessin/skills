---
type: llm
focus: trace
---

Judge only what the assistant wrote. PASS if, when it proposes candidate improvements, at least one is grounded in the current screen (for example: only substring match on the name, no sorting, no category filter, search only on submit). Also PASS if it proposes no candidates at all. FAIL if it proposes candidates that are all generic and unrelated to the actual screen.
