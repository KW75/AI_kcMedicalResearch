"""Shared JSON extraction helpers for SR pipeline modules."""
import re
import json
import logging

logger = logging.getLogger(__name__)


def _try_parse(candidate: str):
    """Attempt json.loads; on failure try light repairs."""
    # Repair 1: trailing commas before } or ]
    repaired = re.sub(r",\s*([}\]])", r"\1", candidate)
    try:
        return json.loads(repaired)
    except json.JSONDecodeError:
        pass

    # Repair 2: add missing closing braces/brackets
    open_braces  = repaired.count("{") - repaired.count("}")
    open_brackets = repaired.count("[") - repaired.count("]")
    if open_braces > 0 or open_brackets > 0:
        padded = repaired.rstrip()
        padded += "]" * open_brackets + "}" * open_braces
        try:
            return json.loads(padded)
        except json.JSONDecodeError:
            pass

    # Repair 3: strip everything after the last complete key-value pair
    # by repeatedly removing the last line until it parses
    lines = repaired.splitlines()
    for trim in range(1, min(10, len(lines))):
        attempt = "\n".join(lines[:-trim]).rstrip().rstrip(",")
        # close open structures
        ob = attempt.count("{") - attempt.count("}")
        ob2 = attempt.count("[") - attempt.count("]")
        attempt += "]" * ob2 + "}" * ob
        try:
            return json.loads(attempt)
        except json.JSONDecodeError:
            continue

    raise json.JSONDecodeError("All repair attempts failed", repaired, 0)


def extract_json(raw: str) -> dict | list:
    """
    Robustly extract the first JSON object or array from a raw LLM response.

    Handles:
    - <think>...</think> preamble (DeepSeek reasoning mode)
    - ```json ... ``` or ``` ... ``` fences
    - Leading/trailing prose before the first { or [
    - Truncated responses (missing closing braces)
    - Trailing commas
    """
    if not raw or not raw.strip():
        raise ValueError("Empty response from model")

    # 1. Strip <think>...</think> blocks (DeepSeek chain-of-thought)
    raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()

    if not raw:
        raise ValueError("Empty response after stripping <think> blocks")

    # 2. Strip ```json ... ``` or ``` ... ``` fences
    fence = re.search(r"```(?:json)?\s*([\s\S]+?)```", raw)
    if fence:
        raw = fence.group(1).strip()

    # 3. Find the first { or [
    brace = raw.find("{")
    bracket = raw.find("[")
    if brace == -1 and bracket == -1:
        raise ValueError(f"No JSON object found in response: {raw[:200]}")

    if brace == -1:
        start = bracket
    elif bracket == -1:
        start = brace
    else:
        start = min(brace, bracket)

    raw = raw[start:]

    # 4. Try direct parse first (fastest path)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # 5. Try repairs
    try:
        return _try_parse(raw)
    except (json.JSONDecodeError, Exception) as e:
        raise ValueError(
            f"JSON repair failed: {e}\nCandidate (first 400 chars): {raw[:400]}"
        ) from e
