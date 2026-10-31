---
type: llm
focus: trace
weight: 1
---

member_test.go exists and is table-driven: named struct fields (name, got/input, want), t.Run subtests, and it covers the '+'-truncation behavior and the empty-email error path