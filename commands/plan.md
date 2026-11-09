---
description: Pin this session to a plan in the ghostty-sessions sidebar (`-` unpins)
argument-hint: <part of the plan's file name, or ->
allowed-tools: Bash(python3:*)
---

Run this and show me its one line of output:

```
python3 "${CLAUDE_PLUGIN_ROOT}/ghostty-sessions" --plan "$ARGUMENTS"
```

If it says the name matches several plans, show me the list and ask which one. If it
says no plans are configured, point to `/ghostty-sessions:setup`.
