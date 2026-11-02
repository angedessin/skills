---
type: llm
focus: trace
---

Judge only what the assistant wrote (its replies and any design document it wrote). PASS if it treats where the category options come from as a decision or open question, given that the API has no endpoint that lists categories (for example: derive them from search results, hard-code them, or add an API). FAIL if it never addresses where the options come from, or silently assumes a category-list API exists.
