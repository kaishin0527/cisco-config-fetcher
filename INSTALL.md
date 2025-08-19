
# Cisco Config Fetcher - 導入手順

## 概要
Cisco Config Fetcherは、Cisco機器の設定を自動で取得・管理するツールです。Webインターフェースを備えており、設定のバックアップ、検証、リロードを簡単に行えます。

## 前提条件
- Python 3.8以上
- pip
- Cisco機器へのSSHアクセス権限

## インストール手順

### 1. リポジトリのクローン
```bash
git clone https://github.com/kaishin0527/cisco-config-fetcher.git
cd cisco-config-fetcher
```

### 2. 仮想環境の作成と依存パッケージのインストール
```bash
# 仮想環境の作成
python3 -m venv venv

# 仮想環境のアクティベート
source venv/bin/activate

# 依存パッケージのインストール
pip install -r requirements.txt
```

### 3. 設定ファイルの作成
`config.yaml`ファイルを作成し、Cisco機器の接続情報を設定します。

```yaml
devices:
  - name: "router1"
    host: "192.168.1.1"
    username: "admin"
    password: "password"
    device_type: "cisco_ios"
    enable_secret: "enable_password"
    backup_dir: "backups/router1"
    
  - name: "switch1"
    host: "192.168.1.2"
    username: "admin"
    password: "password"
    device_type: "cisco_ios"
    enable_secret: "enable_password"
    backup_dir: "backups/switch1"
```

### 4. 実行権限の設定
```bash
chmod +x fetch_config.py
chmod +x web_app_complete_fixed.py
```

## 使用方法

### Webインターフェースの起動
```bash
python3 web_app_complete_fixed.py
```

Webブラウザで `http://localhost:51361` にアクセスします。

### コマンドラインインターフェースの使用
```bash
# 設定の取得
python3 fetch_config.py

# 特定のデバイスから設定を取得
python3 fetch_config.py --device router1

# 設定の検証
python3 fetch_config.py --validate

# 設定のリロード
python3 fetch_config.py --reload
```

## 主要機能

### 1. 設定の自動取得
- 指定されたCisco機器から設定を自動で取得
- バックアップディレクトリに保存
- 差分検出機能

### 2. 設定の検証
- 設定ファイルの構文チェック
- セキュリティポリシーの検証
- 一貫性チェック

### 3. 設定のリロード
- 変更された設定の適用
- ロールバック機能
- 実行ログの記録

### 4. Webインターフェース
- ダッシュボード表示
- デバイス管理
- 設定の閲覧と比較
- 実行結果の表示

## ディレクトリ構成
```
cisco-config-fetcher/
├── fetch_config.py          # メインの設定取得スクリプト
├── web_app_complete_fixed.py # Webインターフェース
├── config_manager.py        # 設定管理機能
├── requirements.txt         # 依存パッケージ
├── config.yaml              # 設定ファイル
├── backups/                 # バックアップディレクトリ
├── templates/               # HTMLテンプレート
└── static/                  # 静的ファイル
```

## トラブルシューティング

### 1. 接続エラー
- Cisco機器との接続を確認
- SSHポート(22)が開いているか確認
- 認証情報が正しいか確認

### 2. Webインターフェースが表示されない
- ポート51361が他のプロセスで使用されていないか確認
- ファイアウォール設定を確認
- IPアドレスが正しいか確認

### 3. 設定取得エラー
- デバイスタイプが正しいか確認
- ネットワーク接続を確認
- 設定ファイルの構文を確認

## 注意事項
- 本ツールを使用する前に、必ずテスト環境で動作確認を行ってください
- 設定のリロードは、本番環境で実行する前に十分にテストしてください
- 認証情報は安全に管理してください
- 定期的にバックアップを実行することをお勧めします

## ライセンス
MIT License
