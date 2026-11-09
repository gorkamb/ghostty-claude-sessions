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

    # the terminal side: a prompt and a few lines of output
    d.polygon(k(600, 230, 650, 262, 600, 294), fill=BLUE)
    for i, w in enumerate((250, 190, 270, 140)):
        yy = 360 + i * 80
        d.rounded_rectangle(k(600, yy, 600 + w, yy + 26), radius=13 * K, fill=FAINT)
    d.rectangle(k(600, 700, 630, 750), fill=LINE)  # the cursor

    img.resize((S, S), Image.LANCZOS).save(OUT)
    print(OUT)


if __name__ == "__main__":
    main()
