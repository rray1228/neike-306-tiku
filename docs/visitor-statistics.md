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
The footer labels this historical snapshot separately. No prior visitor IDs
were transferred to the new provider. Visits that never reached the old
endpoint cannot be reconstructed.

Requests have an eight-second timeout, share one in-flight request, and cache
successful results for one minute. Network failures retry with a bounded
backoff; reconnecting or returning to the page also retries. Previously received
numbers are labelled as not updated if refresh fails. A failure never displays
zero or increments counts locally. The client still cannot guarantee delivery
during a complete network outage or blocking of the replacement service.

GitHub Pages must not fall back to `chatgpt.site/api/visits`; that would restore
the original regional reachability problem. Local browser QA must block that
legacy endpoint and verify the footer still receives independent counts.
