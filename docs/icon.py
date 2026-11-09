"""Builds .claude-plugin/icon.png (1024 px): a terminal window with the sidebar on its left.

Needs Pillow (dev only), like docs/demo.py:
    /tmp/demo-env/bin/python docs/icon.py
"""
import os

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", ".claude-plugin", "icon.png")

S = 1024
K = 4  # drawn at 4x and scaled down, for smooth edges

ORANGE, GREEN, BLUE = (255, 135, 0), (135, 215, 135), (95, 175, 255)
YELLOW, SELECT = (255, 215, 0), (0, 95, 135)
LINE, FAINT = (226, 228, 233), (88, 92, 102)


def main():
    img = Image.new("RGBA", (S * K, S * K), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    k = lambda *v: [x * K for x in v]

    # the window
    d.rounded_rectangle(k(64, 64, 960, 960), radius=180 * K, fill=(30, 31, 36))
    # the sidebar, a shade lighter, clipped to the window's left side
    side = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ds = ImageDraw.Draw(side)
    ds.rounded_rectangle(k(64, 64, 960, 960), radius=180 * K, fill=(44, 46, 53))
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).rectangle(k(64, 64, 512, 960), fill=255)
    img.paste(side, (0, 0), mask)
    d.rectangle(k(508, 64, 516, 960), fill=(22, 23, 27))

    # three groups: a colour bar and one or two sessions each
    groups = [(ORANGE, [(YELLOW, True, False), (GREEN, False, True)]),
              (GREEN, [(YELLOW, True, False)]),
              (BLUE, [(GREEN, False, False)])]
    y = 200
    for colour, sessions in groups:
        d.rounded_rectangle(k(150, y, 166, y + 92 * len(sessions) - 26), radius=8 * K, fill=colour)
        for dot, filled, selected in sessions:
            if selected:
                d.rounded_rectangle(k(184, y - 18, 486, y + 50), radius=18 * K, fill=SELECT)
            cx, cy, r = 220, y + 16, 22
            if filled:
                d.ellipse(k(cx - r, cy - r, cx + r, cy + r), fill=dot)
            else:
                d.ellipse(k(cx - r, cy - r, cx + r, cy + r), outline=dot, width=9 * K)
            d.rounded_rectangle(k(262, y + 4, 452, y + 28), radius=12 * K, fill=LINE)
            y += 92
        y += 44

    # the terminal side: our own little ghost, a nod to Ghostty (not its logo)
    ghost = (238, 240, 245)
    gx, gy, gw, gh = 600, 250, 270, 330          # box of the body
    d.pieslice(k(gx, gy, gx + gw, gy + gw), 180, 360, fill=ghost)        # the dome
    d.rectangle(k(gx, gy + gw // 2 - 1, gx + gw, gy + gh), fill=ghost)  # the body
    n = 3                                         # scalloped hem: touching circles leave the notches
    sw = gw / n
    for i in range(n):
        x0 = gx + i * sw
        d.ellipse(k(x0, gy + gh - sw / 2, x0 + sw, gy + gh + sw / 2), fill=ghost)
    eye = (30, 31, 36)
    for ex in (gx + 78, gx + 162):
        d.ellipse(k(ex, gy + 112, ex + 34, gy + 166), fill=eye)
    # a line of output under it
    d.rounded_rectangle(k(600, 760, 840, 786), radius=13 * K, fill=FAINT)
    d.rectangle(k(860, 750, 888, 796), fill=BLUE)  # the cursor

    img.resize((S, S), Image.LANCZOS).save(OUT)
    print(OUT)


if __name__ == "__main__":
    main()
