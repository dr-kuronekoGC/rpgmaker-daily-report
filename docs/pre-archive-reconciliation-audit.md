# PRE判断とArchive反映の設計・監査（2026-11-12）

## 目的と範囲

PREの人手判断を月別Archiveへ反映する方法を設計するため、mainの既存データを読み取り専用で照合した。今回の作業ではArchive／PRE台帳／判定履歴のデータ本体は変更していない。

対象：
- `data/archive/2026-09.json`：1,862件
- `data/archive/2026-10.json`：2,255件
- `data/archive/2026-11.json`：94件
- Archive合計：4,211件
- `classification_review.json`：549件（resolved 548／open 1）
- `review_decisions.json`：324件

## 監査結果

### PRE ID・内部IDの対応

- ArchiveのうちPRE ID付き：550レコード、PRE IDの種類は549。
- PRE ID付きArchiveのうち、台帳に存在しないPRE ID：0。
- resolvedのPRE台帳項目のうち、internal_idでArchiveに見つからないもの：0。
- PRE ID付きArchiveの重複：PRE-00526が2レコード。同一internal_id `ITEM-8e5d7d04c7c6e362`、同じRPG Maker Unionスレッド。タイトル表記・URL slug・収集時刻が異なる。
- PRE IDなしArchive：3,661件。今回のPRE照合対象外。
- PRE-00549は台帳上openだがArchiveにも存在する。Archive登録とPREレビュー解決は別の状態であり、Archiveにあることをもってレビュー済みとは扱わない。

### PRE台帳とArchiveの分類フィールド差

台帳側に当該フィールドが存在するレコードだけを比較した結果、差があるPRE IDは32件（重複を除く）。

| フィールド | 差のあるPRE ID数 |
|---|---:|
| category | 31 |
| asset_type | 6 |
| content_type | 2 |
| tags | 2 |

差のある32件の情報源内訳：Rpg2S IT 28件、RPG Maker RU 1件、RPG Maker Union 1件、Reddit 2件。

この32件をそのまま「誤分類」とは扱わない。特にRpg2S ITの28件は、Archiveが情報源名を含むcategory（例：`Rpg2S ITプラグイン`）を保持する一方、PRE台帳は一般化した日本語分類を持つケースが中心。さらに台帳の `graphics`／`audio` はschema v8の `graphic`／`sound` と異なる旧表記で、Archive側が既に正規値であるケースもある。categoryやasset_typeを一括コピーしてはいけない。

### 個別に確認が必要な例

- **PRE-00460**：ユーザー判断は音楽素材。PRE台帳の `asset_type=audio` に対しArchiveは `other`。schema v8では `sound` が正規値なので、反映するなら `audio → sound` の明示マッピングが必要。
- **PRE-00540**：ユーザー判断は素材・プラグインではなくプロジェクト一式の配布（`not_applicable`）。PRE台帳は `content_type=project`／`asset_type=project`、Archiveは `plugin`。schema v8に `project` はない。現状のschemaで無理にpluginやgameへ寄せず、プロジェクト配布をどう表現するか決めるまで保留する。
- **PRE-00543**：ユーザー判断はiPhone上でRPG Maker製ゲームを動かす自作プレイヤー。PRE台帳のcategoryは「開発情報」、asset_typeは旧値 `development_tool`、tagsに「iPhone」「ゲームプレイヤー」がある。Archiveは `asset`／`other` のまま。schema v8に沿う反映候補は `content_type=development_info`、`development_info_type=runtime_player`、`asset_type=null`。ただし元のReddit本文はHTTP 403で未取得であることを残し、判断根拠はユーザー確認であると明示する。
- **PRE-00546**：ユーザー判断は有料のキャラクターグラフィック素材。Archiveは `asset_type=other`、tags空。PRE台帳は `graphic`、tagsに「キャラクター素材」「有料」。反映候補だが、価格額や利用条件は未確認なので推測して追加しない。
- **PRE-00526**：同一PRE ID・internal_idのArchiveレコードが2つある。データ削除や重複統合は別判断とし、今回の反映処理で自動削除しない。

## 推奨する反映設計（未実装・データ変更なし）

1. **照合キー**：PRE IDとinternal_idの両方を確認する。URLも補助照合し、どれかが食い違えば自動反映せず競合として出す。
2. **判定と反映を分離**：`review_decisions.json` の `confirmed` だけではArchive更新内容を決めない。PRE台帳のレビュー内容・ユーザー確認メモ・明示的なフィールド指定を根拠にする。
3. **反映内容を明示**：将来は判定記録にArchive用の明示的なpatch（対象internal_id、設定するフィールド、根拠、schema version）を持たせる案を検討する。文章のreview_noteを自動解析して更新内容を推測しない。
4. **許可フィールドを限定**：category／content_type／asset_type／development_info_type／tags等、ユーザーが確認したフィールドだけを更新する。URL・source情報・収集日時・ライセンス等は別根拠なしに変更しない。
5. **競合時は停止**：Archiveに異なる値がある場合は変更前後を提示して保留する。source-specific categoryやschema旧値を単純上書きしない。
6. **冪等性と履歴**：反映済み状態、日時、変更前後の値、反映元PRE IDを記録し、再実行で二重適用しない。全件検証後にのみ書き込み、dry-runを既定にする。
7. **重複・除外**：同じPRE IDに複数Archiveレコードがある場合は自動更新・削除しない。not_applicableは「Archiveから削除」と同義にしない。保持・非公開・除外表示の扱いを別途定義する。

### 最初の試験候補

PRE-00543はschema v8の開発情報モデルを使う具体例として適している。ただし実際のArchive更新はまだ行わない。PRE-00540はschemaにproject種別がないため、最初の反映対象から外して設計課題として残す。

## 今回の変更範囲

- 読み取り監査と設計記録のみ。
- Archive、PRE台帳、review_decisions、seen、pending、Notionは変更なし。
- 重複レコードの削除・統合なし。
- Workflow手動実行なし。
- 実データへの反映は、別途対象と更新内容を確認してから行う。

## 監査時点のGitHub状態

- PR #144（Canonical Item model v8）はGitHub上で2026-11-12 13:20 JSTにmerged。
- Merge commit：`f9b7e9f082b80afbb0424819112d645e00fe4e27`。監査時点のmain HEADも同SHA。
- Canonical Item model tests：41件成功。Engine Backfill Audit：成功（previewのみ）。Classification Audit：既存の `source_status_overrides.json` 形式不整合により失敗。
- PR #143は別件であり、この作業では変更していない。
