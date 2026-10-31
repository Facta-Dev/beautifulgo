---
type: llm
focus: trace
weight: 1
---

The migration that owns the widget tables is updated in the same change — either the priority column is added to migrations/0001_init.sql's Up section and the Down section reverses exactly that (DOWN matches UP), or a new timestamped migration pair is added with both sections present and consistent; no migration ships with a missing or mismatched Down