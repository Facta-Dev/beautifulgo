---
type: llm
focus: trace
weight: 1
---

The parallel run uses goroutines that have an owner and a shutdown path: results are
collected through a channel or WaitGroup, the deadline is enforced with
context.WithTimeout (or equivalent cancellation) rather than sleeps or polling, cancelled
tasks are reported as pending deterministically, and go test -race passes
