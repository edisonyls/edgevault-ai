"""One-shot diagnostic for the Pi's chat model.

The RAG eval swallows HTTP errors (returns None and scores an empty snapshot),
which hides *why* a call failed. This sends a single tiny extraction prompt
straight to the configured endpoint and prints the raw status, latency, and body
— so you can tell a model problem (echoes / bad JSON in a 200 response) from a
serving problem (timeout, 400, 500, connection refused), and whether the server
supports JSON mode (``response_format``).

Usage:
    uv run python scripts/probe_llm.py
"""

import asyncio
import json
import sys
import time
from pathlib import Path

import httpx

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import get_settings  # noqa: E402

SYSTEM = (
    'Extract fields from the document. Output ONLY one JSON object with keys '
    '"vendor" (string|null) and "total_amount" (number-string|null). No prose.'
)
USER = (
    "Document:\n"
    "WOOLWORTHS METRO\n"
    "Milk 2L 3.50\n"
    "Bread 4.20\n"
    "TOTAL 7.70\n"
    "EFTPOS APPROVED\n\n"
    "Answer:"
)


async def probe(
    client: httpx.AsyncClient, url: str, payload: dict, label: str
) -> None:
    print(f"\n--- {label} ---")
    extras = {k: v for k, v in payload.items() if k != "messages"}
    print(f"payload extras: {extras}")
    start = time.monotonic()
    try:
        response = await client.post(url, json=payload)
    except httpx.HTTPError as error:
        elapsed = time.monotonic() - start
        print(
            f"REQUEST FAILED after {elapsed:.1f}s: {type(error).__name__}: {error!r}")
        return

    elapsed = time.monotonic() - start
    print(f"status: {response.status_code}  latency: {elapsed:.1f}s")
    body = response.text
    print(f"raw body (first 800 chars):\n{body[:800]}")
    try:
        content = response.json()["choices"][0]["message"]["content"]
    except (KeyError, IndexError, ValueError):
        print(">> could not read choices[0].message.content")
        return
    print(f"\nmodel content:\n{content!r}")
    try:
        json.loads(content)
        print(">> content parses as JSON: YES")
    except ValueError:
        print(">> content parses as JSON: NO")


async def main() -> None:
    settings = get_settings()
    url = f"{settings.assistant_llm_base_url.rstrip('/')}/chat/completions"
    model = settings.assistant_llm_model
    print(f"endpoint: {url}")
    print(f"model: {model}")

    base = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": USER},
        ],
        "temperature": 0,
        "max_tokens": 128,
    }
    json_mode = {**base, "response_format": {"type": "json_object"}}

    async with httpx.AsyncClient(timeout=120.0) as client:
        await probe(client, url, base, "plain (no response_format)")
        await probe(client, url, json_mode, "json mode (response_format)")
        await context_ladder(client, url, model)


def _receipt_filler(chars: int) -> str:
    """Receipt-like filler (newlines, numbers, $) so the prompt resembles a real
    RAG call rather than a wall of one repeated word."""
    line = "Item {n} description here .... ${n}.50\n"
    body = "".join(line.format(n=i) for i in range(1, chars // 36 + 2))
    return f"STORE NAME PTY LTD\n{body[:chars]}\nTOTAL 123.45\n"


async def context_ladder(client: httpx.AsyncClient, url: str, model: str) -> None:
    """Plain vs JSON mode at increasing sizes. The plain ladder already passed to
    8000 chars, so a length ceiling is ruled out — this isolates whether JSON mode
    (response_format) is what 500s on the larger, structured RAG prompt."""
    print("\n=== plain vs JSON mode at increasing sizes ===")
    system = (
        "Extract fields. Output ONLY one JSON object with keys "
        '"vendor" (string|null) and "total_amount" (number-string|null). No prose.'
    )
    modes = (
        ("plain", {}),
        ("json ", {"response_format": {"type": "json_object"}}),
    )
    for chars in (2000, 4000, 5000, 6000, 7000):
        user = f"{_receipt_filler(chars)}\n\nAnswer:"
        for label, extra in modes:
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "temperature": 0,
                "max_tokens": 200,
                **extra,
            }
            start = time.monotonic()
            try:
                response = await client.post(url, json=payload)
            except httpx.HTTPError as error:
                print(f"~{chars:>5} chars  {label}: FAILED "
                      f"{type(error).__name__}: {error!r}")
                continue
            elapsed = time.monotonic() - start
            note = ""
            if response.status_code != 200:
                note = f"  body: {response.text[:160]}"
            print(f"~{chars:>5} chars  {label}: status "
                  f"{response.status_code}  {elapsed:.1f}s{note}")


if __name__ == "__main__":
    asyncio.run(main())
