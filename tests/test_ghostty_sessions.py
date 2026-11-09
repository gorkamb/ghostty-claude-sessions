"""Tests that need neither Ghostty nor a running session. Run: python3 -m unittest -v"""
import importlib.machinery, json, os, re, subprocess, sys, tempfile, types, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "..", "ghostty-sessions")

loader = importlib.machinery.SourceFileLoader("ghostty_sessions", SCRIPT)
s = types.ModuleType("ghostty_sessions")
s.__file__ = SCRIPT
loader.exec_module(s)
RUN, SIDEBAR_RUNNING = s.run, s.sidebar_running

plain = lambda t: re.sub(r"\x1b\[[0-9;?]*[a-zA-Z]", "", t)
use = lambda name, inp: json.dumps({"message": {"content": [{"type": "tool_use", "name": name, "input": inp}]}})


def config(tmp, plans=None, **extra):
    path = os.path.join(tmp, "config.json")
    with open(path, "w") as fh:
        json.dump({"claude_dirs": [tmp], "plans": plans or [], **extra}, fh)
    return s.load_config(path)


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = os.path.realpath(tempfile.mkdtemp())
        self.plans = os.path.join(self.tmp, "plans")
        os.makedirs(self.plans)
        for p in ("PLAN_A.md", "PLAN_B.md", "PLAN_Tables_Command_Post.md", "PLAN_Tables_Other.md"):
            open(os.path.join(self.plans, p), "w").close()
        s.CFG = config(self.tmp, [{"dir": self.plans, "pattern": "PLAN_*.md"}])
        s._worktree.clear()
        s._repo.clear()
        self.A = os.path.join(self.plans, "PLAN_A.md")
        self.B = os.path.join(self.plans, "PLAN_B.md")


class Config(Base):
    def test_defaults_without_a_file(self):
        cfg = s.load_config(os.path.join(self.tmp, "missing.json"))
        self.assertEqual(cfg["plans"], [])
        self.assertEqual(cfg["edit_weight"], 10)
        self.assertEqual(cfg["sidebar"]["width"], 44)

    def test_sidebar_is_merged_not_replaced(self):
        cfg = config(self.tmp, sidebar={"width": 50})
        self.assertEqual(cfg["sidebar"], {"width": 50, "font_size": 11})

    def test_pattern_needs_one_star(self):
        with self.assertRaises(SystemExit):
            config(self.tmp, [{"dir": self.plans, "pattern": "PLAN.md"}])

    def test_invalid_json_says_where(self):
        bad = os.path.join(self.tmp, "bad.json")
        open(bad, "w").write("{")
        with self.assertRaises(SystemExit) as e:
            s.load_config(bad)
        self.assertIn(bad, str(e.exception))


class Short(Base):
    def test_strip_prefixes(self):
        s.CFG = config(self.tmp, strip_prefixes=["acme-"])
        self.assertEqual(s.short("acme-api-feature"), "api-feature")
        self.assertEqual(s.short("acme-api#12"), "api#12")
        self.assertEqual(s.short("acme-"), "acme-", "never down to nothing")
        self.assertEqual(s.short("other"), "other")
        self.assertIsNone(s.short(None))


class Wrap(unittest.TestCase):
    def test_keeps_every_word(self):
        text = "Improvements to admin/organizations and admin/events"
        self.assertEqual(" ".join(s.wrap(text, 30, 36)), text)

    def test_widths(self):
        w = s.wrap("Improvements to admin/organizations and admin/events", 30, 36)
        self.assertLessEqual(len(w[0]), 30)
        self.assertTrue(all(len(x) <= 36 for x in w[1:]))

    def test_cuts_a_word_longer_than_the_line(self):
        self.assertTrue(all(len(x) <= 10 for x in s.wrap("x" * 25, 10, 10)))


class PickPlan(Base):
    def test_rules(self):
        E, R = s.CFG["edit_weight"], 1
        self.assertIsNone(s.pick_plan([]))
        self.assertEqual(s.pick_plan([("A", E), ("B", R), ("B", R), ("B", R)]), "A", "editing beats reading more often")
        self.assertEqual(s.pick_plan([("A", R), ("A", R), ("B", R)]), "A", "the total wins, not the last")
        self.assertEqual(s.pick_plan([("A", R), ("B", R)]), "B", "on a tie, the most recent")
        self.assertEqual(s.pick_plan([("A", E)] * 3 + [("B", R)] * s.CFG["window"]), "B",
                         "what falls out of the window does not count")


