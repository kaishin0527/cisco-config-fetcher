
#!/usr/bin/env python3
"""
CLIからネットワークデバイス操作を実行するスクリプト
"""

import argparse
import sys
import json
from pathlib import Path

# 設定管理モジュールのインポート
from config_manager import get_devices, get_command_groups, get_scenarios

# ネットワーク実行モジュールのインポート
from network_executor import NetworkDeviceExecutor, test_device_connection

# ログ管理モジュールのインポート
from logger_manager import get_log_manager

def list_devices():
    """デバイス一覧を表示"""
    devices = get_devices()
    if not devices:
        print("デバイスが設定されていません")
        return
    
    print("=== デバイス一覧 ===")
    for device_name, device_config in devices.items():
        print(f"- {device_name}")
        print(f"  ホスト: {device_config.get('host', 'N/A')}")
        print(f"  デバイスタイプ: {device_config.get('device_type', 'N/A')}")
        print(f"  接続タイプ: {device_config.get('connection_type', 'ssh')}")
        print(f"  ユーザー名: {device_config.get('username', 'N/A')}")
        print()

def list_command_groups():
    """コマンドグループ一覧を表示"""
    command_groups = get_command_groups()
    if not command_groups:
        print("コマンドグループが設定されていません")
        return
    
    print("=== コマンドグループ一覧 ===")
    for group_name, group_config in command_groups.items():
        print(f"- {group_name}")
        print(f"  コマンド数: {len(group_config.get('commands', []))}")
        print(f"  コマンド: {group_config.get('commands', [])}")
        print()

def list_scenarios():
    """シナリオ一覧を表示"""
    scenarios = get_scenarios()
    if not scenarios:
        print("シナリオが設定されていません")
        return
    
    print("=== シナリオ一覧 ===")
    for scenario_name, scenario_config in scenarios.items():
        print(f"- {scenario_name}")
        print(f"  デバイス: {scenario_config.get('devices', [])}")
        print(f"  コマンド: {scenario_config.get('commands', [])}")
        print()

def test_connection(device_name):
    """デバイス接続をテスト"""
    devices = get_devices()
    if device_name not in devices:
        print(f"デバイス '{device_name}' が見つかりません")
        return
    
    device_config = devices[device_name]
    print(f"デバイス '{device_name}' の接続テストを開始...")
    
    result = test_device_connection(device_config)
    
    if result['success']:
        print("✅ 接続成功")
        print(f"接続時間: {result['connection_time']:.2f}秒")
    else:
        print("❌ 接続失敗")
        print(f"エラーメッセージ: {result['message']}")

def execute_commands(device_name, commands):
    """デバイスでコマンドを実行"""
    devices = get_devices()
    if device_name not in devices:
        print(f"デバイス '{device_name}' が見つかりません")
        return
    
    device_config = devices[device_name]
    executor = NetworkDeviceExecutor(device_config)
    
    print(f"デバイス '{device_name}' でコマンドを実行...")
    for i, command in enumerate(commands, 1):
        print(f"{i}. {command}")
    
    result = executor.execute_commands(commands)
    
    if result['success']:
        print("✅ コマンド実行成功")
        print(f"実行結果:\n{result['output']}")
    else:
        print("❌ コマンド実行失敗")
        print(f"エラー出力:\n{result['error_output']}")

def execute_command_group(device_name, group_name):
    """デバイスでコマンドグループを実行"""
    devices = get_devices()
    command_groups = get_command_groups()
    
    if device_name not in devices:
        print(f"デバイス '{device_name}' が見つかりません")
        return
    
    if group_name not in command_groups:
        print(f"コマンドグループ '{group_name}' が見つかりません")
        return
    
    device_config = devices[device_name]
    group_config = command_groups[group_name]
    
    executor = NetworkDeviceExecutor(device_config)
    
    print(f"デバイス '{device_name}' でコマンドグループ '{group_name}' を実行...")
    print(f"実行コマンド: {group_config.get('commands', [])}")
    
    result = executor.execute_command_group(group_name, command_groups)
    
    if result['success']:
        print("✅ コマンドグループ実行成功")
        print(f"実行結果:\n{result['output']}")
    else:
        print("❌ コマンドグループ実行失敗")
        print(f"エラー出力:\n{result['error_output']}")

def execute_scenario(device_name, scenario_name):
    """デバイスでシナリオを実行"""
    devices = get_devices()
    scenarios = get_scenarios()
    command_groups = get_command_groups()
    
    if device_name not in devices:
        print(f"デバイス '{device_name}' が見つかりません")
        return
    
    if scenario_name not in scenarios:
        print(f"シナリオ '{scenario_name}' が見つかりません")
        return
    
    device_config = devices[device_name]
    scenario_config = scenarios[scenario_name]
    
    executor = NetworkDeviceExecutor(device_config)
    
    print(f"デバイス '{device_name}' でシナリオ '{scenario_name}' を実行...")
    print(f"実行コマンド: {scenario_config.get('commands', [])}")
    
    result = executor.execute_scenario(scenario_config, command_groups)
    
    if result['success']:
        print("✅ シナリオ実行成功")
        print(f"実行結果:\n{result['output']}")
    else:
        print("❌ シナリオ実行失敗")
        print(f"エラー出力:\n{result['error_output']}")
        
        # 詳細なエラー情報を表示
        for i, cmd_result in enumerate(result.get('results', []), 1):
            if not cmd_result.get('success'):
                print(f"\n失敗したコマンド {i}:")
                print(f"コマンド: {cmd_result.get('command', 'N/A')}")
                print(f"エラー: {cmd_result.get('error_output', 'N/A')}")

