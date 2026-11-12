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

## 正規データモデル v8

- `content_type=development_info` を追加。開発情報は素材・プラグイン・ゲームとは別のトップレベル種別として扱う。
- `development_info_type` は `runtime_player`／`development_tool`／`conversion_tool`／`technical_reference`／`tutorial`／`tip`。プラグイン詳細分類の `development_debug` は流用しない。
- `asset_type` は素材・プラグイン・ゲームの既存分類に限定し、開発情報では `null` とする。既存の `other` は過去データとの互換性のため維持する。
- `engine` は対象RPG Makerの種類・バージョン。OS・端末・実行環境は `supported_platforms` に分ける。
- `url` は元投稿・掲載ページ。配布先・商品ページ・公式ページ・説明書・リポジトリ等は `links` に種別付きで保存する。
- `author` は作者・制作者、`publisher` は販売元・配布元。価格額・通貨は確認できた場合だけ `price_amount`／`price_currency` に保存する。
- `source_published_at` は元投稿の日時、`release_date` は製品・ツールの公開日時。別の概念として保持する。
- `source_site_name`／`source_site_type`／`source_site_language` はSITEマスターのスナップショット。サイト自体の状態 `source_site_status` と個別リンクの利用可能性も混同しない。
- 共通検索項目 `engine_relevant`／`file_formats`／`graphic_style`／`graphic_theme` を正式フィールドとして定義する。
- Collector固有情報は `collector_metadata` の下にCollector名で名前空間化する。広く再利用できる項目だけを共通フィールドへ昇格する。

### 開発情報と既存Tipsの移行

- 既存のTipsカテゴリーは新規収集時に `content_type=development_info`／`development_info_type=tip` として扱う。
- 元の `category` はSlack表示との互換性のため保持し、既存Archiveの一括書き換えは行わない。
- 「開発情報」カテゴリーは、詳細用途が確認できない場合に `development_info_type` を推測で埋めない。

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
- classification_confidence
- classification_status

### 人間の判断でのみ設定する情報
- classification_status = confirmed
- classification_note
- classification_reviewed_at
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
8. 詳細分類は自動判定を基本とするが、確信度が低いものは needs_review として人間確認に回す。
9. BGM/BGS/ME/SEのような短い分類語は、単純な部分一致を避け、明示表記を優先する。
8. WordPress移行時は、source_site_id を情報源ページとのリレーションに利用し、SITE番号自体を公開URLには使用しない。