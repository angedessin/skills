---
type: llm
focus: trace
---

Judge only what the assistant wrote (its replies and any design document it wrote). PASS if it treats how the client learns the total count or whether more pages exist as a decision or open question, given that the API returns a plain array with no paging information (for example: paginate on the client, or extend the API). FAIL if it silently assumes the API already supports paging.
