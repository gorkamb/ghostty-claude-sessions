"""Builds docs/demo-window.gif: the sidebar next to a Ghostty window with five tabs.

Clicking a session in the sidebar brings its tab to the front. The sidebar is drawn
by the real render(), through docs/demo.py; the window and its conversations are
made up. Needs Pillow, like docs/demo.py:
    /tmp/demo-env/bin/python docs/demo_window.py
"""
import copy, os, sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import demo as D  # noqa: E402

S = D.SCALE
TCOLS = 58                                  # the terminal's width, in columns
SMALL = ImageFont.truetype(D.FONT, 11 * S, index=0)
TITLE_H, TAB_H = 28 * S, 26 * S             # window title bar, tab bar
M, GAP = 18 * S, 12 * S                     # desktop margin, gap between windows
DESK = (54, 58, 70)
CHROME, TAB_OFF, EDGE = (44, 45, 50), (36, 37, 41), (24, 25, 28)

O, G, W, DIM, Y = "\x1b[38;5;208m", "\x1b[38;5;114m", "\x1b[38;5;255m", "\x1b[38;5;245m", "\x1b[38;5;220m"
R = "\x1b[0m"
CURSOR = "\x1b[48;5;250m \x1b[0m"


def you(text):
    return [f"{DIM}>{R} {W}{text}{R}", ""]


def tool(call, result=None):
    out = [f"{G}●{R} {W}{call}{R}"]
    if result:
        out.append(f"  {DIM}└ {result}{R}")
    return out


def spin(text):
    return ["", f"{O}●{R} {O}{text}{R}"]


def says(*lines):
    return [""] + [f"{W}{'●' if i == 0 else ' '} {t}{R}" for i, t in enumerate(lines)]


def conversation(tty, phase):
    if tty == "t1":
        return ([f"{DIM}>{R} {W}Validate the card fields before submit, and show{R}",
                 f"  {W}the error under each field.{R}", ""] + tool("Read(src/checkout/PaymentForm.vue)")
                + tool("Edit(src/checkout/PaymentForm.vue)", "Added 24 lines, removed 3 lines")
                + tool("Bash(npm test -- payment-form)", "Running…") + spin("Testing… (2m 10s)"))
    if tty == "t2":
        return (you("Which search queries got slow this week?")
                + says("I'll profile the twenty slowest ones in the log.") + [""]
                + tool("Bash(./scripts/slow-queries --since 7d --top 20)", f"{Y}Running… (1m 02s){R}"))
    if tty == "t3":
        return (you("Add a trigram index for product names.")
                + tool("Write(migrations/0142_trigram_index.sql)", "Wrote 9 lines")
                + tool("Bash(make migrate && make bench-search)", "search p95: 840 ms → 95 ms")
                + tool("Edit(notes/PLAN_search_speed.md)", "Ticked step 3 of 5")
                + spin("Measuring the other queries… (48s)"))
    if tty == "t4":
        head = (you("Add an order summary endpoint: items, taxes, shipping.")
                + tool("Write(api/orders/summary.py)", "Wrote 58 lines")
                + tool("Bash(pytest tests/orders)", "14 passed")
                + says("Done: GET /orders/{id}/summary returns items, taxes",
                       "and shipping. Should it also return the discount",
                       "breakdown, or leave that for the next PR?") + [""])
        answer = "Leave it for the next PR."
        if phase == "ask":
            return head + [f"{DIM}>{R} {CURSOR}"]
        if phase == "typed":
            return head + [f"{DIM}>{R} {W}{answer}{R}{CURSOR}"]
        return (head + you(answer) + tool("Bash(git push)", "Running…") + spin("Updating the pull request… (3s)"))
    return you("Write the release notes for 4.2.") + says("Here is a first draft:") + [
        "", f"  {W}## 4.2{R}", f"  {W}- Faster search{R}", f"  {W}- A clearer checkout{R}"]


ROWS = [
    D.R(idx=1, tty="t1", group="Checkout Redesign", name="Payment form validation",
        wt="shop-web-payment-form", status="busy", mins=4),
    D.R(idx=4, tty="t4", group="Checkout Redesign", name="Order summary API",
        wt="api-order-summary", pr="shop-api#212", mins=18),
    D.R(idx=2, tty="t2", group="Search Speed", name="Profile slow queries", status="shell", mins=1,
        selected=True),
    D.R(idx=3, tty="t3", group="Search Speed", name="Add the trigram index", wt="shop-api-trigram",
        status="busy", mins=7),
    D.R(idx=5, tty="t5", group=None, name="Release notes", mins=45),
]


def chrome(d, box, title):
    """A window: rounded frame, title bar with the three buttons and a centred title."""
    x0, y0, x1, y1 = box
    d.rounded_rectangle(box, radius=10 * S, fill=D.BG, outline=EDGE, width=S)
    d.rounded_rectangle((x0, y0, x1, y0 + TITLE_H + 10 * S), radius=10 * S, fill=CHROME)
    d.rectangle((x0, y0 + TITLE_H, x1, y0 + TITLE_H + 10 * S), fill=D.BG)
    for i, c in enumerate([(255, 95, 87), (254, 188, 46), (40, 200, 64)]):
        cx, cy, r = x0 + (16 + 20 * i) * S, y0 + TITLE_H // 2, 6 * S
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=c)
    tw = d.textlength(title, font=SMALL)
    d.text(((x0 + x1 - tw) / 2, y0 + (TITLE_H - 11 * S) / 2 - S), title, font=SMALL, fill=(170, 173, 180))


