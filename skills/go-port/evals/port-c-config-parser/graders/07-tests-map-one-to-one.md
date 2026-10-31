---
type: llm
focus: trace
weight: 1
---

Every test function in test_config.c has a corresponding Go test covering the same
assertions, with a name that maps back to it (test_basic, test_untrimmed_values_keep_whitespace,
test_get_int_errors, test_duplicates, test_case_insensitive, test_syntax_errors,
test_empty_input)
