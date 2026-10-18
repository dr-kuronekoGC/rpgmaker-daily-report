# Notion PRE確認台帳との同期

## 目的と動作

- `data/review/classification_review.json` をPREの永続的な記録として維持します。
- Notionの「確認状態」を「済」にすると、次回同期でGitHub側のPREも `status: "resolved"` になります。決定内容は `reviewed_in_notion` として記録され、Slackの未確認持ち越し対象から外れます。
- GitHub側で既に決定済みのPREは、Notionでも「済」に更新します。既存の `decision` と `review_note` は上書きしません。
- GitHub側のPREでNotionに行がなければ新規作成します。既に解決済みのPREは「済」で登録し、過去の確認結果も台帳に残します。URLが変わった場合はNotionのURLも更新します。
- Notionの「済」行は削除しません。Notionの「未確認一覧」ビューからのみ非表示になります。
- Notionの優先度はGitHub台帳に同等の項目がないため、Notion内で管理します。新規行の優先度は「通常」です。
- 2時間ごとに同期し、Actions画面から手動実行もできます。

## 初回設定：GitHub ActionsのSecrets

ChatGPTにNotionを接続したことと、GitHub ActionsからNotion APIを使う権限は別です。以下の2つをGitHubリポジトリのSecretsに設定してください。

1. Notionの「マイインテグレーション」で内部インテグレーションを作成し、Internal Integration Secretを取得します。
2. Notionの `PRE確認台帳` データベースを、そのインテグレーションに共有します。共有されていないとAPIはアクセスできません。
3. GitHubのリポジトリを開き、`Settings` → `Secrets and variables` → `Actions` → `New repository secret` で以下を追加します。
   - `NOTION_API_KEY`: Notion Internal Integration Secret
   - `NOTION_DATABASE_ID`: PRE確認台帳のデータベースID。URLの `https://app.notion.com/p/` に続く32桁のID（ハイフンはあってもなくても可）。現在の台帳URLは `https://app.notion.com/p/a34b04d672274e57988aa4f2122f197d` です。
4. PRをmainに取り込んだ後、`Actions` → `Notion PRE Review Sync` → `Run workflow` で初回同期を実行します。

## 安全策と制限

- API認証情報が未設定の場合は同期をスキップします。
- APIエラーや重複PRE番号を検出した場合は同期を失敗させ、曖昧な状態のまま書き換えません。
- Notion側で「済」にする操作は「確認した」という記録であり、`plugin` や `material` などの詳しい分類判断を自動推測するものではありません。具体的な分類はチャットや `review_decisions.json` で明示的に記録してください。
- NotionからGitHubへの同期が成功した後、GitHub Actionsが台帳をコミットします。Slackへの反映は次回の日次レポート実行からです。
