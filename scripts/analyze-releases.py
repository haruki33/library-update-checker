#!/usr/bin/env python3
"""Analyze unprocessed GitHub release notes with Gemini structured output."""

import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "public" / "data" / "releases.json"
MODEL = "gemini-2.5-flash"
API_ROOT = "https://generativelanguage.googleapis.com/v1beta/models"
MAX_ATTEMPTS = 3

SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "breaking": {"type": "BOOLEAN"},
        "impact": {"type": "STRING", "enum": ["high", "medium", "low"]},
        "migration": {
            "type": "OBJECT",
            "properties": {
                "required": {"type": "BOOLEAN"},
                "summary": {"type": "STRING"},
                "steps": {"type": "ARRAY", "items": {"type": "STRING"}},
            },
            "required": ["required", "summary", "steps"],
        },
        "changes": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "id": {"type": "STRING"},
                    "category": {"type": "STRING", "enum": ["feature", "bugfix", "performance", "breaking", "other"]},
                    "title": {"type": "STRING"},
                    "summary": {"type": "STRING"},
                    "impact": {"type": "STRING", "enum": ["high", "medium", "low"]},
                    "breaking": {"type": "BOOLEAN"},
                },
                "required": ["id", "category", "title", "summary", "impact", "breaking"],
            },
        },
    },
    "required": ["breaking", "impact", "migration", "changes"],
}


def request_analysis(api_key: str, record: dict) -> dict:
    url = f"{API_ROOT}/{MODEL}:generateContent?key={api_key}"
    prompt = f"""You are a software release analyst. Analyze the following GitHub Release Notes.

Library: {record['library']}
Version: {record['version']}
Release Notes:
{record.get('releaseNotes', '')}

Rules:
- Respond only with the requested structured JSON.
- Split the notes into meaningful individual changes; do not invent changes that are not supported by the notes.
- Write title and summary in concise Japanese.
- category must be feature, bugfix, performance, breaking, or other.
- impact means the likelihood that an application developer using this library must take action: high, medium, or low.
- breaking is true only when existing users may need code/configuration changes or behavior changes are explicitly breaking.
- migration.required is true only when users likely need migration work. Provide concrete steps only when justified by the notes.
- If the notes do not mention a migration, do not invent one.
- Each change id must be stable for this release and unique within the changes array.
"""
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": SCHEMA,
            "temperature": 0.1,
        },
    }
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json", "User-Agent": "library-update-checker"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        result = json.load(response)

    try:
        text = result["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(text)
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise ValueError("Gemini returned an invalid structured response") from exc


def validate_analysis(data: dict) -> None:
    if not isinstance(data, dict):
        raise ValueError("analysis must be an object")
    if not isinstance(data.get("breaking"), bool):
        raise ValueError("breaking must be boolean")
    if data.get("impact") not in {"high", "medium", "low"}:
        raise ValueError("impact must be high, medium, or low")
    migration = data.get("migration")
    if not isinstance(migration, dict) or not isinstance(migration.get("required"), bool):
        raise ValueError("invalid migration.required")
    if not isinstance(migration.get("summary"), str) or not isinstance(migration.get("steps"), list):
        raise ValueError("invalid migration payload")
    changes = data.get("changes")
    if not isinstance(changes, list):
        raise ValueError("changes must be an array")
    ids = set()
    for change in changes:
        if not isinstance(change, dict):
            raise ValueError("each change must be an object")
        for key in ("id", "category", "title", "summary"):
            if not isinstance(change.get(key), str) or not change[key].strip():
                raise ValueError(f"change.{key} must be a non-empty string")
        if change["category"] not in {"feature", "bugfix", "performance", "breaking", "other"}:
            raise ValueError("invalid change category")
        if change["impact"] not in {"high", "medium", "low"} or not isinstance(change["breaking"], bool):
            raise ValueError("invalid change impact/breaking")
        if change["id"] in ids:
            raise ValueError("duplicate change id")
        ids.add(change["id"])


def analyze_with_retry(api_key: str, record: dict) -> dict:
    last_error = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            data = request_analysis(api_key, record)
            validate_analysis(data)
            return data
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError) as exc:
            last_error = exc
            if attempt < MAX_ATTEMPTS:
                wait = 2 ** (attempt - 1)
                print(f"Analysis failed for {record['id']} (attempt {attempt}): {exc}; retrying in {wait}s")
                time.sleep(wait)
    raise RuntimeError(f"Gemini analysis failed for {record['id']}: {last_error}")


def main() -> None:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")

    releases = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    if not isinstance(releases, list):
        raise ValueError("releases.json must contain an array")

    changed = 0
    for record in releases:
        if not record.get("releaseNotes") or record.get("aiAnalyzed") is True:
            continue
        print(f"Analyzing {record['library']} {record['version']}...")
        analysis = analyze_with_retry(api_key, record)
        record.update(analysis)
        record["aiAnalyzed"] = True
        changed += 1

    if changed:
        DATA_PATH.write_text(json.dumps(releases, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Gemini analysis finished: {changed} release(s) analyzed.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
