#!/usr/bin/env bash
# Assembles the public site into ./_site (used by Cloudflare Pages; mirrors .github/workflows/pages.yml).
# Only the files visitors need are copied: no tests, tools or repo docs.
set -euo pipefail
cd "$(dirname "$0")/.."
rm -rf _site && mkdir -p _site
cp index.html welcome.html LICENSE _site/
cp -r vendor fonts welcome _site/
[ -d templates ] && cp -r templates _site/ || true
touch _site/.nojekyll
echo "site assembled: $(find _site -type f | wc -l) files, $(du -sh _site | cut -f1)"
