---
tags: [go-review, stack]
max_turns: 40
timeout_seconds: 1200
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

Can you review the store slice our contractor wrote? It's a new module
(github.com/acme/store-manager) and we're following our standard
hexagonal/vertical-slice layout with internal/features. Tell me what to fix
first before we wire it into our API. Write the review to REVIEW.md. Don't
change the code.

Input files: go.mod, internal/features/store/domain.go,
internal/features/store/ports.go, internal/features/store/usecase.go,
internal/features/store/postgres.go
