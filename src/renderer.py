"""Deterministic .pptx rendering.

This module never calls an LLM and never makes a freeform visual
decision -- it switches on the fixed `SlideLayout` enum and calls one
hand-coded `_render_<layout>` function per case, each using fixed
geometry/typography and only the solid colors defined on the `Theme`
object. There is no code path here that can produce a gradient fill or
a pill-shaped (fully rounded) button, because those python-pptx APIs
are simply never called in this file.
"""

from __future__ import annotations

import io
from typing import Callable

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

from src.schema import Slide, SlideLayout, SlidePlan
from src.theme import Theme

SLIDE_WIDTH = Inches(13.333)
SLIDE_HEIGHT = Inches(7.5)
MARGIN = Inches(0.75)
CONTENT_WIDTH = SLIDE_WIDTH - 2 * MARGIN
HAIRLINE = Emu(12700)  # 1pt

COVER_TITLE_SIZE = 44
SECTION_TITLE_SIZE = 36
CLOSING_TITLE_SIZE = 40
HEADING_SIZE = 30
SUBTITLE_SIZE = 20
BODY_SIZE = 18
BULLET_SIZE = 18
COLUMN_HEADING_SIZE = 20
STAT_VALUE_SIZE = 80
STAT_LABEL_SIZE = 22
QUOTE_SIZE = 26
ATTRIBUTION_SIZE = 16
CAPTION_SIZE = 12
TABLE_HEADER_SIZE = 15
TABLE_BODY_SIZE = 14


def _truncate(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 3].rstrip() + "..."


def _new_presentation() -> Presentation:
    prs = Presentation()
    prs.slide_width = SLIDE_WIDTH
    prs.slide_height = SLIDE_HEIGHT
    return prs


def _blank_slide(prs: Presentation):
    layout = prs.slide_layouts[6]  # blank layout, no inherited placeholders
    return prs.slides.add_slide(layout)


def _set_background(slide, theme: Theme) -> None:
    background = slide.background
    background.fill.solid()
    background.fill.fore_color.rgb = theme.background


def _add_rect(slide, left, top, width, height, color) -> None:
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()
    shape.shadow.inherit = False


def _textbox(slide, left, top, width, height, anchor=None):
    box = slide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame
    tf.word_wrap = True
    tf.margin_left = 0
    tf.margin_right = 0
    tf.margin_top = 0
    tf.margin_bottom = 0
    if anchor is not None:
        tf.vertical_anchor = anchor
    return box


def _paragraph(tf, index, text, font_name, size, color, bold=False, italic=False, align=PP_ALIGN.LEFT, space_after=0):
    p = tf.paragraphs[0] if index == 0 else tf.add_paragraph()
    p.alignment = align
    if space_after:
        p.space_after = Pt(space_after)
    run = p.add_run()
    run.text = text
    run.font.name = font_name
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    return p


def _render_title(slide, data: Slide, theme: Theme) -> None:
    _add_rect(slide, MARGIN, Inches(0.75), Inches(1.2), Inches(0.08), theme.accent)
    box = _textbox(slide, MARGIN, Inches(2.9), CONTENT_WIDTH, Inches(1.6), anchor=MSO_ANCHOR.BOTTOM)
    _paragraph(box.text_frame, 0, data.title, theme.heading_font, COVER_TITLE_SIZE, theme.primary_text, bold=True)
    if data.subtitle:
        sub_box = _textbox(slide, MARGIN, Inches(4.6), CONTENT_WIDTH, Inches(0.8))
        _paragraph(sub_box.text_frame, 0, data.subtitle, theme.body_font, SUBTITLE_SIZE, theme.secondary_text)


def _render_section_header(slide, data: Slide, theme: Theme) -> None:
    bar_width = Inches(0.12)
    bar_height = Inches(2.2)
    bar_top = (SLIDE_HEIGHT - bar_height) // 2
    _add_rect(slide, MARGIN, bar_top, bar_width, bar_height, theme.accent)

    text_left = MARGIN + bar_width + Inches(0.4)
    text_width = SLIDE_WIDTH - text_left - MARGIN
    box = _textbox(slide, text_left, bar_top, text_width, bar_height, anchor=MSO_ANCHOR.MIDDLE)
    tf = box.text_frame
    _paragraph(tf, 0, data.title, theme.heading_font, SECTION_TITLE_SIZE, theme.primary_text, bold=True)
    if data.subtitle:
        _paragraph(tf, 1, data.subtitle, theme.body_font, SUBTITLE_SIZE, theme.secondary_text)


