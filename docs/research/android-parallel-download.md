# Two-connection Android data download

2026-10-18. Source remains the four immutable preview.5 parts and original SHA-256
pins. Each part keeps its own resume file; imports still concatenate in numeric
order. At most two workers download/verify parts. Aggregate progress includes
existing partial files. Any failure or cancellation stops scheduling work and
joins the workers before returning, so another attempt cannot race existing writers.

## Verification

20 Linux checks passed. GitHubDataTest additionally requires two overlapping
HTTP transfers, a maximum of two, correct aggregate progress, resumed bytes,
SHA-256 validation, numeric concatenation despite parallel completion, cancellation,
and no callbacks after failed-download cleanup. The same files are then reused
successfully in another attempt.

A signed local preview.9-test APK was installed over preview.8 on the Android 15
x86 emulator. The existing first part was 32,663,896 bytes. During a real GitHub
transfer both files grew:

| Observation | Part 1 | Part 2 |
| --- | ---: | ---: |
| First | 44,787,152 | 974,511 |
| Second | 62,058,623 | 4,906,671 |

Screenshot: /tmp/d2r-parallel-active.png (0.74%, 43.4 / 5862.8 MiB, captured
slightly after the first file-size observation). This proves concurrent transfer
and reuse of existing partial data, not a measured speedup on the user's network.

The attempted matched external throughput benchmarks failed during TLS handshakes
both directly and through the emulator host's existing proxy. No speedup ratio is
claimed. No proxy is embedded in the APK and TLS certificate validation is retained.

## Compression measurement

Deflate level 1 over every member of the existing stored ZIP gave compressed
payload totals: game 19,195,239 bytes, RomFS 5,450,141,495 bytes, shaders 143,469,992
bytes, manifest 239 bytes, derived table 13,322 bytes. About 5.62 GB plus ZIP
headers, compared with 6.15 GB, saves about 8.7%. The published data has not been
replaced; preserving resume compatibility takes priority for current downloads.
