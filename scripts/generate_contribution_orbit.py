from __future__ import annotations

from datetime import date, timedelta
from html.parser import HTMLParser
from math import cos, pi, sin
from pathlib import Path
from urllib.request import Request, urlopen

USERNAME = "111984prasannagp"
OUTPUT = Path("dist/contribution-orbit.svg")


class ContributionParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.days: list[tuple[str, int]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "td":
            return
        data = dict(attrs)
        day = data.get("data-date")
        level = data.get("data-level")
        if day and level and level.isdigit():
            self.days.append((day, int(level)))


def fetch_days() -> list[tuple[str, int]]:
    url = f"https://github.com/users/{USERNAME}/contributions"
    request = Request(url, headers={"User-Agent": "ALAN-Contribution-Orbit/1.0"})
    with urlopen(request, timeout=30) as response:
        html = response.read().decode("utf-8", errors="replace")

    parser = ContributionParser()
    parser.feed(html)
    return parser.days


def main() -> None:
    days = fetch_days()
    if not days:
        raise RuntimeError("GitHub contribution data was not found.")

    # Keep the newest 365 days and arrange them around a personal orbital ring.
    days = days[-365:]

    width, height = 980, 520
    cx, cy = width / 2, height / 2
    max_radius = 205
    total = sum(1 for _, level in days if level > 0)

    parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-label="Animated contribution orbit for {USERNAME}">',
        "<defs>",
        '<radialGradient id="bg"><stop offset="0" stop-color="#172554"/><stop offset="0.55" stop-color="#0D1117"/><stop offset="1" stop-color="#05070B"/></radialGradient>',
        '<filter id="glow"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>',
        '<style><![CDATA[.star{transform-box:fill-box;transform-origin:center;animation:pulse 3.8s ease-in-out infinite}.ring{fill:none;stroke:#334155;stroke-opacity:.38;stroke-width:1}.label{font:600 15px Segoe UI,Arial,sans-serif;fill:#E6EDF3;letter-spacing:2px}.sub{font:500 11px Segoe UI,Arial,sans-serif;fill:#94A3B8;letter-spacing:1.2px}@keyframes pulse{0%,100%{opacity:.45;transform:scale(.82)}50%{opacity:1;transform:scale(1.18)}}@keyframes spin{to{transform:rotate(360deg)}}.rotor{transform-origin:490px 260px;animation:spin 28s linear infinite}</style>',
        "</defs>",
        f'<rect width="{width}" height="{height}" rx="28" fill="url(#bg)"/>',
        '<g opacity=".55"><circle cx="490" cy="260" r="205" class="ring"/><circle cx="490" cy="260" r="150" class="ring"/><circle cx="490" cy="260" r="95" class="ring"/></g>',
        '<g class="rotor" filter="url(#glow)">',
    ]

    count = len(days)
    for index, (_, level) in enumerate(days):
        angle = -pi / 2 + (index / max(count, 1)) * 2 * pi
        radius = 88 + (level / 4) * 117
        x = cx + cos(angle) * radius
        y = cy + sin(angle) * radius
        size = 2.3 + level * 1.5
        opacity = 0.18 + level * 0.2
        delay = (index % 19) * 0.17
        parts.append(
            f'<circle class="star" cx="{x:.1f}" cy="{y:.1f}" r="{size:.1f}" '
            f'fill="#67E8F9" opacity="{opacity:.2f}" style="animation-delay:{delay:.2f}s"/>'
        )

    parts += [
        "</g>",
        '<circle cx="490" cy="260" r="56" fill="#0B1020" stroke="#8B5CF6" stroke-width="2" filter="url(#glow)"/>',
        '<circle cx="490" cy="260" r="42" fill="none" stroke="#67E8F9" stroke-opacity=".65"/>',
        '<circle cx="490" cy="260" r="8" fill="#FF72D2" filter="url(#glow)"/>',
        '<text x="490" y="250" text-anchor="middle" class="label">PRASANNA</text>',
        '<text x="490" y="272" text-anchor="middle" class="sub">CONTRIBUTION ORBIT</text>',
        '<line x1="490" y1="46" x2="490" y2="82" stroke="#67E8F9" stroke-opacity=".45"/>',
        '<text x="490" y="31" text-anchor="middle" class="sub">365-DAY DEVELOPMENT SIGNAL</text>',
        f'<text x="490" y="492" text-anchor="middle" class="sub">{total} active contribution days • GitHub activity</text>',
        "</svg>",
    ]

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(parts), encoding="utf-8")


if __name__ == "__main__":
    main()