def _render_bullets(slide, data: Slide, theme: Theme) -> None:
    title_box = _textbox(slide, MARGIN, Inches(0.6), CONTENT_WIDTH, Inches(0.9))
    _paragraph(title_box.text_frame, 0, data.title, theme.heading_font, HEADING_SIZE, theme.primary_text, bold=True)
    _add_rect(slide, MARGIN, Inches(1.5), Inches(1.0), Inches(0.05), theme.accent)

    body_box = _textbox(slide, MARGIN, Inches(1.9), CONTENT_WIDTH, SLIDE_HEIGHT - Inches(1.9) - MARGIN)
    tf = body_box.text_frame
    for i, item in enumerate(data.body):
        _paragraph(tf, i, f"•  {item}", theme.body_font, BULLET_SIZE, theme.primary_text, space_after=14)


def _render_two_column(slide, data: Slide, theme: Theme) -> None:
    if data.title:
        title_box = _textbox(slide, MARGIN, Inches(0.6), CONTENT_WIDTH, Inches(0.8))
        _paragraph(title_box.text_frame, 0, data.title, theme.heading_font, HEADING_SIZE, theme.primary_text, bold=True)
        columns_top = Inches(1.7)
    else:
        columns_top = Inches(1.0)

    columns_height = SLIDE_HEIGHT - columns_top - MARGIN
    col_gap = Inches(0.6)
    col_width = (CONTENT_WIDTH - col_gap) // 2
    left_x = MARGIN
    right_x = MARGIN + col_width + col_gap
    divider_x = MARGIN + col_width + col_gap // 2

    _add_rect(slide, divider_x, columns_top, HAIRLINE, columns_height, theme.secondary_text)

    left_box = _textbox(slide, left_x, columns_top, col_width, columns_height)
    tf = left_box.text_frame
    _paragraph(tf, 0, data.left_heading, theme.heading_font, COLUMN_HEADING_SIZE, theme.accent, bold=True, space_after=12)
    for i, item in enumerate(data.left_items, start=1):
        _paragraph(tf, i, f"•  {item}", theme.body_font, BODY_SIZE, theme.primary_text, space_after=10)

    right_box = _textbox(slide, right_x, columns_top, col_width, columns_height)
    tf2 = right_box.text_frame
    _paragraph(tf2, 0, data.right_heading, theme.heading_font, COLUMN_HEADING_SIZE, theme.accent, bold=True, space_after=12)
    for i, item in enumerate(data.right_items, start=1):
        _paragraph(tf2, i, f"•  {item}", theme.body_font, BODY_SIZE, theme.primary_text, space_after=10)


def _render_big_stat(slide, data: Slide, theme: Theme) -> None:
    if data.title:
        title_box = _textbox(slide, MARGIN, Inches(0.6), CONTENT_WIDTH, Inches(0.8))
        _paragraph(title_box.text_frame, 0, data.title, theme.heading_font, HEADING_SIZE, theme.primary_text, bold=True, align=PP_ALIGN.CENTER)

    stat_box = _textbox(slide, MARGIN, Inches(2.3), CONTENT_WIDTH, Inches(2.0), anchor=MSO_ANCHOR.MIDDLE)
    _paragraph(stat_box.text_frame, 0, data.stat_value, theme.heading_font, STAT_VALUE_SIZE, theme.accent, bold=True, align=PP_ALIGN.CENTER)

    label_box = _textbox(slide, MARGIN, Inches(4.5), CONTENT_WIDTH, Inches(0.7))
    _paragraph(label_box.text_frame, 0, data.stat_label, theme.body_font, STAT_LABEL_SIZE, theme.primary_text, align=PP_ALIGN.CENTER)

    if data.stat_source_quote:
        caption = _truncate(data.stat_source_quote, 140)
        cap_box = _textbox(slide, MARGIN, SLIDE_HEIGHT - MARGIN - Inches(0.5), CONTENT_WIDTH, Inches(0.5))
        _paragraph(cap_box.text_frame, 0, f"Source: {caption}", theme.body_font, CAPTION_SIZE, theme.secondary_text, italic=True, align=PP_ALIGN.CENTER)


