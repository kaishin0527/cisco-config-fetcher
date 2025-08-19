
# Cisco Config Manager プロジェクト

## 目的
Cisco機器への自動化アクセスを提供するスクリプトとWebインターフェースの開発：
- 複数機器への同時コマンド実行
- シナリオベースの設定管理
- 実行結果の構造化保存

## 技術スタック
- **言語**: Python 3.12+
- **主要ライブラリ**:
  - Netmiko (SSH/Telnet接続)
  - Flask (Webインターフェース)
  - PyYAML (設定管理)
- **フロントエンド**: Bootstrap 5

## コード構造
```
/workspace
├── cisco_config_fetcher_parallel.py  # メインスクリプト
├── web_app_complete.py               # Web管理インターフェース
├── templates/                        # HTMLテンプレート
│   ├── base.html
│   ├── devices.html
│   └── ...(7ファイル)
├── configs/                          # 設定ファイル
│   ├── devices_updated.yaml
│   ├── command_groups.yaml
│   └── scenario_list.yaml
```

## 開発ガイドライン
1. 設定ファイルはYAML形式で統一
2. 関数にはdocstringを記載
3. 例外処理を詳細に実装
4. ロギングを活用した実行トレース
