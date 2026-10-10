# Classification Policy Analysis (105 reviewed PRE items)

## Purpose

Use the 105 human-reviewed PRE entries as a regression corpus to improve classification without turning individual preferences or one-off circumstances into global rules.

This document records findings from the review ledger. It does not itself change runtime classification behavior.

## Current corpus snapshot

- Reviewed entries: 105
- Open entries: 0
- `decision=confirmed`: 43
- `decision=not_applicable`: 61
- `decision=reviewed`: 1

Important: these decision values are not a simple include/exclude label. For example, `confirmed` can mean the asset type was confirmed while the note says that publication is not appropriate. Do not train an inclusion filter directly from the decision field alone; use the review note and a normalized purpose label.

## Proposed staged decision flow

1. **Determine post purpose** from source-native category/tags, title, and available description/body:
   - distributable asset
   - reusable plugin
   - general-purpose developer tool
   - official/product information
   - game showcase/devlog/process video
   - question/discussion
   - sale/giveaway/temporary promotion
   - duplicate/reminder
   - unavailable/deleted/unclear
2. **Determine whether there is a usable deliverable**: downloadable resource/plugin/tool, or a clearly useful official development update.
3. **Apply persistence and duplication checks**: temporary sales and reminder reposts are not durable catalog entries; deleted or inaccessible posts should be marked unavailable rather than misclassified as non-assets.
4. **Classify the deliverable** into the existing graphic/sound/plugin taxonomy only after the post is judged in-scope.
5. **Escalate uncertainty**: inspect body and destination page when the title/source metadata is insufficient; inspect image content only when a graphic asset is a plausible candidate and an image is available. If still unclear, create a human review item.

The purpose stage and asset taxonomy should remain separate. A post can clearly mention a plugin but still be a question, a showcase, a reminder, or a transient promotion.

## Strong recurring exclusion signals

Based on review notes, these are candidates for general rules, subject to regression testing:

- Game showcases and screenshots without a reusable deliverable.
- Development-process videos, progress updates, and game-setting introductions.
- Questions, troubleshooting requests, and general discussion without a concrete resource.
- Sample images or previews without an actual downloadable resource.
- Duplicate reminders of previously published content.
- Deleted posts: do not infer the content from the title alone; mark as unavailable and do not register.
- Temporary, time-limited sale/giveaway announcements when they provide no durable resource information.

## Inclusion signals

- Downloadable graphics, sprites, tilesets, character sheets, and sound effects.
- Reusable plugins that are actually released for others to use, including free distribution on the author's own website or another site.
- General-purpose developer tools even when they are not assets in the narrow sense (e.g. save-file editors or visual plugin-authoring tools).
- Official updates that have ongoing relevance to RPG Maker development.

## Conflicts that must not be hidden by automation

The ledger contains inconsistent historical decisions about third-party paid-product announcements and temporary promotions. Examples include PRE-00025, PRE-00027, PRE-00035–00037, PRE-00044–00045, PRE-00047, PRE-00050, PRE-00060–00064 versus later exclusions PRE-00062, PRE-00071–00073, PRE-00080, PRE-00084, PRE-00094–00095, PRE-00099, and PRE-00104.

Possible explanation: older decisions sometimes treated the announcement as a useful pointer to a concrete product, while later decisions exclude promotion-only or time-sensitive posts. This cannot safely be resolved by keyword rules alone. Until the distinction is explicitly normalized, do not use these examples as hard automatic labels. The conservative default should be to retain a durable, identifiable resource/product listing only when it adds useful catalog information; exclude temporary discount/reminder posts; send borderline promotion-only posts to review.

Other cases that must remain exceptions rather than broad rules:
- Personal taste: PRE-00009 and PRE-00059.
- Copyright/fan-work concerns: PRE-00018 and PRE-00102; do not generalize from title keywords alone.
- Deleted/unavailable items: PRE-00028, PRE-00057, PRE-00082, PRE-00089.
- User-confirmed title/description mismatches: PRE-00068 and PRE-00070; trust the user's item-specific correction but do not infer a general rule from mismatched metadata.
- Duplicate merge: PRE-00087 should point to PRE-00093 rather than become a general plugin exclusion.

## Implementation plan

1. Normalize the 105 cases into explicit purpose labels, inclusion decision, evidence availability, and rationale. Do not use the existing `decision` field as the sole target.
2. Add a deterministic page-purpose classifier that uses existing title/body/tags/category fields and emits purpose, confidence, evidence, and review status. Initially run it in audit/shadow mode only; do not suppress report items automatically.
3. Add regression tests from the normalized review corpus, especially boundary cases and historical conflicts.
4. Compare current behavior against the human-reviewed cases. Fix only repeatable, generalizable errors.
5. Add body/link inspection as a fallback for uncertain cases. Image inspection should be an optional final step for plausible graphic assets, not a default for every post.
6. Enable automatic exclusion only for high-confidence, well-tested purposes. Keep uncertain and contradictory cases in human review.

## Non-goals

- Do not introduce a paid API or external model dependency by default.
- Do not retrain a machine-learning model from 105 examples.
- Do not turn individual taste, one-off copyright concerns, or unavailable pages into broad keyword rules.
- Do not rewrite the existing detailed asset taxonomy until the purpose-stage audit shows that it is necessary.
