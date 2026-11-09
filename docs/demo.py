"""Builds docs/demo.gif from the real render() and made-up sessions.

Needs Pillow (dev only, the tool itself does not):
    python3 -m venv /tmp/demo-env && /tmp/demo-env/bin/pip install pillow
    /tmp/demo-env/bin/python docs/demo.py
"""
import copy, importlib.machinery, os, re, sys, time, types

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "..", "claude-sessions")
m = types.ModuleType("claude_sessions")
m.__file__ = SCRIPT
importlib.machinery.SourceFileLoader("claude_sessions", SCRIPT).exec_module(m)
m.CFG = m.load_config("/nonexistent")

COLS, ROWS = 44, 25
SCALE = 2
FONT_PX = 13 * SCALE
FONT = "/System/Library/Fonts/Menlo.ttc"
REG = ImageFont.truetype(FONT, FONT_PX, index=0)
BOLD = ImageFont.truetype(FONT, FONT_PX, index=1)
CW = REG.getlength("M")
LH = int(FONT_PX * 1.3)
PAD = 14 * SCALE
BG = (30, 31, 34)
FG = (215, 218, 224)


def xterm(n):
    """xterm-256 colour number to RGB."""
    base = [(0, 0, 0), (205, 49, 49), (13, 188, 121), (229, 229, 16), (36, 114, 200), (188, 63, 188),
            (17, 168, 205), (229, 229, 229), (102, 102, 102), (241, 76, 76), (35, 209, 139), (245, 245, 67),
            (59, 142, 234), (214, 112, 214), (41, 184, 219), (255, 255, 255)]
    if n < 16:
        return base[n]
    if n < 232:
        n -= 16
        lv = [0, 95, 135, 175, 215, 255]
        return (lv[n // 36], lv[(n // 6) % 6], lv[n % 6])
    g = 8 + (n - 232) * 10
    return (g, g, g)


def cells(line):
    """ANSI line -> list of (char, fg, bg, bold, dim)."""
    out, fg, bg, bold, dim = [], None, None, False, False
    for tok in re.split(r"(\x1b\[[0-9;]*m)", line):
        if tok.startswith("\x1b["):
            codes = [int(c) for c in tok[2:-1].split(";") if c] or [0]
            i = 0
            while i < len(codes):
                c = codes[i]
                if c == 0:
                    fg, bg, bold, dim = None, None, False, False
                elif c == 1:
                    bold = True
                elif c == 2:
                    dim = True
                elif c in (38, 48) and i + 2 < len(codes) and codes[i + 1] == 5:
                    if c == 38:
                        fg = xterm(codes[i + 2])
                    else:
                        bg = xterm(codes[i + 2])
                    i += 2
                i += 1
        else:
            out.extend((ch, fg, bg, bold, dim) for ch in tok)
    return out


def blend(a, b, t):
    return tuple(int(x * (1 - t) + y * t) for x, y in zip(a, b))


def cursor(d, x, y):
    s = SCALE
    pts = [(0, 0), (0, 17), (4, 13), (7, 20), (10, 19), (7, 12), (12, 12)]
    d.polygon([(x + px * s, y + py * s) for px, py in pts], fill=(255, 255, 255), outline=(0, 0, 0))


def frame(rows, clock, hover=None, pointer=None):
    time.strftime = lambda f: clock
    lines, hit = m.render(rows, COLS, hover)
    w = int(PAD * 2 + CW * COLS)
    h = PAD * 2 + LH * ROWS
    img = Image.new("RGB", (w, h), BG)
    d = ImageDraw.Draw(img)
    for r, line in enumerate(lines[:ROWS]):
        y = PAD + r * LH
        for c, (ch, fg, bg, bold, dim) in enumerate(cells(line)):
            x = PAD + c * CW
            if bg:
                d.rectangle([x, y, x + CW + 1, y + LH], fill=bg)
            col = fg or FG
            if dim:
                col = blend(col, bg or BG, 0.45)
            if ch != " ":
                d.text((x, y + (LH - FONT_PX) // 2), ch, font=BOLD if bold else REG, fill=col)
    if pointer:
        row = [i for i, t in sorted(hit.items()) if t == pointer][0]
        cursor(d, PAD + CW * 30, PAD + row * LH + LH // 3)
    return img  # kept at 2x: crisp on retina, shown at half width in the README


def R(**k):
    base = {"win": "1", "selected": False, "title": "", "is_claude": True, "wt": None, "pr": None,
            "status": "idle", "mins": 2}
    base.update(k)
    return base


def main():
    rows = [
        R(idx=1, tty="t1", group="Checkout Redesign", name="Payment form validation",
          wt="shop-web-payment-form", status="busy", mins=4),
        R(idx=4, tty="t4", group="Checkout Redesign", name="Order summary API",
          wt="api-order-summary", pr="shop-api#212", mins=18),
        R(idx=2, tty="t2", group="Search Speed", name="Profile slow queries", status="shell", mins=1,
          selected=True),
        R(idx=3, tty="t3", group="Search Speed", name="Add the trigram index", wt="shop-api-trigram",
          status="busy", mins=7),
        R(idx=5, tty="t5", group=None, name="Release notes", mins=45),
    ]
    by = lambda rs, t: next(r for r in rs if r["tty"] == t)
    frames = []

    def shot(rs, clock, ms, **k):
        frames.append((frame(rs, clock, **k), ms))

    shot(rows, "10:42", 2200)                                    # the list as it is
    shot(rows, "10:42", 900, hover="t4", pointer="t4")           # the one waiting 18 min
    rows = copy.deepcopy(rows)
    for r in rows:
        r["selected"] = r["tty"] == "t4"                         # click: its tab gets focus
    shot(rows, "10:42", 1600, pointer="t4")
    rows = copy.deepcopy(rows)
    by(rows, "t4").update(status="busy", mins=0)                 # answered: it works again
    shot(rows, "10:43", 1800)
    rows = copy.deepcopy(rows)
    by(rows, "t1").update(status="idle", mins=0)                 # another one finishes and waits
    shot(rows, "10:43", 1800)
    rows = copy.deepcopy(rows)
    by(rows, "t5").update(group="Checkout Redesign", status="busy", mins=0,
                          name="Release notes for checkout")     # starts editing the plan: moves group
    shot(rows, "10:44", 3000)

    out = os.path.join(HERE, "demo.gif")
    imgs = [f.convert("P", palette=Image.ADAPTIVE, colors=128) for f, _ in frames]
    imgs[0].save(out, save_all=True, append_images=imgs[1:], duration=[ms for _, ms in frames],
                 loop=0, optimize=True, disposal=1)
    for i, (f, _) in enumerate(frames):
        f.save(os.path.join(os.environ.get("DEMO_FRAMES", "/tmp"), f"demo-{i}.png"))
    print(out, os.path.getsize(out), "bytes")


if __name__ == "__main__":
    sys.exit(main())
