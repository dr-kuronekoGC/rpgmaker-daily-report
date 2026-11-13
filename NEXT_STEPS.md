## 最新更新（2026-11-13 JST・PRE-00549/00550確認／PRE-00543 preview）

### 完了
- PRE-00549：Reddit HTTP 403で本文未取得。検索で類似する募集投稿を確認したが、元投稿との同一性は未確定。募集・協業依頼の可能性が高いものの、確定除外せずGitHubはopenのまま。Notionページは存在し、URL一致・確認状態「未確認」を確認。
- PRE-00550：Reddit HTTP 403で本文未取得。タイトルから自作ゲーム紹介の可能性が高いが、本文・配布先を確認できず確定除外は保留。GitHubはopenのまま。Notionページは存在し、URL一致・確認状態「未確認」を確認。
- PRE-00543：read-only preview相当の検証を実行。Archive月別JSON（2026-09〜11）全4,216件、PRE台帳、review_decisions、patch manifestを照合。PRE ID／internal_idの一意一致、URL一致、resolved／confirmed、expected値一致を確認。結果は `ready_for_review`。差分はcontent_type: asset→development_info、asset_type: other→null、development_info_type: null→runtime_player、tags: []→[iPhone, ゲームプレイヤー]。
- PRE-00543の検証は読み取りのみ。Archive、PRE台帳、判定記録、seen／pending、Notionは変更していない。公式CLIを実行したのではなく、同CLIの検証条件を取得済み全データに対して同等に照合した結果。CLI実行成功とは表現しない。

### 次の作業
1. PR #147マージ後のmainでClassification Auditの最新run／workflow結果を読み取り確認。必要なら手動dispatch前に許可を求める。
2. PRE-00543の差分をユーザーに提示し、Archive実反映の明示許可を待つ。許可前にArchiveを書き換えない。
3. PRE-00549・00550は本文取得可能な正規情報が見つかるまでopen／未確認を維持。Notion全550件の同期完了とは扱わない（今回直接確認したのは該当2ページ）。
4. PR #143の境界ケース（NO_DELIVERABLE_RE優先順、プラットフォーム限定not available、ストアリンク統合テスト）をコードレビュー候補として扱う。

最終確認日：2026-11-13（JST）
---

## 最新更新（2026-11-13 JST・PR #143マージ後）

