# NEXT_STEPS.md

最終確認日：2026-10-24（JST）
対象ブランチ：`main` と `feature/official-news-dates-links`
PR #117マージ後、通常収集Run 40042036545（2026-10-24 08:52 JST）が成功し、Slack HTTP 200・データ保存を確認。35収集モジュール中30 OK／2 PARTIAL／3 ERROR。Source Checkは12件中8件を確認し、4件更新・4件失敗。PRE台帳は523件中84件未確認／439件解決済み。PR #118で毎回のSlackレポートにOfficial Informationリンクを追加しマージ済み。今回、公式ニュースの個別記事URLと公開日を取得してSlackに表示する改善を実装し、PR作成・テスト確認待ち。

このファイルは、次回のチャットや作業で再開するための短期台帳。完了と記載するのは、実行結果を確認できた作業だけとする。長期方針は `PROJECT_STATUS.md` を参照する。

## 1. 最優先：通常収集の復旧確認

**通常収集の復旧を確認済み。** [PR #117](https://github.com/dr-kuronekoGC/rpgmaker-daily-report/pull/117) は2026-10-23にマージ済み。Run 40042036545（2026-10-24 08:52 JST）は成功し、Slack送信とデータ保存を確認。

- PRE-00229は判定値が既存記録と一致していれば、メモに接頭辞等の差があっても既存メモを保持して取込を継続する。異なる判定値は引き続き拒否する。
- 復旧確認：[Run 40042036545](https://github.com/dr-kuronekoGC/rpgmaker-daily-report/actions/runs/40042036545)（2026-10-24 08:52 JST）。Run script、Slack送信（HTTP 200）、pending保存、GitHubへのデータpushが成功。
- 現在のサイト状況：35収集モジュール中30 OK／2 PARTIAL／3 ERROR。Comunidad RPG Maker ESはページ2の404（1ページ目の結果は保持）、RPG Maker SUとRM PlanetとRPG Maker Networkは403。403はアクセス制限を回避せず、公式の公開RSS/API等の代替経路を探し、なければ取得失敗として監視する。

Source Checkは12件中8件を確認、4件更新・4件失敗。失敗はGameDevMarket 403、Maker Devs TLSエラー（再試行後も失敗）、RPG Refugeのアクセスチャレンジ、New RPG Project 403。いずれも2026-10-24のログで再確認した。公式ページやSNSリンクはレポートに常設する方針。Xの投稿日時を安定して自動取得する仕組みは未実装で、今回のリンク追加だけでは「更新検知」にはならない。

## 2. 現在の優先課題

### P0 — Official InformationリンクをSlackに常設する
**状態：PR #118マージ済み。次回の通常収集でSlack表示を確認する。**

- [PR #118](https://github.com/dr-kuronekoGC/rpgmaker-daily-report/pull/118) をマージ。`Official Information` 欄に公式ニュース、ツクール開発部X、新プロジェクトの日英X、公式フォーラム、YouTube、Discordを毎回表示する。
- 新着がない日でも、公式情報の入口から確認できる。
- Xの投稿日時を自動で取得して「更新あり」と表示する機能はまだない。公式ニュースの新着検知とは分けて扱い、次段階では公式RSS/API等の安定した取得経路を調べる。未検証の非公式Xスクレイピングや、投稿があったと断定する表示は導入しない。

### P1 — 公式ニュースの個別記事URL・公開日を表示する
**状態：実装・回帰テストを追加。PR作成後のActions結果を確認する。**

- 公式ニュース一覧の見出しから個別記事URL（例：`/news/4157/`）とページ上に表示される公開日を取得する。
- Slackの公式ニュース項目は一覧ページではなく記事本体にリンクし、日付を `公開日：YYYY.MM.DD` と表示する。
- 公式サイトで確認できるのは日付であり、正確な時刻は見つかっていないため時刻を推定・表示しない。
- 過去の既読状態は見出し文字列でも照合し、新規分はURLを既読キーとして保存してタイトル変更に強くする。
- 記事リンクがHTMLから確認できない場合はURLを推測せず、その見出しを採用しない。

## 3. 現在の優先課題

### P1 — 未確認PREの自動仕分け精度を改善する
**状態：進行中。ユーザーの依頼あり。**

目標は未確認件数を減らすことだが、有用な素材を誤って除外しないことを優先する。本文・配布先リンク・リンク状態・投稿目的の証拠を使い、判定不能な項目は未確認のまま残す。

**現在のmain上の実データ（2026-10-23確認）**
- 全PRE：523件
- 未確認：84件
- 解決済み：439件
- `data/review/auto_screen_audit.json` の直近確認対象は未確認84件。マージ後のAuto-screen Run 39900506829は成功したが、追加解決は0件。
- その前の監査ではPRE-00226を解決済み。Rpg2S ITの41件はすべて `body_unverified` で保護されている。
- Review Link Audit Run 39949380026（再実行attempt 2）は成功。未確認84件の元投稿URLはすべてHTTP到達可能で、投稿ページ自体のリンク切れは0件。ただし、配布先リンクの状態とは別。
- 最新のopen-review監査は74件を `keep_manual_review`、10件を `needs_body_review` と提案。10件のうち7件はRpg2S ITで本文未取得、3件はRMRKで本文取得済みだがタイトル語だけでは配布物と断定できない。提案は監査用で、判定台帳を変更しない。
- 自動スクリーニングで見つかったHTTP 404/410のURLにはプレビュー画像等も含まれる。素材の配布リンクと確認できたものは2項目だけで、どちらも人手の「未確認に戻す／再確認」注記があるため、除外しない判断が正しい。
- 以前の89件監査でPRE-00171・PRE-00231を解決した結果、およびpush競合対策後の保存もmain上に残っている。

**実装・検証済み：PR #113**
[Improve review body verification and plain-text URL detection](https://github.com/dr-kuronekoGC/rpgmaker-daily-report/pull/113) は2026-10-22にマージ済み（マージコミット `b79bae73b15a306ca743b818a0e98a9f2471cb4f`）。
- 本文中に直接記載されたHTTP(S) URLを抽出し、アンカー／メディアリンクと重複させずに候補化する。
- Invisionの汎用レイアウト領域やメタ説明だけの短い本文を `body_unverified` とし、自動解決に使わない。
- 取得テキスト・リンクは監査用に保持。PR自体はPRE台帳の判定を直接変更しない。
- `Auto-screen triage tests` と `Classification Audit` は成功。マージ後の `Auto-screen Open Review Items` も成功し、最新監査結果がmainに保存された。

**実装・検証済み：PR #114**
[Recognize solved requests to upload resources](https://github.com/dr-kuronekoGC/rpgmaker-daily-report/pull/114) はマージ済み（マージコミット `d5980fc9340ed300622e669ab241a7864b69d118`）。
- 「Please up the RTP Earth Animation sheets」のように、素材をアップロードしてほしいと明示する依頼表現を検出する。
- 「Please up the thread」のようなスレッドの再掲依頼を誤検出しない否定テストを追加。
- PRのAuto-screen triage testsは39件すべて成功。Classification Auditも265件すべて成功。マージ後のAuto-screen Open Review Itemsも成功し、52件の関連安全テストが成功したログを確認。
- 実データでPRE-00226を再確認し、配布可能な素材リンクがなく、本文が明確なアップロード依頼であることから `not_applicable` として解決。自動スクリーニング87件中1件解決、未確認86件・解決済み437件となった。

**実装・検証済み：PR #115**
[Recognize withdrawn and explicit recolor requests](https://github.com/dr-kuronekoGC/rpgmaker-daily-report/pull/115) はマージ済み（マージコミット `afe58fd4703f25e89d03d7e607d7dc65ef0253ae`）。
- 「誰かにキャラクターの髪を茶色に塗り直してほしい」という明確な依頼文と、「Request withdrawn（依頼を取り下げ）」を検出する。
- PRE-00367（バトラーの髪色変更依頼）とPRE-00370（VX用Charset依頼の取り下げ）を対象に回帰テストを追加。
- Auto-screen triage testsは41件すべて成功し、Classification Auditも成功。マージ後の自動スクリーニングは86件を走査し、PRE-00367・PRE-00370を解決。関連安全テスト54件も成功したログを確認。
- 人手の再確認注記、配布リンクのある項目を保護する既存ルールは維持。

**根拠となった既存監査の所見**
1. Rpg2S ITでは未確認41件の本文がすべて300文字未満で、配布リンク候補もゼロ。HTML自体は約14万文字ある例でも、取得本文はタイトル・作者・サイト案内の約170〜220文字だった。現状では素材がないとは判断できないため、本文取得を「成功」と扱わず、未確認のまま保護する。
2. RMRKの本文内URL抽出は回帰テストで動作を確認済み。ただし最新監査では `plain_text_url` として記録された候補は0件。PRE-00343のImageshack URLは既に `anchor` として取得されており、同項目には人手の「未確認に戻す」注記があるため、自動解決しない。
3. 本文が取得できた項目でも、質問・依頼・制作日記だけで自動除外せず、配布根拠を確認する。人手の再確認注記は常に優先する。PRE-00471・PRE-00507等の再確認指定は自動解決しない。

**今回の再開時点で確認済みの結果**
1. PR #113・#114・#115はマージ済み。関連テストとClassification Auditは成功。
2. PR #114後にPRE-00226、PR #115後にPRE-00367・PRE-00370を解決。台帳は523件中84件未確認／439件解決済み。
3. Rpg2S ITの41件はすべて `body_unverified` となり、メタデータしか取得できないページを本文取得成功と誤認する問題を抑制できた。
4. 最新監査で `plain_text_url` として記録されたリンクは0件。PRE-00343のImageshack URLは `anchor` として取得され、人手の再確認注記もあるため未確認のまま保持されている。
5. PRE-00226はアップロード依頼、PRE-00367は再着色依頼、PRE-00370は依頼取り下げで、いずれも配布可能な素材リンクがないことを監査で確認し、自動解決された。

**次に行う具体的な手順**
1. 未確認84件を対象に、明確な依頼・取り下げパターンが他にもあるか監査記録から候補を確認する。質問・制作依頼受付・制作日記をタイトルだけで一括除外しない。
2. RMRKの本文内URL抽出はテスト済みだが、実データで新しい `plain_text_url` 候補が出たことは未確認。PRE-00343は人手注記を尊重して未確認のまま維持する。
3. Rpg2S ITの本文取得は別問題として扱う。投稿本文を実際に取得できる経路が見つからない限り、該当項目は未確認のまま維持する。
4. 次回の自動スクリーニング後も、自動解決ID・理由・リンク状態・人手注記を確認し、処理前後の件数を比較する。

**完了条件**
- 構文検証・関連テストが成功している。
- 本文取得失敗や短いメタデータだけのページを、本文取得成功と誤認していない。
- 本文内URLを検出しても、プレビュー画像等を自動的に素材確定しない。
- 404/410以外のエラーをリンク切れと断定しない。
- 人手の修正・例外が保持されている。
- 自動解決IDと根拠、実行後の未確認件数をGitHub上で確認できている。

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
