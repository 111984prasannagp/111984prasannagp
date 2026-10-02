from __future__ import annotations

from datetime import date, timedelta
from html import unescape
from pathlib import Path
import re
from urllib.request import Request, urlopen

USERNAME = "111984prasannagp"
OUTPUT_DIR = Path("dist")
CELL = 13
GAP = 4
LEFT = 72
TOP = 78
ROWS = 7


def fetch_contributions() -> tuple[dict[date, int], int]:
    url = f"https://github.com/users/{USERNAME}/contributions"
    request = Request(url, headers={"User-Agent": "github-profile-contribution-renderer/1.0"})
    with urlopen(request, timeout=30) as response:
        html = response.read().decode("utf-8", errors="replace")

    tooltip_counts: dict[str, int] = {}
    for match in re.finditer(
        r"<tool-tip\b[^>]*for=[\"']([^\"']+)[\"'][^>]*>(.*?)</tool-tip>",
        html,
        re.IGNORECASE | re.DOTALL,
    ):
        text = unescape(re.sub(r"<[^>]+>", "", match.group(2))).strip()
        count_match = re.search(r"(\d[\d,]*)\s+contributions?", text, re.IGNORECASE)
        if count_match:
            tooltip_counts[match.group(1)] = int(count_match.group(1).replace(",", ""))

    days: dict[date, int] = {}
    for tag in re.findall(r"<td\b[^>]*>", html, re.IGNORECASE):
        date_match = re.search(r'data-date=[\"\'](\d{4}-\d{2}-\d{2})[\"\']', tag)
        level_match = re.search(r'data-level=[\"\']([0-4])[\"\']', tag)
        id_match = re.search(r'id=[\"\']([^\"\']+)[\"\']', tag)
        if not (date_match and level_match):
            continue
        days[date.fromisoformat(date_match.group(1))] = int(level_match.group(2))

    if not days:
        raise RuntimeError("GitHub contribution cells were not found.")

    total = 0
    for match in re.finditer(
        r"<td\b[^>]*data-date=[\"'](\d{4}-\d{2}-\d{2})[\"'][^>]*>",
        html,
        re.IGNORECASE,
    ):
        tag = match.group(0)
        date_match = re.search(r'data-date=[\"\'](\d{4}-\d{2}-\d{2})[\"\']', tag)
        id_match = re.search(r'id=[\"\']([^\"\']+)[\"\']', tag)
        if date_match and id_match:
            total += tooltip_counts.get(id_match.group(1), 0)

    return days, total


def color_for(level: int, dark: bool) -> str:
    if dark:
        return ["#161B22", "#0E4429", "#006D32", "#26A641", "#39D353"][level]
    return ["#EBEDF0", "#9BE9A8", "#40C463", "#30A14E", "#216E39"][level]


