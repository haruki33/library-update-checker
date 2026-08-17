#!/usr/bin/env python3
import os
import urllib.request

API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    raise SystemExit("GEMINI_API_KEY is not set")

url = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"
with urllib.request.urlopen(url, timeout=30) as response:
    if response.status != 200:
        raise SystemExit(f"Gemini model discovery failed: HTTP {response.status}")
print("Gemini API model discovery succeeded")
