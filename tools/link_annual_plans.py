#!/usr/bin/env python3
"""
Link /annual-plans from the site: add it to the homepage nav and to the
'policy-links' footer of every page that has one.

Idempotent and additive: it inserts one <a> (plus its separator) inside the
existing policy-links block, or one <li> in the nav; it never rewrites or
removes anything else. Files already containing the link are reported and left
alone.

Usage:  python3 tools/link_annual_plans.py
"""
import pathlib
import re
import sys

W = pathlib.Path(__file__).resolve().parent.parent
LINK = '<a href="/annual-plans">Annual Plans</a>'


def _read(path: pathlib.Path):
    """Read as UTF-8 WITHOUT newline translation, and report the file's newline."""
    raw = path.read_bytes()
    nl = '\r\n' if b'\r\n' in raw else '\n'
    return raw.decode('utf-8'), nl


def _write(path: pathlib.Path, text: str) -> None:
    path.write_bytes(text.encode('utf-8'))


# NOTE: patterns accept \r?\n — several pages in this repo are CRLF, and reading them
# with Path.read_text()/write_text() would silently convert them to LF (whole-file diff).
FOOTER_RE = re.compile(
    r'([ \t]+)(<a href="/refund-policy">Refund &amp; Cancellation</a>\r?\n)([ \t]*</div>)'
)
NAV_RE = re.compile(r'([ \t]*)<li><a href="coverage\.html">Coverage</a></li>\r?\n')


def add_footer_link(path: pathlib.Path) -> str:
    text, nl = _read(path)
    if 'class="policy-links"' not in text:
        return 'no-footer'
    if 'href="/annual-plans"' in text:
        return 'already'
    new, n = FOOTER_RE.subn(
        lambda m: (f'{m.group(1)}{m.group(2)}{m.group(1)}'
                   f'<span style="opacity:0.3">&middot;</span>{nl}'
                   f'{m.group(1)}{LINK}{nl}{m.group(3)}'),
        text, count=1)
    if n != 1:
        return 'NO-MATCH'
    _write(path, new)
    return 'linked'


def add_nav_link(path: pathlib.Path) -> str:
    text, nl = _read(path)
    if '<nav>' not in text:
        return 'no-nav'
    if 'href="/annual-plans"' in text:
        return 'already'
    new, n = NAV_RE.subn(
        lambda m: f'{m.group(1)}<li><a href="/annual-plans">Plans</a></li>{nl}' + m.group(0),
        text, count=1)
    if n != 1:
        return 'NO-MATCH'
    _write(path, new)
    return 'linked'


def main() -> int:
    print('--- footers ---')
    counts = {}
    for p in sorted(W.rglob('*.html')):
        if '.git' in p.parts:
            continue
        res = add_footer_link(p)
        if res not in ('no-footer',):
            counts[res] = counts.get(res, 0) + 1
            print(f'  {res:9} {p.relative_to(W)}')
    print('--- nav ---')
    res = add_nav_link(W / 'index.html')
    counts[res] = counts.get(res, 0) + 1
    print(f'  {res:9} index.html')
    print('--- summary ---', counts)
    return 0 if counts.get('NO-MATCH', 0) == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
