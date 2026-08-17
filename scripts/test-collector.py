#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
config = json.loads((ROOT / "config" / "libraries.json").read_text(encoding="utf-8"))
releases = json.loads((ROOT / "public" / "data" / "releases.json").read_text(encoding="utf-8"))

assert isinstance(config, list) and len(config) == 18
assert len({item["github"] for item in config}) == len(config)
for item in config:
    assert set(item) == {"name", "github", "enabled"}
    assert isinstance(item["name"], str) and item["name"]
    assert isinstance(item["github"], str) and "/" in item["github"]
    assert isinstance(item["enabled"], bool)

assert isinstance(releases, list)
ids = [item.get("id") for item in releases]
assert len(ids) == len(set(ids))

for item in releases:
    for key in ("library", "version", "publishedAt", "url"):
        assert key in item

print("collector data validation passed")
