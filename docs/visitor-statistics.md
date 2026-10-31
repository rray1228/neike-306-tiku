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

The owner stopped historical recovery on 2026-10-31. The footer now shows
current daily UV and “本期累计”, explicitly dated “10月31日起”. These values
are real responses from the new provider and do not include earlier history.
They are not represented as complete historical totals.

The original `visitor-counts-v1` cache, original D1 visitor tables and recovery
snapshots are retained unchanged. The verified early database aggregate is in
`visitor-history-d1-20261031.json`; it is only the earliest counter. No guessed
baseline or additive merge has been applied.

Navigation no longer starts recovery requests. `/api/visitor-recovery` returns
410 with `stopped: true` and performs no database or external network calls.
The optional `?recoverStats=1#visitor-statistics` view only reads the existing
local cache, and states that recovery has stopped. It does not upload it.

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
