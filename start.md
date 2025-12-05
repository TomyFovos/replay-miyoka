# Replay Miyoka クイックスタートガイド

## 1. 事前準備

### OBS Studio の準備
1. OBS Studio を起動
2. スト6録画用のシーンとソース（ゲームキャプチャなど）を設定

### ストリートファイター6 の準備
1. ストリートファイター6を起動
2. ゲーム内の「オプション」→「ディスプレイ設定」で以下を設定：
   - **表示モード**: Window（ウィンドウモード）
   - **解像度**: 1280 x 720

> ⚠️ **注意**: ユーザー検索画面など、初期画面のレイアウトが想定と違うと自動操作が途中で止まる可能性があります。その場合は一度ゲーム内で手動で画面を整えてから再実行してください。

---

## 2. Python 環境のセットアップ

プロジェクトルートで以下のコマンドを実行します。

```powershell
# プロジェクトルートへ移動（パスは環境に合わせて変更）
cd C:\Users\xxxx\Documents\GitHub\replay-miyoka

# 依存関係のインストール
poetry lock
poetry install --with win
```

---

## 3. リプレイ録画の実行

```powershell
powershell.exe -executionpolicy bypass -file .\record-replay.ps1
```

### 動作の流れ
1. OBS が起動していなければ自動起動
2. スト6 の画面・解像度をチェック
3. 問題なければリプレイ録画処理が自動的に開始

---

## トラブルシューティング

エラーが出た場合は、以下を確認してください：

| チェック項目 | 確認内容 |
|-------------|---------|
| スト6 が起動しているか | ゲームが起動していることを確認 |
| ウィンドウモードか | 表示モードが「Window」になっているか確認 |
| 解像度 | 1280×720 に設定されているか確認 |

---

## コマンドまとめ（コピペ用）

### 初回セットアップ（一度だけ実行）
```powershell
poetry lock && poetry install --with win
```

### リプレイ録画（毎回実行）
```powershell
powershell.exe -executionpolicy bypass -file .\record-replay.ps1
```