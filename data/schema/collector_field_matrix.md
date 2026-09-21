# Collector → Common Item field matrix

現在のCollectorが実際に取得・生成している情報を基準にした移行用設計資料。
○=明示的に取得/生成、△=共通処理や条件付きで生成、—=現状ほぼ持たない。

| Collector | content_type | title/url | description | author | source tags | source date | license | engine | detailed classification | thumbnail |
|---|---|---|---|---|---|---|---|---|---|---|
| community_reddit | △ | ○ | — | — | △ | △ | — | △ | △ | — |
| community_forum | △ | ○ | — | — | — | — | — | △ | △ | — |
| community_tsukumate | asset/plugin/Tips系 | ○ | — | — | — | — | — | △ | △ | — |
| community_tkool_forum | △ | ○ | — | — | ○ | ○ | — | △ | △ | — |
| community_save_point | △ | ○ | — | — | ○ | ○ | — | △ | △ | — |
| community_rpgmakerforum_de | △ | ○ | — | — | ○ | ○ | — | △ | △ | — |
| community_chaos_project | asset | ○ | — | — | — | — | — | △ | △ | — |
| official_site | official | ○ | — | — | — | △ | — | △ | official category | — |
| official_steam | official | ○ | — | — | — | △ | — | △ | official category | — |
| official_opengameart | asset | ○ | — | — | △ | △ | △ | △ | asset | — |
| official_kenney | asset | ○ | — | — | △ | △ | △ | △ | asset | — |
| official_craftpix | asset | ○ | — | — | △ | △ | △ | △ | asset | — |
| official_gamedevmarket | asset | ○ | — | — | △ | △ | △ | △ | asset | — |
| official_tsukupura | plugin | ○ | — | — | — | — | — | △ | plugin | — |
| official_visustella | plugin/asset | ○ | — | — | — | — | — | △ | plugin/asset | — |
| official_deviantart | asset/game/etc. | ○ | ○ | ○ | ○ | ○ | ○ | △ | △ | △ |
| asset_itchio | asset/game | ○ | — | — | ○ | — | — | △ | △ | — |
| community_guild | asset/plugin/game | ○ | — | — | ○ | △ | — | △ | △ | — |
| official_makerdevs | plugin/asset | ○ | — | — | — | — | — | △ | plugin/asset | — |
| official_caspergaming | plugin/asset | ○ | — | — | — | — | — | △ | plugin/asset | — |
| official_triacontane | plugin | ○ | — | — | — | ○ (change detection) | — | ○ (repo context) | plugin | — |
| official_source_check | site_update | ○ | — | — | — | ○ (change detection) | — | — | SourceCheck | — |

## 共通Itemの方針

### 必須の識別情報
- internal_id: プロジェクト内で永久に安定したID
- source_site_id: SITEマスターへの参照
- collector: 技術的な取得モジュール
- source_item_id: 元サイト側で安定して識別できる値。無ければURLを暫定利用
- url
- title

### 取得できた場合に保存する情報
- description
- author
- source_tags
- source_published_at
- source_updated_at
- thumbnail_url
- license
- price_status
- license_status

### 共通処理で補完する情報
- content_type
- engine[]
- asset_type
- languages[]
- tags[]

### 人間の判断でのみ設定する情報
- pre_id
- public_id
- editorial_status
- excluded_reason
- review_note
- reviewed_at
- featured
- registered_at

## 設計上の重要事項

1. category は現在のSlack表示との互換性のため当面保持するが、長期的な公開DBの分類キーにはしない。
2. 情報源は source_site_id で管理し、分類と混ぜない。
3. SITE-xxxxx は内部固定IDであり、WordPress訪問者には原則表示しない。
4. SITE番号は順位ではない。初期整理後は既存番号を変更せず、新規SITEだけ末尾に連番追加する。
5. ライセンス・商用利用可否などは、明記がない場合に推測しない。
6. 元サイトの素材そのものは保存せず、原則としてURLとメタデータを保存する。
7. Collectorごとの取得能力に差があるため、全Collectorに全フィールド取得を要求しない。
8. WordPress移行時は、source_site_id を情報源ページとのリレーションに利用し、SITE番号自体を公開URLには使用しない。