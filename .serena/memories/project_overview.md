
# プロジェクト概要: cisco-config-fetcher

## プロジェクトの目的
Ciscoネットワーク機器から設定を取得するためのWebアプリケーション。SSHおよびTelnet接続の両方をサポートし、複数のデバイスに対してシナリオベースのコマンドを実行可能。

## 技術スタック
- Python 3.10
- Flask (Webフレームワーク)
- Paramiko (SSH接続)
- telnetlib3 (Telnet接続)
- asyncio (非同期処理)
- YAML (設定ファイル)
- HTML/CSS (テンプレート)

## コードスタイルと規約
- クラス名: キャメルケース (例: NetworkDeviceExecutor)
- メソッド名: スネークケース
- コメント: 主に日本語
- ロギング: Pythonのloggingモジュールを使用
- 非同期処理: asyncioを使用してasync/await構文で実装
- エラーハンドリング: try-exceptブロックで適切に例外をキャッチ

## タスク完了時のコマンド
1. `python3 app.py` - アプリケーションの実行
2. `python3 -m pytest` - テストの実行 (今後の実装が必要)
3. `python3 -m flake8` - コードの静的解析
4. `python3 -m black .` - コードの自動整形
5. `python3 -m isort .` - インポートの整理

## コードベースの構造
- `app.py`: Flaskのルートと主要なアプリケーションロジック
- `network_executor.py`: ネットワーク接続とコマンド実行のための主要なクラス
- `config_manager.py`: 設定管理
- `command_groups.yaml`: 実行可能なコマンドグループの定義
- `scenarios.yaml`: 設定取得のためのシナリオ
- `devices.yaml`: デバイスの種類と接続情報の定義
- `templates/`: Webテンプレート (results.html, result_detail.html, result_log.html)

## テストと検証
- CLIスクリプトでの基本的な機能テスト済
- Flaskルートの基本的な機能テスト済
- ネットワーク実行の自動テストは今後の実装予定
- 非同期Telnet機能のテストスイート作成予定

## 依存関係
- `paramiko`: SSH接続
- `telnetlib3`: Telnet接続
- `asyncio`: 非同期処理
- `PyYAML`: YAMLファイルの読み込み
- `Flask`: Webインターフェース

## 今後の実装予定
1. 実際のネットワーク機器との統合テスト
2. シナリオリストの並列実行機能の実装
3. タイムアウト固有のエラーハンドリング追加
4. 非同期Telnet機能の包括的なテストスイート作成
5. ロギング機能の拡充
