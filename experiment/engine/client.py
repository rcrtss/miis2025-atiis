"""Minimal OpenRouter client: raw REST over httpx, no provider SDK.

OpenRouter is a single OpenAI-compatible endpoint; we POST to it directly. The
expected JSON reply is validated with pydantic; transient failures (network or
malformed output) are retried with exponential backoff via tenacity.
"""

from __future__ import annotations

import json
import os
import re
import time

import httpx
from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from engine.config import OPENROUTER_URL

load_dotenv()


class BlameResponse(BaseModel):
    """The exact JSON contract the prompt asks the model to return.

    `inferred_probability`/`inferred_alpha` are always requested; `inferred_cost`
    is only present when the prompt carried a switch-cost sentence (no-voters),
    so it is optional and may be null for a yes-voter.
    """

    reasoning: str
    blameworthiness: int = Field(ge=0, le=100)
    inferred_probability: int = Field(ge=0, le=100)
    inferred_alpha: int = Field(ge=0, le=100)
    inferred_cost: int | None = Field(default=None, ge=0, le=100)


class LLMError(Exception):
    """Retryable failure: network error, bad HTTP status, or unparseable reply."""


def _extract_json(text: str) -> dict:
    """Best-effort JSON extraction: tolerate code fences and surrounding prose."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise LLMError(f"No JSON object in response: {text[:200]!r}")
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError as exc:
            raise LLMError(f"Malformed JSON in response: {text[:200]!r}") from exc


@retry(
    reraise=True,
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=1, min=1, max=20),
    retry=retry_if_exception_type(LLMError),
)
def call_model(prompt: str, *, model: str, temperature: float, timeout: float = 60.0) -> dict:
    """Send one prompt, return the parsed response plus raw text and latency."""
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise LLMError("OPENROUTER_API_KEY is not set (see .env.example).")

    payload = {
        "model": model,
        "temperature": temperature,
        "messages": [{"role": "user", "content": prompt}],
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    start = time.time()
    try:
        resp = httpx.post(OPENROUTER_URL, headers=headers, json=payload, timeout=timeout)
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        raise LLMError(f"HTTP error: {exc}") from exc
    latency = time.time() - start

    try:
        content = resp.json()["choices"][0]["message"]["content"]
    except (KeyError, IndexError, json.JSONDecodeError) as exc:
        raise LLMError(f"Unexpected response envelope: {resp.text[:200]!r}") from exc

    obj = _extract_json(content)
    try:
        parsed = BlameResponse.model_validate(obj)
    except ValidationError as exc:
        raise LLMError(f"Schema validation failed: {exc}") from exc

    return {
        "reasoning": parsed.reasoning,
        "blameworthiness": parsed.blameworthiness,
        "inferred_probability": parsed.inferred_probability,
        "inferred_alpha": parsed.inferred_alpha,
        "inferred_cost": parsed.inferred_cost,
        "raw": content,
        "latency": latency,
    }
