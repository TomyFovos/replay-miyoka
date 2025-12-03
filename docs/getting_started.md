# はじめに

## 利用前の確認

### 対応済みの格闘ゲーム

現時点で Miyoka が動作確認できているタイトルは次のとおりです。

- ストリートファイター6

他タイトルへの対応は、コミュニティからの貢献を歓迎します。

### ゲーム内でリプレイを視聴できるか確認

- Windows 11 が動作するデスクトップまたはノート PC を用意している。
- Steam をインストール済みである。
- 対応格闘ゲームを Steam で購入している。
- ゲームを起動し、ゲーム内の UI からリプレイにアクセスできる。

## セットアップ

チュートリアル動画（英語）:

[![Tutorial](https://img.youtube.com/vi/DYYpQVEDRVA/0.jpg)](https://www.youtube.com/watch?v=DYYpQVEDRVA)

### Google Cloud Platform にプロジェクトを作成

※[リプレイをクラウドではなくローカル PC に保存したい場合](./getting_started/sf6.md#save-replays-in-your-computer)は、この手順をスキップできます。

1. [新しい GCP プロジェクトを作成](https://cloud.google.com/resource-manager/docs/creating-managing-projects#console)。
1. [`gcloud` CLI をインストール](https://cloud.google.com/sdk/docs/install)し、ドキュメントに従って `gcloud` から GCP にログインします。

### Miyoka のセットアップ

1. [Python 3.11.3](https://www.python.org/downloads/windows/) をインストール。
    - 推奨: [Windows installer (64-bit)](https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe)
1. [Poetry](https://python-poetry.org/docs/#installing-with-pipx) をインストール。
    - 推奨: [公式インストーラ](https://python-poetry.org/docs/#installing-with-the-official-installer)。提示される PATH 設定の手順も忘れず実施してください。
1. [Miyoka をダウンロード](https://github.com/fgcreplaymiyoka/fgc-replay-miyoka/releases)します。
    1. 最新版の **Source code (zip)** をクリック。
    1. ダウンロードしたファイルを右クリックし、**すべて展開** を選択。
1. 依存関係のインストール:
    1. **Windows PowerShell** を開きます（管理者権限である必要はありません）。
        1. スタートメニューまたは検索アイコンをクリックし、検索ボックスに「powershell」と入力。
        1. 「開く」または「管理者として実行」を選択して PowerShell を起動。
    1. 展開した Miyoka プロジェクトのディレクトリへ移動。例:
        ```shell
        cd c:\Users\name\Downloads\fgc-replay-miyoka-x.x.x\fgc-replay-miyoka-x.x.x
        ```
        ヒント: エクスプローラーからフォルダーを PowerShell にドラッグ＆ドロップするとパスを自動入力できます。
    1. poetry で依存関係をインストール:
        ```shell
        poetry install --with win
        ```
1. `miyoka/setup.ps1` を右クリックし **PowerShell で実行** を選択。
    もしくは PowerShell で以下を実行します。
    ```shell
    powershell.exe -executionpolicy bypass -file .\setup.ps1
    ```
    コマンド実行後、Miyoka フォルダ内に `config.yaml` が作成され、サーバー設定がまとめて保存されます。
    秘匿情報を含むため、他者と共有しないでください。
1. `config.yaml` 内の `<required>` プレースホルダーを自分の情報に置き換えます。

### OBS の設定

1. [OBS をダウンロード](https://obsproject.com/download)。
1. 新規 Game Capture ソースを作成。
    1. **Sources > + (Add Source)** をクリック。
    1. **Game Capture** を選択して **OK**。
    1. **Mode > Capture Specific Window** を選択。
    1. **Window > [<game-title>.exe]** を指定して **OK**。
1. [WebSocket サーバーを有効化](https://fms-manual.readthedocs.io/en/latest/audience-display/obs-integration/obs-websockets.html)。
    1. **Tools > WebSocket Server Settings** を開く。
    1. **Enable WebSocket server** にチェック。
    1. **Server Password** を `secret` に変更。
    1. **Apply** をクリック。
1. [録画解像度を 640x360 または 1280x720 に設定](https://obsproject.com/kb/standard-recording-output-guide)。
    1. **Controls > Settings** をクリック。
    1. **Video** メニューを開く。
    1. **Base (Canvas) Resolution** を 1280x720 に設定。
    1. **Output (Scaled) Resolution** を 640x360 または 1280x720 に設定。Wi-Fi なしで視聴する場合は低解像度が推奨。
    1. **Common FPS Values** を選択し、60 FPS で録画。
    1. **Apply** をクリック。
1. 出力設定:
    1. **Controls > Settings**。
    1. **Output** メニュー。
    1. **Recording format** を **MPEG-4 (.mp4)** に設定。
    1. **Video Encoder** を **Hardware (NVENC, H.264)** または **Software (x264)** に設定（GPU が非対応ならソフトウェアを使用）。
    1. **Apply** をクリック。

## 続き

- [ストリートファイター6向けセットアップ](getting_started/sf6.md)

## Miyoka サーバーの削除

Miyoka サーバーを削除するには、以下の手順を実施します。

- GCP プロジェクトを削除します。手順: https://cloud.google.com/resource-manager/docs/creating-managing-projects#shutting_down_projects
  これにより、ストレージ内のリプレイを含む関連リソースも連鎖的に削除されます。
