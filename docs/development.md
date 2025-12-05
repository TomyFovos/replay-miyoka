# 開発

## 概要

このフォーク版 Miyoka は、リプレイの自動録画とローカル保存に特化しています。

> **注意:** このドキュメントはオリジナル版 [fgcreplaymiyoka/fgc-replay-miyoka](https://github.com/fgcreplaymiyoka/fgc-replay-miyoka) の開発ドキュメントを元にしていますが、本フォーク版では以下の機能は削除されています：
> - Replay Analyzer（シーン解析・ベクトル化）
> - Google Cloud Platform（GCP）へのアップロード
> - ブラウザ版リプレイビューアー

## 開発環境のセットアップ

### 前提条件

- Python 3.11.x
- [Poetry](https://python-poetry.org/docs/#installing-with-pipx)
- Windows 11（リプレイ録画機能はWindows専用）

### インストール

```bash
poetry install --with win
```

## プロジェクト構成

```
miyoka/
├── container.py          # 依存性注入コンテナ
├── replay-recorder.py    # リプレイ録画のエントリーポイント
├── screenshot.py         # スクリーンショット取得
├── customize-screen.py   # 画面設定カスタマイズ
├── libs/                 # 共通ライブラリ
│   ├── game_window_helper.py
│   ├── replay_recorder.py
│   └── ...
└── sf6/                  # ストリートファイター6固有の実装
    ├── game_window_helper.py
    ├── replay_recorder.py
    └── templates/        # テンプレート画像
```

## コントリビューション

バグ報告や機能リクエストは GitHub Issue をご利用ください。

