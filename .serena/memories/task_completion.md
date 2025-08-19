


# タスク完了時のチェックリスト

## コード変更後
1. **フォーマットチェック**
   ```bash
   black --check .
   ```

2. **静的解析**
   ```bash
   pylint *.py
   ```

3. **テスト実行**
   ```bash
   pytest test_*.py
   ```

4. **依存関係更新**
   ```bash
   pip freeze > requirements.txt
   ```

## コミット前
1. 変更ファイルの確認
   ```bash
   git status
   ```

2. 変更点のレビュー
   ```bash
   git diff
   ```

3. 意味のあるコミットメッセージ作成
   ```
   feat: デバイス管理機能の追加
   fix: SSH接続のタイムアウト問題修正
   docs: コマンドグループの説明更新
   ```

## デプロイ前
1. 設定ファイルのバックアップ
   ```bash
   cp devices_updated.yaml devices_$(date +%Y%m%d).yaml
   ```

2. データベースマイグレーション（将来実装時）
   ```bash
   flask db upgrade
   ```

3. サービス再起動
   ```bash
   sudo systemctl restart cisco-config.service
   ```

## ドキュメンテーション更新
1. READMEの更新
2. 変更点のリリースノート追記
3. APIドキュメントの更新（Swaggerなど）

