import pytest

from src import planner
from src.pipeline import MAX_RETRIES, PlanValidationError, generate_deck
from src.schema import SlidePlan
from tests.conftest import RAW_DATA, build_sample_plan


def test_generate_deck_cleans_dirty_content_and_succeeds(monkeypatch):
    calls = []

    def fake_plan_deck(user_prompt, raw_data, target_slide_count=None, correction=None):
        calls.append(correction)
        plan = build_sample_plan()
        plan.deck_title = "Q3 Review—Final 🚀"
        return plan

    monkeypatch.setattr(planner, "plan_deck", fake_plan_deck)

    buffer, deck_title = generate_deck(prompt="test prompt", raw_data=RAW_DATA, theme_name="slate")

    assert len(calls) == 1
    assert buffer.getbuffer().nbytes > 0
    assert "🚀" not in deck_title
    assert "—" not in deck_title


def test_generate_deck_raises_after_exhausting_retries(monkeypatch):
    calls = []

    def fake_plan_deck(user_prompt, raw_data, target_slide_count=None, correction=None):
        calls.append(correction)
        plan = build_sample_plan()
        plan.slides[2].body[0] = "This will revolutionize everything"
        return plan

    monkeypatch.setattr(planner, "plan_deck", fake_plan_deck)

    with pytest.raises(PlanValidationError):
        generate_deck(prompt="test prompt", raw_data=RAW_DATA, theme_name="slate")

    assert len(calls) == MAX_RETRIES + 1
    assert calls[0] is None
    assert all(c is not None for c in calls[1:])


def test_generate_deck_retries_after_schema_validation_error(monkeypatch):
    calls = []

    def fake_plan_deck(user_prompt, raw_data, target_slide_count=None, correction=None):
        calls.append(correction)
        if len(calls) == 1:
            SlidePlan(deck_title="Broken", slides=[])  # raises pydantic ValidationError
        return build_sample_plan()

    monkeypatch.setattr(planner, "plan_deck", fake_plan_deck)

    buffer, deck_title = generate_deck(prompt="test prompt", raw_data=RAW_DATA, theme_name="slate")

    assert len(calls) == 2
    assert buffer.getbuffer().nbytes > 0
    assert deck_title == "Q3 Business Review"


def test_generate_deck_applies_title_override(monkeypatch):
    monkeypatch.setattr(planner, "plan_deck", lambda *a, **k: build_sample_plan())

    _, deck_title = generate_deck(
        prompt="test prompt", raw_data=RAW_DATA, theme_name="slate", deck_title_override="Custom Title"
    )

    assert deck_title == "Custom Title"
