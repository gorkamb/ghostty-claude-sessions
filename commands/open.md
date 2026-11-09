---
description: Open the ghostty-sessions sidebar in Ghostty
allowed-tools: Bash(python3:*)
---

Run this and tell me in one line what it printed, or that the sidebar is open:

```
python3 "${CLAUDE_PLUGIN_ROOT}/ghostty-sessions" --sidebar
```

If it fails because Ghostty is not at /Applications/Ghostty.app, or macOS denied the
terminal permission to control Ghostty, say so and point to `/ghostty-sessions:setup`.
