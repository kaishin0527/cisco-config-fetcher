
import yaml
import os
import sys
from pathlib import Path

# ネットワーク実行モジュールのインポート
from network_executor import NetworkDeviceExecutor, test_device_connection

# 設定管理モジュールのインポート
from config_manager import get_devices, get_command_groups, get_scenarios

def test_ssh_connection():
    """SSH接続テスト"""
    print("\nSSH接続テストを開始します")
    
    # モックデバイス設定
    device_config = {
        'connection_type': 'ssh',
        'device_type': 'cisco_ios',
        'host': '127.0.0.1',
        'username': 'user',
        'password': 'pass',
        'port': 2222,
        'wait_string': '#'
    }
    
    print(f"テスト対象デバイス: モックSSHデバイス")
    print(f"ホスト: {device_config.get('host')}")
    print(f"デバイスタイプ: {device_config.get('device_type')}")
    print(f"接続タイプ: {device_config.get('connection_type')}")
    
    # 接続テスト
    result = test_device_connection(device_config)
    
    print(f"SSH接続テスト結果: {result}")
    return result

def test_telnet_connection():
    """Telnet接続テスト"""
    print("\nTelnet接続テストを開始します")
    
    # モックデバイス設定
    device_config = {
        'connection_type': 'telnet',
        'device_type': 'cisco_ios',
        'host': '127.0.0.1',
        'username': 'user',
        'password': 'pass',
        'port': 2323,
        'wait_string': '#'
    }
    
    print(f"テスト対象デバイス: モックTelnetデバイス")
    print(f"ホスト: {device_config.get('host')}")
    print(f"デバイスタイプ: {device_config.get('device_type')}")
    print(f"接続タイプ: {device_config.get('connection_type')}")
    
    # 接続テスト
    result = test_device_connection(device_config)
    
    print(f"Telnet接続テスト結果: {result}")
    return result

def test_command_execution():
    """コマンド実行テスト"""
    print("\nコマンド実行テストを開始します")
    
    # モックデバイス設定
    device_config = {
        'connection_type': 'ssh',
        'device_type': 'cisco_ios',
        'host': '127.0.0.1',
        'username': 'user',
        'password': 'pass',
        'port': 2222,
        'wait_string': '#'
    }
    
    print(f"テスト対象デバイス: モックSSHデバイス")
    
    # ネットワークデバイスエグゼキュータの作成
    executor = NetworkDeviceExecutor(device_config)
    
    # コマンド実行テスト
    commands = ['show version', 'show running-config']
    result = executor.execute_commands(commands)
    
    print(f"コマンド実行結果: {result}")
    return result

def test_scenario_execution():
    """シナリオ実行テスト"""
    print("\nシナリオ実行テストを開始します")
    
    # モックデバイス設定
    device_config = {
        'connection_type': 'ssh',
        'device_type': 'cisco_ios',
        'host': '127.0.0.1',
        'username': 'user',
        'password': 'pass',
        'port': 2222,
        'wait_string': '#'
    }
    
    # モックシナリオ設定
    scenario_config = {
        'devices': ['mock-device'],
        'commands': ['show version', 'show running-config']
    }
    
    # モックコマンドグループ設定
    command_groups = {
        'basic-config': {
            'commands': ['show version', 'show interface brief']
        },
        'interface-config': {
            'commands': ['show running-config interface']
        }
    }
    
    print(f"テスト対象デバイス: モックSSHデバイス")
    print(f"テスト対象シナリオ: モックシナリオ")
    
    # ネットワークデバイスエグゼキュータの作成
    executor = NetworkDeviceExecutor(device_config)
    
    # シナリオ実行テスト
    result = executor.execute_scenario(scenario_config, command_groups)
    
    print(f"シナリオ実行結果: {result}")
    return result

def test_command_group_execution():
    """コマンドグループ実行テスト"""
    print("\nコマンドグループ実行テストを開始します")
    
    # モックデバイス設定
    device_config = {
        'connection_type': 'ssh',
        'device_type': 'cisco_ios',
        'host': '127.0.0.1',
        'username': 'user',
        'password': 'pass',
        'port': 2222,
        'wait_string': '#'
    }
    
    # モックコマンドグループ設定
    command_groups = {
        'basic-config': {
            'commands': ['show version', 'show interface brief']
        },
        'interface-config': {
            'commands': ['show running-config interface']
        }
    }
    
    group_name = 'basic-config'
    
    print(f"テスト対象デバイス: モックSSHデバイス")
    print(f"テスト対象コマンドグループ: {group_name}")
    print(f"コマンドリスト: {command_groups[group_name].get('commands', [])}")
    
    # ネットワークデバイスエグゼキュータの作成
    executor = NetworkDeviceExecutor(device_config)
    
    # コマンドグループ実行テスト
    result = executor.execute_command_group(group_name, command_groups)
    
    print(f"コマンドグループ実行結果: {result}")
    return result

def main():
    """メイン関数"""
    print("テストを開始します")
    
    # 設定ファイルのバリデーション
    from config_manager import config_manager
    validation_results = config_manager.validate_all_configs()
    
    print(f"設定ファイルのバリデーション結果: {validation_results}")
    
    if not all(validation_results.values()):
        print("設定ファイルに問題があります")
        return
    
    # 各種テストの実行
    tests = [
        ("SSH接続テスト", test_ssh_connection),
        ("Telnet接続テスト", test_telnet_connection),
        ("コマンド実行テスト", test_command_execution),
        ("コマンドグループ実行テスト", test_command_group_execution),
        ("シナリオ実行テスト", test_scenario_execution),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"{test_name}でエラーが発生しました: {e}")
            results[test_name] = {'success': False, 'error': str(e)}
    
    print("\nテストを終了します")
    print(f"テスト結果のサマリー: {results}")

if __name__ == "__main__":
    main()