def _render_quote(slide, data: Slide, theme: Theme) -> None:
    bar_height = Inches(1.6)
    bar_top = (SLIDE_HEIGHT - bar_height) // 2
    _add_rect(slide, MARGIN, bar_top, Inches(0.1), bar_height, theme.accent)

    text_left = MARGIN + Inches(0.5)
    text_width = SLIDE_WIDTH - text_left - MARGIN
    box = _textbox(slide, text_left, bar_top, text_width, bar_height, anchor=MSO_ANCHOR.MIDDLE)
    tf = box.text_frame
    _paragraph(tf, 0, f"“{data.quote_text}”", theme.heading_font, QUOTE_SIZE, theme.primary_text, italic=True, space_after=14)
    if data.quote_attribution:
        _paragraph(tf, 1, data.quote_attribution, theme.body_font, ATTRIBUTION_SIZE, theme.secondary_text)


def _render_table(slide, data: Slide, theme: Theme) -> None:
    if data.title:
        title_box = _textbox(slide, MARGIN, Inches(0.6), CONTENT_WIDTH, Inches(0.8))
        _paragraph(title_box.text_frame, 0, data.title, theme.heading_font, HEADING_SIZE, theme.primary_text, bold=True)
        table_top = Inches(1.6)
    else:
        table_top = Inches(1.0)

    rows = len(data.table_rows) + 1
    cols = len(data.table_headers)
    table_height = min(SLIDE_HEIGHT - table_top - MARGIN, Inches(0.55) * rows)

    graphic_frame = slide.shapes.add_table(rows, cols, MARGIN, table_top, CONTENT_WIDTH, table_height)
    table = graphic_frame.table
    table.first_row = True
    table.horz_banding = False

    col_width = CONTENT_WIDTH // cols
    for c in range(cols):
        table.columns[c].width = col_width

    for c, header in enumerate(data.table_headers):
        cell = table.cell(0, c)
        cell.fill.solid()
        cell.fill.fore_color.rgb = theme.accent
        _paragraph(cell.text_frame, 0, header, theme.body_font, TABLE_HEADER_SIZE, theme.background, bold=True)

    for r, row in enumerate(data.table_rows, start=1):
        for c, value in enumerate(row):
            cell = table.cell(r, c)
            cell.fill.solid()
            cell.fill.fore_color.rgb = theme.background
            _paragraph(cell.text_frame, 0, value, theme.body_font, TABLE_BODY_SIZE, theme.primary_text)


def _render_closing(slide, data: Slide, theme: Theme) -> None:
    _add_rect(slide, MARGIN, Inches(0.75), Inches(1.2), Inches(0.08), theme.accent)
    box = _textbox(slide, MARGIN, Inches(2.9), CONTENT_WIDTH, Inches(1.6), anchor=MSO_ANCHOR.BOTTOM)
    _paragraph(box.text_frame, 0, data.title, theme.heading_font, CLOSING_TITLE_SIZE, theme.primary_text, bold=True, align=PP_ALIGN.CENTER)
    if data.subtitle:
        sub_box = _textbox(slide, MARGIN, Inches(4.6), CONTENT_WIDTH, Inches(0.8))
        _paragraph(sub_box.text_frame, 0, data.subtitle, theme.body_font, SUBTITLE_SIZE, theme.secondary_text, align=PP_ALIGN.CENTER)


_RENDERERS: dict[SlideLayout, Callable] = {
    SlideLayout.TITLE: _render_title,
    SlideLayout.SECTION_HEADER: _render_section_header,
    SlideLayout.BULLETS: _render_bullets,
    SlideLayout.TWO_COLUMN: _render_two_column,
    SlideLayout.BIG_STAT: _render_big_stat,
    SlideLayout.QUOTE: _render_quote,
    SlideLayout.TABLE: _render_table,
    SlideLayout.CLOSING: _render_closing,
}


def render(plan: SlidePlan, theme: Theme) -> io.BytesIO:
    prs = _new_presentation()
    for slide_data in plan.slides:
        slide = _blank_slide(prs)
        _set_background(slide, theme)
        _RENDERERS[slide_data.layout](slide, slide_data, theme)

    buffer = io.BytesIO()
    prs.save(buffer)
    buffer.seek(0)
    return buffer