- PR [#143](https://github.com/dr-kuronekoGC/rpgmaker-daily-report/pull/143) は2026-11-13 18:50 JSTにmainへマージ。merge commit：`b578d3aaa2c0bbe7096dca18339d6adccc08100d`。
- pending-release判定は「近日公開」「配布予定」「not yet released」等の明示的な将来配布表現に限定。一般的な「開発中」「制作中」だけでは自動除外しない。
- 現行配布物、到達可能な個別商品ページ、確認不能・不確実な配布リンクは自動除外から保護。既知ストアの個別商品ページを認識し、ストアトップだけでは商品ページとみなさない。
- 回帰テスト8件追加。PR CI：Auto-screen triage 55テスト成功、Classification Audit全工程成功。
- マージ直後のmain側Auto-screen監査記録更新（commit `c7b50e5`）では2件を確認、auto-resolved 0件。Reddit HTTP 403等は未確認として保持。これは監査記録の更新で、PRE判断の自動変更ではない。
- PR #143後のコード／監査データ確認点：`c7b50e515b07598286160807d07f63b38926f7b6`（PR #143 merge後4コミット先行）。その後、管理MDを更新（`5ba238c`、`dda7e18`）。
- 今回、PRE台帳・review_decisions・Archive・seen/pending・Notionの実データ変更は確認していない。main上の手動dispatchも実施していない。

### 次の作業
1. PRE-00543のread-only Archive patch previewを実行可能な環境で確認。Archive実反映は差分提示と明示許可後のみ。
2. PRE-00549・00550のopen理由とNotion同期状態を確認。403や本文未取得を理由に自動解決しない。
3. main上のClassification Auditを再実行する必要があれば、手動dispatch前に許可を確認する。
4. 自動判定の境界ケース（NO_DELIVERABLE_REとの優先順、プラットフォーム限定の「not available」表現、ストアリンク検出の統合テスト）を次のコードレビュー候補として確認する。

最終確認日：2026-11-13（JST）
対象：dr-kuronekoGC/rpgmaker-daily-report。PR #143はmainへマージ済み。
---

## 最新更新（2026-11-13 JST・PR #147マージ後）

- PR #147 `Fix classification audit archive file selection` はマージ済み。merge commit / main HEAD：`607495f331023b3084838c0ec90e9ba293407a96`。
- 修正：`tools/audit_classification.py` は月別Archiveの `20??-??.json` のみ読み込む。metadata JSONを除外。回帰テスト `tools/test_audit_classification_archive_selection.py` 追加。
- PR #147のClassification Audit Run #43353057499は全工程success。マージ後のmainでコードとテストファイルの存在を確認済み。ただしmain上でのworkflow再実行は未確認（手動dispatchしていない）。
- PR #145もマージ済み。PR #144、#146、#145、#147がmain反映済み。
- PRE-00543は読み取り照合で提案4項目がready相当。実際のpreview CLI実行・Archive実反映は未実施。書き込みなし。
- PRE台帳550件（resolved 548／open 2：PRE-00549、PRE-00550）、判定記録324件。Archive 4,216件（9月1,862／10月2,255／11月99）。Pending 0件、Global seen 4,494件（前回確認値）。
- Notionは2026-11-10に546件を直接確認したのが最後。550件への最新同期は未確認。

### 次の作業
1. PR #147マージ後のmainでClassification Auditを再確認する。必要ならユーザーにActionsの手動実行許可を求める（勝手にdispatchしない）。
2. PRE-00543のread-only previewを実行可能な環境で確認し、出力を提示。Archive実反映は差分提示と明示許可後のみ。
3. PRE-00549・00550のopen理由とNotion同期状態を確認。
4. PR #143を最新mainと照合する。別PRとして扱い、merge/rebase/pushは確認を取る。
5. PRE-00540 project分類はschema v8未定義のため保留。PRE-00526重複は自動統合・削除しない。

---




## 最新更新（2026-11-12 JST・PR #146マージ後）

### 完了
- PR [#146](https://github.com/dr-kuronekoGC/rpgmaker-daily-report/pull/146) はmainへマージ済み。merge commit：`c22580f05a17caa5aa9e2a33c2f42021d36858be`。
- `tools/preview_archive_patches.py` と `data/review/archive_patch_proposals.json` により、PREからArchiveへの明示patchを読み取り専用でプレビューできる。PRE-00543の実データを使ったテストを含む回帰テストは成功済み。
- プレビュー機能は読み取り専用。Archiveへの書き込み・適用機能はなく、PRE-00543のArchive実データも未変更。PRE台帳・判定履歴・seen／pending・Notionも変更していない。
- PR #145の監査・設計文書とPR #146の実装は整合している。PR #145の以下の古い「dry-run仕様をこれから用意する」という記述は履歴として残し、現在の作業順はこの節を正とする。

### 次の作業
1. PR #145の文書差分をmain最新状態と照合し、管理MDの古い状態記述を整理する。PR #145は更新後も未マージ。マージは別途確認する。
2. PRE-00543のプレビュー結果を確認し、値・根拠・差分に問題がないか判断する。Archiveへの実反映は別工程で、ユーザーの明示許可があるまで行わない。
3. PRE-00540のproject配布の表現はschema v8に未定義のため保留。projectをplugin/gameへ無理に変換しない。
4. PRE-00526の重複は保持し、自動削除・統合しない。
5. Classification Auditの既存形式不整合は別課題として扱う。

---

## 最新更新（2026-11-12 JST・Archive反映設計）

### 完了：読み取り監査・設計案
- PR #144はGitHub上で2026-11-12 13:20 JSTにmerged。merge commit／main HEAD：`f9b7e9f082b80afbb0424819112d645e00fe4e27`。再マージ操作は不要。
- 2026-09〜11 Archive 4,211件をPRE台帳549件・判定記録324件と読み取り照合。
- PRE ID付きArchiveは550レコード／549種類。PRE-00526が同じinternal_idで2件重複。台帳にないPRE IDは0、resolved台帳でArchiveに対応しないinternal_idも0。
- 分類フィールド差は32 PRE ID（category 31、asset_type 6、content_type 2、tags 2）。大半は情報源固有categoryと一般化categoryの差。機械的な全項目コピーはしない。
- PRE-00543をschema v8に沿った最初の反映候補として設計。PRE-00540はprojectがschema v8に未定義のため保留。PRE-00460とPRE-00546も個別確認候補。
- 詳細は `docs/pre-archive-reconciliation-audit.md`。今回は読み取り監査・文書化のみ。Archive等のデータ本体は未変更。

### 次の作業
1. この反映設計（照合キー、明示patch、競合停止、冪等性）を確認する。
2. 合意後、PRE-00543だけを対象にdry-run仕様／テストを用意する。Archive本体の変更は差分を提示してから実施する。
3. PRE-00540のproject配布の表現（schema追加かother＋明示メタデータか）を別途決める。
4. PRE-00526重複は自動削除せず、必要なら別作業で統合方針を検討する。
5. Classification Auditの既存不整合は別PRで扱うか判断する。

---

## 最新更新（2026-11-12 JST）

### 正規Itemモデル v8：実装PR作成済み
- ユーザー合意に基づき、開発情報を `content_type=development_info` として独立。詳細分類は `development_info_type`（runtime_player／development_tool／conversion_tool／technical_reference／tutorial／tip）。
- ブランチ `feature/canonical-item-model-v8`、PR [#144](https://github.com/dr-kuronekoGC/rpgmaker-daily-report/pull/144)。mainの `9fc1c967` から分岐。1コミット、12ファイル変更。未マージ。
- schema v8、正規化処理、Tips／開発情報のSlack表示互換性、DeviantArt固有情報の名前空間化、回帰テストとPR用CIを追加。
- PR #144のCanonical Item model tests：構文検証＋41テスト成功。Engine Backfill Auditも成功（監査・プレビューのみ、適用なし）。
- Classification Auditは最後の既存 `tools/audit_classification.py` で失敗。`data/archive/source_status_overrides.json` をリストと仮定する既存不整合であり、今回の変更とは無関係。監査用の前段テスト・成果物作成は成功。
- PR #143（Auto-screen）は別PRとしてopenのまま。両PRともマージしていない。手動Workflow実行なし。
- Archive／PRE台帳／判定履歴／seen／pending／Notionは変更していない。PRE-00543のArchive反映は別課題。

### mainの最新データ確認（読み取りのみ）
- main HEAD：`9fc1c9671d16228ed44bc42f692acf97d8c28772`（2026-11-12 11:19 JST、Update report data）。
- PRE台帳：549件（resolved 548／open 1）。判定記録324件。11月Archive：94件。
- Notionは11/10に546件を直接確認したのが最後。PRE-00547～00549の同期状態は未確認。最新同期済みとは扱わない。

### 次の作業
1. PR #144の差分・CIをレビューし、必要な修正だけ行う。マージはユーザーの明示許可待ち。
2. schema v8に沿った既存Archive／PREの移行方法を別途設計する。現時点で一括変換しない。
3. Classification Auditの既存不整合は、正規データモデルPRとは分けて修正要否を判断する。

---

## 最新更新（2026-11-11 午後 JST）

### 完了
- PRE-00547を `not_applicable`（Coming Soonで現時点の配布素材なし）、PRE-00548を `plugin` としてユーザー判断を記録。台帳548件すべてresolved／open 0、判定記録324件。
- PRE-00547・00548のNotion同期状態は未確認。次回の定期同期後に件数と状態を照合する。手動Workflow実行はしない。

### 情報源再点検（読み取りのみ）
- RPG Maker SU：サイトと対象カテゴリは閲覧可能。プラグイン板は2026年9月の投稿あり。素材板は更新が古く、継続価値を観察。
- RM Planet：運営者の2026年10月報告で活動継続を確認。GitHub側で失敗しているRSS URLの形式・到達性を次に確認する。
- RPG Maker Network：Web確認では520／403。閉鎖とは断定せず、Actions側の最新結果と照合してから継続／停止を判断する。
- Comunidad RPG Maker ES：フォーラムは活動中。API方式は妥当。2ページ目404によるPARTIALを必要に応じて調査。
- Project1（rpg.blue）：MZ板で最近の投稿を確認。継続対象。
- Steam Workshop：現行ページは閲覧可能。既存collectorはPlugins／Tilesets／Music／Sound Effects／Packのみ。Animation・Character Sets・Faces・Icons・Battlers等の追加価値を検討する。
- 外部Web閲覧はActions実行環境からの取得成功を保証しない。情報源・コード・設定は変更していない。

### 次の作業（小さく順番に）
1. **PRE自動判定の精度改善案を作る。** 直近Auto-screenはReddit 403とRPG Maker Union SPAの本文未取得で2件ともkeep_open。誤判定を避ける保守的方針は維持しつつ、RPG Maker Unionの公開データ取得経路を調査。Coming Soon／未配布の明示表現は、文脈と配布リンクの有無を条件に追加できるか検討し、回帰テスト案を作る。Redditの403回避はしない。
2. **情報源の実行環境での状態を確認する。** RM Planet RSSとRPG Maker Networkの最新Actions結果を照合。ESのページネーションPARTIALも必要なら追跡。確認だけで停止・再開はしない。
3. **Steam Workshopのカテゴリ網羅性を検討する。** 追加カテゴリの件数・ノイズ・重複を調べ、必要な範囲だけ提案する。
4. **Notion同期を確認する。** 定期Run後にPRE-00547・00548がNotionへ反映されたか直接照合する。手動実行はしない。
5. 開発情報の正規データモデル検討は、黒ネコの酒場サイト開発で表示・検索を確認しながら進めるため、いったん優先度を下げる。

### 作業ルール
- 原因調査 → 最小修正 → テスト → GitHub Actions確認を分ける。
- 自動判定は本文未取得・403・曖昧なリンクを根拠に解決しない。
- コード変更、PR作成・更新・マージ、workflow手動実行、データ削除・リセットは明示的な許可なしに行わない。情報源のcollection停止も判断根拠を示してから確認する。
- 管理MDは作業節目で更新。mainと未マージPRの差分を混同しない。

最終確認日：2026-11-11（JST）
対象：`dr-kuronekoGC/rpgmaker-daily-report` の `main` のみ。

# NEXT_STEPS.md

## 最新更新（2026-11-11 JST）

**この節を現在の作業指示の正とする。** 過去の調査記録は末尾の「完了・過去の記録」に残す。

### 現在の状態
- mainのデータ最新：`f9504d8004fa6a0e4badad4e30dc32df91128b98`（11/11 10:17 JST）。管理MD更新後のmainは最新コミットを参照。未マージPRなし。
- PRE台帳：548件（resolved 546／open 2、PRE-00547・00548）。判定記録322件。
- Notion：11/10に546件すべて「済」を直接確認済み。追加されたPRE-00547・00548の同期状態は未確認。
- 最新データ：Pending 0件、Global seen 4,480件、11月Archive 85件。
- **RMRK整理は完了。** Pendingの旧RMRK951件を除外済み。RMRK SITE-00034は `closed`／`collection:false`、collector registryにも登録なし。seen_rmrk.json（1,575件）は保持。
- Archive：2026-10の2,255件中RMRK1,571件。月別Archive本体は保持し、`data/archive/source_status_overrides.json` に全1,571件の `internal_id` と `source_site_status:"closed"` を登録。ID重複なし、Archive内RMRK全件と一致。素材そのものの利用可能性・ライセンスとは区別する。サイト側でArchiveを取り込む場合はこの対応表も適用する。
- 閉鎖ステータスは素材用 `tags` ではなく、独立した `source_site_status` で表現。Item schemaと `docs/OPERATIONS.md` に記録済み。

### 次に行う作業（順番に一つずつ）
1. **開発情報の正規データモデルを検討する。** PRE-00543のゲームプレイヤー等を例に、「ゲームプレイヤー・実行環境」「開発支援ツール」「変換・移植ツール」「互換性・技術情報」と既存Tipsを区別し、content_type／asset_type／詳細分類のどこで表現するのが自然か比較する。まだ実装しない。
2. **PRE判断をArchiveへ反映する方法を検討する。** 現状の `review_decisions.json` はレビュー台帳を更新するが、Archive Itemは更新しない。PRE-00543等の既存データについて、対象・上書き条件・重複リスクを整理する。実装は別途許可を得る。
3. **Slack表示と検索メタデータの整合を検討する。** 開発情報の表示マッピング、engine_relevantや検索用詳細項目を整理する。
4. **自動分類への反映案を作る。** 既存の `development_debug` はプラグイン詳細分類なので流用しない。誤分類リスク・人手レビュー優先・回帰テスト対象を整理する。
5. 公開検索サイトとの連携は別プロジェクト・別チャットで扱う。BOT側では実際のサイト技術・データ受け渡し方法を確認してから互換性を検討し、WordPress等を前提にしない。

### 作業ルール
- 原因調査 → 最小修正 → テスト → GitHub Actions確認を分ける。
- 「workflow success」と外部サービスへの実同期・保存成功を区別する。
- コード変更、PR作成・更新・マージ、workflow手動実行、デプロイ、データ削除・リセットは、明示的な許可なしに行わない。管理MDの更新は作業節目で行う。
- `seen_*.json`、`seen_global.json`、`pending_items.json`、`data/archive/` を削除・リセットしない。
- 節目ごとに本ファイルと必要な管理MDを更新する。完了・未解決・未確認を明示する。

最終確認日：2026-11-11（JST）
対象：`dr-kuronekoGC/rpgmaker-daily-report` の `main` のみ。

## 完了・過去の記録

以下は経緯を保持するための履歴。現在の作業順・状態の判断には冒頭の「最新更新」を使う。

## 2026-11-10：RMRK backlog整理（完了）

- ユーザーの明示指示に基づき、RMRK由来のPending951件を除外。Pendingは0件。ほかの情報源のPending項目はなかった。
- 2026-10 Archiveは2,255件中RMRK1,571件。Archive本体を変更・削除せず、`data/archive/source_status_overrides.json` に全1,571件の `internal_id` と `source_site_status:"closed"` を記録。ID重複なし。SITEマスターもRMRKをclosedへ更新。
- `source_site_status` をItem schemaに追加。閉鎖は情報源サイトの状態であり、個々の素材が利用不能という意味ではない。
- `seen_rmrk.json`、Archive本体、archive_index、PRE台帳・判定記録は保持。コード変更・Workflow実行なし。データコミット `3609fd5042a1f76eb727684c0734e468dfb176bf`。

## 2026-11-10：定期実行確認（Notion・Auto-screen・Daily Report）

- Notion同期Run #138（11/10 13:08 JST、schedule）はsuccess、page_updates 0／pages_to_create 0。Notion実データ546件すべて「済」、未確認0件を直接照合。
- Auto-screen Run #56（11/10 08:28 JST、schedule）はsuccess。構文検証・安全性／リンク判定テスト61件成功。open 0のためscanned 0／auto_resolved 0。cron 23:25 JSTに対し約9時間遅延。次回cronは今回確認時点では未到来。
- Daily Report Run #228（11/10 04:44 JST）・#229（12:36 JST）はschedule／success、Slack HTTP 200。#228 Archive +4・Global seen +4・pending 975→961。#229 Archive +1（合計78）・Global seen 4472→4473・pending 962→951。#229の新着ゲーム1件はSlackに表示された。
- Source Healthは#228のOK 28/35・PARTIAL 3・ERROR 4から、#229ではOK 30/35・PARTIAL 1・ERROR 4に改善。SU、Project1中文、RM Planet、RPG Maker Networkのエラーと、Comunidad ESの一部失敗は継続。
- pending 951件は全件RMRK由来で、10月Archiveにも全件存在。内訳：RMRK素材情報708／グラフィック235／サウンド7／プラグイン1。resource_intentはnot_resource 724／resource_candidate 177／uncertain 50。
- RMRKカテゴリーは `categories/display.py` に表示マッピングがなく、#229では選択されたRMRK10件がSlack本文に表示されず、Slack送信成功後にpendingから外れた。Archiveは保持されておりデータ消失ではないが、意図した通知仕様か未確認。pendingの一括削除・リセットは行わず、次の調査課題にした。
- PRE台帳・判定記録・Archive・pending・seen・コードは変更していない。管理MDのみ更新。

## 2026-11-10：Notion同期・Auto-screen定期実行の確認

- 作業開始時のmainは `5d909fe`。未マージPRなし。PRE台帳546件（resolved 546／open 0）、判定記録322件。
- Notion同期Run #135（2026-11-09 18:50 JST）のログで、PRE-00539・00541・00543・00546の4ページ更新、`page_updates: 4`、`pages_to_create: 0` を確認。
- Run #136（2026-11-10 05:46 JST）と#137（08:28 JST）はsuccess・追加更新なし。Notionデータソースを直接集計し、546件すべて「済」、未確認0件。対象4件も「済」を確認。Notion同期は完了。
- Auto-screen Run #56（2026-11-10 08:28 JST）はschedule起動・success。監査ファイルは `scanned_item_count: 0`／`auto_resolved_count: 0`。open項目がなかったため検査対象なし。cronは変更せず、schedule実行時刻の遅延・ばらつきは継続観察。
- コード・PRE台帳・判定記録・収集状態は変更していない。管理MDのみ更新。

## 2026-11-10：開発情報カテゴリーの既存構造調査（読み取りのみ）

- Slackには既存の「開発情報・Tips」グループがあるが、内部カテゴリは主に `Tips`。独立した `開発情報` の表示マッピング・詳細表示順は未整備。
- PRE-00543のレビュー台帳には `category=開発情報`／`asset_type=development_tool`／`content_type=other` とユーザー判断が記録されている。
- 同じPREの月別Archive Itemは旧分類（`Redditグラフィック素材`／`asset`／`other`）のまま。レビュー決定の取り込みはPRE台帳だけを更新し、Archive Itemは更新しないことをコードで確認。
- 自動分類のasset_typeはgraphic／sound／plugin／game／other。development_toolの自動判定は未実装。詳細分類エンジンはsound／graphic／plugin向けで、pluginの `development_debug` は一般的な開発情報分類ではない。
- `content_type` に development_info はなく、検索メタデータも開発情報向けの項目が未定義。engine_relevantはgraphic／plugin／gameのみtrue。
- 今回はコード、Archive、PRE台帳、判定記録を変更していない。テスト・Actions実行も行っていない。読み取り調査と管理MD更新のみ。

## PRE-00539：今回は情報収集方法の確認までで終了（2026-11-08時点の記録）

- 当時は添付ファイル `Villa_MapLightAndShadow.js`（attachment ID 63505）のダウンロード・コード解析には進まない方針とした。
- 理由：スレッドにグリッドずれ、画面スクロール時の光の座標ずれという実用上の不具合報告があり、投稿者自身も解決できていないため。素材としての採用を見送る判断材料とした。
- ただし、環境固有の問題や設定で解消できる可能性は残るため、プラグイン自体が恒久的に使用不能とは断定しない。作者による修正報告や動作確認情報が見つかった場合は再評価可能。
- その後、2026-11-09にユーザー判断で今回は収集対象から除外し、PRE-00539はresolvedに更新済み。現在の状態は本ファイル冒頭と `PROJECT_STATUS.md` を参照する。
- RPG Maker Unionの添付ファイル取得を再度試す場合も、認証・アクセス制限を迂回せず、サイトの利用条件と配布条件を確認する。

## これまでのPRE-00539調査結果（2026-11-08）

- RPG Maker UnionはSPA構造。通常HTMLには本文がなく、ページXHR JSONの `messages` と `uploadedFiles` から本文・添付情報を取得できた。
- メッセージは4件。最初の投稿は `Villa_MapLightAndShadow.js` の添付のみ。後続投稿による説明では、変数で影を生成し、角度・透明度・色調などを制御できるとのこと。ただし説明者自身が詳細未確認。
- 利用者からグリッドずれ、画面スクロール時の光の座標ずれが報告されている。TausiLighting、QJ-Lighting V3.0.6への言及は利用者の経験談であり、比較検証ではない。
- 添付画像ID 63827を確認。投稿本文と添付メタデータの取得はできたが、画像の詳しい内容・プラグイン本体の解析は未完了。
- 直接添付URLは登録ユーザー限定表示だった。ユーザー登録後、元スレッド上の添付リンクからダウンロード画面へ進めることを確認。実ファイル保存は未確認。

最終確認日：2026-11-07（JST）
対象：`dr-kuronekoGC/rpgmaker-daily-report` の `main` のみ。
現在の全体状況は `PROJECT_STATUS.md`、長期的な設計判断は `DECISIONS.md` を参照する。

## 旧申し送り（2026-11-07時点・現在は置き換え済み）

以下は当時の作業メモ。現在の作業順は冒頭の最新更新を参照する。

## 最初に行う作業

### 1. 当時のNotionとGitHubのPRE整合性確認

確認済み：
- ユーザーから `NOTION_DATABASE_ID` をGitHub Actions Secretsに登録したとの報告あり。
- Notion接続経由でPRE確認台帳を検索・集計できた。
- Notionは544件。PRE-00001〜PRE-00544が重複なく存在し、URL空欄なし。
- Notionの状態は「済」538件（PRE-00001〜00538）、「未確認」6件（PRE-00539〜00544）。
- GitHubの `data/review/classification_review.json` 544件（resolved 538／open 6）と件数・番号範囲・状態が一致。以前の413件という集計は古い結果であり、131件の同期漏れとは判断しない。

未確認：
- GitHub ActionsのNotion同期Workflowの最新実行ログと実行履歴（どの実行で現在の一致状態になったか）は未確認。
- ただしNotionとGitHubの現在データは、PRE番号・件数・状態・URL空欄の有無で一致しているため、現時点でユーザーによるSecret確認や手動同期は不要。

確認結果：
- 2026-11-07にNotionデータソースを再集計し、544件／固有PRE番号544件／URL空欄0件を確認。
- 状態別件数は「済」538件、「未確認」6件。PRE番号の範囲もGitHub台帳と一致。
- したがって、現時点で追加の手動同期やSecret確認をユーザーに依頼しない。同期Workflowの最新実行ログ確認は、GitHub Actionsの履歴を取得できる場合に限り別途行う。

注意：Notionの「済」は同期スクリプト上、GitHub台帳をresolvedにする意味を持つ。ユーザーが実際に内容を確認したかどうかと、単なる同期状態を混同しない。同期前にNotion全件を一括で「済」に変更しない。

### 2. 当時のAuto-screen定期実行・判定精度の記録

- Run #47（40609231407、2026-10-28）は55テスト成功・分類処理成功後、pushが `fetch first` で失敗。
- 後続Run #48（40758466462）、#49（40760651094）、#50（40761611024）はすべて成功し、pushも成功。したがって、当時のpush競合は後続実行で再発していない。現時点でpush競合の修正作業は不要。
- Run #51（2026-11-07 17:32 JST、手動実行）はsuccess。構文検証・60テストが成功し、未確認6件を検査。
- PRE-00539/00540はHTTP 200だが、取得HTMLに本文ノードがなくmeta description（76〜113文字）のみ取得されたため `body_unverified`。HTML自体にはattachment/download markerがあるが、本文・配布リンクを確認できず、keep_open。
- PRE-00541〜00544はReddit HTTP 403で本文取得不能。いずれもkeep_open。
- 自動解決は0件。`auto_screen_audit.json` と関連ログが更新され、commit `02a4921` のmain push成功。PRE台帳は544件（resolved 538／open 6）のまま。
- Run #47のpush競合は後続Run #48〜#51で再発していない。現在の課題は、RPG Maker Unionの本文取得方式（HTML内に本文がなくSPAらしい構造）と、Reddit 403時の正規取得経路の検討。403回避や本文未確認の強制判定はしない。
- 2026-11-07にworkflowへ毎日23:25 JST（14:25 UTC）のscheduleを追加。workflowファイル変更によるRun #52（42356724457）はsuccess、60テスト成功、6件すべてkeep_open、監査更新のpush成功。これはpush起動での検証であり、scheduleイベント自体の初回発火は未確認。初回予定は2026-11-07 23:25 JST。
- 定期実行は既存の `rpg-maker-daily-report-main` concurrencyグループで他の台帳更新と直列化される。今後、初回schedule runの起動・完了・pushを確認する。
- PRE-00539/00540のRPG Maker Unionページを調査。HTMLは約34KBで `div#app` があるだけ、投稿本文ノードはなく、`meta description` のみ。これはJavaScriptで後から本文を描画するSPA構造と判断。既存HTMLパーサーに公開script URLを監査診断として記録する機能と回帰テストを追加。
- Auto-screen Run #53（42357110004、2026-11-07 17:49 JST、push起動）はsuccess。構文検証・60テスト成功、6件すべてkeep_open、自動解決0件。監査ログで次のbundle URLを確認：`https://rpgmakerunion.ru/dist/js/main.e2fa8446.js`、`https://rpgmakerunion.ru/dist/js/main-legacy.2a16b241.js`、`https://rpgmakerunion.ru/assets/prism.js`。
- 次は公開JavaScript bundleの内容と、そこから参照される公開データ取得先（API等）を調査する。APIが公開されていれば、認証・アクセス制限を回避せず利用可能か確認してから、最小の読み取り専用取得処理を検討する。bundleを取得・解析できなければ未確認として残す。
- Reddit HTTP 403は別課題として扱い、403回避や本文未確認の強制判定はしない。
- 台帳の手動上書き、PRE ID再採番、既読・pending・archiveの削除はしない。

### 3. 当時のPRE未確認項目（現在はすべて解消済み）

対象：PRE-00539、PRE-00541、PRE-00543、PRE-00546。PRE-00540、PRE-00542、PRE-00544、PRE-00545は確認済みのため対象外。
- まず本文取得・配布先・リンク状態を確認する。
- 本文未取得、403/429、タイムアウトだけで素材なしと断定しない。
- 高確度の除外だけを自動処理し、根拠が弱いものは未確認のまま残す。
- ユーザーが既に判断したPRE-00527〜PRE-00538などを二重に確認・登録しない。

### 4. open PR整理（完了済み）

PR #139/#83は2026-11-09に差分確認後クローズ済み。未マージで、ブランチ削除なし。

## 進め方・完了条件

- 原因調査 → 最小修正 → ローカル／回帰テスト → GitHub Actions確認を分ける。
- 「コードがある」「workflowがsuccess」と「外部同期・保存が実際に成功した」を区別する。
- 変更は小さく、一度に一つずつ進める。無関係なリファクタリングをしない。
- 完了・未解決・未確認を明示する。
- ユーザーはプログラミング初心者。必要な操作は画面の場所から一つずつ説明する。
- 明示的な依頼なしに、コード変更、PR作成・更新・マージ、workflow手動実行、デプロイ、データ削除・リセットをしない。
- 作業の節目でこのファイル、`PROJECT_STATUS.md`、必要に応じて `DECISIONS.md` を更新する。

## 直近の確認記録

- 2026-11-07：mainのPRE台帳544件（538 resolved／6 open）、判定記録314件を確認。
- 2026-11-07：Notion PRE確認台帳を再集計し544件を確認。PRE番号・状態・URLの整合性はGitHub台帳と一致。Workflowの実行ログ確認は未実施。
- 2026-11-07：ユーザーより `NOTION_DATABASE_ID` 登録済みとの報告。APIキーのSecret名・有効性とActionsでの同期実行は別途確認する。
- 2026-11-07：mainの管理ファイル3点を更新。PRE台帳・判定記録・収集データは変更していない。


- 2026-11-08：PRE-00539のRPG Maker Unionスレッド本文4件と添付メタデータを確認。ユーザーがサイト登録し、元スレッドの添付リンクからダウンロード画面へ進めることを確認。プラグイン本体の保存・解析は次の作業。
- 2026-11-08：PROJECT_STATUS.mdとNEXT_STEPS.mdを更新。コード・PRE台帳・判定記録・収集状態・Notionデータは変更していない。

- 2026-11-08：PRE-00539は不具合報告が未解決のため素材採用を見送り。今回は情報収集方法の確認までとし、添付ファイルのダウンロード・コード解析は行わない方針を記録。PREはopenのまま維持。

## PRE-00540：プロジェクト一式の配布として確認（2026-11-09）

- ユーザー確認：RPG Maker UnionのスレッドID 2624「2D Animator Editor」は、素材・プラグイン単体ではなくRPG Makerのプロジェクト一式の配布。
- 素材・プラグインの登録対象外として `not_applicable`／resolved にし、GitHub PRE台帳の分類を「プロジェクト配布」として記録。判定記録にも追加。
- Notion同期Run #133（2026-11-09 07:08 JST）でPRE-00540の状態「済」を確認。NotionとGitHubは同期時点で546件（resolved/済539、open/未確認7）で一致。

## PRE-00545：MZプラグインとして確認（2026-11-09）

- ツクマテ投稿本文でGitHubリポジトリ `nolimits-tukool/NLM_MetallicText` を案内。配布元READMEとJavaScript本体、LICENSEを確認。
- RPG Maker MZ用プラグインv1.0.0。文字に金属調グラデーションを付ける。プラグインコマンドなし。パラメータは縞模様の間隔（stripeInc）と暗部アルファ（stripeAlpha）。
- MIT License。MVでも一応動作するとの記載はあるが、文字幅調整時にグラデーションが外れる制約があるため、MZ用として扱う。
- GitHub PRE台帳をdecision=plugin／resolvedに更新し、判定記録にも追加。実機テストは未実施。
- Notion同期Run #133はこの判定更新前のため、次回定期同期でNotionの状態が「済」に変わることを確認する。


## PRE-00543：開発情報カテゴリーとして確認（2026-11-09）

- ユーザー確認：RPG Maker製ゲームをiPhoneで実行するための自作プレイヤーアプリ。
- 素材・プラグインではなく、ゲーム実行環境／開発支援ツールに当たるため、独立した「開発情報」カテゴリーで扱う。
- `classification_review.json` は category=`開発情報`、asset_type=`development_tool`、content_type=`other` として記録し、decision=`confirmed`／resolvedに更新。`review_decisions.json` にも同じ判断を追加。
- 元のRedditページはHTTP 403で本文未取得。分類根拠はユーザーによる内容確認であり、本文を直接取得できたわけではない。
- Notionは次回の定期同期でPRE-00543が「済」になることを確認する。手動Workflow実行は不要。
