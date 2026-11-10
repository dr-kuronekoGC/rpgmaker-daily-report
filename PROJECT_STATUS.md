# PROJECT_STATUS.md

## 最新確認（2026-11-10 JST・main）

**この節を現在の状態の正とする。** 以下の過去節は当時の履歴。

- 2026-11-10の作業開始時main：`5d909fe61ee9f4b05cdfa62fa7e7e763fd71c81d`。今回の定期実行確認対象となった最新データ更新コミット：`81b6529f569fd5695d3edbd5d1656a0d087c2d96`（11/10 12:38 JST）。その後の管理MD更新もmainへ反映済み。未マージPR：0件。
- PRE台帳 `data/review/classification_review.json`：546件、resolved 546件／open 0件。判定記録 `data/review/review_decisions.json`：322件。今回、PRE判断・台帳は変更なし。
- Notion PRE確認台帳：546件、確認状態「済」546件／「未確認」0件。PRE-00539・00541・00543・00546もすべて「済」。Notion同期Run #138（11/10 13:08 JST、schedule）はsuccess、ページ更新・新規作成とも0件。Notion実データを直接照合済み。Run #137（08:28 JST、workflow_run）もsuccess。手動Workflow実行はしていない。
- Auto-screen Run #56（11/10 08:28 JST、schedule）はsuccess。構文検証・安全性／リンク判定テスト61件すべて成功。open項目0件のため `scanned_item_count: 0`／`auto_resolved_count: 0`。予定cron `25 14 * * *`（23:25 JST）に対して約9時間遅れて起動。次回cron（11/10 23:25 JST）は今回確認時点（13:41 JST）では未到来。設定は変更せず観察継続。
- RPG Maker Daily Report Run #228（11/10 04:44 JST）と#229（11/10 12:36 JST）はどちらもschedule／success、Slack HTTP 200。#228はArchive +4（合計77）、Global seen +4（4472）、pending 975→961（14件選択）。#229はArchive +1（合計78）、Global seen 4472→4473、pending 962→951（11件選択）。#229の新着はRedditのゲーム紹介1件で、Slackにも掲載された。
- 収集元ヘルスは#228のOK 28/35・PARTIAL 3・ERROR 4から、#229ではOK 30/35・PARTIAL 1・ERROR 4へ改善。#229時点のERRORはcommunity_rpgmaker_su、community_rpgmaker_cn（403）、community_rmplanet（RSS解析エラー）、community_rpgmaker_net（403）。community_rpgmaker_esはページネーション404を含むPARTIAL。HTTP 403や取得失敗をコンテンツ消失とは判断しない。
- pending_items.jsonの残り951件は全件RMRK由来。内訳はRMRK素材情報708、グラフィック235、サウンド7、プラグイン・スクリプト1。resource_intentはnot_resource 724、resource_candidate 177、uncertain 50。951件すべてが `data/archive/2026-10.json`（2,255件）にも存在し、Archive未保存のデータではない。
- ただしRMRKの4カテゴリーは現行 `categories/display.py` の表示マッピングに存在しない。#229ではRMRK由来10件と新着ゲーム1件が選択されたが、Slack本文に表示されたのはゲーム1件。Slack HTTP 200後に選択分がpendingから外れるため、RMRKの過去データはArchiveに残る一方、Slack通知されずにpendingを離れる挙動がある。データ消失ではないが、意図した運用か未確認。pendingの一括削除・リセットは行わず、扱いを別途検討する。
- 2026-11-10のユーザー意見：RMRKは閉鎖予定で今後参照できなくなるため、関連データの削除も選択肢。現時点の推奨は、pending内のRMRK951件だけを整理対象とし、Archiveは履歴・照合用に保持すること。951件はすべて10月Archiveにも存在するが、これはpending件数であり、Archive全体のRMRK件数ではない。Archive全体を削除する影響は未調査。ユーザーから削除実行の明示許可はまだなく、データ変更はしていない。実行前にRMRKが新規収集対象から外れていること、対象件数・識別条件・バックアップ／復元方法を確認する。
- PRE-00539・00541・00543・00546のユーザー判断は既存記録のまま。追加判定なし。
- PR #139/#83は2026-11-09に差分確認後クローズ済み（未マージ、ブランチ削除なし）。現在open PRなし。
- 「開発情報」カテゴリーの既存構造調査は完了。正規データモデル、PRE判断をArchiveへ反映する方法、Slack表示・検索メタデータとの整合は未決定。コード変更・Archive修正はまだ行わない。
- 公開検索サイトは別プロジェクト・別チャットで構築中。サイト側の技術をWordPressと決めつけず、BOT側では既存データの互換性を確認する。サイト実装そのものは扱わない。
- 今回は読み取り確認と管理MD更新のみ。コード、PRE台帳、判定記録、Archive、pending、seenを変更していない。

