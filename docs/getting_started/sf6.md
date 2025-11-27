# ストリートファイター6向けセットアップ

## 続行前のチェック

- [セットアップ手順](../getting_started.md#setup)を最後まで完了していることを確認してください。

## リプレイを録画する

Replay Recorder は、ゲーム内リプレイを自動で録画するためのスクリプトです。

1. ストリートファイター6を起動。
1. `miyoka/record-replay.ps1` を右クリックし、**PowerShell で実行** を選択。
    もしくは Windows PowerShell を開いて次のコマンドを実行します。
    ```shell
    powershell.exe -executionpolicy bypass -file .\record-replay.ps1
    ```

注意:

- 録画中はマウスやキーボードを操作しないでください。操作すると録画が停止します。
- 録画には数時間かかる場合があります。PC を使用しない時間帯（就寝中など）に実行することをおすすめします。

### リプレイをローカル PC に保存する

動画を Google Cloud Storage にアップロードせず、ローカル PC に保存することもできます。その場合は `config.yaml` の `replay_recorder.save_to` に `local_file_storage` を指定してください。

録画されたリプレイは Miyoka ディレクトリ内の `replays` フォルダに保存されます。
