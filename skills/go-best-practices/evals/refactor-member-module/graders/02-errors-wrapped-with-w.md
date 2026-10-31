---
type: llm
focus: trace
weight: 1
---

Errors are wrapped with %w and matched with errors.Is: Enroll's fmt.Errorf uses %w (or the discarded Save error is returned properly), Lookup no longer swallows ErrNotFound into a zero member, and no %s/%v wrap of an error remains