---
type: llm
---

Judge the final response, which is a code review of an uncommitted change. PASS if it points out that when the request fails at the network level (fetch rejects with a TypeError, for example offline), the catch block returns without leaving the loading state, so the UI stays on '読み込み中…' forever and the retry button (shown only in the error state) never appears. FAIL if this problem is not mentioned.
