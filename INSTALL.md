
# Cisco Config Fetcher - 導入手順

## 概要
Cisco Config Fetcherは、Cisco機器の設定を自動で取得・管理するツールです。WebインターフェースとCLIの両方を備えており、設定のバックアップ、検証、リロード、コマンド実行を簡単に行えます。新たに追加されたログ機能により、全てのコマンド実行結果の記録と分析が可能です。

## 前提条件
- Python 3.8以上
- pip
- Cisco機器へのSSH/Telnetアクセス権限

## インストール手順

### 1. リポジトリのクローン
```bash
git clone https://github.com/kaishin0527/cisco-config-fetcher.git
cd cisco-config-fetcher
```

### 2. 依存パッケージのインストール
```bash
# 依存パッケージのインストール
pip install -r requirements.txt
```

### 3. 設定ファイルの作成
YAML形式の設定ファイルを作成し、Cisco機器の接続情報を設定します。

#### デバイス設定 (devices.yaml)
```yaml
devices:
  firewall-01:
    host: "192.168.1.3"
    username: "admin"
    password: "password"
    connection_type: "ssh"
    secret: "enable_password"
    group: "firewalls"
    
  router-01:
    host: "192.168.1.1"
    username: "admin"
    password: "password"
    connection_type: "ssh"
    secret: "enable_password"
    group: "routers"
    
  switch-01:
    host: "192.168.1.2"
    username: "admin"
    password: "password"
    connection_type: "telnet"
    group: "switches"
```

#### コマンドグループ設定 (command_groups.yaml)
```yaml
command_groups:
  basic-config:
    description: "基本情報取得"
    commands:
      - "show version"
      - "show running-config"
      - "show interface status"
      
  interface-config:
    description: "インターフェース情報"
    commands:
      - "show ip interface brief"
      - "show interface description"
      - "show interface counters"
      
  security-config:
    description: "セキュリティ設定"
    commands:
      - "show access-lists"
      - "show ip ssh"
      - "show crypto isakmp sa"
```

#### シナリオ設定 (scenarios.yaml)
```yaml
scenarios:
  device-health-check:
    description: "デバイスヘルスチェック"
    devices: ["router-01", "switch-01"]
    commands: ["show version", "show uptime", "show memory"]
    group: "monitoring"
    
  security-audit:
    description: "セキュリティ監査"
    devices: ["firewall-01", "router-01"]
    commands: ["show access-lists", "show ip ssh", "show crypto isakmp sa"]
    group: "security"
```

## 使用方法

### Webインターフェースの起動
```bash
# Webアプリケーションの起動
python3 app.py
```

Webブラウザで `http://localhost:5000` にアクセスします。

### コマンドラインインターフェースの使用
```bash
# CLIツールの起動
python3 cli_executor.py --help

# デバイス一覧の表示
python3 cli_executor.py list-devices

# コマンドグループ一覧の表示
python3 cli_executor.py list-groups

# シナリオ一覧の表示
python3 cli_executor.py list-scenarios

# デバイス接続テスト
python3 cli_executor.py test firewall-01

# 単一コマンドの実行
python3 cli_executor.py exec router-01 "show version" "show running-config"

# コマンドグループの実行
python3 cli_executor.py exec-group router-01 basic-config

# シナリオの実行
python3 cli_executor.py exec-scenario router-01 device-health-check

# ログの表示
python3 cli_executor.py logs --limit 20

# ログサマリーの表示
python3 cli_executor.py logs --summary

# デバイス別ログの表示
python3 cli_executor.py logs --device router-01

# ログのクリア
python3 cli_executor.py clear-logs --device router-01
```

## 主要機能

### 1. デバイス管理
- YAML形式のデバイス設定ファイル
- SSH/Telnet接続のサポート
- デバイスグループ分け機能
- 接続テスト機能

### 2. コマンド実行
- 単一コマンドの実行
- コマンドグループの実行
- シナリオベースの一括実行
- 非同期実行サポート

### 3. ログ機能
- 全コマンド実行結果の自動記録
- JSON形式の永続的ログ保存
- デバイス・コマンド・日付別フィルタリング
- ログサマリーと統計情報
- CLIとWeb GUIでのログ閲覧

### 4. Webインターフェース
- デバイス管理ダッシュボード
- コマンドグループ管理
- シナリオ管理と実行
- 実行結果の表示
- ログ閲覧インターフェース
- 検索とフィルタリング機能

### 5. CLIツール
- 直感的なコマンドラインインターフェース
- 詳細なヘルプと使い方表示
- ログ管理機能
- バッチ処理サポート

## ディレクトリ構成
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
│   ├── base.html
│   ├── index.html
│   ├── devices.html
│   ├── command_groups.html
│   ├── scenarios.html
│   ├── execute.html
│   ├── results.html
│   ├── result_detail.html
│   ├── result_log.html
│   └── logs.html
├── static/                        # 静的ファイル
└── results/                       # 実行結果ディレクトリ
```

## トラブルシューティング

### 1. 接続エラー
- Cisco機器との接続を確認
- SSHポート(22)/Telnetポート(23)が開いているか確認
- 認証情報が正しいか確認
- デバイスの接続タイプ(ssh/telnet)が正しいか確認

### 2. Webインターフェースが表示されない
- ポート5000が他のプロセスで使用されていないか確認
- ファイアウォール設定を確認
- IPアドレスが正しいか確認

### 3. YAML設定ファイルのエラー
- YAMLファイルの構文を確認（インデントに注意）
- 必須フィールド（host, username, password, connection_type）が設定されているか確認
- ファイルパスが正しいか確認

### 4. ログ機能のエラー
- logsディレクトリの書き込み権限を確認
- ディスク容量が十分にあるか確認
- ログファイルの破損がないか確認

### 5. CLIツールのエラー
- Python 3.8以上がインストールされているか確認
- 依存パッケージが正しくインストールされているか確認
- 設定ファイルが存在するか確認

## 注意事項
- 本ツールを使用する前に、必ずテスト環境で動作確認を行ってください
- 設定の変更やコマンド実行は、本番環境で実行する前に十分にテストしてください
- 認証情報は安全に管理してください（YAMLファイルに平文で保存されます）
- 定期的にバックアップを実行することをお勧めします
- ログファイルは定期的にクリアまたはアーカイブしてください

## ライセンス
MIT License
