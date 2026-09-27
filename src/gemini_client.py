"""Thin wrapper around the Gemini API for structured JSON generation.

This is the only module in the project that makes a network call or
invokes an LLM. Everything downstream of `generate_structured` operates
on a validated Pydantic object, not raw model output.
"""

from __future__ import annotations

import os

from google import genai
from google.genai import types
from pydantic import BaseModel

MODEL = "gemini-2.0-flash"

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Copy .env.example to .env and add your key "
                "(get one free at https://aistudio.google.com/apikey)."
            )
        _client = genai.Client(api_key=api_key)
    return _client


def generate_structured(prompt: str, schema: type[BaseModel]) -> BaseModel:
    """Call Gemini, constrained to return JSON matching `schema`, and parse it."""
    client = _get_client()
    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=schema,
        ),
    )
    return schema.model_validate_json(response.text)
