---
type: llm
focus: trace
weight: 1
---

The new query (ListWidgetsBySize or equivalent) is written as a named sqlc query in internal/features/widgets/queries.sql, not as SQL pasted into postgres.go or usecase.go