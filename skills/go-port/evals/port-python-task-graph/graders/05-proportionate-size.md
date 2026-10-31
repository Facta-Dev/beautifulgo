---
type: llm
focus: trace
weight: 1
---

The port is proportionate: it does not reimplement Python string or number semantics by
hand, it adds no public API beyond the original's operations plus the accessors Go
callers expect, and its code lines (excluding tests, comments, and doc comments) are
under three and a half times the code lines of scheduler.py
