#!/usr/bin/env python3
import json
from pathlib import Path

LIBUARYS_COUNT = 22

import importlib.util

ROOT = Path(__file__).resolve().parents[1]
config = json.loads((ROOT / "config" / "libraries.json").read_text(encoding="utf-8"))
excluded_words = json.loads((ROOT / "config" / "excluded_words.json").read_text(encoding="utf-8"))
releases = json.loads((ROOT / "public" / "data" / "releases.json").read_text(encoding="utf-8"))

assert isinstance(config, list) and len(config) == LIBUARYS_COUNT
assert len({item["github"] for item in config}) == len(config)
for item in config:
    assert set(item) == {"name", "github", "enabled"}
    assert isinstance(item["name"], str) and item["name"]
    assert isinstance(item["github"], str) and "/" in item["github"]
    assert isinstance(item["enabled"], bool)

# excluded_words validation
assert isinstance(excluded_words, list) and len(excluded_words) > 0
for word in excluded_words:
    assert isinstance(word, str) and len(word.strip()) > 0

# collector module unit test
spec = importlib.util.spec_from_file_location("collector", ROOT / "scripts" / "collect-releases.py")
collector = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(collector)

assert collector.is_version_excluded("@tanstack/solid-query@5.0.0", ["solid"]) is True
assert collector.is_version_excluded("v1.0.0-beta.1", ["beta"]) is True
assert collector.is_version_excluded("v1.0.0-RC.1", ["rc"]) is True
assert collector.is_version_excluded("v1.0.0", ["beta", "rc"]) is False
assert collector.is_version_excluded("", ["beta"]) is False
assert collector.is_version_excluded("v1.0.0", []) is False

assert isinstance(releases, list)
ids = [item.get("id") for item in releases]
assert len(ids) == len(set(ids))

for item in releases:
    for key in ("library", "version", "publishedAt", "url"):
        assert key in item
    assert not collector.is_version_excluded(item["version"], excluded_words), f"Excluded version found: {item['version']}"

print("collector data validation passed")
