

# プロジェクト操作コマンド集

## 開発環境セットアップ
```bash
# 依存パッケージのインストール
pip install flask pyyaml netmiko

# 環境変数の設定（必要に応じて）
export FLASK_APP=web_app_complete.py
```

## アプリケーション実行
```bash
# Webインターフェース起動
python web_app_complete.py

# バッチスクリプト実行（シナリオ処理）
python cisco_config_fetcher_parallel.py scenario_parallel.yaml
```

## テスト関連
```bash
# 単体テスト実行（テスト作成後）
pytest test_*.py

# カバレッジ計測
coverage run -m pytest
coverage report
```

## コード品質管理
```bash
# コードフォーマット
black *.py

# 静的解析
pylint *.py
```

## バージョン管理
```bash
# 変更ステータス確認
git status

# 変更をコミット
git add .
git commit -m "メッセージ"

# リモートリポジトリにプッシュ
git push origin main
```

## デバッグ
```bash
# 実行ログの監視
tail -f server.log

# ポート使用状況確認
lsof -i :51361
```

## 設定ファイル操作
```bash
# デバイス設定の検証
yamllint devices_updated.yaml

# シナリオファイルのプレビュー
cat scenario_parallel.yaml
```

