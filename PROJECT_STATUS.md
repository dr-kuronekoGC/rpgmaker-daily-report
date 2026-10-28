# PROJECT_STATUS.md

最終確認日：2026-10-28（JST）

## 最新確認（2026-10-28 JST）
- 確認対象は `main`、最新コミットは `b1d45d05b3797ac3c2b5829df24d115b9511c7fe`。管理ファイル `PROJECT_STATUS.md`、`NEXT_STEPS.md`、`DECISIONS.md` はすべて存在する。
- PRE台帳は531件中523件解決済み、8件未確認（PRE-00524〜PRE-00531）。今回ユーザー確認の9件（PRE-00425、00430、00431、00433、00455、00471、00481、00491、00507）は `data/review/review_decisions.json` に記録され、`data/review/classification_review.json` でもresolved。判定ファイルは299件。
- PR #137はmainへ反映済み。Classification Audit [Run 40609149323](https://github.com/dr-kuronekoGC/rpgmaker-daily-report/actions/runs/40609149323) は292テスト成功。通常収集 [Run 40609352093](https://github.com/dr-kuronekoGC/rpgmaker-daily-report/actions/runs/40609352093) は成功。
- Auto-screen [Run 40609231407](https://github.com/dr-kuronekoGC/rpgmaker-daily-report/actions/runs/40609231407) は判定・安全テスト成功後、コミット時にpush拒否（`fetch first`）で失敗。分類判定ではなくGit競合／古いローカルmainが原因とログに示されている。次は最新mainを取り込む安全な保存方法を調べる。
- Notion同期 [Run 40658009044](https://github.com/dr-kuronekoGC/rpgmaker-daily-report/actions/runs/40658009044) はworkflow/job上はsuccessだが、ログでは `NOTION_API_KEY` と `NOTION_DATABASE_ID` が空で、Notion同期処理自体はSkipped。Git pushも `Everything up-to-date`。Notionとの実同期が成功したとは扱わない。8件の個別追加記録はあるが、一括件数照合は未完了。
- PR #135で検索用メタデータ（`file_formats`、`engine_relevant`、`graphic_style`、`graphic_theme`、VOICE分類、map_object分類）は実装済み。WordPress検索UIは未実装。
- 現在openのPRは #112、#111、#83。#111と#112は本文品質判定・本文中URL検出の目的が重複するため、差分・CIを比較してから扱う。未マージのPRをmainに反映済みとみなさない。

分類改善：人手の9件の判定はPR #137の改善とレビュー台帳に反映済み。依頼・雑談・BOT案内・ツール紹介を、具体的な配布物がない限り素材配布と扱わない。ただし個別のツール紹介をすべて除外するなど、過度な一般化はしない。リンク切れ／ダウンロード不能は素材の種類とは別の可用性情報として扱う。
検索メタデータ：サウンドは `engine_relevant=false` とし、将来のWordPressではエンジン表示・絞り込みの対象外。ファイル形式、サウンド種別、対応エンジンは別項目として扱う。グラフィックは用途分類・明示的なスタイル・テーマを分け、不明なエンジンや空タグだけで検索から除外しない。検索UIは未実装。

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
| PREレビュー台帳・判定取込 | 実装済み | 2026-10-28確認時点で台帳531件、未確認8件／解決済み523件。Notion全件数の一括再集計は保留 |
| 未確認PREの自動スクリーニング | 実装済み・継続改善中 | PR #113〜#115の本文品質・URL・依頼表現改善に加え、PR #137で英語・ロシア語・日本語の明示的な依頼表現と曖昧な配布語句の扱いを改善。Classification Auditは292テスト成功。Auto-screen Run [40609231407](https://github.com/dr-kuronekoGC/rpgmaker-daily-report/actions/runs/40609231407) は判定ステップ成功、GitHubへのコミットステップ失敗。詳細はNEXT_STEPS.md参照 |
| リンク監査 | 実装済み | 404/410等を検査する。403/429、タイムアウト、ネットワークエラーをリンク切れと同一視しない |
| Notion同期 | 実装・実行確認済み | Run [40658009044](https://github.com/dr-kuronekoGC/rpgmaker-daily-report/actions/runs/40658009044) で同期処理と同期台帳コミットが成功。一括件数再集計は利用上限で保留 |
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
| `Notion PRE Review Sync` | NotionとPRE台帳の同期 | 2時間ごと、手動実行、関連監査ワークフロー終了後。Secrets未設定ならスキップ |

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

## 6.1 直近の収集元ヘルス確認（最終成功：2026-10-20 09:23 JST）

Run 39347372727では、35収集モジュールのうち31件がOK、1件がPARTIAL、3件がERRORだった。これは2026-10-20時点の結果であり、PR #117修正後の現況ではない。

- **Comunidad RPG Maker ES**：APIの1ページ目は取得できたが、次ページURLがHTTP 404となり、従来コードでは収集全体が失敗扱いになっていた。PR #117で、取得済みページの結果を保持しつつ失敗リクエストをヘルス情報に残すよう修正。
- **RM Planet**：RSSがHTTP 403。アクセス制限を回避せず、現状は取得失敗として扱う。
- **RPG Maker Network**：リソースページがHTTP 403。アクセス制限を回避せず、現状は取得失敗として扱う。
- **Source Check（2026-10-24以降）**：PR #122で失敗を繰り返した4サイトを手動確認のみへ変更。PR #124でGameDevMarketを公開代替ホストへ変更し、Run #196でBaseline保存を確認（変更検知は未確認）。Maker Devs診断Run #3ではDNS解決成功、3つのIPすべてでTCP接続後のTLSハンドシェイクが失敗し、GET/HEADもTLSエラー。根本原因は未確定のため、Maker Devsは手動確認のみを維持。現在は9件監視・3件手動確認のみ、failed=0。アクセス制限の突破やTLS検証の無効化は行わず、正規の公開経路を利用する。
- **サイト台帳**：GameDev MarketとMaker DevsはSource Checkで監視されているが、定期収集レジストリには登録されていない。data/sites/sites.json の collection を false に修正し、状態表示を実態に合わせた。RMRKも新規収集対象外のまま履歴を保持する。

2026-10-25：PR #122で4サイトを手動確認のみへ移行し、Classification Auditで280テスト成功。その後PR #124でGameDevMarketを公開代替ホストへ変更して監視を再有効化。Run #196で取得・Baseline保存を確認したが、変更検知は未確認。現在は監視対象9件、手動確認3件。

PR #117マージ後の通常収集で、各項目が改善・継続・解消のどれに当たるか再確認する。

## 7. 未解決課題

- PREの自動分類精度を継続改善すること。2026-10-28時点では531件中8件が未確認。PR #137の依頼表現改善を踏まえ、誤除外を防ぐ回帰テストとAuto-screenのコミット失敗原因の確認を優先する。古いRpg2S IT・RMRKの監査所見は当時の記録として参照する。
- 自動仕分けの誤判定率を継続的に検証すること。人手で戻された項目や境界事例を回帰テストに含める。
- Notion同期用のGitHub Actions Secretsを設定し、同期を実際に動作確認すること（必要な場合）。
- PR #83（タイトル上はPRE-00163〜PRE-00174の判定記録）が未マージ。実際の差分にはPRE-00177、PRE-00179、PRE-00180、PRE-00186、PRE-00190も含まれるため、タイトルだけで対象範囲を判断せず、差分全体を確認する。
- 各収集元の取得状態は変動するため、Source Healthとサイトごとのログを継続確認すること。
- WordPress移行向けの検索メタデータ（ファイル形式、グラフィック用途・スタイル・テーマ、価格・利用条件等）は整備を開始済み。残作業はWordPress側の検索UI・フィルター設計と、実データでのメタデータ品質確認。

## 8. 将来的な構想（未実装・進行中を含む）

- WordPress上の検索可能な「素材酒場」。
- 素材種別、プラグイン用途、対応RPG Maker、言語、作者、利用条件、価格、公開・更新日による検索・絞り込み。
- 自動分類の品質を高めるため、過去の人手判定を構造化した回帰テストデータとして活用する。
- 収集元の追加・保守を継続し、更新頻度や素材の多さを考慮して情報源を選ぶ。
- 既存の蓄積データを維持し、必要な時点でWordPressへ古いものから順に移行する。リセットを前提にしない。

## 9. 更新ルール

- 本ファイルは、目的、主要な構造、確定方針、実装状況、長期課題が変わったときに更新する。
- 具体的な作業順、直近のActions結果、承認待ち事項は `NEXT_STEPS.md` に記録する。
- GitHubの実状態と会話上の合意を区別する。未確認事項は推測で埋めず「未確認」と記載する。
- 秘密情報を記載しない。
