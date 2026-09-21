import json
from pathlib import Path
from collections import Counter

from classification_scoring import classify_sound_with_evidence


ARCHIVE_DIR = Path("data/archive")


def load_latest_archive():
    files = sorted(ARCHIVE_DIR.glob("*.json"))
    if not files:
        return None, []

    path = files[-1]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Failed to read {path}: {exc}") from exc

    if not isinstance(data, list):
        raise RuntimeError(f"{path} is not a list")

    return path, data


def main():
    path, items = load_latest_archive()

    if path is None:
        print("[Audit] No archive files found.")
        return

    sound_items = [
        item
        for item in items
        if isinstance(item, dict)
        and item.get("asset_type") == "sound"
    ]

    status_counts = Counter()
    confidence_counts = Counter()
    result_counts = Counter()
    changed = []
    review_examples = []

    for item in sound_items:
        result = classify_sound_with_evidence(item)

        status_counts[result["classification_status"]] += 1
        confidence_counts[result["classification_confidence"]] += 1
        result_counts[result["sound_type"] or "unknown"] += 1

        previous = item.get("sound_type")
        if previous != result["sound_type"]:
            changed.append(
                {
                    "title": item.get("title", ""),
                    "previous": previous,
                    "new": result["sound_type"],
                    "scores": result["classification_scores"],
                }
            )

        if result["classification_status"] == "needs_review":
            review_examples.append(
                {
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "sound_type": result["sound_type"],
                    "confidence": result["classification_confidence"],
                    "scores": result["classification_scores"],
                    "evidence": result["classification_evidence"],
                }
            )

    print(f"[Audit] Archive: {path}")
    print(f"[Audit] Total items: {len(items)}")
    print(f"[Audit] Sound items: {len(sound_items)}")
    print(f"[Audit] Status: {dict(status_counts)}")
    print(f"[Audit] Confidence: {dict(confidence_counts)}")
    print(f"[Audit] New classification: {dict(result_counts)}")
    print(f"[Audit] Changed from stored sound_type: {len(changed)}")

    if changed:
        print()
        print("[Audit] Changed examples (max 20):")
        for item in changed[:20]:
            print(
                f"- {item['title']} | "
                f"{item['previous']} -> {item['new']} | "
                f"{item['scores']}"
            )

    if review_examples:
        print()
        print("[Audit] Review examples (max 20):")
        for item in review_examples[:20]:
            print(
                f"- {item['title']} | "
                f"type={item['sound_type']} | "
                f"confidence={item['confidence']} | "
                f"scores={item['scores']}"
            )
            if item["evidence"]:
                print(f"  evidence={item['evidence']}")


if __name__ == "__main__":
    main()
