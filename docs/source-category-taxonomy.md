# Source categories and collection intent

This document describes **the kind of source being monitored**, not the content category assigned to each individual item in a Daily Report. Keep these concepts separate so that official announcements, community posts, developer releases, and asset marketplaces are not conflated.

## 1. Official information

These sources are grouped separately from community posts and independent creators.

| Source | Language | Monitored content | Notes |
|---|---|---|---|
| RPG Maker Official News | Japanese | Official product/company news | Official information |
| RPG Maker Steam News | Mainly English; depends on announcement | Announcements for the configured RPG Maker Steam apps | Official product announcements |
| RPG Maker Web Resources Blog | English | Resource-related posts on the official RPG Maker Web site | Official editorial/resource information, not a marketplace feed |

## 2. Community forums and user-posted resources

These are community/user-post sources. Collection should prioritize reusable resources such as graphics, audio, plugins/scripts, and useful development tips. General questions, personal game showcases, and unrelated discussion should not become useful-resource notifications.

| Source | Main language | Monitored area / content |
|---|---|---|
| Reddit r/RPGMaker | English / multilingual | RPG Maker posts; item-level filtering is needed |
| RPG Maker Web Forum | English | Resource-related forum posts |
| ツクマテ | Japanese | Resource and Tips sections |
| ツクールフォーラム | Japanese | Resource-related posts |
| Save-Point | English | Resource-related forum posts |
| RPG Maker Forum DE | German | Resource-related posts |
| Chaos Project | English | Resource forum |
| RPG Maker SU / Нейтральная полоса | Russian | Resource and plugin sections |
| RPG Maker Union | Russian | Resources and plugins/scripts |
| Oniromancie / RPG-MAKER.FR | French | Scripts/resources |
| RPG Maker Guild | English | Resource and plugin categories |
| Comunidad RPG Maker ES | Spanish | Community resource posts |
| RPG Maker La Communauté FR | French | Resource forum |
| Project1 / RPG Maker Chinese community | Chinese | RPG Maker MZ forum |
| RPG Maker RU | Russian | MZ plugin forum |
| Condado Braveheart | Brazilian Portuguese | Utility/tools forum |
| Rpg2S | Italian | MZ plugin/script forum |
| RPG Refuge | English | Asset, audio, plugin, and development-tool forum sections |

## 3. Official/independent developer and plugin-release sites

These are creator/publisher release channels rather than community forums or official RPG Maker announcements. Some offer free items and some offer paid items; the current collector may monitor a specific resource page rather than the entire site.

| Source | Main language | Monitored content | Distribution note |
|---|---|---|---|
| ツクプラMZ | Japanese | RPG Maker MZ plugins | Plugin catalog; check each item's terms |
| VisuStella | English | Plugin releases | Free and paid offerings may coexist |
| Maker Devs | English | MZ plugin master list | Access/connection reliability has been inconsistent; don't treat an empty run as proof of no updates |
| Casper Gaming | English | Plugins, sound, and map resources | Free and paid offerings may coexist |
| Triacontane (GitHub) | Japanese / code comments may vary | RPG Maker MV/MZ plugin repository | Public source repository |
| Source Check | Mixed | Detects changes on selected creator sites; does not collect individual resource items | Update-only signal; it watches the eight sites listed below |

### Source Check targets

- Galv's Plugins — English
- Atelier RGSS / Moghunter — Portuguese/Spanish and other languages may appear
- KageDesu Workshop — English
- Blue Coral Games — English
- DK Plugins — Russian
- Hakuen Studio (itch.io) — English
- Sang Hendrix (itch.io) — English
- Raizen Plugins (itch.io) — English

Source Check currently detects page changes and sends an “update” signal. It does not establish whether a specific item is free, paid, or newly released.

## 4. Asset libraries and marketplaces

Free/paid status must be determined from the **actual item or monitored page**, not inferred solely from the site's name. The same site can contain free downloads, pay-what-you-want items, and paid products.

| Source | Main language | Current monitored area | Distribution classification |
|---|---|---|---|
| OpenGameArt | English / multilingual | Asset search/listing | Primarily free/open-license assets; each asset's license still needs checking |
| Kenney | English | Asset catalog | Free downloadable asset catalog; optional paid/support offerings may exist |
| CraftPix | English | Freebies page | Current collector targets freebies; the wider site also sells paid packs |
| GameDevMarket | English | 2D marketplace | Commercial marketplace; treat as paid unless an item is explicitly marked free |
| itch.io RPG Maker assets | English / multilingual | RPG Maker asset listings | Mixed: free, pay-what-you-want, and paid |
| DeviantArt | English / multilingual | RPG Maker-related searches | Mixed creator platform; downloads may be free, paid, or unavailable |
| RPG Refuge | English | Community forum sections | Not an asset marketplace; listed here only for reference would be misleading, so its canonical category remains “Community forums” above |

## 5. How to apply this classification

1. **Official information is its own top-level source category.** Do not merge it into community posts or independent plugin releases.
2. **Community forums remain separate** from creator storefronts and asset marketplaces.
3. **Commercial/mixed marketplaces are identified explicitly.** Where reliable, classify the monitored item as free, pay-what-you-want, paid, or unknown. Do not infer item-level price from the site alone.
4. **A free-only page is recorded as such**, even if the wider site also sells products (for example, CraftPix's freebies page).
5. **Source Check remains a separate update-detection mechanism**, not an ordinary resource collector.
6. This document is a source taxonomy/reference. It does not by itself change runtime collection, Slack filtering, or the per-item resource classifier.