最終確認日：2026-11-10（JST）

## 過去の確認記録（2026-11-08 JST・main）

以下は2026-11-08時点の履歴。現在の状態は冒頭の2026-11-09節を参照する。

- 対象は `dr-kuronekoGC/rpgmaker-daily-report` のBOTのみ。Webサイト `kuroneko-tavern` は別プロジェクト。
- 2026-11-08のmain確認時点でPRE-00546まで反映。PRE台帳は546件、resolved 538件／open 8件（PRE-00539〜PRE-00546）。この後、2026-11-09にPRE-00540等のユーザー確認・追加調査結果を反映した。
- Auto-screenの2026-11-08実行では、PRE-00539・PRE-00540のRPG Maker Unionページ取得が `SSLError` で失敗し、両方とも `keep_open`。本文がないと判断したわけではなく、未解決のまま維持。
- PRE-00539（RPG Maker Union、スレッドID 2625）をユーザーのブラウザで追加調査。通常HTMLには本文がなく、ページのXHR JSONを取得する方法を確認。`fetch(location.href, {headers: {'X-Requested-With': 'XMLHttpRequest'}})` で `data.messages` と `data.uploadedFiles` を取得できた。
- PRE-00539のメッセージ4件を確認。最初の投稿は `Villa_MapLightAndShadow.js` の添付のみ。後続投稿では、変数を使って影を生成し、角度・透明度・色調などを制御できるとの説明がある。ただし説明者自身が詳細未確認と述べており、仕様確定ではない。
- 同スレッドではグリッドずれ、画面スクロールに対する光の座標ずれの報告がある。利用者の比較対象としてTausiLighting、QJ-Lighting V3.0.6への言及があるが、互換性・優劣の検証結果ではない。
- ユーザーはRPG Maker Unionに登録済み。添付ファイルの直接URLでは登録ユーザー限定メッセージが表示されたが、登録後、元スレッド内の添付リンクをクリックするとダウンロード画面へ進むことを確認。**ファイル本体の保存・内容確認はまだ未確認**。
- 添付ファイルIDは63505。ファイル名は `Villa_MapLightAndShadow.js`。添付画像ID 63827も確認済み。画像URL・ファイルの詳細は必要に応じてスレッドJSONの `uploadedFiles` を参照する。
- 現時点で分かったのはプラグインの概要と利用者報告まで。対応エンジン、正確な機能、プラグインコマンド、ライセンス・再配布条件は未確認。ユーザー判断により、今回はファイル本体のダウンロード・コード解析には進まず、情報収集方法の確認までで終了。
- 投稿にはグリッドずれ・画面スクロール時の光の座標ずれという実用上の不具合報告があり、投稿者も解決できていない。このため現時点で素材としての採用は見送り。ただし環境固有の可能性もあるため、プラグイン自体が恒久的に使用不能とは断定しない。修正報告等があれば再評価可能。
- PRE-00539は情報収集方法の確認まで完了したが、素材の実用性・仕様は未確定のためopen/未解決のまま維持する。
- 今回の調査ではコード、PRE台帳、判定記録、既読状態、pending、archive、Slack通知、Notionレコードを変更していない。管理ファイルのみ更新。

最終確認日：2026-11-07（JST）

## 過去の確認記録（2026-11-07 JST・main）

以下は2026-11-07時点の履歴。現在の状態は冒頭の最新確認節を参照する。

