---
type: llm
---

Judge the final response, which is a code review of an uncommitted change. PASS if it points out that the new test mocks the app's own API module with vi.mock instead of mocking at the HTTP boundary (MSW, which the project already uses), and only asserts on the call arguments rather than on what the user sees, so it would keep passing if the results were not rendered. FAIL if this problem is not mentioned.
