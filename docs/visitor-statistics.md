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

The user requires the entire history, including the later counter's reported
several hundred visits today. A new provider's small total must not be labelled
as that complete history. The normal footer therefore indicates historical
recovery is pending; if the current browser retains an original response, it
shows that untouched snapshot with an explicit recovery label. New recording
continues independently and is cached, so ongoing visits are not discarded.

`?recoverStats=1#visitor-statistics` opens a local-only backup inspection view.
It reads `visitor-counts-v1` without modifying or uploading that original cache.
The replacement counter's independent data is explicitly labelled separately.

The old D1 database remains intact. Its verified 152 distinct visitors and 177
daily entries are documented in `visitor-history-d1-20261031.json`. This is only
the earliest counter, not all later traffic on 2026-10-31. In particular it does
not disprove or replace the user's recollection of seven hundred plus visits.

`/api/visitor-recovery` tries the original public provider from the server's
network and retains a valid recovery snapshot in D1. Attempts are limited to
one per ten minutes, and page navigation can trigger a background attempt.
Successful payloads are preserved for metric verification. Values below the
user's reported historical range are preserved as evidence but cannot be
declared restored. The threshold is a sanity check, never a displayed count.
`?source=dashboard` reads the fixed original public statistics page from the
server, without accepting arbitrary target URLs. Neither operation changes the
original visitor tables. Recovery remains incomplete until the actual later
provider data is retrieved and reconciled; unreceived or unavailable records
must not be fabricated from memory, traffic estimates or a new small counter.

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
