# Parallel Android data download

2026-10-18. Source remains the four immutable preview.5 parts and original SHA-256
pins. Each part keeps its own resume file; imports still concatenate in numeric
order. At most four workers download/verify parts. Aggregate progress includes
existing partial files. Any failure or cancellation stops scheduling work and
joins the workers before returning, so another attempt cannot race existing writers.

## Verification

20 Linux checks passed. GitHubDataTest additionally requires four overlapping
HTTP transfers, a maximum of four, correct aggregate progress, resumed bytes,
SHA-256 validation, numeric concatenation despite parallel completion, cancellation,
and no callbacks after failed-download cleanup. The same files are then reused
successfully in another attempt.

The initial two-connection candidate, a signed local preview.9-test APK was installed over preview.8 on the Android 15
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

## Matched connection sampling

After urllib TLS failures, curl through the same host proxy completed six rounds.
Each round fetched the same first 1 MiB of all four immutable parts; all 24
responses had correct Content-Range, length, and matching per-part SHA-256.
No Android download ran during these rounds. Order was 1, 2, 4, 4, 2, 1.

| Connections | Round times (seconds) |
| --- | --- |
| 1 | 17.53, 25.51 |
| 2 | 11.46, 10.52 |
| 4 | 8.44, 6.65 |

These small requests include handshake/setup time and support trying four
connections; they do not establish full-package throughput or the user's speed.
Results: /tmp/d2r-curl-speed/results.json. The final candidate uses four workers
and displays observed byte-delta transfer rate. No data URL/hash/file format changes.

Final four-worker APK observation: all four partial files were present at
76,214,907 / 19,236,022 / 5,144,576 / 3,273,314 bytes, reusing the first two
partials. The UI displayed 1.68%, 98.4 MiB and 1.37 MiB/s. Screenshot:
/tmp/d2r-four-download.png. This is an instantaneous observed rate, not a
comparison against serial full-package download.