class ToolUses(Base):
    def read(self, *lines):
        st = {"events": [], "wt": None, "pr": None}
        for ln in lines:
            s.read_tool_uses(ln, st)
        return st

    def test_weights(self):
        E = s.CFG["edit_weight"]
        st = self.read(
            use("Edit", {"file_path": self.A, "new_string": "see PLAN_B.md"}),
            use("Read", {"file_path": self.B}),
            use("Write", {"file_path": self.tmp + "/test.sh", "content": "PLAN_B.md"}),
            use("Read", {"file_path": self.plans + "/PLAN_Missing.md"}),
        )
        self.assertEqual(st["events"], [(self.A, E), (self.B, 1), (self.B, 1), (self.B, 1)])

    def test_pinning_is_not_a_mention(self):
        st = self.read(use("Bash", {"command": "ghostty-sessions --plan PLAN_A.md"}))
        self.assertEqual(st["events"], [])

    def test_same_name_in_another_folder_is_not_the_plan(self):
        other = os.path.join(self.tmp, "elsewhere")
        os.makedirs(other)
        open(os.path.join(other, "PLAN_A.md"), "w").close()
        st = self.read(use("Edit", {"file_path": os.path.join(other, "PLAN_A.md")}))
        self.assertEqual(st["events"], [(self.A, 1)], "named, so it counts 1; edited elsewhere, so not 10")

    def test_pr(self):
        st = self.read(use("Bash", {"command": "gh pr view https://github.com/o/my-repo/pull/553"}))
        self.assertEqual(st["pr"], "my-repo#553")

    def test_pr_link_inside_a_written_file_is_not_the_sessions(self):
        st = self.read(use("Write", {"file_path": self.tmp + "/t.py", "content": "github.com/o/r/pull/9"}))
        self.assertIsNone(st["pr"])

    def test_non_tool_use_content_is_ignored(self):
        st = self.read(json.dumps({"message": {"content": "PLAN_A.md"}}), "not json")
        self.assertEqual(st["events"], [])


class Git(Base):
    def git(self, *args):
        subprocess.run(["git", *args], check=True, capture_output=True)

    def setUp(self):
        super().setUp()
        self.repo = os.path.join(self.tmp, "my-repo")
        self.wt = os.path.join(self.tmp, "my-repo-feature")
        self.git("init", "-q", "-b", "main", self.repo)
        self.git("-C", self.repo, "-c", "user.email=t@t", "-c", "user.name=t",
                 "commit", "-q", "--allow-empty", "-m", "init")
        self.git("-C", self.repo, "worktree", "add", "-q", self.wt, "-b", "feature")
        os.makedirs(os.path.join(self.wt, "src"))

    def test_worktree_from_a_path_the_session_touched(self):
        st = {"events": [], "wt": None, "pr": None}
        s.read_tool_uses(use("Edit", {"file_path": self.wt + "/src/x.py"}), st)
        self.assertEqual(st["wt"], "my-repo-feature")

    def test_main_checkout_is_not_a_worktree(self):
        self.assertIsNone(s.linked_worktree(self.repo))
        self.assertEqual(s.linked_worktree(self.wt + "/src/missing.py"), self.wt)

    def test_a_worktree_groups_with_its_repository(self):
        self.assertEqual(s.repo_name(self.repo), "my-repo")
        self.assertEqual(s.repo_name(self.wt + "/src"), "my-repo")
        self.assertIsNone(s.repo_name(self.plans))


class ResolvePlan(Base):
    def test_exact_and_partial(self):
        self.assertEqual(s.resolve_plan("PLAN_A.md"), self.A)
        self.assertEqual(s.resolve_plan("command post"), os.path.join(self.plans, "PLAN_Tables_Command_Post.md"))

    def refusal(self, text):
        with self.assertRaises(SystemExit) as e:
            s.resolve_plan(text)
        return str(e.exception)

    def test_refusals(self):
        self.assertIn("2 plans", self.refusal("tables"))
        self.assertIn("no plan matches", self.refusal("zzz"))

    def test_without_plans(self):
        s.CFG = config(self.tmp)
        self.assertIn("no plans configured", self.refusal("x"))

    def test_label(self):
        self.assertEqual(s.plan_label(os.path.join(self.plans, "PLAN_Tables_Command_Post.md")), "Tables Command Post")


