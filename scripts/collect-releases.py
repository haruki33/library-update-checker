#!/usr/bin/env python3
"""Collect GitHub releases for enabled libraries into releases.json.

Phase 2 deliberately stores the original release notes. AI interpretation is
handled separately in Phase 3.
"""

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "libraries.json"
DATA_PATH = ROOT / "public" / "data" / "releases.json"
API_ROOT = "https://api.github.com/repos"


def github_get(url: str):
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "library-update-checker",
    }
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API failed ({exc.code}) for {url}: {body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"GitHub API request failed for {url}: {exc.reason}") from exc


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def release_to_record(library: dict, release: dict) -> dict:
    return {
        "id": f"{library['github']}#{release['id']}",
        "library": library["name"],
        "repository": library["github"],
        "version": release["tag_name"],
        "publishedAt": release["published_at"] or release["created_at"],
        "url": release["html_url"],
        "releaseNotes": release.get("body") or "",
        "breaking": False,
        "impact": "low",
        "migration": {
            "required": False,
            "summary": "",
            "steps": [],
        },
        "changes": [],
    }


def collect_library(library: dict):
    url = f"{API_ROOT}/{library['github']}/releases?per_page=30"
    releases = github_get(url)
    return [release_to_record(library, release) for release in releases if not release.get("draft")]


def main():
    config = load_json(CONFIG_PATH)
    existing = load_json(DATA_PATH)
    if not isinstance(existing, list):
        raise ValueError("public/data/releases.json must contain an array")

    existing_by_id = {item["id"]: item for item in existing if item.get("id")}
    collected = []

    for library in config:
        if not library.get("enabled", True):
            continue
        if not library.get("name") or not library.get("github"):
            raise ValueError("Each library must have name, github, and enabled fields")
        print(f"Collecting {library['name']} ({library['github']})...")
        collected.extend(collect_library(library))

    new_count = 0
    for record in collected:
        if record["id"] not in existing_by_id:
            existing_by_id[record["id"]] = record
            new_count += 1

    merged = list(existing_by_id.values())
    merged.sort(key=lambda item: item.get("publishedAt", ""), reverse=True)

    DATA_PATH.write_text(
        json.dumps(merged, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    now = datetime.now(timezone.utc).isoformat()
    print(f"Collection finished at {now}: {new_count} new releases, {len(merged)} total.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
