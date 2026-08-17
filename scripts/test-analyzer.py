#!/usr/bin/env python3
import importlib.util
from pathlib import Path

path = Path(__file__).with_name("analyze-releases.py")
spec = importlib.util.spec_from_file_location("analyzer", path)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)

valid = {
    "breaking": True,
    "impact": "high",
    "migration": {"required": True, "summary": "APIを置き換える", "steps": ["検索", "置換", "テスト"]},
    "changes": [
        {
            "id": "release-api",
            "category": "breaking",
            "title": "APIを変更",
            "summary": "既存APIの仕様が変更された",
            "impact": "high",
            "breaking": True,
        }
    ],
}
module.validate_analysis(valid)

invalid = {**valid, "impact": "critical"}
try:
    module.validate_analysis(invalid)
except ValueError:
    pass
else:
    raise AssertionError("invalid impact was accepted")

print("Analyzer schema validation passed.")
