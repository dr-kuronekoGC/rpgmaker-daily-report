# Historical Review Body Audit — Findings

**Run:** GitHub Actions Historical Review Body Audit  
**Scope:** resolved review records PRE-00001–PRE-00106  
**Purpose:** improve candidate classification rules without rewriting any historical human decision.

## Retrieval result

- Requested: **106** records.
- Page body or description retrieved: **38/106 (35.8%)**.
- Body unavailable: **68/106 (64.2%)**.
- Retrieved: RPG Maker Guild 34, itch.io 2, RPG Maker Union 2.
- Unavailable: Reddit 46 (HTTP 403), DeviantArt 21 (HTTP 403), Source Check 1 (HTTP 429).

This is a partial sample, not a representative sample of all sources. In particular, Reddit and DeviantArt body evidence is still missing. HTTP 403/429 is a retrieval limitation, **not evidence that a post is irrelevant**.

## What the recovered body text shows

Among the 38 records with body text, 20 had historical decision `confirmed` and 18 had `not_applicable`. The body helps distinguish several kinds of posts that share similar titles or keywords:

- **Clear deliverable:** PRE-00088 describes a library of 1,165 sound effects and links to the creator's own library; this is strong evidence for a reusable sound resource.
- **Clear production tool:** PRE-00091 describes a browser-based save-file editor, including how it works and that files stay in the browser. The human note accepted it as a production-support tool, despite it not being a conventional asset.
- **Question/discussion:** PRE-00043 asks for help finding or implementing a particle effect; an attached image does not turn the question into an asset release.
- **Concrete plugin descriptions:** PRE-00020, PRE-00021, PRE-00027, PRE-00030, PRE-00056 and PRE-00095 contain plugin features or behavior. Terms such as plugin, engine, and game-system names therefore cannot alone distinguish an asset release from a question or promotion.
- **Temporary promotion:** PRE-00033, PRE-00064, PRE-00073 and PRE-00099 contain giveaway/discount language. Their historical decisions are not uniform, so promotion wording alone is not a safe automatic exclusion.
- **Paid products / external sales links:** some product posts were confirmed (for example PRE-00035–PRE-00037 and PRE-00045), while other similar product announcements were excluded (for example PRE-00071–PRE-00072 and PRE-00080/PRE-00084). The ledger therefore does not support a blanket rule to exclude all paid resources or all links to another store.
- **Duplicates:** PRE-00021 is marked as a duplicate candidate of PRE-00020, while PRE-00087 was explicitly merged into PRE-00093. Duplicate detection should be a separate decision from resource detection.

## Candidate rules for the classifier

1. **Positive evidence should describe a deliverable:** downloadable file, named plugin/resource, a library or pack, included files, concrete features, or an explicit distribution link. Count evidence from the title, body/description, and source tags.
2. **Question intent is a strong negative signal only when there is no concrete deliverable.** Phrases asking for help, recommendations, or a solution should not override a clear linked release.
3. **Do not use engine or video as standalone exclusion words.** Real plugin/product titles can include “Engine”, and a video can accompany a plugin release. Prefer phrases such as “gameplay video” or “process video”.
4. **Do not exclude solely for price, external storefront, or promotional wording.** If the post only announces a short-lived discount/giveaway and contains no durable resource information, it can be a lower-priority or manual-review candidate; otherwise preserve the product/resource candidate.
5. **Unavailable body means unknown, not excluded.** Keep a separate retrieval status and do not infer non-resource status from HTTP errors or deleted pages.
6. **Deduplicate separately.** Two pages describing the same release should be linked to one canonical item rather than each being judged as a separate resource.
7. **Keep personal/editorial exceptions explicit.** A past not_applicable decision is useful evidence, but it is not always a reusable universal rule.

## Limitations and next validation

- The 68 inaccessible pages must not be silently labelled as non-resources.
- Several historical decisions around paid storefront announcements and giveaways are inconsistent. Before turning these into automatic rules, they need a clear current editorial policy.
- This audit did not change classification_review.json, any archive, seen-state, or past decision. The fetched text remains in a temporary workflow artifact; this report records only findings and examples, not full page bodies.
