from src.sanitize import (
    check_stat_traceability,
    find_branding,
    find_filler_phrases,
    normalize_dashes,
    sanitize_plan,
    strip_emoji,
    validate_plan,
)
from tests.conftest import RAW_DATA, build_sample_plan


def test_strip_emoji_removes_emoji():
    assert strip_emoji("Great quarter 🚀🎉") == "Great quarter"
    assert strip_emoji("No emoji here") == "No emoji here"


def test_normalize_dashes_handles_em_and_en_dash():
    assert normalize_dashes("Revenue grew—a lot") == "Revenue grew, a lot"
    assert normalize_dashes("Q3 results – strong") == "Q3 results, strong"


def test_normalize_dashes_collapses_numeric_range():
    assert normalize_dashes("The 2020–2024 period") == "The 2020-2024 period"


def test_find_filler_phrases_flags_known_phrase():
    assert "revolutionize" in find_filler_phrases("We will revolutionize the industry")


def test_find_filler_phrases_clean_text():
    assert find_filler_phrases("Revenue grew steadily this quarter") == []


def test_find_branding_flags_ai_mentions_case_insensitively():
    assert find_branding("Made With AI") != []
    assert find_branding("Regular closing slide text") == []


def test_check_stat_traceability_flags_untraceable_number():
    plan = build_sample_plan()
    plan.slides[4].stat_value = "99%"  # not present anywhere in RAW_DATA
    violations = check_stat_traceability(plan, RAW_DATA)
    assert any("99" in v for v in violations)


def test_check_stat_traceability_passes_traceable_number():
    plan = build_sample_plan()
    violations = check_stat_traceability(plan, RAW_DATA)
    assert violations == []


def test_sanitize_plan_cleans_nested_fields():
    plan = build_sample_plan()
    plan.slides[2].body[0] = "Revenue grew—42% 🚀"
    cleaned = sanitize_plan(plan)
    assert "🚀" not in cleaned.slides[2].body[0]
    assert "—" not in cleaned.slides[2].body[0]


def test_validate_plan_aggregates_violations():
    plan = build_sample_plan()
    plan.slides[2].body[0] = "This will revolutionize everything, made with AI"
    violations = validate_plan(plan, RAW_DATA)
    assert any("revolutionize" in v for v in violations)
    assert any("made with ai" in v for v in violations)