def show_logs(device=None, command=None, start_date=None, end_date=None, limit=50):
    """ログを表示"""
    log_manager = get_log_manager()
    logs = log_manager.get_logs(device, command, start_date, end_date, limit)
    
    if not logs:
        print("ログが見つかりません")
        return
    
    print(f"=== ログ一覧 (合計 {len(logs)} 件) ===")
    for log in logs:
        timestamp = log.get('timestamp', 'N/A')
        device_name = log.get('device_name', 'N/A')
        cmd = log.get('command', 'N/A')
        success = log.get('success', False)
        exec_time = log.get('execution_time', 0)
        
        status = "✅" if success else "❌"
        print(f"{timestamp} | {status} {device_name} > {cmd} ({exec_time:.2f}s)")
        
        if not success:
            error = log.get('error_output', '')
            if error:
                print(f"  エラー: {error.strip()}")

def show_log_summary():
    """ログサマリーを表示"""
    log_manager = get_log_manager()
    summary = log_manager.get_log_summary()
    
    print("=== ログサマリー ===")
    print(f"総セッション数: {summary['total_sessions']}")
    print(f"成功セッション数: {summary['successful_sessions']}")
    print(f"失敗セッション数: {summary['failed_sessions']}")
    print(f"デバイス数: {summary['device_count']}")
    print(f"コマンド数: {summary['command_count']}")
    print(f"ログディレクトリ: {summary['log_directory']}")
    print(f"最終更新: {summary['last_updated']}")

def clear_logs(device=None, older_than_days=None):
    """ログをクリア"""
    log_manager = get_log_manager()
    
    if device:
        print(f"デバイス '{device}' のログをクリア...")
    elif older_than_days:
        print(f"{older_than_days}日より古いログをクリア...")
    else:
        print("すべてのログをクリア...")
    
    log_manager.clear_logs(device, older_than_days)
    print("ログをクリアしました")

def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description='ネットワークデバイス操作CLIツール')
    subparsers = parser.add_subparsers(dest='command', help='実行するコマンド')
    
    # デバイス一覧表示
    subparsers.add_parser('list-devices', help='デバイス一覧を表示')
    
    # コマンドグループ一覧表示
    subparsers.add_parser('list-groups', help='コマンドグループ一覧を表示')
    
    # シナリオ一覧表示
    subparsers.add_parser('list-scenarios', help='シナリオ一覧を表示')
    
    # 接続テスト
    test_parser = subparsers.add_parser('test', help='デバイス接続をテスト')
    test_parser.add_argument('device', help='テストするデバイス名')
    
    # コマンド実行
    cmd_parser = subparsers.add_parser('exec', help='コマンドを実行')
    cmd_parser.add_argument('device', help='実行対象デバイス名')
    cmd_parser.add_argument('commands', nargs='+', help='実行するコマンド')
    
    # コマンドグループ実行
    group_parser = subparsers.add_parser('exec-group', help='コマンドグループを実行')
    group_parser.add_argument('device', help='実行対象デバイス名')
    group_parser.add_argument('group', help='実行するコマンドグループ名')
    
    # シナリオ実行
    scenario_parser = subparsers.add_parser('exec-scenario', help='シナリオを実行')
    scenario_parser.add_argument('device', help='実行対象デバイス名')
    scenario_parser.add_argument('scenario', help='実行するシナリオ名')
    
    # ログ関連コマンド
    log_parser = subparsers.add_parser('logs', help='ログを表示')
    log_parser.add_argument('--device', help='デバイス名でフィルタ')
    log_parser.add_argument('--command', help='コマンドでフィルタ')
    log_parser.add_argument('--start-date', help='開始日 (YYYY-MM-DD)')
    log_parser.add_argument('--end-date', help='終了日 (YYYY-MM-DD)')
    log_parser.add_argument('--limit', type=int, default=50, help='表示件数')
    log_parser.add_argument('--summary', action='store_true', help='ログサマリーを表示')
    
    # ログクリアコマンド
    clear_parser = subparsers.add_parser('clear-logs', help='ログをクリア')
    clear_parser.add_argument('--device', help='デバイス名でフィルタ')
    clear_parser.add_argument('--older-than-days', type=int, help='指定日数より古いログをクリア')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == 'list-devices':
            list_devices()
        elif args.command == 'list-groups':
            list_command_groups()
        elif args.command == 'list-scenarios':
            list_scenarios()
        elif args.command == 'test':
            test_connection(args.device)
        elif args.command == 'exec':
            execute_commands(args.device, args.commands)
        elif args.command == 'exec-group':
            execute_command_group(args.device, args.group)
        elif args.command == 'exec-scenario':
            execute_scenario(args.device, args.scenario)
        elif args.command == 'logs':
            if args.summary:
                show_log_summary()
            else:
                show_logs(args.device, args.command, args.start_date, args.end_date, args.limit)
        elif args.command == 'clear-logs':
            clear_logs(args.device, args.older_than_days)
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