def build_svg(days: dict[date, int], total: int, dark: bool) -> str:
    first = min(days)
    last = max(days)

    start = first - timedelta(days=(first.weekday() + 1) % 7)
    end = last + timedelta(days=6 - ((last.weekday() + 1) % 7))
    weeks = ((end - start).days + 1) // 7

    width = max(1180, LEFT + weeks * (CELL + GAP) + 40)
    height = 365
    bg = "#0D1117" if dark else "#FFFFFF"
    text = "#E6EDF3" if dark else "#24292F"
    muted = "#8B949E" if dark else "#57606A"
    border = "#30363D" if dark else "#D0D7DE"
    snake = "#F0883E" if dark else "#D1242F"

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" role="img" aria-label="GitHub contribution calendar for {USERNAME}">',
        "<defs>",
        '<filter id="snakeGlow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>',
        '<style><![CDATA[.day{shape-rendering:geometricPrecision}.month{font:600 14px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}.weekday{font:500 12px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}.title{font:600 20px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}.settings{font:500 14px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}.legend{font:500 12px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}]]></style>',
        "</defs>",
        f'<rect x="0" y="0" width="{width}" height="{height}" rx="12" fill="{bg}" stroke="{border}" stroke-width="1"/>',
        f'<text x="18" y="30" class="title" fill="{text}">{total:,} contributions in the last year</text>',
        f'<text x="{width - 18}" y="30" text-anchor="end" class="settings" fill="{muted}">Contribution settings ▾</text>',
    ]

    weekday_names = ["", "Mon", "", "Wed", "", "Fri", ""]
    for row, name in enumerate(weekday_names):
        if name:
            y = TOP + row * (CELL + GAP) + 11
            parts.append(f'<text x="50" y="{y}" text-anchor="end" class="weekday" fill="{text}">{name}</text>')

    # Month labels are anchored to the week containing each month's first day.
    seen_months: set[tuple[int, int]] = set()
    for week in range(weeks):
        week_start = start + timedelta(days=week * 7)
        for offset in range(7):
            current = week_start + timedelta(days=offset)
            key = (current.year, current.month)
            if current.day == 1 and key not in seen_months:
                seen_months.add(key)
                x = LEFT + week * (CELL + GAP)
                month_name = current.strftime("%b")
                parts.append(f'<text x="{x}" y="64" class="month" fill="{text}">{month_name}</text>')

    for week in range(weeks):
        for row in range(ROWS):
            current = start + timedelta(days=week * 7 + row)
            level = days.get(current, 0)
            x = LEFT + week * (CELL + GAP)
            y = TOP + row * (CELL + GAP)
            parts.append(
                f'<rect class="day" x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="3" fill="{color_for(level, dark)}" stroke="{border}" stroke-width=".6"/>'
            )

    grid_x0 = LEFT + CELL / 2
    grid_x1 = LEFT + (weeks - 1) * (CELL + GAP) + CELL / 2
    row_y = [TOP + r * (CELL + GAP) + CELL / 2 for r in range(ROWS)]

    path_parts = [f"M {grid_x0:.1f} {row_y[0]:.1f}"]
    for row in range(ROWS):
        path_parts.append(f" H {grid_x1 if row % 2 == 0 else grid_x0:.1f}")
        if row < ROWS - 1:
            path_parts.append(f" V {row_y[row + 1]:.1f}")
    path_d = "".join(path_parts)
    parts.append(f'<path id="snakePath" d="{path_d}" fill="none" stroke="none"/>')

    for radius, begin, opacity in [(4.2, "0s", "1"), (3.2, "-0.28s", ".9"), (2.5, "-0.56s", ".75")]:
        parts.append(
            f'<circle cx="{grid_x0:.1f}" cy="{row_y[0]:.1f}" r="{radius}" fill="{snake}" opacity="{opacity}" filter="url(#snakeGlow)">'
            f'<animateMotion dur="21s" repeatCount="indefinite" rotate="auto" begin="{begin}"><mpath href="#snakePath"/></animateMotion>'
            "</circle>"
        )

    # Tiny eye marker on the head keeps the moving object visibly snake-like.
    parts.append(
        f'<circle cx="{grid_x0 + 1.2:.1f}" cy="{row_y[0] - 1.2:.1f}" r=".55" fill="{bg}">'
        '<animateMotion dur="21s" repeatCount="indefinite" rotate="auto"><mpath href="#snakePath"/></animateMotion>'
        "</circle>"
    )

    legend_y = TOP + ROWS * (CELL + GAP) + 34
    parts.append(f'<text x="{LEFT}" y="{legend_y}" class="legend" fill="{muted}">Learn how we count contributions</text>')

    legend_start = width - 210
    parts.append(f'<text x="{legend_start}" y="{legend_y}" class="legend" fill="{muted}">Less</text>')
    for i in range(5):
        x = legend_start + 36 + i * 20
        parts.append(f'<rect x="{x}" y="{legend_y - 12}" width="14" height="14" rx="3" fill="{color_for(i, dark)}" stroke="{border}" stroke-width=".5"/>')
    parts.append(f'<text x="{legend_start + 142}" y="{legend_y}" class="legend" fill="{muted}">More</text>')

    parts.append("</svg>")
    return "\n".join(parts)


def main() -> None:
    days, total = fetch_contributions()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "contribution-calendar-snake.svg").write_text(build_svg(days, total, False), encoding="utf-8")
    (OUTPUT_DIR / "contribution-calendar-snake-dark.svg").write_text(build_svg(days, total, True), encoding="utf-8")


if __name__ == "__main__":
    main()
