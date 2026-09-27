from pptx import Presentation
from pptx.enum.dml import MSO_FILL_TYPE

from src.renderer import render
from src.theme import resolve_theme
from tests.conftest import build_sample_plan


def _slide_text(slide) -> str:
    parts = []
    for shape in slide.shapes:
        if shape.has_text_frame:
            parts.append(shape.text_frame.text)
        if shape.has_table:
            for row in shape.table.rows:
                for cell in row.cells:
                    parts.append(cell.text_frame.text)
    return "\n".join(parts)


def _has_gradient_fill(shape) -> bool:
    try:
        fill = shape.fill
    except (AttributeError, TypeError, NotImplementedError):
        return False
    try:
        return fill.type == MSO_FILL_TYPE.GRADIENT
    except (AttributeError, TypeError, ValueError):
        return False


def test_render_produces_expected_slide_count():
    plan = build_sample_plan()
    theme = resolve_theme("slate")
    buffer = render(plan, theme)
    prs = Presentation(buffer)
    assert len(prs.slides) == len(plan.slides)


def test_render_never_produces_gradient_fills():
    plan = build_sample_plan()
    theme = resolve_theme("charcoal")
    buffer = render(plan, theme)
    prs = Presentation(buffer)

    for slide in prs.slides:
        assert slide.background.fill.type != MSO_FILL_TYPE.GRADIENT
        for shape in slide.shapes:
            assert not _has_gradient_fill(shape)


def test_render_includes_expected_content():
    plan = build_sample_plan()
    theme = resolve_theme("slate")
    buffer = render(plan, theme)
    prs = Presentation(buffer)

    title_text = _slide_text(prs.slides[0])
    assert "Q3 Business Review" in title_text

    stat_text = _slide_text(prs.slides[4])
    assert "42%" in stat_text

    table_text = _slide_text(prs.slides[6])
    assert "Region" in table_text
    assert "North" in table_text
    assert "500k" in table_text

    closing_text = _slide_text(prs.slides[7])
    assert "Thank You" in closing_text