class Session(Base):
    def test_meta_needs_a_session_id(self):
        os.makedirs(os.path.join(self.tmp, "sessions"))
        with open(os.path.join(self.tmp, "sessions", "1.json"), "w") as fh:
            json.dump({"peerToken": "x"}, fh)
        with open(os.path.join(self.tmp, "sessions", "2.json"), "w") as fh:
            json.dump({"sessionId": "abc", "cwd": "/"}, fh)
        self.assertIsNone(s.session_meta(1))
        self.assertEqual(s.session_meta(2)["sessionId"], "abc")

    def test_transcript_is_read_incrementally(self):
        proj = os.path.join(self.tmp, "projects", "p")
        os.makedirs(proj)
        path = os.path.join(proj, "abc.jsonl")
        meta = {"_config": self.tmp, "sessionId": "abc"}
        with open(path, "w") as fh:
            fh.write(use("Read", {"file_path": self.A}) + "\n" + use("Edit", {"file_path": self.B}))  # 2nd half-written
        self.assertEqual(s.transcript_facts(meta)["plan"], self.A)
        with open(path, "a") as fh:
            fh.write("\n")
        self.assertEqual(s.transcript_facts(meta)["plan"], self.B, "the completed line is read on the next pass")


def row(**k):
    base = {"win": "1", "idx": 1, "tty": "ttys001", "selected": False, "title": "",
            "group": None, "name": "Session", "is_claude": True, "wt": None, "pr": None,
            "status": "idle", "mins": 3}
    base.update(k)
    return base


class Render(Base):
    def setUp(self):
        super().setUp()
        rows = [row(idx=1, tty="ttys001", group="Event Comms", name="Sends in events",
                    wt="events-sends", pr="events#553"),
                row(idx=2, tty="ttys002", group="Event Comms", status="busy", name="Another"),
                row(idx=3, tty="ttys003", group=None, name="Loose", mins=20)]
        self.lines, self.hit = s.render(rows, 44)
        self.text = [plain(l) for l in self.lines]

    def test_header_counts(self):
        self.assertIn("3 · ● 1 working · ○ 2 waiting", self.text[1])

    def test_groups(self):
        heads = [t for t in self.text if t.startswith("▌")]
        self.assertTrue(heads[0].startswith("▌ Event Comms 2"))
        self.assertTrue(heads[-1].startswith("▌ other"), "ungrouped goes last")

    def test_details(self):
        self.assertTrue(any("events-sends · events#553" in t for t in self.text))
        self.assertTrue(any(t.strip() == "working" for t in self.text))

    def test_width(self):
        self.assertTrue(all(len(t) <= 44 for t in self.text))

    def test_whole_block_is_clickable(self):
        self.assertEqual(sorted(i for i, t in self.hit.items() if t == "ttys001"),
                         [i for i, t in enumerate(self.text) if "Sends in" in t or "events-sends" in t])
        self.assertTrue(all(self.text[i].strip() for i in self.hit), "blank lines are not")

    def test_long_wait_in_orange(self):
        self.assertTrue(any("\x1b[38;5;209m20m" in l for l in self.lines))


class Sidebar(Base):
    def test_command_quotes_paths_with_spaces(self):
        s.__file__ = "/Users/me/My Tools/ghostty-sessions"
        try:
            cmd = s.sidebar_command()
        finally:
            s.__file__ = SCRIPT
        self.assertEqual(cmd[:3], ["open", "-na", "/Applications/Ghostty.app"])
        last = cmd[-1]
        self.assertTrue(last.startswith("--command="))
        import shlex
        parts = shlex.split(last[len("--command="):])
        self.assertEqual(parts[1:], ["/Users/me/My Tools/ghostty-sessions", "--watch", "3"])


class SidebarRunning(Base):
    def ps(self, *lines):
        s.run = lambda cmd, timeout=10: "\n".join(lines)

    def tearDown(self):
        s.run = RUN

    def test_finds_a_running_sidebar(self):
        self.ps("  12 /usr/bin/python3 /opt/x/ghostty-sessions --watch 3")
        self.assertTrue(s.sidebar_running())
        self.ps("  12 /bin/sh -c '/usr/bin/python3' '/My Tools/ghostty-sessions' --watch 3")
        self.assertTrue(s.sidebar_running())

    def test_ignores_other_processes(self):
        self.ps("  12 /usr/bin/python3 /opt/x/ghostty-sessions --sidebar",
                "  13 /usr/bin/python3 /opt/x/old-ghostty-sessions --watch 3",
                f"  {os.getpid()} /usr/bin/python3 /opt/x/ghostty-sessions --watch 3",
                "")
        self.assertFalse(s.sidebar_running())


