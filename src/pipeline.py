"""Orchestrates planner -> sanitize -> retry -> renderer.

This is the only module that talks to both pipeline stages, so app.py's
Flask routes stay thin.
"""

from __future__ import annotations

import io

from pydantic import ValidationError

from src import planner, renderer
from src.sanitize import sanitize_plan, validate_plan
from src.theme import resolve_theme

MAX_RETRIES = 2


class PlanValidationError(Exception):
    """Raised when no draft satisfies the design rules within the retry budget."""


def generate_deck(
    prompt: str,
    raw_data: str,
    theme_name: str,
    accent_override: str | None = None,
    deck_title_override: str | None = None,
    target_slide_count: int | None = None,
) -> tuple[io.BytesIO, str]:
    theme = resolve_theme(theme_name, accent_override)

    correction: str | None = None
    last_message = "no attempts were made"

    for _ in range(MAX_RETRIES + 1):
        try:
            plan = planner.plan_deck(prompt, raw_data, target_slide_count, correction)
        except ValidationError as exc:
            last_message = str(exc)
            correction = f"The previous JSON response did not match the required schema: {exc}"
            continue

        plan = sanitize_plan(plan)
        violations = validate_plan(plan, raw_data)

        if not violations:
            if deck_title_override:
                plan = plan.model_copy(update={"deck_title": deck_title_override})
            return renderer.render(plan, theme), plan.deck_title

        last_message = "\n".join(violations)
        correction = "\n".join(f"- {v}" for v in violations)

    raise PlanValidationError(
        f"Could not produce a deck that satisfies the design rules after {MAX_RETRIES} "
        f"retries. Remaining issues:\n{last_message}"
    )
