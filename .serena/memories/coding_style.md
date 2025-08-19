

# コーディングスタイルガイドライン

## 命名規則
- **変数/関数**: スネークケース (`snake_case`)
- **クラス**: キャメルケース (`CamelCase`)
- **定数**: 大文字スネークケース (`UPPER_SNAKE_CASE`)
- **プライベートメンバ**: 接頭辞にアンダースコア (`_private_var`)

## ドキュメンテーション
```python
def connect_to_device(device_config):
    """
    Ciscoデバイスに接続する
    
    Args:
        device_config (dict): デバイス設定情報
            - host: ホスト名/IP
            - device_type: デバイスタイプ
            - username: ユーザー名
            - password: パスワード
            - secret: 特権モードパスワード
    
    Returns:
        netmiko.ConnectHandler: 接続オブジェクト
    
    Raises:
        NetMikoAuthenticationException: 認証エラー
        NetMikoTimeoutException: 接続タイムアウト
    """
    # 実装コード
```

## 型ヒント
```python
from typing import Dict, List, Optional

def send_commands(
    connection: netmiko.BaseConnection,
    commands: List[str],
    config_mode: bool = False
) -> Dict[str, str]:
    """
    コマンドを実行し結果を返す
    """
```

## コード構造
1. インポートは標準ライブラリ→サードパーティ→ローカルモジュールの順
2. クラスメソッドの順序:
   - `__init__`
   - `@property`
   - `@classmethod`
   - その他メソッド（公開→非公開）
3. 1関数あたり最大50行

## エラーハンドリング
```python
try:
    output = connection.send_command(command)
except (NetMikoTimeoutException, NetMikoAuthenticationException) as e:
    logger.error(f"デバイス接続エラー: {device['host']} - {str(e)}")
    return None
finally:
    if connection:
        connection.disconnect()
```

## ロギング
```python
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# ファイルハンドラ設定
file_handler = logging.FileHandler('app.log')
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))
logger.addHandler(file_handler)
```

