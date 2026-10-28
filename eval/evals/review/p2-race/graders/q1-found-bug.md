---
type: llm
---

Judge the final response, which is a code review of an uncommitted change. PASS if it points out that, because a request is sent on every keystroke without cancelling or ignoring earlier requests, a slower response for an older query can arrive after a newer one and overwrite the results (a race; for example missing cleanup, AbortController, or an ignore flag in the effect). FAIL if this problem is not mentioned.
