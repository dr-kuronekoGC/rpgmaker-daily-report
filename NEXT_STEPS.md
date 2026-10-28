# NEXT_STEPS.md


## 次のチャットで最初に確認すること（2026-10-28）
1. `data/review/review_decisions.json` の9件と `data/review/classification_review.json` の状態は反映済み。まず二重更新せず、必要ならNotion側の9件の状態だけ確認する。
2. Auto-screen Run [40609231407](https://github.com/dr-kuronekoGC/rpgmaker-daily-report/actions/runs/40609231407) はcommit stepで失敗。Actionsの該当stepログを開き、認証・push権限・競合等の原因を特定する。スクリーニング判定自体とGitHubへの保存失敗を分けて扱う。
3. main台帳は531件中8件未確認（PRE-00524〜PRE-00531）。Notionの一括再集計は上限で保留。Notion同期のsuccess表示を実同期完了とみなさず、Secretsとログを確認する。
4. 次に分類精度を改善するときは、今回9件の人手判定を参考に、(a)素材配布と依頼・雑談・紹介の区別、(b)リンク切れ／アクセス不能と素材種別の区別、(c)個別の除外判断を一般ルールへ拡張しすぎない、を回帰テストで守る。
5. WordPress検索向けメタデータはPR #135済み。次段階は検索項目とUIの設計であり、現時点でWordPress実装はない。


最終確認日：2026-10-28（JST）
対象ブランチ：`main`。PR #137（[Improve resource-intent classification from review feedback](https://github.com/dr-kuronekoGC/rpgmaker-daily-report/pull/137)）を2026-10-28にマージ。Classification Audit Run [40609149323](https://github.com/dr-kuronekoGC/rpgmaker-daily-report/actions/runs/40609149323) は292テスト成功。英語・ロシア語・日本語の明示的な依頼表現を本文から検出し、素材カテゴリの掲示板でも依頼投稿を素材候補と誤認しにくくした。曖昧な「resource pack」「released」「free to use」等だけでは配布の確証にしない。具体的なダウンロード根拠は依頼語より優先する。
今回のユーザー確認9件（PRE-00425、00430、00431、00433、00455、00471、00481、00491、00507）は `data/review/review_decisions.json` に記録済み。判定ファイルは299件。PR #134（2026-10-28マージ）で、過去にユーザー確認済みだった47件のPRE状態・分類メモをmainへ反映した。現在のmainレビュー台帳は531件中8件未確認／523件解決済み。NotionにもPRE-00524〜PRE-00531の8件を「未確認」として追加し、各ページの状態・URLを個別に確認した。NotionのQuery Data Source利用上限に達したため、一括件数の再集計は保留。GitHub ActionsのNotion同期Secretsが未設定の記録があるため、自動同期は未確認。通常収集の次回実行でSlack表示が8件に追随するか、Actionsログと出力を確認する。
PR #135（2026-10-26マージ）でWordPress検索向けメタデータ（`file_formats`、`engine_relevant`、`graphic_style`、`graphic_theme`、音声VOICE分類、グラフィックmap_object分類）を追加済み。サウンドはエンジン検索の対象外。WordPress側の検索UIは未実装。

## 直近完了：WordPress検索向け素材メタデータ

**状態：PR #135マージ済み（2026-10-26）。** [PR #135](https://github.com/dr-kuronekoGC/rpgmaker-daily-report/pull/135)

- `file_formats`：音声形式（MID/MIDI、OGG、M4A、MP3、WAV、WMA、FLAC、AIFF/AIF）と画像形式を、タイトル・タグ・説明・本文に明示された場合だけ記録。素材ページURLの拡張子だけから配布形式を推測しない。
- `engine_relevant`：サウンドはfalse。将来のWordPressではエンジン情報を表示せず、エンジン指定検索でもサウンド素材を除外しない。グラフィック・プラグイン・ゲームはtrue。エンジン情報が不明なグラフィックを検索から除外しない。
- `graphic_style`：ドット絵、イラスト、アニメ調、写実、ベクター、フラット等を明示的な語句から抽出。
- `graphic_theme`：ファンタジー、現代、SF、和風、ホラー、中世、サイバーパンク、自然、都市等を明示的な語句から抽出。
- 用途分類に `map_object` を追加し、音素材はVOICEを独立分類。
- 不明な特徴は空リストのまま保持し、「その特徴がない」とは解釈しない。
- Classification Audit：286 tests passed。Engine Backfill Audit：success。
- WordPressの検索画面自体は未実装。次の段階で、WP側のフィルターとこのメタデータの対応付けを設計する。


このファイルは、次回のチャットや作業で再開するための短期台帳。完了と記載するのは、実行結果を確認できた作業だけとする。長期方針は `PROJECT_STATUS.md` を参照する。

## 1. 最優先：通常収集の復旧確認

**通常収集の復旧を確認済み。** [PR #117](https://github.com/dr-kuronekoGC/rpgmaker-daily-report/pull/117) は2026-10-23にマージ済み。Run 40042036545（2026-10-24 08:52 JST）は成功し、Slack送信とデータ保存を確認。

- PRE-00229は判定値が既存記録と一致していれば、メモに接頭辞等の差があっても既存メモを保持して取込を継続する。異なる判定値は引き続き拒否する。
- 復旧確認：[Run 40042036545](https://github.com/dr-kuronekoGC/rpgmaker-daily-report/actions/runs/40042036545)（2026-10-24 08:52 JST）。Run script、Slack送信（HTTP 200）、pending保存、GitHubへのデータpushが成功。
- 現在のサイト状況：35収集モジュール中30 OK／2 PARTIAL／3 ERROR。Comunidad RPG Maker ESはページ2の404（1ページ目の結果は保持）、RPG Maker SUとRM PlanetとRPG Maker Networkは403。403はアクセス制限を回避せず、公式の公開RSS/API等の代替経路を探し、なければ取得失敗として監視する。

PR #122マージ前のSource Checkは12件中8件を確認、4件更新・4件失敗。失敗はGameDevMarket 403、Maker Devs TLSエラー（再試行後も失敗）、RPG Refugeのアクセスチャレンジ、New RPG Project 403。いずれも2026-10-24のログで再確認した。PR #122で4サイトを手動確認のみへ移行したが、PR #124でGameDevMarketは `mail.gamedevmarket.net/category/2d` から取得可能と確認できたため監視を再有効化。Run #196ではBaseline保存まで成功し、変更検知はまだ未確認。現在はMaker Devs・RPG Refuge・New RPG Projectの3サイトを手動確認のみとし、参考リンク欄で「自動監視：保留」と表示する。公式ページやSNSリンクはレポートに常設する方針。Xの投稿日時を安定して自動取得する仕組みは未実装で、今回のリンク追加だけでは「更新検知」にはならない。

### P0 — Source Checkサイトの接続問題を1サイトずつ解決する
**状態：Maker Devs・RPG Refuge・New RPG Projectの接続調査は完了。安全な自動監視経路を確認できず、3サイトとも手動確認のみを維持。次はGameDevMarketの変更検知を検証する。**

- PR #122で4サイトを手動確認のみへ変更した後、PR #124でGameDevMarketを `https://mail.gamedevmarket.net/category/2d` に変更し、監視を再有効化。
- [Run #196](https://github.com/dr-kuronekoGC/rpgmaker-daily-report/actions/runs/40157459003)：Source Checkは `checked=9/9 monitored / manual_only=3 / updated=1 / baseline=1 / unchanged=7 / failed=0`。GameDevMarketはBaseline保存まで確認済みで、変更検知は未確認。
- [読み取り専用照合Run](https://github.com/dr-kuronekoGC/rpgmaker-daily-report/actions/runs/40162817759)：GameDevMarketのHTTP GET/HEADはいずれも200。通常収集と同じ `build_signature` で計算した現在のsignatureは保存済みBaselineと一致した。診断は `seen_source_check.json` を書き換えず、実際の変更検知やSlack通知を発生させない。次回の実際のページ更新時にSource Checkが検知するかは継続確認。
- Maker Devs専用の診断を [Run #3](https://github.com/dr-kuronekoGC/rpgmaker-daily-report/actions/runs/40159739308) で実施。DNSは3つのIPアドレスを返し、3つすべてでTCP接続後のTLSハンドシェイクが `TLSV1_ALERT_INTERNAL_ERROR` で失敗。通常のHTTPS GET/HEADも同じTLSエラー。DNS不調、TCP接続失敗、HTML解析の問題ではないことを確認したが、サーバー側設定とGitHub Actionsとの相性等のどれが根本原因かは確定できない。
- RPG RefugeはPR #127の [診断Run](https://github.com/dr-kuronekoGC/rpgmaker-daily-report/actions/runs/40162535349) でDNS/TCP/TLSが成功した一方、通常ページと公式XenForo RSSのGETは両方とも `/.stile/challenge` に転送され、HTMLのアクセスチャレンジを返した。両URLのHEADはHTTP 429。RSSも代替経路にならず、HTTP 200のチャレンジページを有効な内容として扱わない現在の保護は妥当。
- TLS検証の無効化、アクセスチャレンジの突破、未確認ホストへの切替は行わない。Maker Devs・RPG Refugeとも参照リンクを残し、自動監視は保留。正規の代替フィード・ホストは確認できていない。
- New RPG ProjectはPR #129の [診断Run](https://github.com/dr-kuronekoGC/rpgmaker-daily-report/actions/runs/40162662728) でトップページと公開RDFフィードの両方を確認。DNS/TCP/TLSは成功したが、GET/HEADはすべてHTTP 403 Forbidden。Web上ではサイトとフィードへのリンクを確認できる一方、GitHub Actionsからは両URLとも拒否され、正規の代替ホストは未確認。アクセス制限は回避せず、New RPG Projectは手動確認のみを維持。Maker Devs・RPG Refuge・New RPG Projectの3サイトの接続調査が一巡したため、次はGameDevMarketの変更検知を検証する。既読状態、pending、archive、収集履歴は変更しない。テスト、実地取得、Baseline保存、変更検知を別々に記録する。

## 2. 現在の優先課題

### P0 — Official InformationリンクをSlackに常設する
**状態：PR #118マージ済み。次回の通常収集でSlack表示を確認する。**

- [PR #118](https://github.com/dr-kuronekoGC/rpgmaker-daily-report/pull/118) をマージ。`Official Information` 欄に公式ニュース、ツクール開発部X、U2U公式Xの日英アカウント、公式フォーラム、YouTube、Discordを毎回表示する。
- 新着がない日でも、公式情報の入口から確認できる。
- Xの投稿日時を自動で取得して「更新あり」と表示する機能はまだない。公式ニュースの新着検知とは分けて扱い、次段階では公式RSS/API等の安定した取得経路を調べる。未検証の非公式Xスクレイピングや、投稿があったと断定する表示は導入しない。

### P1 — 公式ニュースの個別記事URL・公開日を表示する
**状態：PR #119マージ済み。278件のテスト成功。次回の通常収集で実データ表示を確認する。**

- [PR #119](https://github.com/dr-kuronekoGC/rpgmaker-daily-report/pull/119) をマージ。公式ニュース一覧の見出しから個別記事URL（例：`/news/4157/`）とページ上に表示される公開日を取得する。
- Slackの公式ニュース項目は一覧ページではなく記事本体にリンクし、日付を `公開日：YYYY.MM.DD` と表示する。
- 公式サイトで確認できるのは日付であり、正確な時刻は見つかっていないため時刻を推定・表示しない。
- 過去の既読状態は見出し文字列でも照合し、新規分はURLを既読キーとして保存してタイトル変更に強くする。
- 記事リンクがHTMLから確認できない場合はURLを推測せず、その見出しを採用しない。
- Classification Auditの全278テストが成功（2026-10-24）。次回の通常収集で、公式ニュースが新着として検出された際のSlack表示を確認する。既に既読のニュースを再送していないため、マージ直後に新着がなければ実地表示の確認は次の新着まで保留となる。

## 3. 現在の優先課題

### P1 — 未確認PREの自動仕分け精度を改善する
**状態：PR #137の分類改善はmainへマージ済み。次はActions保存エラーの原因確認と、Notion／Slackへの反映確認。**

- ユーザーが確認したPRE-00425、00430、00431、00433、00455、00471、00481、00491、00507の9件は、`data/review/review_decisions.json` に記録済みで、`data/review/classification_review.json` でも全件resolved。二重に台帳更新しない。
- PR #137（[Improve resource-intent classification from review feedback](https://github.com/dr-kuronekoGC/rpgmaker-daily-report/pull/137)）で、本文中の明示的な依頼表現（英語・ロシア語・日本語）を検出し、素材カテゴリの投稿でも依頼を配布物と誤認しにくくした。曖昧な「resource pack」「released」「free to use」だけでは配布済みと断定しない。具体的なダウンロード根拠があればそれを優先する。
- Classification Audit Run [40609149323](https://github.com/dr-kuronekoGC/rpgmaker-daily-report/actions/runs/40609149323)：292テスト成功。
- Auto-screen Run [40609231407](https://github.com/dr-kuronekoGC/rpgmaker-daily-report/actions/runs/40609231407)：構文・分類安全テスト・監査は成功したが、「Commit high-confidence resolutions」stepで失敗。次はそのstepの詳細ログを確認し、原因を特定する。分類判定の失敗と、GitHubへの保存失敗を混同しない。
- mainのレビュー台帳は531件中523件resolved／8件open（PRE-00524〜PRE-00531）。Notionに8件を個別追加した記録はあるが、一括件数再集計は上限で保留。Notion同期のsuccess表示だけで実同期済みと判断しない。
- 次回の通常収集後にSlackの未確認PRE一覧が最新台帳に追随したか確認する。通常収集Run [40609352093](https://github.com/dr-kuronekoGC/rpgmaker-daily-report/actions/runs/40609352093) はsuccessだが、変更後のSlack表示はまだ確認できていない。
- 自動分類をさらに改善する場合は、人手判定を回帰テストに追加し、リンク切れ・アクセス不能（可用性）と素材種別（分類）を分離する。個別の「ツール紹介」等を根拠に広範な一律除外ルールを作らず、有用素材の誤除外防止を優先する。
- PR #113〜#115で本文品質判定、本文URL検出、明示的なアップロード依頼、再着色依頼・取り下げ検出を追加済み。詳細な過去監査はGit履歴・過去記録を参照する。古い84件／439件の数字は2026-10-23時点の履歴であり、現在値ではない。

### P2 — Notion PRE確認台帳との実同期を有効化する
**状態：コード実装済み、外部接続は未完了。ユーザー作業が必要。**

直近の `Notion PRE Review Sync` はActions上でsuccessだが、ログで `NOTION_API_KEY` と `NOTION_DATABASE_ID` が空と確認され、同期処理はスキップされた。

**必要な作業**
1. Notion側で内部インテグレーションを用意し、PRE確認台帳データベースを共有する。
2. GitHubリポジトリの `Settings → Secrets and variables → Actions` に `NOTION_API_KEY` と `NOTION_DATABASE_ID` を登録する。秘密値はチャットやこのファイルに貼り付けない。
3. Actionsから `Notion PRE Review Sync` を手動実行する。
4. ログにSkippedがないこと、同期件数、GitHub側の台帳コミット、Notion側の確認状態を照合する。
5. GitHubとNotionの未確認一覧が一致するかを確認する。

Notion同期を使わない場合、この項目は保留のままでよい。

### P3 — 未マージの判定記録PRを確認する
**状態：承認待ち。**

PR #83: [Record review decisions for PRE-00163 to PRE-00174](https://github.com/dr-kuronekoGC/rpgmaker-daily-report/pull/83)

タイトルはPRE-00163〜PRE-00174だが、実際の差分にはPRE-00177、PRE-00179、PRE-00180、PRE-00186、PRE-00190も含まれる。`data/review/review_decisions.json` のみを変更し、質問・相談、収集対象外、リンク切れ、修正依頼等の判定を記録する内容。確認時点ではopenであり、`main` に反映済みとは扱わない。

**必要な作業**
1. PRの差分と各PREの判断内容を確認する。
2. 判断に同意できる場合に限り、承認・マージする。
3. マージ後に日次ワークフローまたは該当する判定取込処理を実行し、対象PREが正しく解決済みになることを確認する。
4. 台帳・Notionを使う場合は、両者の状態を照合する。

## 4. 今回の独立評価：精度改善の有望点

1. **Rpg2S ITの本文取得に問題がある可能性が高い。** 未確認41件すべてで本文長が300文字未満、配布リンク候補ゼロ。代表例ではHTTP 200・HTML約14万文字なのに、抽出結果はタイトル・作者・カテゴリ等の約170〜220文字で、本文セレクタは `#ipsLayout_mainArea` にフォールバックしている。代替URL・Waybackも同様。投稿本文がないのに `body_found` と記録されているため、本文取得の成功判定を厳密にする必要がある。本文を取得できない間は、リンクがないことを理由に自動除外しない。

2. **RMRKの本文内プレーンテキストURLを拾えていない可能性がある。** 未確認28件中16件は本文長300文字未満。PRE-00343などでは画像URLが本文文字列に直接記載されているが、現在の候補抽出はHTMLのリンク要素中心。本文中の明示的なHTTP(S) URLも検査候補に追加するのが有望。ただしプレビュー画像と実素材の区別を回帰テストする。

3. **本文を取得できている項目に限って、非素材の目的を見分ける。** 質問・素材募集・制作依頼受付・個人制作日記は候補だが、配布根拠がないことだけで断定しない。人手の「自動判定を取り消し／未確認に戻す」注記は必ず優先する。PRE-00471・PRE-00507などの再確認指定は自動解決しない。

次の実装順は、(a)本文取得の品質判定、(b)本文内URLの検出と境界テスト、(c)取得済み本文での非素材判定の改善。単なるタイトル語彙の追加を先行させない。

## 5. 直近で確認できた作業結果

- 現在のmain上のレビュー台帳は523件中、未確認84件・解決済み439件（2026-10-23にGitHubから直接確認）。
- 以前の自動スクリーニング実行 [Run 39750871482](https://github.com/dr-kuronekoGC/rpgmaker-daily-report/actions/runs/39750871482) は最初のpushが拒否されたが、競合対策後にPRE-00171・PRE-00231の結果がmainに反映された。PR #113後の [Run 39804761982](https://github.com/dr-kuronekoGC/rpgmaker-daily-report/actions/runs/39804761982)、PR #114後の [Run 39865772273](https://github.com/dr-kuronekoGC/rpgmaker-daily-report/actions/runs/39865772273)、PR #115後の [Run 39866632518](https://github.com/dr-kuronekoGC/rpgmaker-daily-report/actions/runs/39866632518) はすべて成功し、PRE-00226・PRE-00367・PRE-00370が解決済みとしてmainに反映された。
- PR #110（[Recognize named legacy RMRK attachment downloads](https://github.com/dr-kuronekoGC/rpgmaker-daily-report/pull/110)）はコミット 09d3e306c91762c126c7fe25594a0e7dce7d17c6 でマージ済み。
- PR #113（[Improve review body verification and plain-text URL detection](https://github.com/dr-kuronekoGC/rpgmaker-daily-report/pull/113)）、PR #114（[Recognize solved requests to upload resources](https://github.com/dr-kuronekoGC/rpgmaker-daily-report/pull/114)）、PR #115（[Recognize withdrawn and explicit recolor requests](https://github.com/dr-kuronekoGC/rpgmaker-daily-report/pull/115)）はマージ済み。関連テスト・Classification Audit・各マージ後の自動スクリーニングはいずれも成功。PRE-00226・PRE-00367・PRE-00370を解決。本文内URL抽出が実データ上の新しい候補を生んだかは未確認。
- Notion PRE Review Syncは、Secrets未設定時には処理がSkippedになる。外部同期を実際に確認するまでは未完了扱い。
- PR #83は判定記録の承認待ち。差分にタイトル記載以外のPRE IDも含まれるため、別途差分全体を確認する必要がある。

## 6. 承認・制約の整理

### ユーザーから依頼済み
- 自動分類の精度を高め、正確性を保ちながら未確認PREを減らす。
- 改善ロジックを十分に検証できたら、既存の未確認リストにも適用する。
- PR #113によるBot本体の変更は既にマージ済み。今後も今回の検証で必要性が確認できた範囲だけを小さく変更し、無関係なコード変更は避ける。
- 秘密情報を記載しない。
- 台帳のためだけに無関係なコードやワークフローを変更しない。

### 明示的な確認・承認が必要
- PR #83の判定を最終承認してマージすること。
- リセット系ワークフローの実行、既読状態・アーカイブ・掲載待ち・レビュー履歴の削除。
- 素材の誤除外につながり得る大幅な自動判定変更や、根拠が不十分な一括解決。

### ユーザーが実施する可能性のある作業
- Notion同期を有効化したい場合のGitHub Actions Secrets設定。
- PR #83の内容確認・承認（判断内容が意図に合っている場合）。

## 7. 修正済みの実行障害・確認待ち

- PRE-00229による通常収集の停止はPR #117で修正済み。既存のレビュー注記は上書きしない。通常収集が再び成功するか、次回の定期実行で確認する。
- Review Link Audit Run 39900506855は、別のmain更新とのpush競合で失敗。PR #117でpush前のrebaseを追加し、Run 39949380026の再実行attempt 2は成功。84件の元投稿URLがすべて到達可能と確認した。
- 本文内URL検出はテスト済みだが、実データ上の追加候補はまだ確認できていない。Rpg2S ITの41件は本文取得改善が必要で、本文未取得を理由に除外しない。
- GameDev MarketとMaker DevsはSource Check監視のみで、定期収集レジストリには未登録。PR #117でsites.jsonのcollectionフラグをfalseに揃えた。両サイトの個別コレクタを有効化したわけではない。

## 8. 次の作業後に必ず確認すること

- 関連するテストと構文検証の結論。
- GitHub Actionsの最終結論だけでなく、各ステップの実行結果。
- 自動解決件数、PRE ID、判断理由、リンク検査結果。
- `classification_review.json` の未確認・解決済み件数が実際にどう変わったか。
- 403/429、タイムアウト、その他の取得失敗を「リンク切れ」と誤認していないか。
- 人手で戻された項目や明示的な例外が保持されているか。
- Notion同期は、Secretsが有効で実処理が走ったことをログで確認するまで完了扱いにしない。

## 9. 台帳更新のルール

- 作業を開始したときは、このファイルの状態・優先順位を更新する。
- 完了はコードやファイルの存在ではなく、実行結果まで確認してから記載する。
- 新しい作業を始めるときは、前の作業が未完了ならその状態を残す。
- GitHubの現在状態と過去の会話上の合意が異なる場合は、どちらかを黙って上書きせず、差異を明記する。
