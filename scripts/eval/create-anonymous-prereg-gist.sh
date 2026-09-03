#!/usr/bin/env bash
# create-anonymous-prereg-gist.sh
#
# One-time script to publish the v5 §4.5 pre-registration to a public
# GitHub Gist for double-blind integrity. Run this from a shell session
# that is NOT logged in to your primary GitHub account.
#
# Pre-requisites:
#   1. Create a fresh GitHub account that has NO connection to the
#      codermillat namespace (use a different email, different username).
#      The account should have no public repos, no follows, no activity
#      that would link back to your real identity.
#   2. From that account, generate a personal access token (classic) with
#      the `gist` scope only:
#         https://github.com/settings/tokens/new
#         Note: <something-anonymous>
#         Expiration: 90 days (or whatever; just longer than Feb 2027)
#         Scopes: [x] gist
#         (Do NOT enable repo, workflow, or any other scope.)
#   3. Export the token in this terminal:
#         export GITHUB_GIST_TOKEN=ghp_xxxxxxxxxxxxxxxx
#
# Then run this script. The script will:
#   - Read the Gist content from /tmp/v5-prereg-gist.md
#   - POST it to the GitHub Gists API as a PUBLIC single-file Gist
#   - Print the resulting Gist URL
#   - Save the URL to /tmp/v5-gist-url.txt for easy reference
#
# The Gist will be:
#   - Public (so reviewers can read it during the review phase)
#   - Single file (the pre-registration content)
#   - Anonymous (created from the throwaway account)
#   - Time-stamped by GitHub (the gist creation time is public)
#   - Retrievable by SHA forever (gist IDs are stable)

set -euo pipefail

if [ -z "${GITHUB_GIST_TOKEN:-}" ]; then
    echo "ERROR: GITHUB_GIST_TOKEN env var is not set." >&2
    echo "Create a token at https://github.com/settings/tokens/new (gist scope only)" >&2
    echo "from an anonymous account, then: export GITHUB_GIST_TOKEN=ghp_..." >&2
    exit 1
fi

GIST_FILE="/tmp/v5-prereg-gist.md"
if [ ! -f "$GIST_FILE" ]; then
    echo "ERROR: $GIST_FILE not found. Run the build step first to create it." >&2
    exit 1
fi

# The "files" object in the Gist API expects {filename: {content: "..."}}
PAYLOAD=$(python3 -c "
import json
with open('$GIST_FILE') as f:
    content = f.read()
payload = {
    'description': 'v5 §4.5 Stratified Causal Test — Pre-Registration (NAACL 2027 BEA Workshop)',
    'public': True,
    'files': {
        '2026-09-02-stratified-causal-test.md': {'content': content}
    }
}
print(json.dumps(payload))
")

echo "Creating Gist (this may take a few seconds)..."
RESPONSE=$(curl -sS -X POST \
    -H "Authorization: token $GITHUB_GIST_TOKEN" \
    -H "Accept: application/vnd.github+json" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD" \
    https://api.github.com/gists)

GIST_URL=$(echo "$RESPONSE" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('html_url',''))" 2>/dev/null || echo "")

if [ -z "$GIST_URL" ]; then
    echo "ERROR: Failed to create Gist. Response was:" >&2
    echo "$RESPONSE" >&2
    exit 1
fi

echo "$GIST_URL" | tee /tmp/v5-gist-url.txt
echo
echo "Gist URL saved to /tmp/v5-gist-url.txt"
echo
echo "Next steps:"
echo "  1. Open the URL above in a browser and confirm the content is correct"
echo "  2. Add the URL to paper/v5-draft.tex §4.5 footnote (and remove the 'Gist' "
echo "     mention that says it will be added at submission time)"
echo "  3. Recompile the paper: cd paper && pdflatex v5-draft.tex"
echo "  4. Commit and push the paper update"
echo
echo "DO NOT push the Gist URL or any identifying info to the codermillat repo"
echo "before the camera-ready version is accepted (the supplementary is the only"
echo "place the Gist URL should appear, and it is anonymized until then)."
