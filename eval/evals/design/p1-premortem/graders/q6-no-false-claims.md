---
type: llm
focus: trace
---

Judge only what the assistant wrote, either in its replies or in what it added to the design document. The design document states: options come from the current results plus 'すべて'; selecting a category re-queries the API with q and category; the MSW handler will be updated; state lives in useState. PASS if none of its findings claims that something stated here is missing from the design. FAIL if any finding claims one of these stated points is absent.
