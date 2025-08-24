
#!/usr/bin/env python3
"""
設定ファイル変換ツール
TXT形式とYAML形式の相互変換を行うツール
"""

import yaml
import os
import sys
import csv
from typing import Dict, List, Any
from datetime import datetime


class ConfigConverter:
    """設定ファイル変換クラス"""
    
    def __init__(self):
        self.supported_formats = ['txt', 'yaml']
    
    def convert_devices_txt_to_yaml(self, txt_file: str, output_file: str = None) -> str:
        """
        device_list.txtをYAML形式に変換
        
        Args:
            txt_file: device_list.txtファイルパス
            output_file: 出力先YAMLファイルパス（指定しない場合は自動生成）
        
        Returns:
            出力されたYAMLファイルのパス
        """
        if not os.path.exists(txt_file):
            raise FileNotFoundError(f"ファイルが見つかりません: {txt_file}")
        
        # デフォルトの出力ファイル名
        if output_file is None:
            base_name = os.path.splitext(os.path.basename(txt_file))[0]
            output_file = f"{base_name}_converted.yaml"
        
        devices = {}
        
        def determine_device_group(hostname: str) -> str:
            """デバイス名からデバイスグループを判定"""
            hostname_lower = hostname.lower()
            
            # APICデバイス
            if hostname_lower.startswith('apic'):
                return 'apic_devices'
            
            # Leafスイッチ
            if hostname_lower.startswith('leaf'):
                return 'leaf_devices'
            
            # Spineスイッチ
            if hostname_lower.startswith('spine'):
                return 'spine_devices'
            
            # L3スイッチ
            if hostname_lower.startswith('l3sw') or hostname_lower.startswith('ext-l3sw'):
                return 'l3_devices'
            
            # デフォルト（変換ツールで登録されたデバイス）
            return 'txt_yaml'
        
        with open(txt_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                device_name = row['hostname']
                device_group = determine_device_group(device_name)
                
                devices[device_name] = {
                    'host': row['host'],
                    'username': row['username'],
                    'password': row['password'],
                    'prompt': row['prompt'],
                    'connection_type': 'ssh',  # デフォルトSSH
                    'device_group': device_group,  # デバイスが属するグループ
                    'command_group': row.get('command_group', 'default'),  # 実行するコマンドグループ
                    'description': f"{device_name} - {row.get('hostname', device_name)}"
                }
        
        # YAMLファイルの書き出し
        yaml_data = {'devices': devices}
        with open(output_file, 'w', encoding='utf-8') as f:
            yaml.dump(yaml_data, f, default_flow_style=False, allow_unicode=True, indent=2)
        
        print(f"✅ デバイス設定をYAML形式に変換しました: {output_file}")
        print(f"  - 変換されたデバイス数: {len(devices)}")
        
        # デバイスグループの内訳を表示
        device_groups = {}
        for device_name, config in devices.items():
            group = config['device_group']
            if group not in device_groups:
                device_groups[group] = []
            device_groups[group].append(device_name)
        
        print("  - デバイスグループ内訳:")
        for group, device_names in device_groups.items():
            print(f"    - {group}: {len(device_names)} devices")
        
        return output_file
    
    def convert_groups_txt_to_yaml(self, txt_file: str, output_file: str = None) -> str:
        """
        group_name_command.txtをYAML形式に変換
        
        Args:
            txt_file: group_name_command.txtファイルパス
            output_file: 出力先YAMLファイルパス（指定しない場合は自動生成）
        
        Returns:
            出力されたYAMLファイルのパス
        """
        if not os.path.exists(txt_file):
            raise FileNotFoundError(f"ファイルが見つかりません: {txt_file}")
        
        # デフォルトの出力ファイル名
        if output_file is None:
            base_name = os.path.splitext(os.path.basename(txt_file))[0]
            output_file = f"{base_name}_converted.yaml"
        
        command_groups = {}
        
        with open(txt_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                group_name = row['group_name']
                command = row['command']
                
                if group_name not in command_groups:
                    command_groups[group_name] = {
                        'description': f"{group_name}用のコマンドグループ",
                        'commands': []
                    }
                
                command_groups[group_name]['commands'].append(command)
        
        # YAMLファイルの書き出し
        with open(output_file, 'w', encoding='utf-8') as f:
            yaml.dump(command_groups, f, default_flow_style=False, allow_unicode=True, indent=2)
        
        print(f"✅ コマンドグループをYAML形式に変換しました: {output_file}")
        print(f"  - 変換されたグループ数: {len(command_groups)}")
        
        # 各グループのコマンド数を表示
        for group_name, config in command_groups.items():
            print(f"    - {group_name}: {len(config['commands'])} commands")
        
        return output_file
    
    def convert_yaml_to_devices_txt(self, yaml_file: str, output_file: str = None) -> str:
        """
        YAML形式のデバイス設定をTXT形式に変換
        
        Args:
            yaml_file: YAML形式のデバイス設定ファイルパス
            output_file: 出力先TXTファイルパス（指定しない場合は自動生成）
        
        Returns:
            出力されたTXTファイルのパス
        """
        if not os.path.exists(yaml_file):
            raise FileNotFoundError(f"ファイルが見つかりません: {yaml_file}")
        
        # デフォルトの出力ファイル名
        if output_file is None:
            base_name = os.path.splitext(os.path.basename(yaml_file))[0]
            output_file = f"{base_name}_converted.txt"
        
        # YAMLファイルの読み込み
        with open(yaml_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        devices = data.get('devices', {})
        
        # TXTファイルの書き出し
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            # ヘッダー
            writer.writerow(['host', 'hostname', 'username', 'password', 'prompt', 'command_group'])
            
            # データ
            for device_name, config in devices.items():
                host = config.get('host', '')
                username = config.get('username', '')
                password = config.get('password', '')
                prompt = config.get('prompt', '')
                command_group = config.get('command_group', 'default')
                
                writer.writerow([host, device_name, username, password, prompt, command_group])
        
        print(f"✅ デバイス設定をTXT形式に変換しました: {output_file}")
        return output_file
    
    def convert_yaml_to_groups_txt(self, yaml_file: str, output_file: str = None) -> str:
        """
        YAML形式のコマンドグループをTXT形式に変換
        
        Args:
            yaml_file: YAML形式のコマンドグループファイルパス
            output_file: 出力先TXTファイルパス（指定しない場合は自動生成）
        
        Returns:
            出力されたTXTファイルのパス
        """
        if not os.path.exists(yaml_file):
            raise FileNotFoundError(f"ファイルが見つかりません: {yaml_file}")
        
        # デフォルトの出力ファイル名
        if output_file is None:
            base_name = os.path.splitext(os.path.basename(yaml_file))[0]
            output_file = f"{base_name}_converted.txt"
        
        # YAMLファイルの読み込み
        with open(yaml_file, 'r', encoding='utf-8') as f:
            command_groups = yaml.safe_load(f)
        
        # TXTファイルの書き出し
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            # ヘッダー
            writer.writerow(['group_name', 'command'])
            
            # データ
            for group_name, config in command_groups.items():
                commands = config.get('commands', [])
                for command in commands:
                    writer.writerow([group_name, command])
        
        print(f"✅ コマンドグループをTXT形式に変換しました: {output_file}")
        return output_file
    
    def create_sample_files(self) -> None:
        """サンプルファイルを作成する"""
        # サンプルデバイスリスト (CSV形式)
        sample_devices_csv = """host,hostname,username,password,prompt,command_group
10.1.1.1,router1,admin,password,router1#,router_commands
10.1.1.2,switch1,admin,password,switch1#,switch_commands
10.1.1.3,firewall1,admin,password,firewall1#,firewall_commands
"""
        
        with open('sample_device_list.txt', 'w', encoding='utf-8', newline='') as f:
            f.write(sample_devices_csv)
        
        # サンプルコマンドグループ (CSV形式)
        sample_groups_csv = """group_name,command
router_commands,"show version"
router_commands,"show running-config"
router_commands,"show interface brief"
router_commands,"show ip route"

switch_commands,"show version"
switch_commands,"show interface status"
switch_commands,"show vlan brief"
switch_commands,"show mac address-table"

firewall_commands,"show version"
firewall_commands,"show running-config"
firewall_commands,"show access-lists"
firewall_commands,"show conn count"
"""
        
        with open('sample_group_name_command.txt', 'w', encoding='utf-8', newline='') as f:
            f.write(sample_groups_csv)
        
        print("✅ サンプルファイルを作成しました:")
        print("  - sample_device_list.txt")
        print("  - sample_group_name_command.txt")
        print("\nこれらのファイルを元にYAMLファイルを生成できます")


def main():
    """メイン関数"""
    import argparse
    
    converter = ConfigConverter()
    
    parser = argparse.ArgumentParser(description='設定ファイルのTXT形式とYAML形式を相互変換するツール')
    subparsers = parser.add_subparsers(dest='command', help='実行するコマンド')
    
    # TXT → YAML (デバイス)
    parser_txt_to_devices = subparsers.add_parser('txt-to-devices', help='device_list.txtをYAML形式に変換')
    parser_txt_to_devices.add_argument('input_file', help='入力TXTファイル (device_list.txt)')
    parser_txt_to_devices.add_argument('-o', '--output', help='出力YAMLファイル')
    
    # TXT → YAML (コマンドグループ)
    parser_txt_to_groups = subparsers.add_parser('txt-to-groups', help='group_name_command.txtをYAML形式に変換')
    parser_txt_to_groups.add_argument('input_file', help='入力TXTファイル (group_name_command.txt)')
    parser_txt_to_groups.add_argument('-o', '--output', help='出力YAMLファイル')
    
    # YAML → TXT (デバイス)
    parser_yaml_to_devices = subparsers.add_parser('yaml-to-devices', help='YAML形式のデバイス設定をTXT形式に変換')
    parser_yaml_to_devices.add_argument('input_file', help='入力YAMLファイル')
    parser_yaml_to_devices.add_argument('-o', '--output', help='出力TXTファイル')
    
    # YAML → TXT (コマンドグループ)
    parser_yaml_to_groups = subparsers.add_parser('yaml-to-groups', help='YAML形式のコマンドグループをTXT形式に変換')
    parser_yaml_to_groups.add_argument('input_file', help='入力YAMLファイル')
    parser_yaml_to_groups.add_argument('-o', '--output', help='出力TXTファイル')
    
    # サンプルファイル作成
    parser_samples = subparsers.add_parser('create-samples', help='サンプルファイルを作成')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == 'txt-to-devices':
            converter.convert_devices_txt_to_yaml(args.input_file, args.output)
        elif args.command == 'txt-to-groups':
            converter.convert_groups_txt_to_yaml(args.input_file, args.output)
        elif args.command == 'yaml-to-devices':
            converter.convert_yaml_to_devices_txt(args.input_file, args.output)
        elif args.command == 'yaml-to-groups':
            converter.convert_yaml_to_groups_txt(args.input_file, args.output)
        elif args.command == 'create-samples':
            converter.create_sample_files()
            
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
