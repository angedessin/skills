---
type: llm
focus: trace
---

Judge only what the assistant wrote, either in its replies or in what it added to the design document. PASS if it points out a race between requests: a slower, older response can overwrite the result of a newer request (for example when changing the category or keyword quickly). FAIL otherwise.
