"""Structured slide plan schema.

This is the contract between the LLM (planner) and the deterministic
renderer. The LLM is constrained (via Gemini's structured-output /
response_schema feature) to only ever produce data matching this shape --
it never emits freeform layout/visual instructions. A flat model with a
`layout` enum is used instead of a discriminated union because Gemini's
structured-output support for nested unions is unreliable; per-layout
required fields are instead enforced here in a validator.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, model_validator


class SlideLayout(str, Enum):
    TITLE = "title"
    SECTION_HEADER = "section_header"
    BULLETS = "bullets"
    TWO_COLUMN = "two_column"
    BIG_STAT = "big_stat"
    QUOTE = "quote"
    TABLE = "table"
    CLOSING = "closing"


# Field names required for each layout. Checked generically in
# Slide.check_required_fields below.
_REQUIRED_FIELDS: dict[SlideLayout, tuple[str, ...]] = {
    SlideLayout.TITLE: ("title",),
    SlideLayout.SECTION_HEADER: ("title",),
    SlideLayout.BULLETS: ("title", "body"),
    SlideLayout.TWO_COLUMN: ("left_heading", "left_items", "right_heading", "right_items"),
    SlideLayout.BIG_STAT: ("stat_value", "stat_label", "stat_source_quote"),
    SlideLayout.QUOTE: ("quote_text",),
    SlideLayout.TABLE: ("table_headers", "table_rows"),
    SlideLayout.CLOSING: ("title",),
}


class Slide(BaseModel):
    layout: SlideLayout

    title: str | None = None
    subtitle: str | None = None

    body: list[str] | None = Field(default=None, max_length=6)

    left_heading: str | None = None
    left_items: list[str] | None = Field(default=None, max_length=6)
    right_heading: str | None = None
    right_items: list[str] | None = Field(default=None, max_length=6)

    stat_value: str | None = None
    stat_label: str | None = None
    # Verbatim substring of the raw input data that backs stat_value --
    # checked for traceability in sanitize.check_stat_traceability.
    stat_source_quote: str | None = None

    quote_text: str | None = None
    quote_attribution: str | None = None

    table_headers: list[str] | None = Field(default=None, max_length=6)
    table_rows: list[list[str]] | None = Field(default=None, max_length=8)

    @model_validator(mode="after")
    def check_required_fields(self) -> "Slide":
        missing = [
            field
            for field in _REQUIRED_FIELDS[self.layout]
            if not getattr(self, field)
        ]
        if missing:
            raise ValueError(
                f"slide with layout={self.layout.value!r} is missing required "
                f"field(s): {', '.join(missing)}"
            )

        if self.layout is SlideLayout.TABLE and self.table_headers and self.table_rows:
            bad_rows = [i for i, row in enumerate(self.table_rows) if len(row) != len(self.table_headers)]
            if bad_rows:
                raise ValueError(
                    f"table slide row(s) {bad_rows} do not have the same number of "
                    f"cells as table_headers ({len(self.table_headers)})"
                )

        return self


class SlidePlan(BaseModel):
    deck_title: str
    deck_subtitle: str | None = None
    slides: list[Slide] = Field(min_length=4, max_length=20)

    @model_validator(mode="after")
    def check_structure(self) -> "SlidePlan":
        if self.slides[0].layout is not SlideLayout.TITLE:
            raise ValueError("the first slide must have layout=title")
        if self.slides[-1].layout is not SlideLayout.CLOSING:
            raise ValueError("the last slide must have layout=closing")
        return self