- 対象リポジトリ：`dr-kuronekoGC/rpgmaker-daily-report`。Webサイト `kuroneko-tavern` は別プロジェクトであり、このBOTの作業対象に含めない。
- 確認時のmain最新コミット：`4eb4ff68e8e1306691bee9f0aea417755925395f`（2026-11-06 16:45 UTC、`Update report data`）。直近のコミットは通常のレポートデータ更新。main上の管理ファイル3点を確認した。
- PRE台帳 `data/review/classification_review.json`：544件、resolved 538件、open 6件。未確認はPRE-00539〜PRE-00544（2026-11-07時点）。
- 判定入力 `data/review/review_decisions.json`：314件。末尾にはPRE-00527〜PRE-00538のユーザー判定が記録されている。既存判定を二重登録しない。
- Notion PRE確認台帳：2026-11-07の再集計で544件。PRE-00001〜PRE-00544が重複なく存在し、URL空欄なし。確認状態は「済」538件（PRE-00001〜PRE-00538）、「未確認」6件（PRE-00539〜PRE-00544）。GitHubのclassification_review.json（544件、resolved 538／open 6）と件数・番号範囲・状態が一致。以前の413件という集計は古い結果であり、131件の同期漏れとは判断しない。
- ユーザー確認：`NOTION_DATABASE_ID` はGitHub Actions Secretsに登録済みとのこと。Secretsの値は閲覧できないため、`NOTION_API_KEY` の登録・有効性と、ActionsからのNotion API実アクセスは未確認。過去の「両Secretsが空」という記録は2026-10-28当時の状態であり、現在の状態を示さない。
- Notion同期workflow `.github/workflows/notion-pre-review-sync.yml` は2時間ごと、手動実行、および関連監査workflow完了後に起動する設定。同期スクリプトはGitHub台帳を基準にNotionの不足ページを作成し、Notionの「済」をGitHubのresolvedへ反映する。2026-11-07の再集計ではNotionとGitHubのPRE番号・件数・状態が一致しているため、追加同期は不要。どのActions実行で現在の一致状態になったかという実行ログの追跡のみ未確認。今回、workflowの新規実行は行っていない。
- open PR：#139（管理ファイル更新、head `docs/handoff-refresh-20261028`、base mainから29コミット遅れ）と #83（判定記録）。PR #139の内容は2026-10-28時点の古い状態で、Secrets未設定など現在と異なる記述がある。未マージPRの内容をmainへ反映済みと扱わない。どちらも今回マージしていない。
- Auto-screen：Run #51（42355888989）・#52（42356724457）・#53（42357110004）はsuccess。#53では構文検証・60テスト成功、未確認6件を検査し、PRE-00539/00540はHTTP 200だが本文未取得、PRE-00541〜00544はReddit HTTP 403。6件すべてkeep_open、自動解決0件。#53で監査ログにJavaScriptのscript asset URLを記録する診断を追加し、PRE台帳は544件（resolved 538／open 6）のまま。RPG Maker Unionの2ページともHTMLは約34KB、`div#app`のみで本文ノードなし。script URLは `https://rpgmakerunion.ru/dist/js/main.e2fa8446.js` とlegacy bundle `https://rpgmakerunion.ru/dist/js/main-legacy.2a16b241.js`、ほかprism.js。クライアント側JavaScriptで本文を描画するSPA構造と判断。bundleの取得・解析は未完了。workflowは毎日23:25 JST（14:25 UTC）のschedule設定済みだが、scheduleイベント初回実行は未確認。
- 今回は診断用コード・回帰テストを追加し、Auto-screen #53をpush起動で実行。監査ログのみ更新。PRE台帳（544件、538 resolved／6 open）、判定入力、収集履歴、既読状態、pending、アーカイブ、Slack通知、Notionレコードは変更していない。


最終確認日：2026-10-28（JST）

