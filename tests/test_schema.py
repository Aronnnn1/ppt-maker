import pytest
from pydantic import ValidationError

from src.schema import Slide, SlideLayout, SlidePlan
from tests.conftest import build_sample_plan


def test_valid_plan_constructs_cleanly():
    plan = build_sample_plan()
    assert len(plan.slides) == 8


def test_bullets_missing_body_raises():
    with pytest.raises(ValidationError):
        Slide(layout=SlideLayout.BULLETS, title="Highlights")


def test_big_stat_missing_stat_value_raises():
    with pytest.raises(ValidationError):
        Slide(layout=SlideLayout.BIG_STAT, stat_label="Revenue growth", stat_source_quote="42%")


def test_table_row_length_mismatch_raises():
    with pytest.raises(ValidationError):
        Slide(
            layout=SlideLayout.TABLE,
            table_headers=["Region", "Revenue"],
            table_rows=[["North", "500k", "extra"]],
        )


def test_first_slide_must_be_title():
    slides = build_sample_plan().slides
    slides[0] = Slide(layout=SlideLayout.BULLETS, title="Oops", body=["not a title slide"])
    with pytest.raises(ValidationError):
        SlidePlan(deck_title="Broken", slides=slides)


def test_last_slide_must_be_closing():
    slides = build_sample_plan().slides
    slides[-1] = Slide(layout=SlideLayout.BULLETS, title="Oops", body=["not a closing slide"])
    with pytest.raises(ValidationError):
        SlidePlan(deck_title="Broken", slides=slides)


def test_minimum_slide_count_enforced():
    title = Slide(layout=SlideLayout.TITLE, title="Too Short")
    closing = Slide(layout=SlideLayout.CLOSING, title="Thanks")
    with pytest.raises(ValidationError):
        SlidePlan(deck_title="Too Short", slides=[title, closing])
