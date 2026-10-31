---
tags: [go-best-practices]
max_turns: 30
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

I need a small rate limiter package in Go for our tools — a token-bucket
limiter that several goroutines can share. Give me the full package as a
single `ratelimit.go` file: a `Limiter` type that is safe for concurrent use,
an `Allow` method that reports whether an event fits under the current rate,
and a `Wait(ctx context.Context) error` method that blocks until a token is
available or the context is done. Construct with `New(rate, burst)`; a zero
Limiter should be usable in some documented way rather than a trap. Include
table-driven unit tests in a `ratelimit_test.go`. Keep it dependency-free —
standard library only. Write both files to the current directory.