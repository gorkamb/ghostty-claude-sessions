<div align="center">

<img src=".claude-plugin/icon.png" width="128" alt="">

# ghostty-sessions

**See which of your Claude Code sessions are working, and which are waiting for you.**

[![test](https://github.com/gorkamb/ghostty-claude-sessions/actions/workflows/test.yml/badge.svg)](https://github.com/gorkamb/ghostty-claude-sessions/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![macOS](https://img.shields.io/badge/macOS-Ghostty-555?logo=apple&logoColor=white)
![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-3776AB?logo=python&logoColor=white)
[![Claude Code plugin](https://img.shields.io/badge/Claude%20Code-plugin-D97757)](#get-started)

</div>

<img src="docs/demo-window.gif" width="100%" alt="The sidebar next to a Ghostty window with five tabs. Clicking the session that has waited 18 minutes brings its tab to the front, where Claude is asking a question; once answered it works again, and clicking another session switches to its tab.">

<sub>Made-up sessions. The sidebar is drawn by the real code: <code>docs/demo_window.py</code>.</sub>

With ten sessions in ten tabs, the tab bar tells you nothing. This sidebar lists them
all, grouped by what each one is working on, with how long each has waited for you.
Click one to jump to its tab.

**You need** macOS, [Ghostty](https://ghostty.org) and
[Claude Code](https://claude.com/claude-code). It is one Python file with no
dependencies; it uses the Python 3 that comes with Apple's Command Line Tools.

## Get started

**1. Install.** In Claude Code, run:

```
/plugin install ghostty-sessions --marketplace gorkamb/ghostty-claude-sessions
```

Answer `y` to add the marketplace, and pick "user" to have it in every project.
Then `/reload-plugins`.

**2. Set it up.** Run:

```
/ghostty-sessions:setup
```

Claude checks that everything is in place, looks for where you keep plan files,
writes the config and opens the sidebar. From then on the sidebar opens by itself
when a session starts in Ghostty.

The first time, macOS asks whether your terminal may control Ghostty. Say yes:
that is how it reads the tabs and switches between them.

| Command | What it does |
| --- | --- |
| `/ghostty-sessions:setup` | checks, finds your plans, writes the config, opens the sidebar |
| `/ghostty-sessions:open` | opens the sidebar, if it is not open |
| `/ghostty-sessions:plan NAME` | puts this session under a plan (see Grouping); `-` undoes it |

**To remove it:** `/plugin uninstall ghostty-sessions`, and delete
`~/.config/ghostty-sessions/` if you want the config gone too.

<details>
<summary>Without the plugin</summary>

```sh
git clone https://github.com/gorkamb/ghostty-claude-sessions.git
ln -s "$PWD/ghostty-claude-sessions/ghostty-sessions" /usr/local/bin/ghostty-sessions
ghostty-sessions --check      # what is missing, if anything
ghostty-sessions --sidebar
```

Any folder on your `PATH` works instead of `/usr/local/bin`. Write the config by
hand (see Configuration). The other commands:

| Command | What it does |
| --- | --- |
| `ghostty-sessions` | prints the list once |
| `ghostty-sessions --watch 3` | the list in the current terminal, refreshed every 3 s |
| `ghostty-sessions --plan NAME` | from inside a session: puts it under a plan; `-` undoes it |

</details>

## Reading the list

| Mark | Meaning |
| --- | --- |
| `●` | working |
| `◆` | running a shell command |
| `○` | waiting for you; the time turns orange after 15 minutes |
| `·` | a tab with no Claude Code session |

Under each session: its worktree and pull request, if it has them. Click a session
to go to its tab, `q` to quit.

## Grouping

**By repository**, out of the box.

**By plan**, if you keep plans or specs as files: the setup finds them.
Each session then goes under the plan it is editing, and moves when it moves on to
another one.

<img src="docs/demo.gif" width="380" alt="The sidebar alone: a session that starts editing a plan moves into that plan's group.">

If it gets one wrong, for example a session that edited someone else's plan in
passing, tell the session: `/ghostty-sessions:plan checkout` (any part of the file
name that matches only one plan works).

## Configuration

All optional, in `~/.config/ghostty-sessions/config.json` (or the file named by
`GHOSTTY_SESSIONS_CONFIG`). The setup writes it for you.

| Key | Default | |
| --- | --- | --- |
| `plans` | `[]` | where plan files live, e.g. `[{"dir": "~/work/notes", "pattern": "PLAN_*.md"}]` (one `*`) |
| `edit_weight` | `10` | editing a plan counts this many times more than reading it |
| `window` | `60` | how many recent plan mentions count |
| `strip_prefixes` | `[]` | prefixes removed from worktree and repository names, e.g. `["acme-"]` |
| `claude_dirs` | every `~/.claude*` with sessions | Claude Code config folders to read |
| `auto_open` | `false` | open the sidebar when a session starts in Ghostty (the setup turns it on) |
| `ghostty_app` | `/Applications/Ghostty.app` | |
| `sidebar` | `{"width": 44, "font_size": 11}` | width in columns |

## What it reads

Everything stays on your machine. It sends nothing anywhere.

- Ghostty's windows and tabs, through Ghostty's AppleScript support.
- `~/.claude/sessions/<pid>.json`, where Claude Code keeps each running session's
  status.
- The saved conversations in `~/.claude/projects/`, and only the tool calls in
  them (which files a session read or edited, which commands it ran), to find
  its plan, worktree and pull request. It never shows their content.

The only thing it changes is which tab has focus, when you click. The plugin's
start-up hook only opens the sidebar, and never blocks or fails the session.

## Limits

- `sessions/<pid>.json` is an internal Claude Code file, not a documented API. A
  Claude Code update can break the status column. Tested with Ghostty 1.4.0 and
  Claude Code 2.1.319.
- The sidebar always opens at the left edge of the main display.
- After using another window, the first click on the sidebar only brings it to the
  front, unless the pointer moved over it first.
- The worktree and pull request shown are the last ones the session touched, which
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
