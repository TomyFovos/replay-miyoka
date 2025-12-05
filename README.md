[![License](https://img.shields.io/github/license/TomyFovos/replay-miyoka)](https://www.gnu.org/licenses/gpl-3.0.html)

# Replay Miyoka 🕹️

Replay Miyoka（以下 Miyoka）は、対戦格闘ゲームのリプレイ録画を自動化し、ローカルに保存するオープンソースのツールです。

> **📝 このリポジトリについて:** 本プロジェクトは [fgcreplaymiyoka/fgc-replay-miyoka](https://github.com/fgcreplaymiyoka/fgc-replay-miyoka) からフォークしたものです。オリジナルプロジェクトの素晴らしい基盤に感謝いたします。

## 主な機能

- **リプレイの自動録画** - ゲーム内リプレイを自動で再生・録画
- **ローカル保存** - 録画したリプレイをローカルディレクトリに保存
- **日本語対応** - 日本語版ゲームに対応したテンプレート画像を同梱

## オリジナル版との違い

このフォーク版は、オリジナル版から以下の機能を変更・削除しています：

- ❌ ブラウザ版リプレイビューアー機能の削除
- ❌ Google Cloud Platform（GCP）へのアップロード機能の削除
- ❌ シーン解析・ベクトル化機能の削除
- ✅ ローカルファイル保存機能の強化
- ✅ 日本語版ゲームへの対応

## なぜ Miyoka なのか

多くの格闘ゲームはコンソールや PC（Steam）上でリプレイを視聴できますが、一つずつ手動で再生するのは手間がかかります。

Miyoka は、次のような流れを自動化することで、こうした手間を解消します。

- リプレイを自動で連続録画し、動画ファイルとして保存
- 録画した動画は任意のプレイヤーで視聴可能
- プレイヤーID やリプレイ ID を指定して特定のリプレイのみを録画

まとめると、Miyoka は格闘ゲームのリプレイ管理を効率化するためのツールです。🕹️

## リプレイは完全にプライベート

録画されたリプレイはすべてローカル PC に保存されます。クラウドへのアップロードは行われないため、プライバシーが確保されます。

## はじめ方

[Getting Started](./docs/getting_started.md) を参照してください。

## 謝辞

このプロジェクトは [fgcreplaymiyoka/fgc-replay-miyoka](https://github.com/fgcreplaymiyoka/fgc-replay-miyoka) をベースにしています。
オリジナルプロジェクトの開発者の皆様に心より感謝申し上げます。

## ライセンス

本プロジェクトは [GPL-3.0 License](./LICENSE) の下で公開されています。

