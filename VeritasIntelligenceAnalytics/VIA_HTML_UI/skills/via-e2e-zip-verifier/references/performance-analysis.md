# E2E performance interpretation

The E2E runner records the duration of each browser interaction and assertion. These values measure test execution overhead under the current Chromium and sandbox conditions. They are useful for identifying relative slow journeys, but they are not production FCP, Largest Contentful Paint, Time to Interactive, or network latency measurements.

Report at least the following per device: total test duration, arithmetic mean, median, p95, slowest checks, pass rate, source bytes, overflow result, and investment-card widths. Compare the same check across devices to identify responsive interaction overhead. Mobile settings drawers, chart range changes, and search often take longer because the test waits for responsive transitions or filters.

Treat a higher mobile duration as a diagnostic signal rather than a defect when the check passes and console/page errors remain zero. Escalate it when the same action repeatedly grows across runs, blocks interaction, or coincides with layout overflow or failed state assertions.

Keep performance observations separate from compatibility claims. A page can be fully compatible while a particular test journey is slower. If production performance is required, add browser Performance API measurements or an explicit Lighthouse-style test instead of inferring them from E2E interaction time.