def fit(d, text, width):
    if d.textlength(text, font=SMALL) <= width:
        return text
    while text and d.textlength(text + "…", font=SMALL) > width:
        text = text[:-1]
    return text.rstrip() + "…"


def shot(rows, clock, active, phase="", hover=None, pointer=None):
    side = D.frame(rows, clock, hover=hover, pointer=pointer)
    sw, sh = side.size
    tw = int(2 * D.PAD + D.CW * TCOLS)
    W_, H_ = M + sw + GAP + tw + M, M + TITLE_H + sh + M
    img = Image.new("RGB", (W_, H_), DESK)
    d = ImageDraw.Draw(img)

    # the sidebar's own window
    chrome(d, (M, M, M + sw, M + TITLE_H + sh), "ghostty-sessions")
    mask = Image.new("L", side.size, 0)                 # keep the window's rounded bottom corners
    md = ImageDraw.Draw(mask)
    md.rounded_rectangle((S, -20 * S, sw - 1 - S, sh - 1 - S), radius=10 * S, fill=255)
    img.paste(side, (M, M + TITLE_H), mask)

    # the Ghostty window, its tabs in window order
    tabs = sorted(rows, key=lambda r: r["idx"])
    name = {r["tty"]: r["name"] for r in rows}
    x0 = M + sw + GAP
    chrome(d, (x0, M, x0 + tw, M + TITLE_H + sh), name[active])
    ty = M + TITLE_H
    d.rectangle((x0 + S, ty, x0 + tw - S, ty + TAB_H), fill=TAB_OFF)
    each = (tw - 2 * S) / len(tabs)
    for i, r in enumerate(tabs):
        a, b = x0 + S + i * each, x0 + S + (i + 1) * each
        on = r["tty"] == active
        if on:
            d.rectangle((a, ty, b, ty + TAB_H), fill=D.BG)
        elif i:
            d.line((a, ty + 6 * S, a, ty + TAB_H - 6 * S), fill=EDGE, width=S)
        label = fit(d, r["name"], each - 16 * S)
        lw = d.textlength(label, font=SMALL)
        d.text(((a + b - lw) / 2, ty + (TAB_H - 11 * S) / 2 - S), label, font=SMALL,
               fill=(225, 228, 234) if on else (130, 134, 142))

    # the active tab's conversation
    top = ty + TAB_H + D.PAD // 2
    for n, line in enumerate(conversation(active, phase)):
        y = top + n * D.LH
        if y + D.LH > M + TITLE_H + sh - D.PAD // 2:
            break
        for c, (ch, fg, bg, bold, dim) in enumerate(D.cells(line)):
            x = x0 + D.PAD + c * D.CW
            if bg:
                d.rectangle([x, y, x + D.CW, y + D.LH], fill=bg)
            if ch != " ":
                d.text((x, y + (D.LH - D.FONT_PX) // 2), ch, font=D.BOLD if bold else D.REG, fill=fg or D.FG)
    return img


def main():
    by = lambda rs, t: next(r for r in rs if r["tty"] == t)

    def select(rs, t):
        rs = copy.deepcopy(rs)
        for r in rs:
            r["selected"] = r["tty"] == t
        return rs

    rows = ROWS
    frames = [
        (shot(rows, "10:42", "t2"), 2200),                                  # the window shows tab 2
        (shot(rows, "10:42", "t2", hover="t4", pointer="t4"), 1000),       # 18 min waiting: that one
    ]
    rows = select(rows, "t4")
    frames.append((shot(rows, "10:42", "t4", "ask", pointer="t4"), 2200))  # click: its tab comes forward
    frames.append((shot(rows, "10:42", "t4", "typed", pointer="t4"), 1400))
    rows = copy.deepcopy(rows)
    by(rows, "t4").update(status="busy", mins=0)
    frames.append((shot(rows, "10:43", "t4", "busy"), 2000))               # answered: it works again
    frames.append((shot(rows, "10:43", "t4", "busy", hover="t3", pointer="t3"), 1000))
    rows = select(rows, "t3")
    frames.append((shot(rows, "10:43", "t3", pointer="t3"), 3000))         # and on to another one

    out = os.path.join(D.HERE, "demo-window.gif")
    imgs = [f.convert("P", palette=Image.ADAPTIVE, colors=128) for f, _ in frames]
    imgs[0].save(out, save_all=True, append_images=imgs[1:], duration=[ms for _, ms in frames],
                 loop=0, optimize=True, disposal=1)
    for i, (f, _) in enumerate(frames):
        f.save(os.path.join(os.environ.get("DEMO_FRAMES", "/tmp"), f"window-{i}.png"))
    print(out, os.path.getsize(out), "bytes", frames[0][0].size)


if __name__ == "__main__":
    sys.exit(main())
