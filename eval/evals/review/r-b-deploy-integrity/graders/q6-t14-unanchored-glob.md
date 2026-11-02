---
type: llm
---

Judge the final response, which is a code review of an uncommitted change. PASS if it points out that the hook's path glob is not anchored, so edits in another worktree (or another path containing the same segment) also trigger it. FAIL otherwise.
