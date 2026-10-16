"""Shared source-health status rules for the daily collection run."""


def determine_source_status(request_stats=None, summary=None):
    """Return OK, PARTIAL, or ERROR based on request and collector diagnostics.

    A caught request failure must not be hidden just because the collector
    returned normally. If every tracked request failed, the source is ERROR;
    mixed successes and failures are PARTIAL. Collector-specific summaries
    (such as Source Check) can also mark a run PARTIAL.
    """
    request_stats = request_stats if isinstance(request_stats, dict) else {}
    summary = summary if isinstance(summary, dict) else {}

    succeeded = int(request_stats.get("succeeded", 0) or 0)
    failed = int(request_stats.get("failed", 0) or 0)
    summary_failed = int(summary.get("failed", 0) or 0)

    if failed and succeeded == 0:
        return "ERROR"
    if failed or summary_failed:
        return "PARTIAL"
    return "OK"
