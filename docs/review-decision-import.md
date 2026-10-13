# Importing human classification-review decisions

The daily run reads `data/review/review_decisions.json` before collecting new items.
Add only decisions that have been explicitly confirmed in the conversation.

Example:

```json
{
  "decisions": [
    {
      "pre_id": "PRE-00107",
      "decision": "plugin",
      "note": "A reusable plugin release, not a help request."
    },
    {
      "pre_id": "PRE-00108",
      "decision": "not_applicable",
      "note": "A request for a plugin, not a released resource."
    }
  ]
}
```

- `pre_id` must already exist in `data/review/classification_review.json`.
- `decision` is a short human decision label (for example `confirmed`, `not_applicable`, `plugin`, `material`, `BGM`, or `exclude`).
- `note` is optional, but a short rationale is helpful.
- The importer validates the entire batch before changing anything. Unknown IDs, duplicate IDs, and conflicting attempts to change an already-resolved decision stop the import rather than partially applying it.
- Successfully imported items receive `status: "resolved"`, `decision`, `resolved_at`, and `review_note`; resolved items are then excluded from the carryover queue.
- Keep previously imported entries unchanged. Re-running the daily workflow is safe: identical decisions are recognized as already applied.
- To inspect a batch without writing, run `python tools/apply_review_decisions.py --decisions data/review/review_decisions.json`. The utility is dry-run by default. Its `--apply` option is intended for deliberate local use; the daily workflow imports the committed input automatically.

No decisions are added to the file automatically. This keeps human editorial decisions explicit and reviewable.
