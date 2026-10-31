---
type: llm
focus: trace
weight: 1
---

The test file is table-driven with named struct fields (name plus inputs and want fields), t.Run subtests, and covers boundary cases (burst exhausted, context canceled mid-wait, zero/negative rate input)