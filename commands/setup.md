---
description: Set up the ghostty-sessions sidebar (finds your plan files, writes the config, opens the sidebar)
allowed-tools: Read, Glob, Grep, Bash(uname:*), Bash(ls:*), Bash(echo:*), Bash(python3:*), Bash(mkdir -p:*), Write(~/.config/ghostty-sessions/config.json), Edit(~/.config/ghostty-sessions/config.json)
---

Set up the ghostty-sessions sidebar for me. Work through these steps without asking me
anything unless a step says to, then give me a short summary.

**1. Check it can run.** Run this; it prints one line per requirement:

```
python3 "${CLAUDE_PLUGIN_ROOT}/ghostty-sessions" --check
```

If macOS, Python or Ghostty is MISSING, stop and tell me how to fix it (if Ghostty
lives somewhere other than `/Applications/Ghostty.app`, find it and use that path as
`ghostty_app` in the config). If only "running inside Ghostty" is missing, go on, but
say the sidebar only lists sessions running in Ghostty.

**2. Find where I keep plans.** The sidebar groups sessions by the plan each one is
working on: a file that describes a piece of work (plan, spec, RFC, task brief). Look
in this project and in its sibling folders (the folder that contains this project,
one level down) for folders that hold several such Markdown files with a shared name
shape, for example `PLAN_*.md`, `*.plan.md`, `docs/plans/*.md`, `specs/*.md`,
`rfcs/*.md`, `.plans/*.md`. Read the CLAUDE.md or README of the project if it says
where plans live.

Each entry is a folder and a pattern with exactly one `*` and no `/` (files directly
inside the folder). Do not count READMEs, changelogs, ADRs or general docs as plans.
If you find none, leave `plans` empty: sessions will be grouped by repository, which
works well too. If you find candidates you are unsure about, list them and ask me.

**3. Shorten names, if it helps.** If most sibling repositories share a prefix (like
`acme-api`, `acme-web`), add it to `strip_prefixes`, so worktree and repository names
fit in the narrow sidebar.

**4. Write the config** to `~/.config/ghostty-sessions/config.json` (create the
folder if needed). If the file exists, keep every key it has and change only what
you found. Write `"auto_open": true`, so the sidebar opens by itself when a session
starts in Ghostty, unless the file already sets it to false. Paths may start with `~`.

The file looks like this (every key is optional):

```json
{
  "plans": [{"dir": "~/work/notes", "pattern": "PLAN_*.md"}],
  "strip_prefixes": ["acme-"],
  "auto_open": true
}
```

**5. Open the sidebar now**, after running `--check` again to confirm the plan
patterns match files:

```
python3 "${CLAUDE_PLUGIN_ROOT}/ghostty-sessions" --sidebar
```

The first time, macOS may ask whether the terminal can control Ghostty; tell me to
allow it, since that is how the sidebar reads tabs and switches between them.

**6. Summary.** Show me the config file, with one line per entry on why it is there,
and remind me that `/ghostty-sessions:plan <name>` pins a session to a plan when the
automatic guess is wrong.
