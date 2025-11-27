# 開発

## 概要

Miyoka は大きく次の 2 コンポーネントで構成されています。

1. [Replay Uploader](docs/uploader.md) … 格闘ゲームから取得したリプレイをクラウドストレージへアップロードするプログラム。
1. [Replay Analyzer](docs/analyzer.md) … リプレイを解析し、データセットを生成するプログラム。

> **補足:** ブラウザ版リプレイビューアーは別プロジェクトへ移行済みです。本リポジトリはリプレイのアップロードと解析機能に特化しています。

## 類似シーンのグルーピング

インストール例:

```
poetry install
```

実行例:

```
make group_scenes
```

出力:

```
# Scenes:
# `scenes/<replay-id>/<round-id>/scene-<scene-id>.mp4`

# Scenes by similarity:
# ベースシーンと他のシーンを比較し、類似度が閾値を超えた場合に同フォルダへコピーします。
# `scenes/<base-replay-id>/<base-round-id>/scene-<base-scene-id>/<target-replay-id>-<target-round-id>-scene-<target-scene-id>.mp4`
```

アプローチ概要:

- シーン分割:
    - 各シーンを[クラスタリング](https://scikit-learn.org/stable/modules/clustering.html)。クラスタの中心（Centroid）は LP, MP, HP などのアクションが含まれるフレームです。
    - アクションフレームの距離が近い場合は 1 つのシーンとして結合（DBSCAN の `eps=30` など）。
    - プレフィックス／サフィックスのフレームをシーンへ付加。
    - 例: p1: ["4", "4 LP", "4 LP", "1", "1", "1", "1", "1 HP", "2"] => p1 scenes: [["4", "4 LP", "4 LP", "1"], ["1", "1 HP", "2"]]
- シーンのベクトル化:
    - Bag-of-Words 形式で特徴量を抽出。各フレームをトークン化し、シーンごとのユニークカウントを計測。
    - 矢印方向の変化はバイグラムで表現。
- 類似度によるグルーピング:
    - ベクトル化したシーン同士の類似度を計算。
    - 指標としてコサイン類似度を使用。

## Google Cloud Platform (GCP)

Miyoka で扱うデータはすべて、自分が所有する GCP プロジェクト内に保存されます。利用にあたり有効化が必要な主なサービスは次のとおりです。

- [BigQuery](https://cloud.google.com/bigquery?hl=en) … リプレイ記録を管理するデータベース。
- [Cloud Storage](https://cloud.google.com/storage?hl=en)（GCS）… リプレイ動画（mp4/hls）を保管するオブジェクトストレージ。
- [Cloud Vision](https://cloud.google.com/vision?hl=en) … 画像からテキストを読み取る OCR。
- [Cloud Run](https://cloud.google.com/run?hl=en) … リプレイ解析ジョブを実行するサーバーレス基盤。
- [IAM Service Account Credentials API](https://cloud.google.com/iam/docs/reference/credentials/rest) … サービスアカウントのトークンを発行し、リプレイ向け署名付き URL を生成。
- （任意）[Artifact Registry](https://cloud.google.com/artifact-registry) … リプレイアナライザー用 Docker イメージのレジストリ。デフォルトでは不要。

これらのサービス利用分については Google から課金されますが、Miyoka はランニングコストを抑える設計になっています。目安として月額 5～20 USD 程度です。繰り返しになりますが、Miyoka 自体は無償で提供されており、開発者側が料金を受け取ることはありません。

## GCR コンテナレジストリにログイン

```
gcloud auth configure-docker asia-northeast1-docker.pkg.dev
```

```
make build-analyzer
```

## Replay Analyzer

前提条件の一例:

- 対応 OS: Linux / macOS
- Python 3.11.3
- [poetry](https://python-poetry.org/docs/#installing-with-pipx)
- GNU make https://gnuwin32.sourceforge.net/packages/make.htm

インストール:

```
poetry install
```

コマンド:

```
REPLAY_ANALYZER_REPLAY_ID="id" \
  CONTINOUS_DEBUG_MODE="true" \
  make analyze
```

Docker コンテナで実行する場合:

```
make analyzed
```

