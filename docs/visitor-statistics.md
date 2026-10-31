# Visitor statistics

Since 2026-10-31, both public editions use the same Busuanzi counter at
`https://cdn.busuanzi.cc/api.php`. The canonical site key is
`https://rray1228.github.io/neike-306-tiku/`.

The browser makes a simple CORS POST directly to the independent service.
It sends only that fixed public URL and an empty referrer. It sends no search
parameters, practice answers, notes, old browser identifiers or cookies. No
third-party script is executed. See the provider's current usage documentation:
https://www.busuanzi.cc/doc.php

The footer uses the provider's `busuanzi_today_uv` and `busuanzi_site_uv` fields,
not PV or a fabricated browser-local increment. The provider deduplicates by
IP and its own server-side rules; this differs from the old UUID-in-localStorage
counter. Switching VPNs may change the provider's visitor identity. The two
definitions must not be added together.

The old D1 tables and handler remain intact. A read-only snapshot of
`site_visitors` contained **152** records at **2026-10-31 09:11 Asia/Shanghai**.
The footer only shows the current provider's daily and cumulative counts;
the historical snapshot is not displayed. No prior visitor IDs
were transferred to the new provider. Visits that never reached the old
endpoint cannot be reconstructed.

Requests have an eight-second timeout, share one in-flight request, and cache
successful results for one minute. Network failures retry with a bounded
backoff; reconnecting or returning to the page also retries. Previously received
numbers are labelled as not updated if refresh fails. A failure never displays
zero or increments counts locally. The client still cannot guarantee delivery
during a complete network outage or blocking of the replacement service.

Successful service responses are also cached in the current browser for up to
seven days, keyed to this site's counter. Reloading can display the last received
values while reconnecting, marked as not updated. A daily value from an earlier
Shanghai date is shown as a dash, never as today's count. Corrupt, future-dated,
expired or other-site cache entries are ignored. No cache entry is a visitor ID.
Without a valid response or cache, failures show “统计暂不可用” with a retry
button instead of claiming to be continuously connecting. Background retries
continue. This preserves honest failure feedback; it cannot repair a third-party
service outage or reconstruct visits it did not receive.

GitHub Pages must not fall back to `chatgpt.site/api/visits`; that would restore
the original regional reachability problem. Local browser QA must block that
legacy endpoint and verify the footer still receives independent counts.
