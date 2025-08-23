

# Cisco Config Fetcher

Cisco機器の設定を自動で取得・管理するツールです。WebインターフェースとCLIの両方を備えており、設定のバックアップ、検証、リロード、コマンド実行を簡単に行えます。新たに追加されたログ機能により、全てのコマンド実行結果の記録と分析が可能です。

## 🌟 主な特徴

### 📋 デバイス管理
- **YAML設定ファイル**: 直感的なYAML形式でデバイスを管理
- **多プロトコル対応**: SSHとTelnetの両方に対応
- **デバイスグループ**: デバイスをグループ分けして一括管理
- **接続テスト**: デバイスへの接続を簡単にテスト

### ⚡ コマンド実行
- **単一コマンド実行**: 個別のコマンドを即座に実行
- **コマンドグループ**: 事前定義したコマンドセットを一括実行
- **シナリオベース**: 複数デバイスに対する複雑な実行シナリオ
- **非同期実行**: 複数デバイスの並列実行サポート

### 📊 ログ機能
- **自動記録**: 全てのコマンド実行結果を自動で記録
- **永続保存**: JSON形式でログを永続的に保存
- **高度なフィルタリング**: デバイス、コマンド、日付別にフィルタリング
- **統計情報**: 実行成功率、実行時間などの統計分析
- **多インターフェース**: CLIとWeb GUIの両方でログ閲覧可能

### 🌐 Webインターフェース
- **ダッシュボード**: デバイス状態の一目瞭然な表示
- **管理機能**: デバイス、コマンドグループ、シナリオの管理
- **実行管理**: シナリオの実行と結果表示
- **ログ閲覧**: 検索・フィルタリング機能付きのログビューア

### 💻 CLIツール
- **直感的な操作**: コマンドラインから簡単に操作
- **詳細なヘルプ**: 各コマンドの詳細なヘルプ表示
- **ログ管理**: ログの表示、サマリー、クリア機能
- **バッチ処理**: スクリプトによる自動化対応

## 🚀 クイックスタート

### インストール
```bash
# リポジトリのクローン
git clone https://github.com/kaishin0527/cisco-config-fetcher.git
cd cisco-config-fetcher

# 依存パッケージのインストール
pip install -r requirements.txt
```

### 設定ファイルの準備
```yaml
# devices.yaml
devices:
  router-01:
    host: "192.168.1.1"
    username: "admin"
    password: "password"
    connection_type: "ssh"
    secret: "enable_password"
    group: "routers"

# command_groups.yaml
command_groups:
  basic-info:
    description: "基本情報取得"
    commands:
      - "show version"
      - "show running-config"
      - "show interface status"

# scenarios.yaml
scenarios:
  health-check:
    description: "デバイスヘルスチェック"
    devices: ["router-01"]
    commands: ["show version", "show uptime", "show memory"]
```

### Webインターフェースの起動
```bash
python3 app.py
```
ブラウザで `http://localhost:5000` にアクセス

### CLIツールの使用
```bash
# ヘルプの表示
python3 cli_executor.py --help

# デバイス一覧の表示
python3 cli_executor.py list-devices

# コマンド実行
python3 cli_executor.py exec router-01 "show version"

# シナリオ実行
python3 cli_executor.py exec-scenario router-01 health-check

# ログの表示
python3 cli_executor.py logs --summary
```

## 📖 詳細な使い方

### デバイス管理
デバイスは `devices.yaml` ファイルで管理します。各デバイスには以下の情報を設定できます：

```yaml
devices:
  device-name:
    host: "192.168.1.1"           # デバイスのIPアドレスまたはホスト名
    username: "admin"              # ユーザー名
    password: "password"            # パスワード
    connection_type: "ssh"         # 接続タイプ (ssh/telnet)
    secret: "enable_password"      # プライベートモード用パスワード（オプション）
    group: "routers"              # グループ名（オプション）
```

### コマンドグループ
よく実行するコマンドのセットを `command_groups.yaml` で定義できます：

```yaml
command_groups:
  basic-config:
    description: "基本情報取得"
    commands:
      - "show version"
      - "show running-config"
      - "show interface status"
```

