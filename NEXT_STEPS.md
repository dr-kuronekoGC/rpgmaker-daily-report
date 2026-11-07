# NEXT_STEPS.md

最終確認日：2026-11-07（JST）
対象：`dr-kuronekoGC/rpgmaker-daily-report` の `main` のみ。
現在の全体状況は `PROJECT_STATUS.md`、長期的な設計判断は `DECISIONS.md` を参照する。

## 最初に行う作業

### 1. Notion同期を実際に動かして差分を解消する（最優先）

確認済み：
- ユーザーから `NOTION_DATABASE_ID` をGitHub Actions Secretsに登録したとの報告あり。
- Notion接続経由でPRE確認台帳を検索・集計できた。
- Notionは413件、確認状態は全件「済」。
- GitHubの `data/review/classification_review.json` は544件（resolved 538／open 6）。
- Notion側の最新PREは00538。GitHub側の00539〜00544はNotionに存在しない。

未確認：
- `NOTION_API_KEY` がActions Secretsに登録され、有効な値か。
- ActionsからNotion APIへ接続し、実際に同期処理が完了するか。
- 既存413件とGitHub側のPRE ID・URL・状態が全件一致するか。

手順：
1. GitHubリポジトリの Settings → Secrets and variables → Actions で、`NOTION_API_KEY` と `NOTION_DATABASE_ID` のSecret名が存在することを確認する。値はチャットへ貼らない。
2. Actions → Notion PRE Review Sync → Run workflow で手動実行する。
3. workflow/jobのsuccess表示だけで判断せず、ログでSkippedではないこと、Notion API同期件数、Notionページ作成・更新件数、GitHub台帳のコミット結果を確認する。
4. 同期後にNotionとGitHubの件数・PRE番号・確認状態を再集計する。GitHubの6件（PRE-00539〜00544）がNotionで「未確認」となり、過去の判定・URLが壊れていないことを確認する。
5. 413件との差131件を機械的に作成する前に、同期スクリプトの動作（GitHub台帳を基準にNotion不足ページを作成する仕様）と既存IDの重複がないことを確認する。

注意：Notionの「済」は同期スクリプト上、GitHub台帳をresolvedにする意味を持つ。ユーザーが実際に内容を確認したかどうかと、単なる同期状態を混同しない。同期前にNotion全件を一括で「済」に変更しない。

### 2. Auto-screenの最新実行と保存失敗を確認する

- 過去のAuto-screen Run 40609231407では分類・テストは通過したが、GitHubへのpushが `fetch first` で失敗した。
- これは2026-10-28時点の履歴。現在も同じ問題が発生しているかは未確認。
- まずActionsの最新 `Auto-screen Open Review Items` 実行を確認し、判定処理、テスト、コミット、rebase、pushを個別に見る。
- 失敗が再現している場合のみ原因を調査する。判定精度の問題とGitへの保存競合を分ける。
- 台帳の手動上書き、PRE ID再採番、既読・pending・archiveの削除はしない。

### 3. 6件の未確認PREを確認する

対象：PRE-00539〜PRE-00544。
- まず本文取得・配布先・リンク状態を確認する。
- 本文未取得、403/429、タイムアウトだけで素材なしと断定しない。
- 高確度の除外だけを自動処理し、根拠が弱いものは未確認のまま残す。
- ユーザーが既に判断したPRE-00527〜PRE-00538などを二重に確認・登録しない。

### 4. open PRを整理する

- PR #139：2026-10-28時点の管理ファイル更新PR。mainから29コミット遅れで、Secrets未設定など古い情報を含む。今回、mainの管理ファイルを直接更新したため、PR #139の差分はそのままマージしない。差分を再確認し、不要ならクローズするか、必要な変更だけを整理する。勝手にマージ・クローズしない。
- PR #83：判定記録のPR。main未反映。差分に含まれるPRE番号と判断根拠を確認し、ユーザー承認なしにマージしない。

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
- 2026-11-07：Notion PRE確認台帳413件、すべて「済」を確認。GitHub台帳との差131件。Notion接続経由の参照は成功したが、GitHub Actionsからの実同期は未確認。
- 2026-11-07：ユーザーより `NOTION_DATABASE_ID` 登録済みとの報告。APIキーのSecret名・有効性とActionsでの同期実行は別途確認する。
- 2026-11-07：mainの管理ファイル3点を更新。PRE台帳・判定記録・収集データは変更していない。
