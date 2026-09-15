#!/usr/bin/env python3
"""
Generate /annual-plans for the Part Collector site from the existing legal-page
shell (so the styling is byte-identical) and register the pretty-URL rewrite.

The page exists because the annual plan is the only rail that carries the
Corporate Seller tier, and it needs a public, linkable description.

Safe by construction:
  * the shell of refund-policy.html is reused verbatim (head + styles + footer);
  * only the block between the card's <h1> and the footer is replaced;
  * both copies are written (the site serves /annual-plans from the
    /annual-plans/index.html copy, but the .html file is also reachable);
  * nothing existing is modified except appending one line to _redirects.
"""
import pathlib
import re
import sys

W = pathlib.Path('/home/ubuntu/website')

BODY = '''<h1>Annual Plans</h1>
\t\t\t<p class="legal-meta">A full year of access &nbsp;&middot;&nbsp; billed as 12 monthly instalments &nbsp;&middot;&nbsp; prices exclude VAT</p>

\t\t\t<div class="legal-highlight">
\t\t\t\t<strong>Annual plans are billed by us directly through PayPal</strong> as twelve equal monthly instalments &mdash; there is no large upfront payment. An annual plan opens exactly the same selling tools and grants the same community role as the monthly plan, and is a twelve-month commitment.
\t\t\t</div>

\t\t\t<h2>The annual ladder</h2>
\t\t\t<div class="table-wrapper">
\t\t\t\t<table>
\t\t\t\t\t<thead>
\t\t\t\t\t\t<tr><th>Tier</th><th>Active listings</th><th>Per month</th><th>Per year</th><th>You save</th></tr>
\t\t\t\t\t</thead>
\t\t\t\t\t<tbody>
\t\t\t\t\t\t<tr><td>Essential Seller</td><td>250</td><td>&euro;4.94</td><td><strong>&euro;59.28</strong></td><td>10%</td></tr>
\t\t\t\t\t\t<tr><td>Pro Seller</td><td>2,000</td><td>&euro;18.69</td><td><strong>&euro;224.28</strong></td><td>15%</td></tr>
\t\t\t\t\t\t<tr><td>Elite Seller</td><td>15,000</td><td>&euro;43.99</td><td><strong>&euro;527.88</strong></td><td>20%</td></tr>
\t\t\t\t\t\t<tr><td>Power Seller</td><td>100,000</td><td>&euro;150.00</td><td><strong>&euro;1,800.00</strong></td><td>25%</td></tr>
\t\t\t\t\t\t<tr><td>Corporate Seller</td><td>Unlimited</td><td>&euro;280.00</td><td><strong>&euro;3,360.00</strong></td><td>30%</td></tr>
\t\t\t\t\t</tbody>
\t\t\t\t</table>
\t\t\t</div>
\t\t\t<p>Each annual plan is exactly twelve instalments &mdash; the yearly figure is twelve times the monthly amount shown &mdash; so the total never rounds up beyond the price in the table.</p>

\t\t\t<h2>Monthly prices, for comparison</h2>
\t\t\t<p>Essential Seller <strong>&euro;5.49</strong> &middot; Pro Seller <strong>&euro;21.99</strong> &middot; Elite Seller <strong>&euro;54.99</strong> &middot; Power Seller <strong>&euro;200.00</strong> per month. The <strong>Corporate Seller</strong> tier is an annual plan only &mdash; it has no monthly option.</p>

\t\t\t<h2>VAT</h2>
\t\t\t<ul>
\t\t\t\t<li><strong>Sellers in the EU (private):</strong> VAT is added at your own country&rsquo;s rate under the EU One-Stop-Shop scheme, so the total depends on where you are established.</li>
\t\t\t\t<li><strong>EU businesses with a valid VAT number (VIES):</strong> no VAT is charged &mdash; reverse charge applies.</li>
\t\t\t\t<li><strong>Sellers outside the EU:</strong> no VAT is charged.</li>
\t\t\t</ul>
\t\t\t<p>The prices above exclude VAT. Your exact total, including VAT where it applies, is shown before you confirm any payment.</p>

\t\t\t<h2>What every tier includes</h2>
\t\t\t<ul>
\t\t\t\t<li>The tier role in the community server, granted as soon as the subscription starts.</li>
\t\t\t\t<li>The listing allowance shown above &mdash; unlimited on the Corporate tier.</li>
\t\t\t\t<li>Bulk listing management with the Excel (.xlsx) import and export tools.</li>
\t\t\t\t<li>Help from the Part Collector team in the community server.</li>
\t\t\t</ul>

\t\t\t<h2>How to subscribe</h2>
\t\t\t<ol>
\t\t\t\t<li>Open the Discord server and go to the <strong>Subscription Setup</strong> section.</li>
\t\t\t\t<li>Choose your tier and press the <strong>Yearly</strong> button &mdash; it shows the monthly instalment you will pay before you approve anything.</li>
\t\t\t\t<li>Approve the PayPal agreement. Your role and listing allowance activate within minutes.</li>
\t\t\t</ol>
\t\t\t<p>Monthly plans can be started in the same place at any time.</p>

\t\t\t<h2>Early exit and refunds</h2>
\t\t\t<p>An annual plan is a twelve-month commitment. Cancelling or downgrading before the final month may incur an <strong>Early Termination Fee of one third of the remaining instalments</strong>, which is shown to you before you confirm. Subscription payments are non-refundable once a billing period has begun, and you keep full access until the end of the period you have already paid for. See the <a href="/refund-policy">Refund &amp; Cancellation Policy</a> and our <a href="/terms">Seller Terms</a> for full detail.</p>
'''