### シナリオ
複数のデバイスに対する実行シナリオを `scenarios.yaml` で定義できます：

```yaml
scenarios:
  network-audit:
    description: "ネットワーク監査"
    devices: ["router-01", "switch-01"]
    commands: ["show version", "show interface", "show log"]
    group: "audit"
```

### ログ機能
全てのコマンド実行結果は自動的に記録されます：

```bash
# 最新の20件のログを表示
python3 cli_executor.py logs --limit 20

# 特定デバイスのログを表示
python3 cli_executor.py logs --device router-01

# 特定コマンドのログを表示
python3 cli_executor.py logs --command "show version"

# 日付範囲を指定してログを表示
python3 cli_executor.py logs --start-date 2024-01-01 --end-date 2024-01-31

# ログサマリーを表示
python3 cli_executor.py logs --summary

# ログをクリア
python3 cli_executor.py clear-logs --device router-01
```

## 🔧 構成

### ディレクトリ構成
```
cisco-config-fetcher/
├── app.py                         # Webアプリケーション
├── cli_executor.py                # CLIツール
├── network_executor.py            # ネットワーク実行エンジン
├── logger_manager.py              # ログ管理機能
├── config_manager.py              # 設定管理機能
├── mock_device.py                 # モックデバイス（テスト用）
├── test_mock.py                   # テストスクリプト
├── requirements.txt               # 依存パッケージ
├── devices.yaml                   # デバイス設定ファイル
├── command_groups.yaml            # コマンドグループ設定
├── scenarios.yaml                 # シナリオ設定
├── logs/                          # ログディレクトリ
├── templates/                     # HTMLテンプレート
├── static/                        # 静的ファイル
└── results/                       # 実行結果ディレクトリ
```

### 主要ファイルの役割

| ファイル | 役割 |
|---------|------|
| `app.py` | Webアプリケーションメイン |
| `cli_executor.py` | コマンドラインインターフェース |
| `network_executor.py` | ネットワーク接続とコマンド実行 |
| `logger_manager.py` | ログ管理機能 |
| `config_manager.py` | 設定ファイル管理 |
| `devices.yaml` | デバイス設定 |
| `command_groups.yaml` | コマンドグループ設定 |
| `scenarios.yaml` | 実行シナリオ設定 |

## 🛠️ 依存パッケージ

```txt
Flask==2.3.3
paramiko==3.3.1
telnetlib3==3.7.0
PyYAML==6.0.1
```

## 🔍 トラブルシューティング

### 接続エラー
- デバイスとの接続を確認
- SSHポート(22)/Telnetポート(23)が開いているか確認
- 認証情報が正しいか確認
- デバイスの接続タイプが正しいか確認

### YAML設定ファイルのエラー
- YAMLファイルの構文を確認（インデントに注意）
- 必須フィールドが設定されているか確認
- ファイルパスが正しいか確認

### ログ機能のエラー
- `logs` ディレクトリの書き込み権限を確認
- ディスク容量が十分にあるか確認
- ログファイルの破損がないか確認

### CLIツールのエラー
- Python 3.8以上がインストールされているか確認
- 依存パッケージが正しくインストールされているか確認
- 設定ファイルが存在するか確認

## ⚠️ 注意事項

- 本ツールを使用する前に、必ずテスト環境で動作確認を行ってください
- 設定の変更やコマンド実行は、本番環境で実行する前に十分にテストしてください
- 認証情報は安全に管理してください（YAMLファイルに平文で保存されます）
- 定期的にバックアップを実行することをお勧めします
- ログファイルは定期的にクリアまたはアーカイブしてください

## 📄 ライセンス

MIT License

## 🤝 貢献

バグ報告や機能リクエストは [GitHub Issues](https://github.com/kaishin0527/cisco-config-fetcher/issues) までお願いします。

## 📞 サポート

ご質問やサポートが必要な場合は、GitHubのIssuesまたはPull Requestsをご利用ください。

---

**Cisco Config Fetcher** - ネットワーク管理を自動化する強力なツール
