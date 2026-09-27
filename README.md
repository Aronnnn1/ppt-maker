# Deck Builder

Paste a freeform prompt plus a blob of raw, unstructured data (not
pre-divided into slides) and get back a downloadable `.pptx`. An LLM
decides how to structure the content into slides; a deterministic
renderer built on `python-pptx` turns that structure into the actual
deck. Rendering never uses gradients, pill-shaped shapes, or generated
"AI" branding, and content is checked before rendering for filler
language, invented statistics, and self-referential AI mentions.

## How it works

1. **Planner** (`src/planner.py`, `src/gemini_client.py`) sends the
   prompt + raw data to Gemini, constrained via structured output to
   return JSON matching the `SlidePlan` schema (`src/schema.py`). The
   LLM only ever picks from a fixed set of slide layouts and fills in
   typed fields -- it never issues freeform visual instructions.
2. **Sanitize** (`src/sanitize.py`) strips emoji and dashes from every
   field, then checks the plan for filler phrases, AI-branding
   mentions, and statistics that don't trace back to the supplied raw
   data. Violations trigger a bounded number of retries with the
   specific issues fed back to the model; if the plan still doesn't
   pass, generation fails with an error rather than shipping a deck
   that breaks the rules.
3. **Renderer** (`src/renderer.py`) deterministically builds the
   `.pptx` from the validated plan using a fixed color/typography
   system (`src/theme.py`). No LLM involvement, no freeform layout
   decisions.

## Setup

```
uv sync
cp .env.example .env   # add your Gemini API key
uv run flask run
```

Get a free Gemini API key at https://aistudio.google.com/apikey.

## Testing

```
uv run pytest
```

Tests run entirely offline (no network / API key required) -- the
Gemini call is mocked in `tests/test_pipeline.py`.
