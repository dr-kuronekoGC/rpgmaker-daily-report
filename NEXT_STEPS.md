# NEXT_STEPS.md

## 最新更新（2026-11-10 JST）

**この節を現在の作業指示の正とする。** 過去の調査記録は末尾の「完了・過去の記録」に残す。

### 現在の状態
- PRE台帳：546件、resolved 546／open 0。判定記録322件。
- Notion PRE確認台帳：546件すべて存在し、「済」546件／「未確認」0件。PRE-00539・00541・00543・00546も反映済み。
- Notion同期Run #135で4ページ更新（`page_updates: 4`）。Run #136/#137はsuccess・追加更新なし。Notionの実データを直接照合済み。
- Auto-screen Run #56：2026-11-10 08:28 JSTにschedule起動、success。open項目がないため `scanned_item_count: 0`／`auto_resolved_count: 0`。cron `25 14 * * *`（23:25 JST）は変更せず、実行遅延・ばらつきを観察する。
- 2026-11-10の作業開始時main：`5d909fe61ee9f4b05cdfa62fa7e7e763fd71c81d`。管理MD更新後も未マージPRなし。
- 公開検索サイトは別プロジェクト・別チャットで構築中。WordPressを前提にせず、サイト側の構成を確認するまではBOT側の連携設計をデータ互換性の検討に留める。
- 「開発情報」カテゴリーの既存構造調査は完了。PREレビュー台帳とArchiveの分類が一致していない点を確認。コード変更・Archive修正は未実施。

### 次に行う作業（順番に一つずつ）
1. **開発情報の正規データモデルを検討する。** 「ゲームプレイヤー・実行環境」「開発支援ツール」「変換・移植ツール」「互換性・技術情報」と既存のTipsを区別し、content_type／asset_type／新しい詳細分類のどこで表現するのが自然か比較する。まだ実装しない。
2. **PRE判断をArchiveへ反映する方法を検討する。** 現状の `review_decisions.json` はPREレビュー台帳だけを更新し、Archiveは更新しない。PRE-00543のような既存データをどのタイミングで・どの範囲まで直すか、重複・上書きリスクを含めて設計する。データ変更は別途許可を得る。
3. **Slack表示と検索メタデータの整合を検討する。** 現在の「開発情報・Tips」グループにどう接続するか、engine_relevantや検索用詳細項目をどう扱うかを整理する。
4. **自動分類への反映案を作る。** 既存の `development_debug` はプラグイン詳細分類なので流用しない。誤分類リスク・人手レビュー優先・回帰テスト対象を整理し、実装は別途許可を得る。
5. 公開検索サイトとの連携は、別プロジェクト側の実際の技術構成・データ受け渡し方法を確認してから検討する。WordPress前提の設計はしない。

### 作業ルール
- 原因調査 → 最小修正 → テスト → GitHub Actions確認を分ける。
- 「workflow success」と外部サービスへの実同期・保存成功を区別する。
- コード変更、PR作成・更新・マージ、workflow手動実行、デプロイ、データ削除・リセットは、明示的な許可なしに行わない。管理MDの更新は作業節目で行う。
- `seen_*.json`、`seen_global.json`、`pending_items.json`、`data/archive/` を削除・リセットしない。
- 節目ごとに本ファイルと必要な管理MDを更新する。完了・未解決・未確認を明示する。

最終確認日：2026-11-10（JST）
対象：`dr-kuronekoGC/rpgmaker-daily-report` の `main` のみ。

## 完了・過去の記録

以下は経緯を保持するための履歴。現在の作業順・状態の判断には冒頭の「最新更新」を使う。

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
