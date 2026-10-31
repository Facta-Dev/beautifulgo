---
type: llm
focus: trace
weight: 1
---

Wait returns a wrapped error on context cancellation (fmt.Errorf with %w or errors.Is against context.Canceled/ErrLimiterStopping) rather than a plain string-created error, and the limiter declares at least one sentinel error with errors.New
---