TITLE = '<title>Annual Plans | Part Collector</title>'
DESC = ('<meta name="description" content="Annual plans for Part Collector sellers &mdash; a full year of access '
        'billed as twelve monthly instalments through PayPal. Prices exclude VAT." />')
CANON = '<link rel="canonical" href="https://www.partcollector.com/annual-plans" />'

SHELLS = [('refund-policy.html', 'annual-plans.html'),
          ('refund-policy/index.html', 'annual-plans/index.html')]


def build(src_name: str, dst_name: str) -> pathlib.Path:
    src = W / src_name
    text = src.read_text(encoding='utf-8')
    if '<h1>' not in text or '<!-- Footer -->' not in text:
        raise SystemExit(f'shell markers not found in {src_name}')

    head = text.split('<h1>', 1)[0]               # head + styles + logo, up to the h1
    tail = text[text.index('<!-- Footer -->'):]   # footer + closing tags, verbatim

    for pattern, repl in ((r'<title>.*?</title>', TITLE),
                          (r'<meta name="description" content=".*?" />', DESC),
                          (r'<link rel="canonical" href=".*?" />', CANON)):
        head, n = re.subn(pattern, repl, head, count=1, flags=re.S)
        if n != 1:
            raise SystemExit(f'{pattern!r} not found in {src_name}')

    out = head + BODY + '\n\t\t' + tail
    dst = W / dst_name
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(out, encoding='utf-8')
    return dst


def main() -> int:
    for src, dst in SHELLS:
        p = build(src, dst)
        print(f'  wrote {p.relative_to(W)}  {p.stat().st_size} bytes')

    # pretty URL (same pattern as the other legal pages)
    rd = W / '_redirects'
    line = '/annual-plans  /annual-plans/index.html  200'
    text = rd.read_text(encoding='utf-8')
    if line in text:
        print('  _redirects already has the rewrite')
    else:
        rd.write_text(text.rstrip('\n') + '\n' + line + '\n', encoding='utf-8')
        print('  _redirects: added /annual-plans')
    return 0


if __name__ == '__main__':
    sys.exit(main())
