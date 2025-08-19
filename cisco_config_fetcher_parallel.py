



import yaml
import logging
import os
import time
import re
import concurrent.futures
from datetime import datetime
from netmiko import ConnectHandler
from getpass import getpass

# 設定管理モジュールのインポート
from config_manager import config_manager, get_devices, get_command_groups, get_scenarios

# ロギング設定
logging.basicConfig(
    filename='cisco_config_fetcher.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def load_config(file_path):
    """YAML設定ファイルを読み込む（互換性のため）"""
    try:
        with open(file_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logging.error(f"設定ファイル {file_path} が見つかりません")
        return None
    except yaml.YAMLError as e:
        logging.error(f"設定ファイル {file_path} の解析エラー: {str(e)}")
        return None

def get_device_config(device_name):
    """デバイス設定を取得（config_manager経由）"""
    return config_manager.get_device(device_name)

def get_command_group(group_name):
    """コマンドグループを取得（config_manager経由）"""
    return config_manager.get_command_group(group_name)

def get_scenario(scenario_name):
    """シナリオを取得（config_manager経由）"""
    return config_manager.get_scenario(scenario_name)

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

def execute_task(device_name, device_config, cmd_group_config, base_dir, seq, cmd_group_name):
    """個別タスクを実行するヘルパー関数"""
    # シーケンスサブディレクトリ作成
    sub_dir = os.path.join(base_dir, f"{seq}_{device_name}_{cmd_group_name}")
    os.makedirs(sub_dir, exist_ok=True)
    
    print(f"\n処理中: {device_name} ({device_config['host']})")
    
    # 装置に接続
    conn = connect_to_device(device_config)
    if not conn:
        return None
        
    # コマンド実行 (コンフィグモードフラグを渡す)
    commands = cmd_group_config.get('commands', [])
    config_mode = cmd_group_config.get('config_mode', False)
    output = send_commands(conn, commands, config_mode=config_mode)
    
    # 出力をファイルに保存
    filename = os.path.join(sub_dir, f"{device_name}_output.txt")
    with open(filename, 'w') as f:
        f.write(output)
    print(f"出力を保存: {filename}")
    
    conn.disconnect()
    return filename

def main():
    # 基本設定ファイルの読み込み
    devices_config = load_config('devices_updated.yaml')
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
            print(f"\n=== ステップ {seq} 開始 ===")
            
            # タスクリストを取得 (旧形式との互換性維持)
            tasks = step.get('tasks', [{
                'device_group': step.get('device_group'),
                'devices': step.get('devices'),
                'command_group': step.get('command_group')
            }])
            
            # スレッドプールを作成
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = []
                
                # 各タスクをスレッドで実行
                for task in tasks:
                    if not task.get('command_group'):
                        continue
                        
                    cmd_group_name = task['command_group']
                    cmd_group_config = command_groups['command_groups'].get(cmd_group_name, {})
                    
                    if not cmd_group_config:
                        print(f"警告: {cmd_group_name} コマンドグループが定義されていません")
                        continue
                        
                    # 対象デバイスの決定
                    if 'devices' in task:
                        # 特定デバイスのみを対象
                        target_devices = {name: config for name, config in devices_config['devices'].items() 
                                         if name in task['devices']}
                    elif 'device_group' in task:
                        # デバイスグループを対象
                        device_group = task['device_group']
                        target_devices = {name: config for name, config in devices_config['devices'].items() 
                                         if config.get('group') == device_group}
                    else:
                        continue
                        
                    if not target_devices:
                        print(f"警告: タスク {cmd_group_name} の対象デバイスが見つかりません")
                        continue
                        
                    # 各デバイスでタスクを実行
                    for device_name, device_config in target_devices.items():
                        future = executor.submit(
                            execute_task,
                            device_name,
                            device_config,
                            cmd_group_config,
                            base_dir,
                            seq,
                            cmd_group_name
                        )
                        futures.append(future)
                
                # 全タスクの完了を待機
                for future in concurrent.futures.as_completed(futures):
                    try:
                        future.result()
                    except Exception as e:
                        logging.error(f"タスク実行中にエラーが発生: {str(e)}")
            
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



