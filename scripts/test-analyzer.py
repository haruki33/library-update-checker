#!/usr/bin/env python3
import importlib.util
from pathlib import Path
from unittest.mock import patch

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

assert module._is_retryable_error(RuntimeError("HTTP 503: unavailable"))
assert module._is_retryable_error(RuntimeError("HTTP 429: rate limited"))
assert not module._is_retryable_error(RuntimeError("HTTP 400: bad request"))

record = {"id": "react-router-6.30.6", "library": "React Router", "version": "6.30.6"}
with patch.object(module, "request_analysis", side_effect=[RuntimeError("HTTP 503: unavailable"), valid]) as request_mock:
    with patch.object(module.time, "sleep") as sleep_mock:
        result = module.analyze_with_retry("test-key", "models/gemini-3.6-flash", record)

assert result == valid
assert request_mock.call_count == 2
sleep_mock.assert_called_once_with(10)

print("Analyzer schema validation and transient-error retry tests passed.")
