---
tags: [go-best-practices, stack]
max_turns: 40
timeout_seconds: 1200
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

Our backend module has a widgets slice under internal/features/widgets. Widgets
need a Priority: every widget carries a priority from 1 to 5 (1 is highest),
every widget must have one, and admins list widgets filtered by size. Add
priority end to end — domain, queries, migration — and persist it. The
existing tests and the existing slice shape need to go on working unchanged.
Note anything you deliberately did not change.

Input files: internal/features/widgets/domain.go, ports.go, usecase.go,
http.go, postgres.go, module.go, queries.sql, migrations/0001_init.sql