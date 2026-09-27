"""Flask web app: paste a prompt + raw data, download a generated .pptx.

Nothing is written to disk -- the deck is built in memory and streamed
back as an attachment.
"""

import re

from dotenv import load_dotenv
from flask import Flask, render_template, request, send_file

from src.pipeline import PlanValidationError, generate_deck
from src.theme import DEFAULT_THEME, THEMES

load_dotenv()

app = Flask(__name__)


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "deck"


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", themes=THEMES, default_theme=DEFAULT_THEME)


@app.route("/generate", methods=["POST"])
def generate():
    prompt = request.form.get("prompt", "").strip()
    raw_data = request.form.get("raw_data", "").strip()
    theme_name = request.form.get("theme", DEFAULT_THEME).strip()
    accent_color = request.form.get("accent_color", "").strip() or None
    deck_title = request.form.get("deck_title", "").strip() or None
    slide_count_raw = request.form.get("target_slide_count", "").strip()
    target_slide_count = int(slide_count_raw) if slide_count_raw.isdigit() else None

    if not prompt or not raw_data:
        return render_template(
            "index.html",
            themes=THEMES,
            default_theme=DEFAULT_THEME,
            error="Please provide both instructions and the source data.",
        )

    try:
        pptx_buffer, deck_title_used = generate_deck(
            prompt=prompt,
            raw_data=raw_data,
            theme_name=theme_name,
            accent_override=accent_color,
            deck_title_override=deck_title,
            target_slide_count=target_slide_count,
        )
    except PlanValidationError:
        return render_template(
            "index.html",
            themes=THEMES,
            default_theme=DEFAULT_THEME,
            error="Couldn't produce a clean deck after retries. Try trimming the data or rephrasing the instructions.",
        )
    except RuntimeError as exc:
        return render_template(
            "index.html", themes=THEMES, default_theme=DEFAULT_THEME, error=str(exc)
        )
    except Exception:
        return render_template(
            "index.html",
            themes=THEMES,
            default_theme=DEFAULT_THEME,
            error="Something went wrong calling the Gemini API. Check the API key and try again.",
        )

    return send_file(
        pptx_buffer,
        mimetype="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        as_attachment=True,
        download_name=f"{_slugify(deck_title_used)}.pptx",
    )


if __name__ == "__main__":
    app.run(debug=True)
