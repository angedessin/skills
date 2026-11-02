---
type: llm
---

Judge the final response, which is a code review of an uncommitted change. PASS if it points out that the highlight builds HTML from the user's keyword (and product names) without escaping and renders it with dangerouslySetInnerHTML, which allows HTML/script injection (XSS); suggesting rendering <mark> as React elements or escaping is fine. FAIL if this problem is not mentioned.
