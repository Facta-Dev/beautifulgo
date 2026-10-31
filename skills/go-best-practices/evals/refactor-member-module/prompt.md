---
tags: [go-best-practices]
max_turns: 30
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

Here is a module from our members service that a contractor wrote. It works
but review comments keep piling up. Refactor it to be idiomatic Go and give
me a short list of what you changed and why. Keep the observable behavior the
same — including the odd-but-load-bearing bits, which you should flag rather
than fix. Write the refactored module as member.go, add a member_test.go with
table-driven tests, and put the change list in CHANGES.md in the current
directory.

Input files: member.go