#!/usr/bin/env bash
set -euo pipefail
REPO="kylehawkinsa/true-probability-hammer-public"
cd "$(dirname "$0")"
for path in app.py tph_core.py requirements.txt .github/workflows/verify.yml .streamlit/config.toml; do
  if [[ ! -f "$path" ]]; then echo "Missing required source: $path" >&2; exit 1; fi
done
if ! command -v gh >/dev/null 2>&1; then
  echo 'GitHub CLI not found. Install from https://cli.github.com/ then rerun.' >&2; exit 1
fi
if ! gh auth status >/dev/null 2>&1; then
  echo 'Authenticate your own GitHub account to continue.'
  gh auth login --hostname github.com --web
fi
ACCOUNT="$(gh api user --jq .login)"
if [[ "$ACCOUNT" != "kylehawkinsa" ]]; then
  echo "Wrong GitHub account: $ACCOUNT. Expected kylehawkinsa." >&2; exit 1
fi
if gh repo view "$REPO" >/dev/null 2>&1; then
  echo "Refusing to change an existing repository: $REPO" >&2; exit 1
fi
python -m unittest discover -s tests -v
python -m compileall -q app.py tph_core.py odds_worker.py storage.py publish_forecasts.py setup_password.py
if [[ -d .git ]]; then
  echo 'Refusing to create a new repository from an existing Git checkout.' >&2; exit 1
fi
if [[ -f .streamlit/secrets.toml || -f .env ]]; then
  echo 'Refusing public publishing with private credential files present.' >&2; exit 1
fi
git init -b main
git add .
if git diff --cached --name-only | grep -E '(^|/)(secrets[.]toml|[.]env|[.]git-credentials|id_rsa|id_ed25519)$'; then
  echo 'Refusing to publish secrets.' >&2; exit 1
fi
git commit -m 'Publish True Probability Hammer research portal source'
gh repo create "$REPO" --public --source . --remote origin --push
echo "Published: https://github.com/$REPO"
echo 'NOTE: Streamlit deployment not activated, private sharing must be configured separately.'
