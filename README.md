# claude-sessions

A sidebar for [Ghostty](https://ghostty.org) that lists every
[Claude Code](https://claude.com/claude-code) session you have open, grouped by
what each one is working on. Click a session to jump to its tab.

<img src="docs/demo.gif" width="380" alt="The sidebar: sessions grouped under two plans. Clicking one that has waited 18 minutes focuses its tab; it starts working again, another finishes and waits, and a third moves into a plan's group when it starts editing that plan.">

<sub>Made-up sessions, drawn by the real code: <code>docs/demo.py</code>.</sub>

With ten sessions in ten tabs, the tab bar tells you nothing. This tells you which
sessions are working, which are waiting for you and for how long (orange after 15
minutes), which worktree and pull request each one is on, and which ones belong to
the same piece of work.

macOS and Ghostty only. One Python file, no dependencies.

## Install

```sh
git clone https://github.com/gorkamb/ghostty-claude-sessions.git
ln -s "$PWD/ghostty-claude-sessions/claude-sessions" /usr/local/bin/claude-sessions
```

Any folder on your `PATH` works instead of `/usr/local/bin`.

Then open the sidebar:

```sh
claude-sessions --sidebar
```

The first time, macOS asks whether your terminal may control Ghostty. Say yes:
that is how it reads the tabs and switches between them.

## Use

| Command | What it does |
| --- | --- |
| `claude-sessions --sidebar` | opens the list in a narrow Ghostty window on the left |
| `claude-sessions` | prints the list once |
| `claude-sessions --watch 3` | the interactive list in the current terminal, refreshed every 3 s |
| `claude-sessions --plan NAME` | from inside a session: pins it to a plan (see below); `-` unpins |

In the list: click a session to go to its tab, `q` to quit.

| Mark | Meaning |
| --- | --- |
| `●` | working |
| `◆` | running a shell command |
| `○` | waiting for you; the time turns orange after 15 minutes |
| `·` | a tab with no Claude Code session |

## Grouping

**By repository**, out of the box: each session goes under the git repository it
was started in, and a worktree goes with its repository.

**By plan**, if you keep plans or specs as files. Tell it where they are:

```json
{
  "plans": [{"dir": "~/work/notes", "pattern": "PLAN_*.md"}]
}
```

Each session then goes under the plan it is working on, judged from what it does
with its tools: among its last 60 mentions of a plan file, the one with the most
weight. Editing a plan weighs 10, reading or naming it weighs 1. A session that
moves on to another plan moves group.

When that guess is wrong, for example a session that edited someone else's plan in
passing, the session can say so itself: ask Claude to run
`claude-sessions --plan checkout` (any part of the file name that matches only one
plan works).

## Configuration

All optional, in `~/.config/claude-sessions/config.json` (or the file named by
`CLAUDE_SESSIONS_CONFIG`):

| Key | Default | |
| --- | --- | --- |
| `plans` | `[]` | folders of plan files and their pattern, with one `*` |
| `edit_weight` | `10` | how much editing a plan weighs against reading it |
| `window` | `60` | how many recent plan mentions count |
| `strip_prefixes` | `[]` | prefixes removed from worktree and repository names, e.g. `["acme-"]` |
| `claude_dirs` | every `~/.claude*` with sessions | Claude Code config folders to read |
| `ghostty_app` | `/Applications/Ghostty.app` | |
| `sidebar` | `{"width": 44, "font_size": 11}` | width in columns |

## What it reads

Everything stays on your machine. It sends nothing anywhere.

- Ghostty's windows and tabs, through Ghostty's AppleScript support (JXA).
- `~/.claude/sessions/<pid>.json`, where Claude Code keeps each running session's
  status.
- The saved conversations in `~/.claude/projects/`, and only the tool calls in
  them (which files a session read or edited, which commands it ran), to find
  its plan, worktree and pull request. It never shows their content.

The only thing it changes is which tab has focus, when you click.

## Limits

- Ghostty on macOS only: it needs Ghostty's AppleScript support. Tested with
  Ghostty 1.4.0 and Claude Code 2.1.319.
- `sessions/<pid>.json` is an internal Claude Code file, not a documented API. A
  Claude Code update can change it and break the status column.
- The sidebar opens on the main display, at the left edge. Ghostty does not take a
  negative position, and moving it afterwards would need the Accessibility
  permission, which this tool does not ask for.
- The first click on the sidebar after using another window only activates it,
  unless the pointer moved over it first.
- A worktree or pull request is the last one the session touched or opened, which
  is usually, but not always, the one it is working on.

## Development

```sh
python3 -m unittest discover -s tests -v
```

The tests need neither Ghostty nor a running session.

This is a personal tool shared as is. Issues and pull requests are welcome, but
there is no promise of support.

## License

[MIT](LICENSE)
