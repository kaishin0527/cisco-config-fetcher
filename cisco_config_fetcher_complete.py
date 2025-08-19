


import yaml
import logging
import os
import time
import re
from datetime import datetime
from netmiko import ConnectHandler
from getpass import getpass

# ロギング設定
logging.basicConfig(
    filename='cisco_config_fetcher.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def load_config(file_path):
    """YAML設定ファイルを読み込む"""
    try:
        with open(file_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logging.error(f"設定ファイル {file_path} が見つかりません")
        return None
    except yaml.YAMLError as e:
        logging.error(f"設定ファイル {file_path} の解析エラー: {str(e)}")
        return None

def connect_to_device(device_config):
    """Netmikoを使用して装置に接続"""
    try:
        # パスワードが提供されていない場合はプロンプト表示
        if 'password' not in device_config:
            device_config['password'] = getpass(
                f"{device_config['host']} のログインパスワードを入力: "
            )
            
        # 特権モードパスワードが提供されていない場合はプロンプト表示
        if 'secret' not in device_config:
            device_config['secret'] = getpass(
                f"{device_config['host']} の特権モードパスワードを入力: "
            )
            
        # プロンプトパターンが指定されている場合は正規表現としてコンパイル
        if 'prompt_pattern' in device_config:
            device_config['secret'] = device_config.get('secret', '')
            
        connection = ConnectHandler(**device_config)
        
        # カスタムプロンプトパターンを設定
        if 'prompt_pattern' in device_config:
            prompt_pattern = re.compile(device_config['prompt_pattern'])
            connection.set_base_prompt(prompt_pattern=prompt_pattern)
            logging.info(f"カスタムプロンプトパターンを設定: {device_config['prompt_pattern']}")
        
        logging.info(f"{device_config['host']} に接続しました")
        return connection
    except Exception as e:
        logging.error(f"{device_config['host']} への接続失敗: {str(e)}")
        return None

def send_commands(connection, commands, prompt=None, config_mode=False):
    """装置にコマンドを送信し出力を返す"""
    outputs = []
    
    try:
        # コンフィグモードが必要な場合
        if config_mode:
            connection.enable()
            connection.config_mode()
            logging.info("コンフィグモードに入りました")
        
        for cmd in commands:
            try:
                output = connection.send_command(cmd)
                outputs.append(f"=== {cmd} ===\n{output}\n")
                logging.info(f"{connection.host} で '{cmd}' を実行")
            except Exception as e:
                logging.error(f"コマンド '{cmd}' の実行失敗: {str(e)}")
                outputs.append(f"!!! コマンド '{cmd}' の実行エラー: {str(e)}")
        
        # コンフィグモードから退出
        if config_mode:
            connection.exit_config_mode()
            logging.info("コンフィグモードを退出しました")
            
    except Exception as e:
        logging.error(f"コマンド実行中にエラーが発生: {str(e)}")
        outputs.append(f"!!! コマンド実行中にエラーが発生: {str(e)}")
    
    return "\n".join(outputs)

def main():
    # 基本設定ファイルの読み込み
    devices_config = load_config('devices.yaml')
    command_groups = load_config('command_groups.yaml')
    scenario_list = load_config('scenario_list.yaml')
    
    if not devices_config or not command_groups or not scenario_list:
        print("設定ファイルの読み込みエラー。ログを確認してください。")
        return

    # シナリオリスト内の各シナリオを実行
    for scenario_file in scenario_list['scenarios']:
        # 個別シナリオの読み込み
        scenario = load_config(scenario_file)
        if not scenario:
            print(f"シナリオファイル {scenario_file} の読み込みに失敗しました。スキップします。")
            continue
            
        print(f"\n=== シナリオ実行開始: {scenario['name']} ===")
        
        # 日時ディレクトリの作成 (西暦と時刻を含む)
        datetime_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_dir = f"{datetime_str}_{scenario['name']}"
        os.makedirs(base_dir, exist_ok=True)
        print(f"出力ディレクトリを作成: {base_dir}")
        
        # シナリオの各ステップを実行
        for step in scenario['steps']:
            seq = step['sequence']
            cmd_group = step['command_group']
            
            # 対象デバイスの決定: 特定デバイス指定 or デバイスグループ
            if 'devices' in step:
                # 特定デバイスのみを対象
                target_devices = {name: config for name, config in devices_config['devices'].items() 
                                 if name in step['devices']}
                print(f"\n=== ステップ {seq}: 特定デバイスに {cmd_group} コマンドを実行 ===")
            else:
                # デバイスグループを対象
                device_group = step['device_group']
                target_devices = {name: config for name, config in devices_config['devices'].items() 
                                 if config.get('group') == device_group}
                print(f"\n=== ステップ {seq}: {device_group} グループの装置に {cmd_group} コマンドを実行 ===")
            
            if not target_devices:
                print("警告: 対象デバイスが見つかりません")
                logging.warning("対象デバイスが見つかりません")
                continue
                
            # コマンドグループを取得
            cmd_group_config = command_groups['command_groups'].get(cmd_group, {})
            if not cmd_group_config:
                print(f"警告: {cmd_group} コマンドグループが定義されていません")
                logging.warning(f"{cmd_group} コマンドグループが定義されていません")
                continue
                
            commands = cmd_group_config.get('commands', [])
            config_mode = cmd_group_config.get('config_mode', False)
            
            if not commands:
                print(f"警告: {cmd_group} コマンドグループにコマンドが定義されていません")
                logging.warning(f"{cmd_group} コマンドグループにコマンドが定義されていません")
                continue
                
            # 各装置でコマンド実行
            for device_name, device_config in target_devices.items():
                # シーケンスサブディレクトリ作成
                sub_dir = os.path.join(base_dir, f"{seq}_{device_name}_{cmd_group}")
                os.makedirs(sub_dir, exist_ok=True)
                
                print(f"\n処理中: {device_name} ({device_config['host']})")
                
                # 装置に接続
                conn = connect_to_device(device_config)
                if not conn:
                    continue
                    
                # コマンド実行 (コンフィグモードフラグを渡す)
                output = send_commands(
                    conn, 
                    commands, 
                    config_mode=config_mode
                )
                
                # 出力をファイルに保存
                filename = os.path.join(sub_dir, f"{device_name}_output.txt")
                with open(filename, 'w') as f:
                    f.write(output)
                print(f"出力を保存: {filename}")
                
                conn.disconnect()
            
            # 待機処理
            if 'wait_after' in step:
                wait_sec = step['wait_after']
                print(f"\n{wait_sec}秒待機中...")
                time.sleep(wait_sec)
                
            # ユーザー入力待ち
            if step.get('wait_for_user'):
                input("\nユーザー入力待ち: 続行するにはEnterキーを押してください...")
        
        print(f"\nシナリオ {scenario['name']} が完了しました！")
    
    print("\n全てのシナリオが完了しました！")

if __name__ == "__main__":
    main()


