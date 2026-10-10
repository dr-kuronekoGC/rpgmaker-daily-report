# Classification Policy Analysis (105 reviewed PRE items)

## Purpose

Use the 105 human-reviewed PRE entries as a regression corpus to improve classification without turning individual preferences or one-off circumstances into global rules.

This document records findings and policy clarifications. It does not itself change runtime classification behavior.

## Current corpus snapshot

- Reviewed entries: 105
- Open entries: 0
- `decision=confirmed`: 43
- `decision=not_applicable`: 61
- `decision=reviewed`: 1

These decision values are not simple include/exclude labels. `confirmed` can mean the asset type was confirmed even when the note says publication is inappropriate. Do not use the field alone as a training target; normalize purpose, inclusion, evidence, and rationale.

## Editorial goal

The eventual WordPress site is intended to be a useful RPG Maker update and discovery site, not merely a personal list of free assets. **Both free and paid resources are in scope.** Paid status is metadata, not an exclusion criterion. Include useful paid assets, plugins, and development tools so readers can discover them alongside free offerings.

Where available, retain price/free status, product or store URL, creator/publisher, engine compatibility, and whether the item is a new release or update. Inclusion is not an endorsement or ranking.

## Proposed staged decision flow

1. **Determine post purpose** from source-native category/tags, title, and available description/body:
   - distributable asset
   - reusable plugin
   - general-purpose developer tool
   - durable product/store listing
   - official/product information
   - game showcase/devlog/process video
   - question/discussion
   - temporary sale/giveaway promotion
   - duplicate/reminder
   - unavailable/deleted/unclear
2. **Determine whether there is a usable deliverable or useful product listing**: downloadable free or paid resource/plugin/tool, a durable listing for a concrete product, or a clearly useful official development update.
3. **Apply persistence and duplication checks**. A temporary promotion does not make an otherwise useful product out of scope: retain the durable product entry and treat the sale as secondary metadata when useful. Exclude sale countdowns, reminders, or giveaway-only notices that add no lasting product information. Deleted or inaccessible posts should be marked unavailable rather than misclassified as non-assets.
4. **Classify the deliverable** into the existing graphic/sound/plugin taxonomy only after the post is judged in-scope.
5. **Escalate uncertainty**: inspect body and destination page when title/source metadata is insufficient; inspect image content only when a graphic asset is a plausible candidate and an image is available. If still unclear, create a human review item.

The purpose stage and asset taxonomy should remain separate. A post can mention a plugin but still be a question, showcase, reminder, or transient promotion. Likewise, the fact that a product is paid, sold by a third-party store, or hosted on the creator's own website is not a reason to exclude it.

## Strong recurring exclusion signals

Candidates for general rules, subject to regression testing:

- Game showcases and screenshots without a reusable deliverable.
- Development-process videos, progress updates, and game-setting introductions.
- Questions, troubleshooting requests, and general discussion without a concrete resource.
- Sample images or previews without an actual downloadable resource or durable product listing.
- Duplicate reminders of previously published content.
- Deleted posts: do not infer content from title alone; mark unavailable and do not register.
- Sale countdowns, discount reminders, or giveaway-only announcements when they add no lasting product information.

## Inclusion signals

- Downloadable graphics, sprites, tilesets, character sheets, sound effects, and other reusable materials, whether free or paid.
- Reusable plugins actually released for others to use, whether free or paid.
- Durable listings for paid assets/plugins, including listings on a creator's own site or a third-party store.
- General-purpose developer tools, including save-file editors or visual plugin-authoring tools, whether free or paid.
- Official updates with ongoing relevance to RPG Maker development.

## Historical conflicts and exceptions

Older decisions differ on some paid-product announcements and temporary promotions. The clarified policy is that paid products themselves are in scope; do not exclude an item merely because it mentions a price or store. The distinction is between a durable product/resource entry and a transient promotion-only post. Keep a concrete new release or identifiable product listing. Exclude short-lived sale countdowns, sale reminders, or giveaway-only notices that add no lasting product information. If a post mixes a real product listing with a sale, retain the product entry and record the promotion only as secondary metadata when useful. Send borderline cases to review rather than using keyword-only rules.

Historical examples remain useful regression cases, but their old decision values should not be copied blindly. Examples include PRE-00025, PRE-00027, PRE-00035–00037, PRE-00044–00045, PRE-00047, PRE-00050, PRE-00060–00064, and later exclusions PRE-00071–00073, PRE-00080, PRE-00084, PRE-00094–00095, PRE-00099, and PRE-00104.

Other cases that must remain exceptions rather than broad rules:
- Personal taste: PRE-00009 and PRE-00059.
- Copyright/fan-work concerns: PRE-00018 and PRE-00102; do not generalize from title keywords alone.
- Deleted/unavailable items: PRE-00028, PRE-00057, PRE-00082, PRE-00089.
- User-confirmed title/description mismatches: PRE-00068 and PRE-00070.
- Duplicate merge: PRE-00087 should point to PRE-00093 rather than become a general plugin exclusion.

## Implementation plan

1. Normalize the 105 cases into explicit purpose labels, inclusion decision, evidence availability, and rationale. Do not use the existing `decision` field as the sole target.
2. Add a deterministic page-purpose classifier using existing title/body/tags/category fields; emit purpose, confidence, evidence, and review status. Initially run in audit/shadow mode only; do not suppress report items automatically.
3. Add regression tests from the normalized review corpus, especially boundary cases and historical conflicts.
4. Compare current behavior against the human-reviewed cases. Fix only repeatable, generalizable errors.
5. Add body/link inspection as a fallback for uncertain cases. Image inspection should be an optional final step for plausible graphic assets, not a default for every post.
6. Enable automatic exclusion only for high-confidence, well-tested purposes. Keep uncertain and contradictory cases in human review.

## Non-goals

- Do not introduce a paid API or external model dependency by default.
- Do not retrain a machine-learning model from 105 examples.
- Do not turn individual taste, one-off copyright concerns, or unavailable pages into broad keyword rules.
- Do not exclude an item solely because it is paid, hosted on a creator's own website, or sold through a third-party store.
- Do not rewrite the existing detailed asset taxonomy until the purpose-stage audit shows that it is necessary.
