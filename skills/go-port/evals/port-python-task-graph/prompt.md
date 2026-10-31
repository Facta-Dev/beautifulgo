---
tags: [go-port]
max_turns: 40
timeout_seconds: 1200
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

Can you port scheduler.py to Go? I want an idiomatic Go package with the same behavior,
and port test_scheduler.py too so we know it matches. Put the package in the current
directory (go.mod, scheduler.go, scheduler_test.go) and add a PORTING.md with notes for
the reviewer.

Input files: scheduler.py, test_scheduler.py