## 最新確認（2026-10-28）
- mainの最新確認ではPR #138までマージ済み。PRE台帳は531件中523件解決済み、8件未確認（PRE-00524〜PRE-00531）。
- ユーザー確認の9件（PRE-00425、00430、00431、00433、00455、00471、00481、00491、00507）は、`data/review/review_decisions.json` に記録され、`data/review/classification_review.json` でも全件 `resolved`。PR #137で依頼表現の検出と回帰テストを追加済み。
- Classification Audit Run [40609149323](https://github.com/dr-kuronekoGC/rpgmaker-daily-report/actions/runs/40609149323) は成功（292 tests）。通常収集Run [40609352093](https://github.com/dr-kuronekoGC/rpgmaker-daily-report/actions/runs/40609352093) はsuccess。ただしPR #137後のAuto-screen Run [40609231407](https://github.com/dr-kuronekoGC/rpgmaker-daily-report/actions/runs/40609231407) は判定テストまで成功したが、Commit high-confidence resolutions stepで失敗。失敗理由の詳細ログは未確認。
- NotionにはPRE-00524〜PRE-00531の8件を未確認として個別追加した記録があるが、一括件数照合は未完了。Notion同期Run [40658009044](https://github.com/dr-kuronekoGC/rpgmaker-daily-report/actions/runs/40658009044) はsuccess表示でも、同期実行・Secrets設定の有効性はログで再確認する。
- サウンド／グラフィックの検索メタデータはPR #135で実装済み。WordPress側の検索UIは未実装。


分類改善：PR #137（2026-10-28マージ）で、本文に含まれる明示的な依頼表現を検出し、グラフィック／音楽カテゴリに掲載された依頼投稿の誤分類を抑える回帰テストを追加。汎用的な「resource pack」「released」「free to use」だけでは配布済みと断定せず、具体的なダウンロード根拠と区別する。Classification Audit Run [40609149323](https://github.com/dr-kuronekoGC/rpgmaker-daily-report/actions/runs/40609149323) は292テスト成功。ユーザー確認9件の判定は反映済み。PR #134（2026-10-28マージ）で、これまでユーザーが確認済みながらmainに残っていた47件を解決済みに反映した。mainのPRE台帳は531件中8件未確認／523件解決済み。NotionのPRE確認台帳にも残る8件（PRE-00524〜PRE-00531）を「未確認」として登録し、各ページの状態を個別に確認した。Notionの一括再集計は利用上限に達したため未実施。最新のNotion同期Run [40658009044](https://github.com/dr-kuronekoGC/rpgmaker-daily-report/actions/runs/40658009044) では同期処理と同期台帳のコミットがともに成功し、この実行での同期動作を確認。全件数の再集計は別途未完了。
検索メタデータ：PR #135（2026-10-26マージ）で、素材検索用の `file_formats`、グラフィックの `graphic_style` / `graphic_theme`、エンジン検索対象を示す `engine_relevant` を追加。サウンドは `engine_relevant=false` とし、将来のWordPressではエンジン表示・エンジン絞り込みの対象外にする。音声のVOICE分類とグラフィックのmap_object分類も追加。Classification Auditは286テスト成功、Engine Backfill Auditも成功。既存の収集履歴・既読状態・pendingデータは変更していない。WordPress側の検索UI実装は未着手。
PR #125でMaker Devs専用の診断スクリプトと手動実行可能なGitHub Actions workflowを追加。診断Run [40159739308](https://github.com/dr-kuronekoGC/rpgmaker-daily-report/actions/runs/40159739308) でDNS解決成功、3つのIPすべてでTCP接続後にTLS `TLSV1_ALERT_INTERNAL_ERROR`、GET/HEADも同じTLSエラーを確認。TLS検証無効化や未確認ホストへの切替は行わず、Maker Devsは手動確認のみを維持。根本原因がサイト側か接続経路・環境との相性かは未確定。GameDevMarketはPR #124で公開代替ホストへ変更し、Run #196でBaseline保存済み。読み取り専用照合Run [40162817759](https://github.com/dr-kuronekoGC/rpgmaker-daily-report/actions/runs/40162817759) で現在ページのsignatureがBaselineと一致することを確認したが、実際のページ更新を検知する動作は未確認。Source Checkは9/9監視対象を確認、失敗0、手動確認のみ3件。PR #127で診断を拡張し、RPG Refugeの通常ページと公式XenForo RSSをGitHub Actionsから確認。Run [40162535349](https://github.com/dr-kuronekoGC/rpgmaker-daily-report/actions/runs/40162535349) ではDNS/TCP/TLSは成功したが、GETは両URLとも `/.stile/challenge` へ転送され、RSSではなくHTMLチャレンジを返した。HEADは両URLともHTTP 429。通常ページ・公開RSSとも同じアクセス保護に止められており、回避は行わずRPG Refugeは手動確認のみを維持。PR #127とClassification Auditは成功。PR #129でNew RPG Projectのトップページと公開RDFフィードを診断。Run [40162662728](https://github.com/dr-kuronekoGC/rpgmaker-daily-report/actions/runs/40162662728) ではDNS/TCP/TLSは成功したが、トップページと `index.rdf` のGET/HEADがすべてHTTP 403 Forbidden。サイトのトップページとフィードはWeb上で閲覧可能だが、GitHub Actionsからは両方とも取得拒否された。正規の別ホストは確認できず、403を回避しないため手動確認のみを維持。PR #129とClassification Auditは成功。3つの手動確認サイトの調査が一巡したため、次はGameDevMarketの変更検知を検証する。
確認対象：GitHub mainブランチ。PR #113〜#119をマージし、関連テスト・監査を確認。PR #117でPRE-00229の判定メモ差分による定期実行停止、スペイン語フォーラムの2ページ目404による全件破棄、サイト台帳と収集レジストリの不一致を修正した。PR #117の全 tools/test_*.py テストとClassification Auditは成功。
2026-10-23時点ではPRE台帳523件中84件未確認／439件解決済みだった（履歴）。2026-10-28時点の最新値は冒頭の531件中8件未確認／523件解決済み。Rpg2S ITの本文取得品質に関する過去の監査記録は履歴として保持する。
PR #117マージ後の通常収集Run 40042036545（2026-10-24 08:52 JST）は成功。Slack HTTP 200、pending保存、データpushを確認。サイト状況は35収集モジュール中30 OK／2 PARTIAL／3 ERROR。Comunidad RPG Maker ESはページ2の404（先行ページの結果は保持）、RPG Maker SU・RM Planet・RPG Maker Networkは403。Source Checkは12件中8件を確認、4件更新・4件失敗（GameDevMarket 403、Maker Devs TLSエラー、RPG Refugeアクセスチャレンジ、New RPG Project 403）。403/アクセスチャレンジを回避せず、公開RSS/API等の正規代替経路を調査する。RPG RefugeはPR #127の診断で公式RSSも同じアクセスチャレンジに転送されることを確認したため、現時点で安全な自動監視経路は未確認。PR #122（2026-10-25マージ）で失敗を繰り返した4サイトを手動確認のみへ移行。PR #124（同日マージ）でGameDevMarketは公開代替ホスト `mail.gamedevmarket.net/category/2d` がGitHub Actionsから取得可能と確認できたため、自動監視を再有効化。Run #196ではBaseline保存に成功。読み取り専用照合Run [40162817759](https://github.com/dr-kuronekoGC/rpgmaker-daily-report/actions/runs/40162817759) で保存済みsignatureと現在ページが一致し、状態ファイルを書き換えずに照合できることを確認した。実際のページ更新を検知する動作は未確認。現在は9件を自動監視、Maker Devs・RPG Refuge・New RPG Projectの3件を手動確認のみとして表示する。既読・収集データは変更していない。
PR #118（2026-10-24マージ）でOfficial Informationリンクを毎回のSlackレポートに表示するよう変更。公式ニュース、ツクール開発部X、U2U公式Xの日英アカウント、公式フォーラム、YouTube、Discordを掲載する。2026-10-24 22:04 JSTの手動Run 40096568691はリンク切替前のコードで成功。Official InformationのXリンクは、ユーザー提示のU2U公式日本語・英語アカウント（https://x.com/rpgmakeru2u_jp、https://x.com/rpgmakeru2u_en）に切り替えた。変更後の再実行は行わず、次回の通常収集で表示を確認する。Xの投稿日時の自動検知は未実装であり、リンク常設とは別課題として扱う。
PR #119（2026-10-24マージ）で、公式ニュース一覧から個別記事URLと公開日を取得し、Slack項目に記事リンクと「公開日：YYYY.MM.DD」を表示するよう変更。テストは278件すべて成功（[Classification Audit](https://github.com/dr-kuronekoGC/rpgmaker-daily-report/actions/runs/40055876293)）。公式ページに正確な公開時刻が確認できないため、日付のみを表示する。次回の通常収集で実際の公式ニュースが検出された際にSlack表示を確認する。
この文書は長期的な目的・設計方針・実装状況を記録する。次の具体的な作業は NEXT_STEPS.md を参照する。

## 1. プロジェクトの目的

### 現在の目的
RPG Maker／RPGツクールに関連する素材、プラグイン、開発情報などを複数の公式サイト・個人サイト・掲示板・マーケットプレイスから継続的に収集し、重複を抑えながらSlackで確認できるようにする。

### 長期目標
収集・整理した情報を、将来的にWordPress上の検索可能な情報サイト「素材酒場」として活用する。ランキングサイトではなく、素材・プラグイン・開発情報を探しやすくすることを重視する。無料・有料の両方を対象とし、有料であることだけを理由に除外しない。

## 2. 技術スタックと実行環境

- Python（GitHub ActionsではPython 3.12または3.xを使用。ワークフローごとに指定が異なる）
- `requests`、BeautifulSoup等によるHTTP取得・HTML解析
- GitHub Actionsによる定期実行、手動実行、テスト、監査
- JSONファイルによる既読状態、掲載待ち、アーカイブ、分類レビュー、判定記録の永続化
- Slack Incoming Webhookによるレポート通知
- Notion PRE確認台帳との同期機能（GitHub Actions Secretsが必要。確認時点ではSecrets未設定により同期がスキップされている）
- 開発・コード管理：GitHub。開発時のユーザー環境はWindows／VS Codeを想定（現在の端末環境はこの台帳作成では未確認）

秘密情報そのものはこの文書に記載しない。Webhook URL、APIキー、トークンはGitHub Actions Secretsで管理する。

## 3. ディレクトリと主要ファイル

### 収集・実行
- `main.py`：収集元を順次実行し、項目の正規化、重複処理、レビューキュー、アーカイブ、レポート送信等を統括する。
- `sources/registry.py`：定期実行する収集元の登録一覧。収集元の追加・削除時は、原則としてここを確認する。
- `sources/`：各サイト・掲示板・マーケットプレイス等の個別収集処理。
- `config.py`：収集URL、カテゴリ別設定、各種上限等。
- `common.py`：状態ファイル、共通処理等。
- `item_model.py`：収集項目の正規化、安定ID、サイトメタデータ等。
- `language.py`：言語判定。
- `archive.py`：アーカイブ保存。
- `report.py`、`report_formatters.py`：レポート作成・整形。
- `slack_client.py`：Slack送信処理。

### 分類・メタデータ
- `asset_metadata.py`：素材種別、ライセンス・価格、分類、詳細カテゴリ等のメタデータ構築。
- `asset_metadata_engine.py`：対応するRPG Makerエンジンの判定。
- `asset_metadata_fields.py`：分類・ライセンス・価格等のフィールド定義と補助判定。
- `asset_metadata_intent.py`：素材・プラグイン等の目的判定。
- `classification_rules.py`、`classification_scoring.py`：分類規則・根拠スコアリング。
- `categories/`：素材、フォーラム、公式情報、Steam、itch.io等のカテゴリ判定。

### レビュー・監査
- `review_queue.py`：PREレビューキューの生成、持ち越し、既存項目の監査。
- `data/review/classification_review.json`：PRE項目の永続的なレビュー台帳。2026-10-28に確認した最新状態は531件（未確認8件、解決済み523件）。
- `data/review/review_decisions.json`：明示的に記録された判定を日次処理に取り込むための入力。2026-10-28確認時点で299件の判定レコード。
- `tools/apply_review_decisions.py`：判定記録の検証・取り込み。
- `tools/auto_screen_open_reviews.py`：未確認PREの自動スクリーニング。本文・配布先・リンク状態等を使い、高確度の項目のみ自動処理する。
- `tools/fetch_historical_review_bodies.py`：レビュー済み項目等の本文・リンクを取得する監査用処理。通常のレビュー台帳を直接変更する目的ではない。
- `tools/audit_review_links.py`、`tools/audit_open_review_queue.py`：リンク状態・レビュー対象の監査。
- `tools/sync_notion_review.py`：Notionの確認状態とGitHub台帳の同期。
- `tools/test_*.py`：各機能の回帰テスト。

### データ・運用資料
- `data/sites/sites.json`：収集元ID、名称、種別、言語、状態等のサイト台帳。内部IDは安定識別子として扱い、理由なく変更・再採番しない。
- `data/archive/`：収集した履歴データ。
- `data/schema/`：データ形式関連。
- `data/forum_vault/`：フォーラム関連の保存データ。独立したForum Vaultの運用範囲・連携状態は、この確認だけでは詳細未確認。
- `seen_*.json`、`seen_global.json`：収集済み項目の状態。
- `pending_items.json`：Slack通知等の掲載待ち状態。
- `docs/OPERATIONS.md`：運用・障害時の基本方針。
- `docs/classification-policy-analysis.md`：人手で確認したPRE事例に基づく分類方針の分析。
- `docs/source-category-taxonomy.md`：収集元の種類と言語・収集意図の整理。
- `docs/review-decision-import.md`、`docs/notion-pre-review-sync.md`：判定記録・Notion同期の手順。
- `PROJECT_STATUS.md`：長期的なプロジェクト台帳（本ファイル）。
- `NEXT_STEPS.md`：短期的な作業台帳。

## 4. 主要機能と確認状況

「実装済み」はコードや設定が存在すること、「動作確認済み」は確認できたテスト・Actions実行の範囲を意味する。すべてのサイトが常時正常に取得できることを保証するものではない。

| 機能 | 実装状況 | 確認状況・制約 |
|---|---|---|
| 複数サイトからの収集 | 実装済み | `sources/registry.py` に35収集モジュールを登録。サイトごとの直近稼働状況は個別ログで確認が必要 |
| 既読・重複処理 | 実装済み | URLを基本にグローバル重複判定。Source Checkは同一URLを繰り返し使うため例外扱い |
| 掲載待ち・アーカイブ | 実装済み | JSON状態ファイルを利用。通常運用で手動削除・リセットしない |
| Slackレポート | 実装済み | 成功前に掲載済みとして状態を進めない方針。各実行のHTTP結果・通知結果はログで確認する |
| 言語・素材種別・エンジン分類 | 実装済み | 分類コードと回帰テストあり。個別項目の誤分類が完全になくなったことは未確認 |
| PREレビュー台帳・判定取込 | 実装済み | 2026-11-09確認時点で546件すべてresolved。判定記録322件。Notionへの最新反映は次回定期同期後に照合する |
| 未確認PREの自動スクリーニング | 実装済み・継続改善中 | 2026-11-09時点でPRE台帳のopen項目なし。Auto-screenは毎日23:25 JST設定。実行時刻の遅延を継続観察中。過去のpush競合は後続実行で成功を確認済み |
| リンク監査 | 実装済み | 404/410等を検査する。403/429、タイムアウト、ネットワークエラーをリンク切れと同一視しない |
| Notion同期 | 実装済み・定期同期の反映確認待ち | NOTION_API_KEY と NOTION_DATABASE_ID はユーザーがActions Secretsへ登録済み。過去のRun #134で同期成功を確認したが、最新PRE判定の反映は次回定期同期後に照合する |
| WordPress公開・検索サイト | 構想段階 | 本リポジトリで完成済みとは確認できない |
| 収集データ全体の正確性・網羅性 | 継続改善中 | サイト側の仕様変更、アクセス制限、取得範囲の差があり、全収集元を一括して保証できない |

## 5. GitHub Actionsの運用

| Workflow | 主な役割 | 起動方法・注意点 |
|---|---|---|
| `RPG Maker Daily Report` | 通常収集・レポート | 毎日2回（日本時間おおむね6:15・18:15）および手動実行 |
| `Auto-screen Open Review Items` | 未確認PREの本文・配布リンク等を確認し、高確度項目を自動処理 | 手動実行、および関連コード／ワークフロー変更時のmainへのpush |
| `Auto-screen triage tests` | 自動仕分けの安全性テスト | 関連ファイルを変更するPull Request |
| `Review Link Audit` | リンク監査・レビューキュー監査 | 手動実行、または関連コード変更時 |
| `Classification Audit` | 分類・レビュー台帳の監査 | ワークフロー定義を参照。各監査提案が台帳を直接変更するとは限らない |
| `Historical Review Body Audit` | 過去のレビュー項目の本文取得 | 手動実行または関連ファイル変更時。監査結果は成果物として保存 |
| `Notion PRE Review Sync` | NotionとPRE台帳の同期 | 2時間ごと、手動実行、関連監査ワークフロー終了後。Secretsは登録済み。最新判定の反映は次回定期同期後に確認 |

- 通常収集ワークフローは、収集状態・掲載待ち・アーカイブ・レビュー台帳等をGitに保存する。
- PRE IDの採番やレビュー台帳を変更するワークフローは、競合を避けるため同じconcurrencyグループ `rpg-maker-daily-report-main` を使用する。自動スクリーニングにも2026-10-22に設定を追加した。さらに待機中のイベントSHAが古くなる問題を避けるため、最新mainをcheckoutするよう指定した。設定後の自動スクリーニング結果がmainへ反映され、台帳更新が保存されたことを確認済み。今後も実行ごとにpushと件数を確認する。
- リセット系ワークフローも存在する。データ消失を防ぐため、ユーザーが明示的に希望しない限り実行しない。
- 「Actionsがsuccess」と表示されても、外部サービスとの同期が実際に行われたとは限らない。ログのSkipped、処理件数、最終コミットまで確認する。

## 6. 確定済みの設計方針・制約

1. **収集データを保全する。** `seen_*.json`、`seen_global.json`、`pending_items.json`、`data/archive/`、`data/review/` を通常の障害対応で削除しない。リセットは明示的な承認が必要。
2. **リンク確認は証拠に基づく。** HTTP 404/410や明確な削除表示は強い証拠だが、403/429、タイムアウト、TLS・ネットワーク障害は「存在しない」根拠にしない。
3. **有用な素材と有料商品は対象。** 無料／有料だけで除外しない。商品・配布物そのものと、短期セール・抽選告知だけの投稿を区別する。
4. **配布素材と質問・相談・制作日記・ゲーム紹介を区別する。** タイトルだけで断定せず、利用可能な本文、タグ、添付、配布リンク等を参照する。
5. **自動判定は高確度に限定する。** 人手の修正・例外を尊重する。未確定のものを、確認件数を減らす目的だけで無理に解決しない。
6. **分類の意味を混同しない。** PREの `decision` 値だけをそのまま機械学習の正解ラベルとみなさず、用途・採否・根拠・理由を分けて扱う。
7. **サイトIDと履歴を保つ。** `data/sites/sites.json` のIDは安定識別子。停止サイトの既存データも、理由なく消去しない。
8. **変更は小さく、検証可能にする。** 関連テストを追加・実行し、Pull RequestやActionsログで根拠を確認する。長いファイルを分割する場合も、重複処理や既存動作への影響を先に評価する。
9. **説明・コード変更は初心者にも追える形にする。** 大きなコード変更を提案する場合は、目的、リスク、確認方法を説明し、必要時には修正後のファイル全文を提示する。

## 6.1 収集元ヘルス確認の履歴（2026-10-20〜10-25）

以下は当時の診断記録であり、現在の収集状態を示すものではない。最新の稼働状況はActionsの直近実行ログで確認する。

Run 39347372727では、35収集モジュールのうち31件がOK、1件がPARTIAL、3件がERRORだった。

- **Comunidad RPG Maker ES**：APIの1ページ目は取得できたが、次ページURLがHTTP 404となり、従来コードでは収集全体が失敗扱いになっていた。PR #117で、取得済みページの結果を保持しつつ失敗リクエストをヘルス情報に残すよう修正。
- **RM Planet**：RSSがHTTP 403。アクセス制限を回避せず、現状は取得失敗として扱う。
- **RPG Maker Network**：リソースページがHTTP 403。アクセス制限を回避せず、現状は取得失敗として扱う。
- **Source Check（2026-10-24以降）**：PR #122で失敗を繰り返した4サイトを手動確認のみへ変更。PR #124でGameDevMarketを公開代替ホストへ変更し、Run #196でBaseline保存を確認（変更検知は未確認）。Maker Devs診断Run #3ではDNS解決成功、3つのIPすべてでTCP接続後のTLSハンドシェイクが失敗し、GET/HEADもTLSエラー。根本原因は未確定のため、Maker Devsは手動確認のみを維持。現在は9件監視・3件手動確認のみ、failed=0。アクセス制限の突破やTLS検証の無効化は行わず、正規の公開経路を利用する。
- **サイト台帳**：GameDev MarketとMaker DevsはSource Checkで監視されているが、定期収集レジストリには登録されていない。data/sites/sites.json の collection を false に修正し、状態表示を実態に合わせた。RMRKも新規収集対象外のまま履歴を保持する。

2026-10-25：PR #122で4サイトを手動確認のみへ移行し、Classification Auditで280テスト成功。その後PR #124でGameDevMarketを公開代替ホストへ変更して監視を再有効化。Run #196で取得・Baseline保存を確認したが、変更検知は未確認。現在は監視対象9件、手動確認3件。

PR #117マージ後の通常収集で、各項目が改善・継続・解消のどれに当たるか再確認する。

## 7. 今後の課題

- 「開発情報」カテゴリーについて、既存の分類コード、自動判定、検索メタデータ、検索対象を調査する。PRE-00543の個別手動分類を、そのまま自動分類ルールに拡張しない。
- 開発情報の分類候補（ゲームプレイヤー・実行環境／開発支援ツール／変換・移植ツール／互換性・技術情報）を既存構造と照合し、必要性・粒度・誤分類リスクを検討する。
- PREの自動分類精度を継続改善する。人手で戻された項目や境界事例は回帰テスト候補として扱う。
- 収集元の取得状態は変動するため、必要に応じてSource Healthとサイトごとのログを確認する。
- 公開検索サイトとの連携に向け、BOT側の既存メタデータと実データ品質を確認する。サイト側の技術構成・検索UIは別プロジェクトで確認し、BOT側で先回りして決めない。

## 8. 将来的な構想（未実装・進行中を含む）

- 素材・プラグイン・開発情報を探しやすい公開検索サイトとの連携。
- 素材種別、プラグイン用途、対応RPG Maker、言語、作者、利用条件、価格、公開・更新日など、検索に必要な項目を整理する。
- 開発情報も素材・プラグインと混同せず、内容に応じた検索・絞り込みを可能にする。
- BOTで蓄積したデータを維持し、サイト側の実装・データ形式を確認してから移行方法を決める。WordPress等の特定プラットフォームを前提にしない。
- 自動分類の品質を高めるため、過去の人手判定を構造化した回帰テストデータとして活用する。
- 収集元の追加・保守を継続し、更新頻度や情報の有用性を考慮して情報源を選ぶ。

## 9. 更新ルール

- 本ファイルは、目的、主要な構造、確定方針、実装状況、長期課題が変わったときに更新する。
- 具体的な作業順、直近のActions結果、承認待ち事項は `NEXT_STEPS.md` に記録する。
- GitHubの実状態と会話上の合意を区別する。未確認事項は推測で埋めず「未確認」と記載する。
- 秘密情報を記載しない。

- 2026-11-09：PRE-00540（RPG Maker Union、スレッドID 2624）は、ユーザー確認により素材・プラグインではなくRPG Makerプロジェクト一式の配布と判明。`classification_review.json` を「プロジェクト配布」として記録し、素材・プラグインの登録対象外（`not_applicable`／resolved）に更新。判定記録にも追加。Notionへの反映は次回の同期実行待ち。
