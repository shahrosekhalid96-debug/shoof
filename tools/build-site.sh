#!/usr/bin/env bash
# Assembles the public site into ./_site (used by Cloudflare Pages; mirrors .github/workflows/pages.yml).
# Only the files visitors need are copied: no tests, tools or repo docs.
set -euo pipefail
cd "$(dirname "$0")/.."
rm -rf _site && mkdir -p _site
# front door: the landing page is the home page, the editor lives at /editor (editor.html)
cp index.html _site/editor.html
cp welcome.html _site/index.html
cp welcome.html LICENSE manifest.webmanifest sw.js _site/
cp -r vendor fonts welcome icons _site/
# the free AI writer (Cloudflare Pages Function) is read from ./functions by Cloudflare itself; nothing to copy
[ -d templates ] && cp -r templates _site/ || true
touch _site/.nojekyll
echo "site assembled: $(find _site -type f | wc -l) files, $(du -sh _site | cut -f1)"
