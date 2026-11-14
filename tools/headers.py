#!/usr/bin/env python3
"""Security headers for the public site (Cloudflare Pages `_headers`).

The Content-Security-Policy allows only Shoof's own files plus the exact inline
scripts in the editor and the landing page (matched by SHA-256 hash), so an
injected <script> can never run. Turnstile (Cloudflare's free bot check) is
the only outside site allowed. The tests serve the editor with this same
policy, so any feature that breaks under it fails the suite.

  python3 tools/headers.py            -> prints the _headers file
  python3 tools/headers.py OUT_FILE   -> writes it
"""
import base64, hashlib, os, re, sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
PAGES = ['index.html', 'welcome.html']
TURNSTILE = 'https://challenges.cloudflare.com'


def inline_hashes(paths=PAGES):
    out = []
    for p in paths:
        html = open(os.path.join(ROOT, p), encoding='utf-8').read()
        for body in re.findall(r'<script>(.*?)</script>', html, re.S):
            h = "'sha256-" + base64.b64encode(hashlib.sha256(body.encode('utf-8')).digest()).decode() + "'"
            if h not in out:
                out.append(h)
    return out


def csp():
    return '; '.join([
        "default-src 'self'",
        "script-src 'self' 'wasm-unsafe-eval' " + ' '.join(inline_hashes()) + ' ' + TURNSTILE,
        "style-src 'self' 'unsafe-inline'",
        "img-src 'self' data: blob:",
        "font-src 'self' data:",
        "connect-src 'self' data: blob:",
        "worker-src 'self' blob:",
        "frame-src " + TURNSTILE,
        "manifest-src 'self'",
        "object-src 'none'",
        "base-uri 'none'",
        "form-action 'self'",
        "frame-ancestors 'none'",
        "upgrade-insecure-requests",
    ])


HEADERS = {
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'Referrer-Policy': 'strict-origin-when-cross-origin',
    'Permissions-Policy': 'camera=(), microphone=(), geolocation=(), payment=(), usb=(), interest-cohort=()',
    'Cross-Origin-Opener-Policy': 'same-origin',
}


def headers_file():
    lines = ['/*'] + [f'  {k}: {v}' for k, v in HEADERS.items()] + [f'  Content-Security-Policy: {csp()}', '']
    return '\n'.join(lines)


if __name__ == '__main__':
    text = headers_file()
    if len(sys.argv) > 1:
        open(sys.argv[1], 'w').write(text)
        print('wrote', sys.argv[1], f'({len(inline_hashes())} inline scripts pinned)')
    else:
        print(text)
