# Release collector

`collect-releases.py` reads enabled repositories from `config/libraries.json`, fetches their latest GitHub Releases, and merges new releases into `public/data/releases.json`.

## Local execution

```bash
python3 scripts/collect-releases.py
```

Set `GITHUB_TOKEN` when using a token-authenticated GitHub API request. The workflow uses the built-in `GITHUB_TOKEN` automatically.

The collector stores the original `releaseNotes` unchanged. AI classification and Japanese summaries are intentionally deferred to Phase 3.
