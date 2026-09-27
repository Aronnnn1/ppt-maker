"""Fixed, hand-designed visual themes.

The LLM never chooses colors or fonts -- it only picks a theme name from
a fixed menu, and `resolve_theme` turns that into concrete values here in
code. This is the main structural defense against "AI slop" visuals:
there is simply no code path that can produce a gradient or a purple
palette, because the only fills ever constructed are the solid colors
below.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace

from pptx.dml.color import RGBColor

_HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")

# Fonts restricted to faces that ship by default with Windows/Office and
# LibreOffice, so a deck never silently falls back to an ugly substitute
# font on the recipient's machine.
_SAFE_FONTS = {"Calibri", "Georgia", "Arial", "Cambria", "Times New Roman"}


@dataclass(frozen=True)
class Theme:
    name: str
    background: RGBColor
    primary_text: RGBColor
    secondary_text: RGBColor
    accent: RGBColor
    heading_font: str
    body_font: str

    def __post_init__(self) -> None:
        if self.heading_font not in _SAFE_FONTS or self.body_font not in _SAFE_FONTS:
            raise ValueError(f"theme {self.name!r} uses a font outside the safe list {_SAFE_FONTS}")


def _rgb(hex_str: str) -> RGBColor:
    return RGBColor.from_string(hex_str.lstrip("#"))


THEMES: dict[str, Theme] = {
    "slate": Theme(
        name="slate",
        background=_rgb("#FFFFFF"),
        primary_text=_rgb("#1A1A1A"),
        secondary_text=_rgb("#5A5A5A"),
        accent=_rgb("#2F5D8C"),
        heading_font="Georgia",
        body_font="Calibri",
    ),
    "charcoal": Theme(
        name="charcoal",
        background=_rgb("#1E1E1E"),
        primary_text=_rgb("#F2F2F2"),
        secondary_text=_rgb("#B0B0B0"),
        accent=_rgb("#4FA6A6"),
        heading_font="Calibri",
        body_font="Calibri",
    ),
    "forest": Theme(
        name="forest",
        background=_rgb("#FFFFFF"),
        primary_text=_rgb("#1B2B1E"),
        secondary_text=_rgb("#4C5C4F"),
        accent=_rgb("#3F7A4E"),
        heading_font="Georgia",
        body_font="Calibri",
    ),
    "clay": Theme(
        name="clay",
        background=_rgb("#FBF8F3"),
        primary_text=_rgb("#2B2521"),
        secondary_text=_rgb("#6B6058"),
        accent=_rgb("#B4552F"),
        heading_font="Georgia",
        body_font="Calibri",
    ),
    "mono": Theme(
        name="mono",
        background=_rgb("#FFFFFF"),
        primary_text=_rgb("#111111"),
        secondary_text=_rgb("#666666"),
        accent=_rgb("#111111"),
        heading_font="Calibri",
        body_font="Calibri",
    ),
}

DEFAULT_THEME = "slate"


def _relative_luminance(rgb: RGBColor) -> float:
    def linearize(channel: int) -> float:
        c = channel / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = linearize(rgb[0]), linearize(rgb[1]), linearize(rgb[2])
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _contrast_ratio(a: RGBColor, b: RGBColor) -> float:
    la, lb = _relative_luminance(a), _relative_luminance(b)
    lighter, darker = max(la, lb), min(la, lb)
    return (lighter + 0.05) / (darker + 0.05)


def resolve_theme(name: str, accent_override: str | None = None) -> Theme:
    """Resolve a theme name (+ optional user accent hex) into a concrete Theme.

    An invalid or unreadable accent override (contrast ratio against the
    theme background below 3.0) is silently ignored in favor of the
    theme's built-in accent, rather than surfacing an error to the user.
    """
    base = THEMES.get(name, THEMES[DEFAULT_THEME])

    if accent_override and _HEX_RE.match(accent_override):
        candidate = _rgb(accent_override)
        if _contrast_ratio(candidate, base.background) >= 3.0:
            return replace(base, accent=candidate)

    return base
