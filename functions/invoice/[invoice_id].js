/**
 * Cloudflare Pages Function — proxy /invoice/:id to the webhook server so
 * invoice downloads stay under www.partcollector.com (clean masked URLs).
 *
 * All signature / expiry / ownership validation happens on the webhook side
 * (notifier.py /invoice/{invoice_id} route using INVOICE_SIGN_SECRET). This
 * function only forwards the request and streams the response back.
 */
export async function onRequestGet(context) {
  const { request, params } = context;
  const invoiceId = (params.invoice_id || '').toString();
  if (!invoiceId) {
    return new Response(JSON.stringify({ error: 'not_found' }), {
      status: 404,
      headers: { 'content-type': 'application/json' },
    });
  }

  // Rebuild the target URL under the webhook host, preserving the original
  // query string (?u=..&e=..&t=..) that carries the signed token.
  const url = new URL(request.url);
  const target = new URL(
    `/invoice/${encodeURIComponent(invoiceId)}`,
    'https://webhooks.partcollector.com'
  );
  target.search = url.search;

  try {
    const upstream = await fetch(target.toString(), {
      headers: {
        'User-Agent': request.headers.get('user-agent') || 'Cloudflare-Pages-Function',
        'Accept': '*/*',
      },
    });
    const body = await upstream.arrayBuffer();
    const headers = new Headers();
    const ct = upstream.headers.get('content-type');
    const cd = upstream.headers.get('content-disposition');
    if (ct) headers.set('content-type', ct);
    if (cd) headers.set('content-disposition', cd);
    return new Response(body, { status: upstream.status, headers });
  } catch (e) {
    return new Response(JSON.stringify({ error: 'upstream_error' }), {
      status: 502,
      headers: { 'content-type': 'application/json' },
    });
  }
}
