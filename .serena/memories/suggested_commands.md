

# cisco-config-fetcher でよく使うコマンド

## 開発コマンド
```bash
# アプリケーションの起動
python3 app.py

# コードの静的解析
python3 -m flake8

# コードの自動整形
python3 -m black .
python3 -m isort .

# テストの実行 (テストが実装された後)
python3 -m pytest

# 依存関係のインストール
pip3 install -r requirements.txt
```

## ネットワーク接続テスト
```bash
# SSH接続のテスト
python3 -c "from network_executor import NetworkDeviceExecutor; \
    executor = NetworkDeviceExecutor('device_name', 'ssh', 'hostname', 'username', 'password'); \
    executor.connect(); \
    print(executor.execute_commands(['show version'])); \
    executor.disconnect()"

# Telnet接続のテスト
python3 -c "from network_executor import NetworkDeviceExecutor; \
    executor = NetworkDeviceExecutor('device_name', 'telnet', 'hostname', 'username', 'password'); \
    executor.connect(); \
    print(executor.execute_commands(['show version'])); \
    executor.disconnect()"
```

## デバッグコマンド
```bash
# ロギングレベルの変更
export LOG_LEVEL=DEBUG
python3 app.py

# ネットワークパケットのキャプチャ
tcpdump -i any port 23 -w telnet_capture.pcap

# コードカバレッジの確認
python3 -m pytest --cov=network_executor.py
```

## バージョン管理コマンド
```bash
# 現在の変更の確認
git status

# 変更のコミット
git add .
git commit --author="openhands <openhands@all-hands.dev>" -m "Telnet接続の非同期切断処理を改善"

# ブランチの作成と切り替え
git checkout -b feature/telnet-async
git push origin feature/telnet-async

# プルリクエストの作成
gh pr create --title \"Telnet非同期切断の実装\" --body \"Telnet接続の切断処理を非同期に対応させました。\n- network_executor.pyのdisconnect()メソッドを修正\n- telnetlib3の非同期close()をawaitで適切に処理\n- イベントループ管理を最適化\n- 日本語コメントの修正\" --head feature/telnet-async
```

## テストの実装計画
```bash
# テスト環境のセットアップ
python3 -m pytest --setup-only -q

# テストの実行 (今後の実装)
python3 -m pytest tests/network_executor_test.py

# テストカバレッジの実行 (今後の実装)
python3 -m pytest --cov=network_executor.py --cov-report=term-missing
```

