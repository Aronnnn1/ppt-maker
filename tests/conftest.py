"""Shared test fixtures: a hand-built, schema-valid slide plan covering every layout."""

from __future__ import annotations

from src.schema import Slide, SlideLayout, SlidePlan

RAW_DATA = (
    "Revenue grew 42% year over year to reach 1.2 million dollars across 8 regions. "
    "We doubled our support team this year. "
    "Region North brought in 500k, Region South brought in 300k."
)


def build_sample_plan(**overrides) -> SlidePlan:
    slides = [
        Slide(layout=SlideLayout.TITLE, title="Q3 Business Review", subtitle="Prepared for leadership"),
        Slide(layout=SlideLayout.SECTION_HEADER, title="Financial Performance"),
        Slide(
            layout=SlideLayout.BULLETS,
            title="Highlights",
            body=["Revenue grew 42% year over year.", "Expanded into 8 regions."],
        ),
        Slide(
            layout=SlideLayout.TWO_COLUMN,
            left_heading="Strengths",
            left_items=["Strong retention"],
            right_heading="Risks",
            right_items=["Support costs rising"],
        ),
        Slide(
            layout=SlideLayout.BIG_STAT,
            stat_value="42%",
            stat_label="Revenue growth",
            stat_source_quote="Revenue grew 42% year over year",
        ),
        Slide(
            layout=SlideLayout.QUOTE,
            quote_text="We doubled our support team this year.",
            quote_attribution="Operations Lead",
        ),
        Slide(
            layout=SlideLayout.TABLE,
            table_headers=["Region", "Revenue"],
            table_rows=[["North", "500k"], ["South", "300k"]],
        ),
        Slide(layout=SlideLayout.CLOSING, title="Thank You", subtitle="Questions welcome"),
    ]
    data = {"deck_title": "Q3 Business Review", "slides": slides}
    data.update(overrides)
    return SlidePlan(**data)