class AutoOpen(Base):
    def setUp(self):
        super().setUp()
        self.opened = []
        self.env = os.environ.get("TERM_PROGRAM")
        os.environ["TERM_PROGRAM"] = "ghostty"
        s.sidebar_running = lambda: False
        s.subprocess = types.SimpleNamespace(run=lambda cmd, **k: self.opened.append(cmd))
        s.CFG = config(self.tmp, auto_open=True, ghostty_app=self.tmp)

    def tearDown(self):
        s.sidebar_running = SIDEBAR_RUNNING
        s.subprocess = subprocess
        if self.env is None:
            os.environ.pop("TERM_PROGRAM", None)
        else:
            os.environ["TERM_PROGRAM"] = self.env

    def test_opens_when_everything_says_so(self):
        s.auto_open()
        self.assertEqual(len(self.opened), 1)

    def test_off_by_default(self):
        s.CFG = config(self.tmp, ghostty_app=self.tmp)
        s.auto_open()
        self.assertEqual(self.opened, [])

    def test_not_outside_ghostty(self):
        os.environ["TERM_PROGRAM"] = "iTerm.app"
        s.auto_open()
        self.assertEqual(self.opened, [])

    def test_not_twice(self):
        s.sidebar_running = lambda: True
        s.auto_open()
        self.assertEqual(self.opened, [])

    def test_never_raises(self):
        def boom():
            raise RuntimeError("ps died")
        s.sidebar_running = boom
        s.auto_open()

    def test_broken_config_is_silent(self):
        bad = os.path.join(self.tmp, "bad.json")
        open(bad, "w").write("{")
        env = dict(os.environ, GHOSTTY_SESSIONS_CONFIG=bad)
        out = subprocess.run([sys.executable, SCRIPT, "--auto-open"], capture_output=True, text=True, env=env)
        self.assertEqual((out.returncode, out.stdout, out.stderr), (0, "", ""))


class Check(Base):
    def run_check(self, **cfg):
        import contextlib, io, platform
        s.CFG = config(self.tmp, **cfg)
        s.sidebar_running = lambda: False
        env = os.environ.get("TERM_PROGRAM")
        os.environ["TERM_PROGRAM"] = "ghostty"
        out = io.StringIO()
        try:
            with contextlib.redirect_stdout(out):
                rc = s.check()
        finally:
            s.sidebar_running = SIDEBAR_RUNNING
            if env is None:
                os.environ.pop("TERM_PROGRAM", None)
            else:
                os.environ["TERM_PROGRAM"] = env
        return rc, out.getvalue(), platform.system() == "Darwin"

    def test_all_in_place(self):
        rc, out, mac = self.run_check(ghostty_app=self.tmp, plans=[{"dir": self.plans, "pattern": "PLAN_*.md"}])
        self.assertIn("plans: 4 files match", out)
        self.assertEqual(rc, 0 if mac else 1, out)

    def test_a_pattern_that_matches_nothing(self):
        rc, out, _ = self.run_check(ghostty_app=self.tmp, plans=[{"dir": self.plans, "pattern": "SPEC_*.md"}])
        self.assertIn("MISSING plans: 0 files match", out)
        self.assertEqual(rc, 1)

    def test_missing_ghostty(self):
        rc, out, _ = self.run_check(ghostty_app=self.tmp + "/nope.app")
        self.assertIn("MISSING Ghostty at", out)
        self.assertEqual(rc, 1)


class Cli(unittest.TestCase):
    def test_help_and_unknown_option(self):
        out = subprocess.run([sys.executable, SCRIPT, "--help"], capture_output=True, text=True)
        self.assertEqual(out.returncode, 0)
        self.assertIn("--sidebar", out.stdout)
        bad = subprocess.run([sys.executable, SCRIPT, "--nope"], capture_output=True, text=True)
        self.assertNotEqual(bad.returncode, 0)
        self.assertIn("unknown option", bad.stderr)


if __name__ == "__main__":
    unittest.main()
