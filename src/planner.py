"""Builds the prompt sent to Gemini for the content-structuring stage.

This is Stage 1 of the pipeline. It never touches colors, fonts, or
layout geometry -- it only decides which of the fixed SlideLayout types
each piece of content belongs in. All visual decisions live in
src/theme.py and src/renderer.py instead.
"""

from __future__ import annotations

from src import gemini_client
from src.sanitize import BRANDING_PHRASES, FILLER_PHRASES
from src.schema import SlidePlan

_LAYOUT_GUIDE = """
- title: opening slide. Needs `title` (the deck's main title) and optionally `subtitle`.
- section_header: a divider slide introducing a new section. Needs `title`.
- bullets: a slide making a point with supporting bullets. Needs `title` and `body` (1-6 short bullet strings).
- two_column: a side-by-side comparison. Needs `left_heading`, `left_items`, `right_heading`, `right_items`.
- big_stat: one prominent number as the focus of the slide. Needs `stat_value` (e.g. "42%"), `stat_label` (what it measures), and `stat_source_quote` (the exact substring of the supplied raw data that this number comes from).
- quote: a verbatim quote pulled from the supplied data. Needs `quote_text` and optionally `quote_attribution`.
- table: tabular data. Needs `table_headers` and `table_rows` (every row must have the same number of cells as there are headers).
- closing: the final slide (e.g. thank you / questions / next steps). Needs `title`.
""".strip()


def build_prompt(
    user_prompt: str,
    raw_data: str,
    target_slide_count: int | None = None,
    correction: str | None = None,
) -> str:
    slide_count_instruction = (
        f"Aim for approximately {target_slide_count} slides (the format still hard-caps you between 4 and 20)."
        if target_slide_count
        else "Choose however many slides (between 4 and 20) best fit the amount of data given. "
        "Do not pad with filler slides just to hit a number."
    )

    banned_phrases = ", ".join(f'"{p}"' for p in FILLER_PHRASES + BRANDING_PHRASES)

    prompt = f"""
You are structuring a presentation deck from raw source material.

You will be given (1) instructions from the user about the deck's purpose and tone, and (2) a raw, unstructured blob of source data -- notes, numbers, paragraphs -- that has NOT been pre-divided into slides.

Your job: decide how to divide the substance of the raw data into a logical slide sequence. Cut anything unimportant. Do not invent facts, numbers, or claims that are not present in or directly derivable from the raw data. Never invent a customer review, testimonial, or metric that was not given to you.

User's instructions:
{user_prompt}

Raw data:
{raw_data}

Available slide layouts (use ONLY these; pick whichever fits each point):
{_LAYOUT_GUIDE}

Rules:
- The very first slide must be layout=title. The very last slide must be layout=closing.
- Every number you put in a big_stat or bullets slide must be traceable to the raw data above.
- Never use vague filler or marketing language, and never use any of these phrases in any form: {banned_phrases}.
- Never write text that mentions AI, this tool, or how the deck was generated.
- Do not use emoji. Do not use em-dashes or en-dashes; use plain commas or periods instead.
- Keep bullets short, one line each. No padding.
- {slide_count_instruction}
""".strip()

    if correction:
        prompt += (
            "\n\nYour previous draft was rejected for the following reasons. Regenerate the "
            "ENTIRE deck from scratch, fixing every one of them:\n" + correction
        )

    return prompt


def plan_deck(
    user_prompt: str,
    raw_data: str,
    target_slide_count: int | None = None,
    correction: str | None = None,
) -> SlidePlan:
    prompt = build_prompt(user_prompt, raw_data, target_slide_count, correction)
    result = gemini_client.generate_structured(prompt, SlidePlan)
    assert isinstance(result, SlidePlan)
    return result
