# ストリートファイター6向けセットアップ

## 続行前のチェック

- [セットアップ手順](../getting_started.md#セットアップ)を最後まで完了していることを確認してください。

## リプレイを録画する

Replay Recorder は、ゲーム内リプレイを自動で録画するためのスクリプトです。

1. ストリートファイター6を起動。
1. `record-replay.ps1` を右クリックし、**PowerShell で実行** を選択。
    もしくは Windows PowerShell を開いて次のコマンドを実行します。
    ```shell
    powershell.exe -executionpolicy bypass -file .\record-replay.ps1
    ```

注意:

- 録画中はマウスやキーボードを操作しないでください。操作すると録画が停止します。
- 録画には数時間かかる場合があります。PC を使用しない時間帯（就寝中など）に実行することをおすすめします。

## リプレイの保存先

録画されたリプレイは `config.yaml` の `replay_recorder.local_file_storage_dir` で指定されたディレクトリに保存されます。
デフォルトでは Miyoka ディレクトリ内の `replays` フォルダに保存されます。

ファイルは `<local_file_storage_dir>/<player_id>/` の形式で整理されます。

## config.yaml の設定

### プレイヤー設定

`game.players` で録画対象のプレイヤーを設定します：

```yaml
game:
  players:
    - name: "自分の名前"
      id: "プレイヤーID"
      pattern: "ゲーム内表示名"
```

### 言語設定

日本語版ゲームを使用している場合は、`game.extra.original_language` を `jp` に設定してください：

```yaml
game:
  extra:
    original_language: jp
```
