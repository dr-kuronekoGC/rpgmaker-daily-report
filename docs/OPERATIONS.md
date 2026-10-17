# Operations guide

This document describes the purpose of the GitHub Actions workflows and the first checks to make when something looks wrong. It does not authorize resets or bulk edits to collection state.

## Scheduled collection

Workflow: `.github/workflows/rpg-maker-daily-report.yml`

- Runs twice daily (scheduled times are offset from the hour) and can also be started with **Run workflow**.
- Collectors run sequentially. Each collector's seen file is committed only through the normal workflow.
- Slack delivery must succeed before pending items are saved as delivered.
- Do not delete `seen_*.json`, `seen_global.json`, `pending_items.json`, `data/archive/`, or `data/review/` to troubleshoot an ordinary run.

### Source-health status

- **OK**: no tracked request failures and no collector-reported failures.
- **PARTIAL**: at least one tracked request or monitored page failed, while some part of the scan may have succeeded.
- **ERROR**: every tracked request for the collector failed, or the collector raised an uncaught error.

Some legacy collectors use their own HTTP calls rather than the shared request wrapper. Their request-level status may therefore be incomplete until they are migrated. Source Check has its own checked/failed summary. An HTTP 403/429, timeout, TLS error, or malformed feed should be treated as an acquisition problem, not as proof that the source has no new posts. Do not bypass access controls; reduce frequency or use a supported feed when appropriate.

## Classification audit

Workflow: `.github/workflows/classification-audit.yml`

- Runs unit tests and audit-only scripts.
- Uploads `open-review-queue-audit` and `normalized-review-corpus` artifacts.
- Audit recommendations do **not** resolve items and do not modify the human decision ledger.
- Only explicit decisions in `data/review/review_decisions.json` are imported by the normal collection workflow.

## What to check after a run

1. Confirm the workflow conclusion is **success**.
2. Read the **Source Health** lines. Check PARTIAL/ERROR sources before concluding there were no new posts.
3. Confirm the Slack status is HTTP 200 and the pending state was saved after successful delivery.
4. Watch the pending and classification-carryover counts over several runs; a single increase can be caused by backfill.
5. For malformed titles, open the source URL and determine whether the collector selected metadata (for example a date label) instead of the actual topic title.
6. For repeated items, compare normalized URL, source item ID, and title before considering any deduplication change.

## Recovery principles

- Prefer a small fix with tests and a pull request.
- Do not bulk-delete archives, seen state, pending items, or review records.
- Do not mark an inaccessible source healthy by suppressing errors.
- If a collector fails after a partial scan, preserve its seen state unless the collector can prove which entries were successfully processed.
- Keep the source registry in `data/sites/sites.json` aligned with active collectors. Site IDs are stable internal identifiers and should not be renumbered.


## Retired collectors

- **RMRK** is no longer in the scheduled collector registry. Its existing seen_rmrk.json, archive entries, and classification-review records are intentionally retained. The site may still be useful as a historical reference, but it is not scanned for new items.
- **Save-Point** remains an active collector and is the preferred ongoing forum source for resource-related posts. Its coverage is not a complete replacement for RMRK's historical database.


## Additional source coverage

- **Steam Workshop for RPG Maker MZ** is collected separately from Steam news. The collector checks resource-oriented workshop filters for plugins, tilesets, music, sound effects, and packs. The first successful run establishes a baseline rather than reporting old items as new. If all category pages parse as zero items, the collector raises an error and preserves the previous seen state instead of accepting an empty baseline.
- **New RPG Project** is monitored by Source Check for page changes. If the main page is inaccessible, Source Check may use its public Seesaa RSS endpoint (`index.rdf`) as a fallback. RSS access is not assumed successful until a run confirms it.
- **Comunidad RPG Maker ES** uses the forum's public Flarum discussion API rather than the old `/latest.rss` URL, which returned HTTP 404 in run #176. An empty or malformed API response is treated as an acquisition error, not as proof that the forum has no discussions.
- **RPG Maker RU** collection now checks the existing plugin section plus the graphics and music sections. Questions and help requests are excluded using conservative title markers; the forum's historical entries are retained.
