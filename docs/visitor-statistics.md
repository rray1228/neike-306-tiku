# Visitor statistics

On 2026-10-31 the `cdn.busuanzi.cc/api.php` service repeatedly timed out in
both real-browser requests and direct network checks. Rewording the error was
not a counting fix. Both editions now use the current official API from
soxft/busuanzi's client: `https://bsz.iirose.cn/api`.

References:
- https://busuanzi.9420.ltd/js (official client and current API URL)
- https://github.com/soxft/busuanzi/wiki/api (POST, GET and identity protocol)
- https://github.com/soxft/busuanzi/wiki/usage (server deduplication)

One POST supplies both values. `x-bsz-referer` identifies a shared logical
page at `https://rray1228.github.io/neike-306-tiku/__visitor_day__/YYYY-MM-DD`,
where the date is in Asia/Shanghai. The response's `page_uv` is therefore the
number of distinct visitors in that day's bucket; `site_uv` is cumulative
server-deduplicated UV. PV is never displayed as people. Both publications use
the same host and bucket. A response crossing midnight is retried for the new
day instead of being presented as today's count.

The service deduplicates using a server-signed visitor identity, IP and browser
UserAgent. Its `Set-Bsz-Identity` response is retained under the dedicated
`visitor-identity-soxft-v1` key and sent as `Authorization: Bearer ...` to this
service alone. Without storage, the in-memory identity and the server's
IP/browser fallback still work. No actual page query, search terms, answers,
notes, referring page, old UUID or other service credential is sent. No external
JavaScript is executed. CORS preflight and real POST responses were checked
from both production origins, including repeat UV deduplication.

This is a new provider and starts counting at the switch. Old service numbers,
the old D1 database and their browser records are neither deleted nor added to
this provider's totals. Unreceived visits cannot be reconstructed. The footer
shows only the current daily and cumulative counts, with no old-statistics row.

Requests time out after eight seconds, share one in-flight request and reuse
successes for one minute. Successful responses are also cached for seven days
under a provider-specific key, so old-provider numbers cannot flash as new
counts. Earlier-day daily cache values display a dash; stale cumulative values
are labelled as not updated. Invalid, future, expired and other-site caches are
ignored. A cache is only a previous response, never a locally incremented count.

Failures retry with bounded backoff, on reconnect and when the page becomes
visible. The footer offers manual retry, and honestly reports unavailability if
neither the service nor a cache is available. Public services have no guaranteed
availability; the application does not fabricate counts during an outage.
