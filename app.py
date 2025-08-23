
from flask import Flask, render_template, request, redirect, url_for, send_file, flash
import yaml
import os
import subprocess
import threading
import json
from datetime import datetime
import io

# 設定管理モジュールのインポート
from config_manager import config_manager, get_devices, get_command_groups, get_scenarios

# ネットワーク実行モジュールのインポート
from network_executor import NetworkDeviceExecutor, execute_scenario_on_device, test_device_connection

# ログ管理モジュールのインポート
from logger_manager import get_log_manager

def validate_all_configs():
    """すべての設定ファイルをバリデーション"""
    results = {
        'devices': True,
        'command_groups': True,
        'scenarios': True
    }
    
    # デバイス設定のバリデーション
    devices = get_devices()
    for device_name, device_config in devices.items():
        required_fields = ['host', 'device_type', 'username']
        for field in required_fields:
            if field not in device_config:
                results['devices'] = False
                break
    
    # コマンドグループ設定のバリデーション
    command_groups = get_command_groups()
    for group_name, group_config in command_groups.items():
        if 'commands' not in group_config:
            results['command_groups'] = False
            break
    
    # シナリオ設定のバリデーション
    scenarios = get_scenarios()
    for scenario_name, scenario_config in scenarios.items():
        if 'devices' not in scenario_config or 'commands' not in scenario_config:
            results['scenarios'] = False
            break
    
    return results

def execute_scenario_on_device(device_name: str, scenario_name: str):
    """
    デバイスでシナリオを実行
    
    Args:
        device_name: デバイス名
        scenario_name: シナリオ名
        
    Returns:
        実行結果
    """
    devices = get_devices()
    scenarios = get_scenarios()
    command_groups = get_command_groups()
    
    if device_name not in devices:
        return {'success': False, 'error': f'Device {device_name} not found'}
    
    if scenario_name not in scenarios:
        return {'success': False, 'error': f'Scenario {scenario_name} not found'}
    
    device_config = devices[device_name]
    scenario_config = scenarios[scenario_name]
    
    executor = NetworkDeviceExecutor(device_config)
    return executor.execute_scenario(scenario_config, command_groups)

def get_config_summary():
    """設定のサマリーを取得"""
    devices = get_devices()
    command_groups = get_command_groups()
    scenarios = get_scenarios()
    
    return {
        'device_count': len(devices),
        'command_group_count': len(command_groups),
        'scenario_count': len(scenarios),
        'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.secret_key = 'supersecretkey'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 設定ファイルパス（互換性のため）
DEVICES_FILE = 'devices_updated.yaml'
COMMAND_GROUPS_FILE = 'command_groups.yaml'
SCENARIO_LIST_FILE = 'scenario_list.yaml'

def create_sample_data():
    """サンプルデータを作成"""
    # サンプルデバイス
    sample_devices = {
        'router-01': {
            'host': '192.168.1.1',
            'device_type': 'cisco_ios',
            'username': 'admin',
            'password': 'password',
            'secret': 'enable_password',
            'connection_type': 'ssh',
            'wait_string': '#',
            'enable_password': 'enable_password',
            'group': 'routers',
            'description': 'Core Router 01'
        },
        'switch-01': {
            'host': '192.168.1.2',
            'device_type': 'cisco_ios',
            'username': 'admin',
            'password': 'password',
            'secret': 'enable_password',
            'connection_type': 'ssh',
            'wait_string': '#',
            'enable_password': 'enable_password',
            'group': 'switches',
            'description': 'Core Switch 01'
        },
        'firewall-01': {
            'host': '192.168.1.3',
            'device_type': 'cisco_asa',
            'username': 'admin',
            'password': 'password',
            'secret': '',
            'connection_type': 'ssh',
            'wait_string': '#',
            'enable_password': '',
            'group': 'firewalls',
            'description': 'Firewall 01'
        }
    }
    
    # サンプルコマンドグループ
    sample_command_groups = {
        'basic-config': {
            'commands': [
                'show version',
                'show running-config',
                'show interface status',
                'show ip interface brief'
            ],
            'description': '基本設定確認コマンド',
            'group': 'common'
        },
        'interface-config': {
            'commands': [
                'configure terminal',
                'interface GigabitEthernet0/1',
                'description Connected to Server',
                'switchport mode access',
                'switchport access vlan 10',
                'no shutdown',
                'exit',
                'write memory'
            ],
            'description': 'インターフェース設定コマンド',
            'group': 'interfaces'
        },
        'security-config': {
            'commands': [
                'configure terminal',
                'enable secret secure_password',
                'line vty 0 4',
                'password telnet_password',
                'login',
                'exit',
                'access-list 10 permit 192.168.1.0 0.0.0.255',
                'exit',
                'write memory'
            ],
            'description': 'セキュリティ設定コマンド',
            'group': 'security'
        },
        'troubleshooting': {
            'commands': [
                'ping 8.8.8.8',
                'traceroute 8.8.8.8',
                'show log',
                'show arp',
                'show mac address-table',
                'show ip route',
                'show cdp neighbor detail'
            ],
            'description': 'トラブルシューティングコマンド',
            'group': 'troubleshooting'
        }
    }
    
    # サンプルシナリオ
    sample_scenarios = {
        'network-health-check': {
            'devices': ['router-01', 'switch-01'],
            'commands': ['basic-config'],
            'description': 'ネットワークヘルスチェック',
            'group': 'monitoring',
            'delay': 2,
            'timeout': 30,
            'save_config': False
        },
        'interface-configuration': {
            'devices': ['switch-01'],
            'commands': ['interface-config'],
            'description': 'インターフェース設定',
            'group': 'configuration',
            'delay': 3,
            'timeout': 60,
            'save_config': True
        },
        'security-audit': {
            'devices': ['router-01', 'switch-01', 'firewall-01'],
            'commands': ['security-config', 'basic-config'],
            'description': 'セキュリティ監査',
            'group': 'security',
            'delay': 5,
            'timeout': 120,
            'save_config': True
        },
        'troubleshooting-session': {
            'devices': ['router-01', 'switch-01'],
            'commands': ['troubleshooting'],
            'description': 'トラブルシューティングセッション',
            'group': 'troubleshooting',
            'delay': 1,
            'timeout': 45,
            'save_config': False
        }
    }
    
    # サンプルデータを保存
    config_manager.save_config('devices', sample_devices)
    config_manager.save_config('command_groups', sample_command_groups)
    config_manager.save_config('scenarios', sample_scenarios)
    
    print("サンプルデータを作成しました")

# アプリケーション初期化時にサンプルデータを作成
create_sample_data()

def load_yaml(file_path):
    """YAMLファイルを読み込む（互換性のため）"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        return {}
    except yaml.YAMLError as e:
        print(f"YAMLファイルの読み込みエラー: {e}")
        return {}

# デバイス管理
@app.route('/devices')
def devices():
    """デバイス管理ページ"""
    devices = get_devices()
    return render_template('devices.html', devices=devices)

@app.route('/add_device', methods=['GET', 'POST'])
def add_device():
    """デバイスを追加"""
    if request.method == 'GET':
        # フォームを表示
        return render_template('add_device.html')
    
    devices = get_devices()
    device_name = request.form['device_name']
    
    if device_name in devices:
        flash('デバイス名が既に存在します', 'danger')
    else:
        devices[device_name] = {
            'host': request.form['host'],
            'device_type': request.form['device_type'],
            'username': request.form['username'],
            'password': request.form['password'],
            'secret': request.form.get('secret', ''),
            'connection_type': request.form.get('connection_type', 'ssh'),
            'wait_string': request.form.get('wait_string', '#'),
            'enable_password': request.form.get('enable_password', ''),
            'group': request.form.get('group', 'default')
        }
        config_manager.save_config('devices', devices)
        flash('デバイスを追加しました', 'success')
    
    return redirect(url_for('devices'))

@app.route('/edit_device/<device_name>', methods=['GET', 'POST'])
def edit_device(device_name):
    """デバイスを編集"""
    devices = get_devices()
    
    if request.method == 'POST':
        if device_name in devices:
            devices[device_name] = {
                'host': request.form['host'],
                'device_type': request.form['device_type'],
                'username': request.form['username'],
                'password': request.form['password'],
                'secret': request.form.get('secret', ''),
                'connection_type': request.form.get('connection_type', 'ssh'),
                'wait_string': request.form.get('wait_string', '#'),
                'enable_password': request.form.get('enable_password', ''),
                'group': request.form.get('group', 'default')
            }
            config_manager.save_config('devices', devices)
            flash('デバイスを更新しました', 'success')
        else:
            flash('デバイスが見つかりません', 'danger')
        return redirect(url_for('devices'))
    else:
        device = devices.get(device_name)
        if device:
            return render_template('edit_device.html', device=device, device_name=device_name)
        else:
            flash('デバイスが見つかりません', 'danger')
            return redirect(url_for('devices'))

@app.route('/delete_device/<device_name>')
def delete_device(device_name):
    """デバイスを削除"""
    devices = get_devices()
    if device_name in devices:
        del devices[device_name]
        config_manager.save_config('devices', devices)
        flash('デバイスを削除しました', 'success')
    else:
        flash('デバイスが見つかりません', 'danger')
    return redirect(url_for('devices'))

# コマンドグループ管理
@app.route('/command_groups')
def command_groups():
    """コマンドグループ管理ページ"""
    command_groups = get_command_groups()
    return render_template('command_groups.html', command_groups=command_groups)

@app.route('/add_command_group', methods=['GET', 'POST'])
def add_command_group():
    """コマンドグループを追加"""
    if request.method == 'GET':
        # フォームを表示
        return render_template('add_command_group.html')
    
    command_groups = get_command_groups()
    group_name = request.form['group_name']
    
    if group_name in command_groups:
        flash('コマンドグループ名が既に存在します', 'danger')
    else:
        command_groups[group_name] = {
            'commands': request.form['commands'].split('\n'),
            'description': request.form.get('description', ''),
            'group': request.form.get('group', 'default')
        }
        config_manager.save_config('command_groups', command_groups)
        flash('コマンドグループを追加しました', 'success')
    
    return redirect(url_for('command_groups'))

@app.route('/edit_command_group/<group_name>', methods=['GET', 'POST'])
def edit_command_group(group_name):
    """コマンドグループを編集"""
    command_groups = get_command_groups()
    
    if request.method == 'POST':
        if group_name in command_groups:
            command_groups[group_name] = {
                'commands': request.form['commands'].split('\n'),
                'description': request.form.get('description', ''),
                'group': request.form.get('group', 'default')
            }
            config_manager.save_config('command_groups', command_groups)
            flash('コマンドグループを更新しました', 'success')
        else:
            flash('コマンドグループが見つかりません', 'danger')
        return redirect(url_for('command_groups'))
    else:
        group = command_groups.get(group_name)
        if group:
            return render_template('edit_command_group.html', group=group, group_name=group_name)
        else:
            flash('コマンドグループが見つかりません', 'danger')
            return redirect(url_for('command_groups'))

@app.route('/delete_command_group/<group_name>')
def delete_command_group(group_name):
    """コマンドグループを削除"""
    command_groups = get_command_groups()
    if group_name in command_groups:
        del command_groups[group_name]
        config_manager.save_config('command_groups', command_groups)
        flash('コマンドグループを削除しました', 'success')
    else:
        flash('コマンドグループが見つかりません', 'danger')
    return redirect(url_for('command_groups'))

# シナリオ管理
@app.route('/scenarios')
def scenarios():
    """シナリオ管理ページ"""
    scenarios = get_scenarios()
    return render_template('scenarios.html', scenarios=scenarios)

@app.route('/add_scenario', methods=['GET', 'POST'])
def add_scenario():
    """シナリオを追加"""
    if request.method == 'GET':
        # フォームを表示
        return render_template('add_scenario.html')
    
    scenarios = get_scenarios()
    scenario_name = request.form['scenario_name']
    
    if scenario_name in scenarios:
        flash('シナリオ名が既に存在します', 'danger')
    else:
        scenarios[scenario_name] = {
            'devices': request.form['devices'].split(','),
            'commands': request.form['commands'].split(','),
            'description': request.form.get('description', ''),
            'group': request.form.get('group', 'default')
        }
        config_manager.save_config('scenarios', scenarios)
        flash('シナリオを追加しました', 'success')
    
    return redirect(url_for('scenarios'))

@app.route('/edit_scenario/<scenario_name>', methods=['GET', 'POST'])
def edit_scenario(scenario_name):
    """シナリオを編集"""
    scenarios = get_scenarios()
    devices = get_devices()
    
    # デバイスグループの取得
    device_groups = list(set(device['group'] for device in devices.values() if 'group' in device))
    
    if request.method == 'POST':
        if scenario_name in scenarios:
            # デバイス選択の処理
            device_selection = request.form.get('device_selection', 'individual')
            if device_selection == 'group':
                # グループ選択の場合
                selected_groups = request.form.getlist('device_groups')
                # グループに属するデバイスを取得
                selected_devices = []
                for group in selected_groups:
                    for device_name, device in devices.items():
                        if device.get('group') == group:
                            selected_devices.append(device_name)
                devices_list = selected_devices
            else:
                # 個別デバイス選択の場合
                selected_devices = request.form.getlist('individual_devices')
                devices_list = selected_devices
            
            scenarios[scenario_name] = {
                'devices': devices_list,
                'commands': request.form['commands'].split(','),
                'description': request.form.get('description', ''),
                'group': request.form.get('group', 'default')
            }
            config_manager.save_config('scenarios', scenarios)
            flash('シナリオを更新しました', 'success')
        else:
            flash('シナリオが見つかりません', 'danger')
        return redirect(url_for('scenarios'))
    else:
        scenario = scenarios.get(scenario_name)
        if scenario:
            return render_template('edit_scenario.html', scenario=scenario, scenario_name=scenario_name, devices=devices, device_groups=device_groups)
        else:
            flash('シナリオが見つかりません', 'danger')
            return redirect(url_for('scenarios'))

@app.route('/delete_scenario/<scenario_name>')
def delete_scenario(scenario_name):
    """シナリオを削除"""
    scenarios = get_scenarios()
    if scenario_name in scenarios:
        del scenarios[scenario_name]
        config_manager.save_config('scenarios', scenarios)
        flash('シナリオを削除しました', 'success')
    else:
        flash('シナリオが見つかりません', 'danger')
    return redirect(url_for('scenarios'))

# シナリオ一覧
@app.route('/scenario_lists')
def scenario_lists():
    """シナリオ一覧ページ"""
    scenarios = get_scenarios()
    
    # 保存されたシナリオリストを読み込む
    scenario_lists_data = {}
    try:
        if os.path.exists('scenario_lists'):
            for filename in os.listdir('scenario_lists'):
                if filename.endswith('.yaml'):
                    list_name = filename[:-5]  # .yamlを除く
                    with open(f'scenario_lists/{filename}', 'r', encoding='utf-8') as f:
                        list_data = yaml.safe_load(f)
                        if list_data and 'scenarios' in list_data:
                            scenario_lists_data[list_name] = list_data['scenarios']
    except Exception as e:
        print(f"シナリオリストの読み込みエラー: {e}")
        scenario_lists_data = {}
    
    return render_template('scenario_lists.html', scenarios=scenarios, scenario_lists=scenario_lists_data)

@app.route('/edit_scenario_list/<list_name>', methods=['GET', 'POST'])
def edit_scenario_list(list_name):
    """シナリオリストを編集"""
    scenarios = get_scenarios()
    
    # scenario_listsディレクトリが存在しない場合は作成
    os.makedirs('scenario_lists', exist_ok=True)
    
    if request.method == 'POST':
        # シナリオリストの更新処理
        selected_scenarios = request.form.getlist('scenarios')
        
        # シナリオリストを保存（ここではシナリオ名を保存）
        scenario_list_data = {
            'name': list_name,
            'scenarios': selected_scenarios,
            'description': request.form.get('description', ''),
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        try:
            # シナリオリストを保存（ファイルやデータベースに保存）
            with open(f'scenario_lists/{list_name}.yaml', 'w', encoding='utf-8') as f:
                yaml.dump(scenario_list_data, f, default_flow_style=False, allow_unicode=True)
            
            flash('シナリオリストを更新しました', 'success')
            return redirect(url_for('scenario_lists'))
        except Exception as e:
            flash(f'シナリオリストの保存に失敗しました: {str(e)}', 'danger')
            return redirect(url_for('scenario_lists'))
    else:
        # 編集フォームを表示
        # ここでは既存のシナリオをすべて表示
        return render_template('edit_scenario_list.html', scenarios=scenarios, list_name=list_name)

# 実行管理
@app.route('/execute')
def execute():
    """実行管理ページ"""
    devices = get_devices()
    command_groups = get_command_groups()
    scenarios = get_scenarios()
    
    # シナリオリストのデータを読み込む
    scenario_lists_data = {}
    try:
        if os.path.exists('scenario_lists'):
            for filename in os.listdir('scenario_lists'):
                if filename.endswith('.yaml'):
                    list_name = filename[:-5]  # .yamlを除く
                    with open(f'scenario_lists/{filename}', 'r', encoding='utf-8') as f:
                        list_data = yaml.safe_load(f)
                        if list_data and 'scenarios' in list_data:
                            scenario_lists_data[list_name] = list_data['scenarios']
    except Exception as e:
        print(f"シナリオリストの読み込みエラー: {e}")
        scenario_lists_data = {}
    
    return render_template('execute.html', devices=devices, command_groups=command_groups, scenarios=scenarios, scenario_lists=scenario_lists_data)

def _execute_scenario_logic(scenario_name):
    """シナリオ実行のロジック（Flaskルートではない）"""
    scenarios = get_scenarios()
    
    if scenario_name not in scenarios:
        flash('シナリオが見つかりません', 'danger')
        return redirect(url_for('execute'))
    
    scenario = scenarios[scenario_name]
    
    # 非同期で実行
    def execute_scenario():
        try:
            # デバイスとコマンドグループを取得
            devices = get_devices()
            command_groups = get_command_groups()
            
            # 実行結果を保存するディレクトリを作成
            result_dir = os.path.join('results', datetime.now().strftime('%Y%m%d'))
            os.makedirs(result_dir, exist_ok=True)
            
            # 各デバイスでシナリオを実行
            scenario_results = []
            total_devices = len(scenario['devices'])
            successful_devices = 0
            failed_devices = 0
            
            for device_name in scenario['devices']:
                if device_name in devices:
                    device_config = devices[device_name]
                    
                    # シナリオを実行
                    device_result = execute_scenario_on_device(
                        device_config, 
                        command_groups, 
                        scenario
                    )
                    
                    scenario_results.append(device_result)
                    
                    if device_result['success']:
                        successful_devices += 1
                    else:
                        failed_devices += 1
                else:
                    # デバイスが存在しない場合
                    scenario_results.append({
                        'device_name': device_name,
                        'device_host': 'unknown',
                        'success': False,
                        'start_time': datetime.now().isoformat(),
                        'end_time': datetime.now().isoformat(),
                        'total_commands': 0,
                        'successful_commands': 0,
                        'failed_commands': 0,
                        'error_message': f'Device {device_name} not found'
                    })
                    failed_devices += 1
            
            # 全体の結果を作成
            overall_success = failed_devices == 0
            result = {
                'scenario_name': scenario_name,
                'devices': scenario['devices'],
                'commands': scenario['commands'],
                'status': 'success' if overall_success else 'partial_success',
                'total_devices': total_devices,
                'successful_devices': successful_devices,
                'failed_devices': failed_devices,
                'device_results': scenario_results,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'execution_summary': f'{successful_devices}/{total_devices} デバイスで成功'
            }
            
            # 結果を保存
            result_file = os.path.join(result_dir, f'{scenario_name}_{datetime.now().strftime("%H%M%S")}.yaml')
            with open(result_file, 'w', encoding='utf-8') as f:
                yaml.dump(result, f, default_flow_style=False, allow_unicode=True)
                
            # 実行ログを保存
            log_file = os.path.join(result_dir, f'{scenario_name}_{datetime.now().strftime("%H%M%S")}.log')
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(f"シナリオ実行結果: {scenario_name}\n")
                f.write(f"実行時刻: {result['timestamp']}\n")
                f.write(f"全体の状態: {result['status']}\n")
                f.write(f"デバイス結果: {successful_devices}/{total_devices} 成功\n")
                f.write("=" * 50 + "\n\n")
                
                for device_result in scenario_results:
                    f.write(f"デバイス: {device_result['device_name']} ({device_result['device_host']})\n")
                    f.write(f"状態: {'成功' if device_result['success'] else '失敗'}\n")
                    f.write(f"実行コマンド数: {device_result['total_commands']}\n")
                    f.write(f"成功コマンド数: {device_result['successful_commands']}\n")
                    f.write(f"失敗コマンド数: {device_result['failed_commands']}\n")
                    if device_result['error_message']:
                        f.write(f"エラーメッセージ: {device_result['error_message']}\n")
                    f.write("-" * 30 + "\n")
                    
        except Exception as e:
            print(f"シナリオ実行エラー: {e}")
            # エラーログを保存
            error_dir = os.path.join('results', 'errors')
            os.makedirs(error_dir, exist_ok=True)
            error_file = os.path.join(error_dir, f'{scenario_name}_{datetime.now().strftime("%H%M%S")}.log')
            with open(error_file, 'w', encoding='utf-8') as f:
                f.write(f"シナリオ実行エラー: {scenario_name}\n")
                f.write(f"エラー時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"エラー内容: {str(e)}\n")
    
    # 別スレッドで実行
    thread = threading.Thread(target=execute_scenario)
    thread.daemon = True
    thread.start()
    
    flash(f'シナリオ "{scenario_name}" を実行中です...', 'info')
    return redirect(url_for('execute'))

@app.route('/run_scenario', methods=['POST'])
def run_scenario():
    """シナリオを実行（Flaskルート）"""
    scenario_name = request.form['scenario_name']
    return _execute_scenario_logic(scenario_name)

# 追加のルート
@app.route('/execute_scenario/<scenario_name>', methods=['GET'])
def execute_scenario(scenario_name):
    """シナリオを実行（GET用）"""
    return _execute_scenario_logic(scenario_name)

@app.route('/execute_scenario_post', methods=['GET', 'POST'])
def execute_scenario_post():
    """シナリオを実行（GET/POST用）"""
    scenario_name = request.args.get('scenario_name') or request.form.get('scenario_name')
    
    if not scenario_name:
        flash('シナリオ名が指定されていません', 'danger')
        return redirect(url_for('execute'))
    
    # シナリオリストのデータを読み込む
    try:
        if os.path.exists(f'scenario_lists/{scenario_name}.yaml'):
            with open(f'scenario_lists/{scenario_name}.yaml', 'r', encoding='utf-8') as f:
                scenario_list_data = yaml.safe_load(f)
                if scenario_list_data and 'scenarios' in scenario_list_data:
                    # シナリオリスト内のすべてのシナリオを実行
                    scenarios_to_run = scenario_list_data['scenarios']
                    
                    # 非同期で実行
                    def execute_scenario_list():
                        try:
                            # 並列でシナリオを実行
                            from concurrent.futures import ThreadPoolExecutor, as_completed
                            
                            # 結果を保存するディレクトリを作成
                            result_dir = os.path.join('results', datetime.now().strftime('%Y%m%d'))
                            os.makedirs(result_dir, exist_ok=True)
                            
                            # 各シナリオの実行結果を保存
                            list_results = []
                            total_scenarios = len(scenarios_to_run)
                            successful_scenarios = 0
                            failed_scenarios = 0
                            
                            # ThreadPoolExecutorで並列実行
                            with ThreadPoolExecutor(max_workers=min(5, total_scenarios)) as executor:
                                # 各シナリオの実行をサミット
                                future_to_scenario = {}
                                for scenario_name in scenarios_to_run:
                                    future = executor.submit(_execute_single_scenario_for_list, scenario_name)
                                    future_to_scenario[future] = scenario_name
                                
                                # 実行結果を収集
                                for future in as_completed(future_to_scenario):
                                    scenario_name = future_to_scenario[future]
                                    try:
                                        scenario_result = future.result()
                                        list_results.append(scenario_result)
                                        
                                        if scenario_result['success']:
                                            successful_scenarios += 1
                                        else:
                                            failed_scenarios += 1
                                            
                                    except Exception as e:
                                        # シナリオ実行が失敗した場合
                                        list_results.append({
                                            'scenario_name': scenario_name,
                                            'success': False,
                                            'error_message': str(e),
                                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                        })
                                        failed_scenarios += 1
                            
                            # シナリオリスト全体の結果を作成
                            overall_success = failed_scenarios == 0
                            list_result = {
                                'scenario_list_name': scenario_name,
                                'scenarios': scenarios_to_run,
                                'status': 'success' if overall_success else 'partial_success',
                                'total_scenarios': total_scenarios,
                                'successful_scenarios': successful_scenarios,
                                'failed_scenarios': failed_scenarios,
                                'scenario_results': list_results,
                                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                'execution_summary': f'{successful_scenarios}/{total_scenarios} シナリオで成功'
                            }
                            
                            # 結果を保存
                            result_file = os.path.join(result_dir, f'scenario_list_{scenario_name}_{datetime.now().strftime("%H%M%S")}.yaml')
                            with open(result_file, 'w', encoding='utf-8') as f:
                                yaml.dump(list_result, f, default_flow_style=False, allow_unicode=True)
                            
                            # 実行ログを保存
                            log_file = os.path.join(result_dir, f'scenario_list_{scenario_name}_{datetime.now().strftime("%H%M%S")}.log')
                            with open(log_file, 'w', encoding='utf-8') as f:
                                f.write(f"シナリオリスト実行結果: {scenario_name}\n")
                                f.write(f"実行時刻: {list_result['timestamp']}\n")
                                f.write(f"全体の状態: {list_result['status']}\n")
                                f.write(f"シナリオ結果: {successful_scenarios}/{total_scenarios} 成功\n")
                                f.write("=" * 50 + "\n\n")
                                
                                for scenario_result in list_results:
                                    f.write(f"シナリオ: {scenario_result['scenario_name']}\n")
                                    f.write(f"状態: {'成功' if scenario_result['success'] else '失敗'}\n")
                                    if scenario_result.get('execution_summary'):
                                        f.write(f"実行サマリー: {scenario_result['execution_summary']}\n")
                                    if scenario_result.get('error_message'):
                                        f.write(f"エラーメッセージ: {scenario_result['error_message']}\n")
                                    f.write("-" * 30 + "\n")
                                    
                        except Exception as e:
                            print(f"シナリオリスト実行エラー: {e}")
                            # エラーログを保存
                            error_dir = os.path.join('results', 'errors')
                            os.makedirs(error_dir, exist_ok=True)
                            error_file = os.path.join(error_dir, f'scenario_list_{scenario_name}_{datetime.now().strftime("%H%M%S")}.log')
                            with open(error_file, 'w', encoding='utf-8') as f:
                                f.write(f"シナリオリスト実行エラー: {scenario_name}\n")
                                f.write(f"エラー時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                                f.write(f"エラー内容: {str(e)}\n")
                    
                    thread = threading.Thread(target=execute_scenario_list)
                    thread.daemon = True
                    thread.start()
                    
                    flash(f'シナリオリスト "{scenario_name}" 内の {len(scenarios_to_run)} 件のシナリオを並列実行中です...', 'info')
                    return redirect(url_for('scenario_lists'))
    
    except Exception as e:
        print(f"シナリオリスト読み込みエラー: {e}")
    
    # シナリオリストが存在しない場合は通常のシナリオ実行
    return _execute_scenario_logic(scenario_name)

def _execute_single_scenario_for_list(scenario_name):
    """シナリオリスト用の単一シナリオ実行（並列実行用）"""
    scenarios = get_scenarios()
    
    if scenario_name not in scenarios:
        return {
            'scenario_name': scenario_name,
            'success': False,
            'error_message': f'Scenario {scenario_name} not found',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    scenario = scenarios[scenario_name]
    
    try:
        # デバイスとコマンドグループを取得
        devices = get_devices()
        command_groups = get_command_groups()
        
        # 実行結果を保存するディレクトリを作成
        result_dir = os.path.join('results', datetime.now().strftime('%Y%m%d'))
        os.makedirs(result_dir, exist_ok=True)
        
        # 各デバイスでシナリオを実行
        scenario_results = []
        total_devices = len(scenario['devices'])
        successful_devices = 0
        failed_devices = 0
        
        for device_name in scenario['devices']:
            if device_name in devices:
                device_config = devices[device_name]
                
                # シナリオを実行
                device_result = execute_scenario_on_device(
                    device_config, 
                    command_groups, 
                    scenario
                )
                
                scenario_results.append(device_result)
                
                if device_result['success']:
                    successful_devices += 1
                else:
                    failed_devices += 1
            else:
                # デバイスが存在しない場合
                scenario_results.append({
                    'device_name': device_name,
                    'device_host': 'unknown',
                    'success': False,
                    'start_time': datetime.now().isoformat(),
                    'end_time': datetime.now().isoformat(),
                    'total_commands': 0,
                    'successful_commands': 0,
                    'failed_commands': 0,
                    'error_message': f'Device {device_name} not found'
                })
                failed_devices += 1
        
        # 全体の結果を作成
        overall_success = failed_devices == 0
        result = {
            'scenario_name': scenario_name,
            'devices': scenario['devices'],
            'commands': scenario['commands'],
            'success': overall_success,
            'status': 'success' if overall_success else 'partial_success',
            'total_devices': total_devices,
            'successful_devices': successful_devices,
            'failed_devices': failed_devices,
            'device_results': scenario_results,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'execution_summary': f'{successful_devices}/{total_devices} デバイスで成功'
        }
        
        # 結果を保存
        result_file = os.path.join(result_dir, f'{scenario_name}_{datetime.now().strftime("%H%M%S")}.yaml')
        with open(result_file, 'w', encoding='utf-8') as f:
            yaml.dump(result, f, default_flow_style=False, allow_unicode=True)
            
        return result
        
    except Exception as e:
        return {
            'scenario_name': scenario_name,
            'success': False,
            'error_message': str(e),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

@app.route('/execute_scenario_list', methods=['GET', 'POST'])
def execute_scenario_list():
    """シナリオ一覧を実行"""
    if request.method == 'POST':
        scenario_list_name = request.form.get('scenario_list')
        if scenario_list_name:
            return redirect(url_for('execute_scenario_post', scenario_name=scenario_list_name))
    
    scenarios = get_scenarios()
    return render_template('scenario_lists.html', scenarios=scenarios)

@app.route('/test_device_connection', methods=['POST'])
def test_device_connection():
    """デバイス接続テスト"""
    device_name = request.form.get('device_name')
    
    if not device_name:
        return jsonify({'success': False, 'message': 'デバイス名が指定されていません'})
    
    try:
        devices = get_devices()
        
        if device_name not in devices:
            return jsonify({'success': False, 'message': f'デバイス "{device_name}" が見つかりません'})
        
        device_config = devices[device_name]
        
        # 接続テストを実行
        test_result = test_device_connection(device_config)
        
        if test_result['success']:
            message = f'デバイス "{device_name}" に接続成功（接続時間: {test_result["connection_time"]:.2f}秒）'
        else:
            message = f'デバイス "{device_name}" に接続失敗: {test_result["message"]}'
        
        return jsonify({
            'success': test_result['success'],
            'message': message,
            'connection_time': test_result.get('connection_time', 0)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'テスト実行エラー: {str(e)}'})

# ダウンロード機能
@app.route('/download/<path:filename>')
def download_file(filename):
    return send_file(filename, as_attachment=True)

# 実行結果表示機能
@app.route('/results')
def show_results():
    """実行結果一覧を表示"""
    try:
        results_dir = 'results'
        if not os.path.exists(results_dir):
            return render_template('results.html', results=[], error_message='実行結果がありません')
        
        # 日付ごとの結果を収集
        results_by_date = {}
        
        for date_dir in os.listdir(results_dir):
            date_path = os.path.join(results_dir, date_dir)
            if os.path.isdir(date_path):
                results_by_date[date_dir] = []
                
                for result_file in os.listdir(date_path):
                    if result_file.endswith('.yaml'):
                        result_path = os.path.join(date_path, result_file)
                        try:
                            with open(result_path, 'r', encoding='utf-8') as f:
                                result_data = yaml.safe_load(f)
                                results_by_date[date_dir].append(result_data)
                        except Exception as e:
                            print(f"結果ファイルの読み込みエラー: {result_file}, {e}")
        
        # 日付でソート（新しい順）
        sorted_dates = sorted(results_by_date.keys(), reverse=True)
        
        return render_template('results.html', 
                             results_by_date=results_by_date, 
                             sorted_dates=sorted_dates)
        
    except Exception as e:
        return render_template('results.html', results=[], error_message=f'結果の読み込みエラー: {e}')

@app.route('/result/<path:filename>')
def show_result(filename):
    """個別の実行結果を表示"""
    try:
        result_path = os.path.join('results', filename)
        
        if not os.path.exists(result_path):
            flash('結果ファイルが見つかりません', 'danger')
            return redirect(url_for('show_results'))
        
        with open(result_path, 'r', encoding='utf-8') as f:
            result_data = yaml.safe_load(f)
        
        return render_template('result_detail.html', result=result_data, filename=filename)
        
    except Exception as e:
        flash(f'結果の読み込みエラー: {e}', 'danger')
        return redirect(url_for('show_results'))

@app.route('/result_log/<path:filename>')
def show_result_log(filename):
    """実行ログを表示"""
    try:
        log_path = os.path.join('results', filename)
        
        if not os.path.exists(log_path):
            flash('ログファイルが見つかりません', 'danger')
            return redirect(url_for('show_results'))
        
        with open(log_path, 'r', encoding='utf-8') as f:
            log_content = f.read()
        
        return render_template('result_log.html', log_content=log_content, filename=filename)
        
    except Exception as e:
        flash(f'ログの読み込みエラー: {e}', 'danger')
        return redirect(url_for('show_results'))

# ログ閲覧機能
@app.route('/logs')
def view_logs():
    """ログ閲覧ページ"""
    try:
        log_manager = get_log_manager()
        summary = log_manager.get_log_summary()
        
        # デバイス別ログ統計
        device_stats = {}
        for device_name in summary['devices'].keys():
            device_logs = log_manager.get_device_logs(device_name, limit=1)
            if device_logs:
                latest_log = device_logs[0]
                device_stats[device_name] = {
                    'total_logs': len(log_manager.get_device_logs(device_name)),
                    'latest_timestamp': latest_log.get('timestamp', 'N/A'),
                    'success_rate': sum(1 for log in device_logs if log.get('success')) / len(device_logs) * 100 if device_logs else 0
                }
        
        return render_template('logs.html', summary=summary, device_stats=device_stats)
        
    except Exception as e:
        flash(f'ログの読み込みエラー: {e}', 'danger')
        return render_template('logs.html', summary={}, device_stats={}, error=str(e))

@app.route('/api/logs')
def api_logs():
    """ログAPI - JSON形式でログを返す"""
    try:
        log_manager = get_log_manager()
        
        # クエリパラメータ取得
        device = request.args.get('device')
        command = request.args.get('command')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        limit = int(request.args.get('limit', 50))
        
        logs = log_manager.get_logs(device, command, start_date, end_date, limit)
        
        return jsonify({
            'success': True,
            'logs': logs,
            'total': len(logs),
            'device': device,
            'command': command,
            'start_date': start_date,
            'end_date': end_date,
            'limit': limit
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'logs': [],
            'total': 0
        })

@app.route('/api/logs/summary')
def api_logs_summary():
    """ログサマリーAPI"""
    try:
        log_manager = get_log_manager()
        summary = log_manager.get_log_summary()
        
        return jsonify({
            'success': True,
            'summary': summary
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/logs/device/<device_name>')
def api_device_logs(device_name):
    """デバイス別ログAPI"""
    try:
        log_manager = get_log_manager()
        logs = log_manager.get_device_logs(device_name, limit=100)
        
        return jsonify({
            'success': True,
            'logs': logs,
            'total': len(logs),
            'device_name': device_name
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'logs': [],
            'total': 0
        })

@app.route('/api/logs/command/<command>')
def api_command_logs(command):
    """コマンド別ログAPI"""
    try:
        log_manager = get_log_manager()
        logs = log_manager.get_command_logs(command, limit=100)
        
        return jsonify({
            'success': True,
            'logs': logs,
            'total': len(logs),
            'command': command
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'logs': [],
            'total': 0
        })

@app.route('/clear_logs', methods=['POST'])
def clear_logs_web():
    """ログクリア（Web用）"""
    try:
        log_manager = get_log_manager()
        
        # フォームデータ取得
        device = request.form.get('device')
        older_than_days = request.form.get('older_than_days')
        
        if older_than_days:
            older_than_days = int(older_than_days)
        
        log_manager.clear_logs(device, older_than_days)
        
        flash('ログをクリアしました', 'success')
        
    except Exception as e:
        flash(f'ログクリアエラー: {e}', 'danger')
    
    return redirect(url_for('view_logs'))

# インポート機能
@app.route('/import_devices', methods=['GET', 'POST'])
def import_devices():
    """デバイスをYAMLファイルからインポート"""
    if request.method == 'GET':
        return render_template('import_devices.html')
    
    if 'file' not in request.files:
        flash('ファイルが選択されていません', 'danger')
        return redirect(url_for('import_devices'))
    
    file = request.files['file']
    if file.filename == '':
        flash('ファイルが選択されていません', 'danger')
        return redirect(url_for('import_devices'))
    
    if file and file.filename.endswith('.yaml'):
        try:
            content = file.read().decode('utf-8')
            new_devices = yaml.safe_load(content) or {}
            
            devices = get_devices()
            imported_count = 0
            skipped_count = 0
            
            for device_name, device_config in new_devices.items():
                if device_name and device_config:
                    if device_name not in devices:
                        devices[device_name] = device_config
                        imported_count += 1
                    else:
                        skipped_count += 1
            
            config_manager.save_config('devices', devices)
            flash(f'デバイスを {imported_count}件インポートしました（重複: {skipped_count}件）', 'success')
        except Exception as e:
            flash(f'ファイルの読み込みに失敗しました: {str(e)}', 'danger')
    else:
        flash('YAMLファイルを選択してください', 'danger')
    
    return redirect(url_for('devices'))

@app.route('/import_command_groups', methods=['GET', 'POST'])
def import_command_groups():
    """コマンドグループをYAMLファイルからインポート"""
    if request.method == 'GET':
        return render_template('import_command_groups.html')
    
    if 'file' not in request.files:
        flash('ファイルが選択されていません', 'danger')
        return redirect(url_for('import_command_groups'))
    
    file = request.files['file']
    if file.filename == '':
        flash('ファイルが選択されていません', 'danger')
        return redirect(url_for('import_command_groups'))
    
    if file and file.filename.endswith('.yaml'):
        try:
            content = file.read().decode('utf-8')
            new_command_groups = yaml.safe_load(content) or {}
            
            command_groups = get_command_groups()
            imported_count = 0
            skipped_count = 0
            
            for group_name, group_config in new_command_groups.items():
                if group_name and group_config:
                    if group_name not in command_groups:
                        command_groups[group_name] = group_config
                        imported_count += 1
                    else:
                        skipped_count += 1
            
            config_manager.save_config('command_groups', command_groups)
            flash(f'コマンドグループを {imported_count}件インポートしました（重複: {skipped_count}件）', 'success')
        except Exception as e:
            flash(f'ファイルの読み込みに失敗しました: {str(e)}', 'danger')
    else:
        flash('YAMLファイルを選択してください', 'danger')
    
    return redirect(url_for('command_groups'))

@app.route('/import_scenarios', methods=['GET', 'POST'])
def import_scenarios():
    """シナリオをYAMLファイルからインポート"""
    if request.method == 'GET':
        return render_template('import_scenarios.html')
    
    if 'file' not in request.files:
        flash('ファイルが選択されていません', 'danger')
        return redirect(url_for('import_scenarios'))
    
    file = request.files['file']
    if file.filename == '':
        flash('ファイルが選択されていません', 'danger')
        return redirect(url_for('import_scenarios'))
    
    if file and file.filename.endswith('.yaml'):
        try:
            content = file.read().decode('utf-8')
            new_scenarios = yaml.safe_load(content) or {}
            
            scenarios = get_scenarios()
            imported_count = 0
            skipped_count = 0
            
            for scenario_name, scenario_config in new_scenarios.items():
                if scenario_name and scenario_config:
                    if scenario_name not in scenarios:
                        scenarios[scenario_name] = scenario_config
                        imported_count += 1
                    else:
                        skipped_count += 1
            
            config_manager.save_config('scenarios', scenarios)
            flash(f'シナリオを {imported_count}件インポートしました（重複: {skipped_count}件）', 'success')
        except Exception as e:
            flash(f'ファイルの読み込みに失敗しました: {str(e)}', 'danger')
    else:
        flash('YAMLファイルを選択してください', 'danger')
    
    return redirect(url_for('scenarios'))

# 設定バリデーション
@app.route('/config_validation')
def config_validation():
    """設定バリデーションページ"""
    validation_results = validate_all_configs()
    config_summary = get_config_summary()
    
    # 詳細なログを取得
    detailed_logs = []
    for config_type in ['devices', 'command_groups', 'scenarios']:
        if not validation_results[config_type]:
            config = config_manager.load_config(config_type)
            if config_type == 'devices':
                for device_name, device_config in config.items():
                    required_fields = ['host', 'device_type', 'username']
                    for field in required_fields:
                        if field not in device_config:
                            detailed_logs.append(f"デバイス '{device_name}' に必須フィールド '{field}' がありません")
            elif config_type == 'command_groups':
                for group_name, group_config in config.items():
                    if 'commands' not in group_config:
                        detailed_logs.append(f"コマンドグループ '{group_name}' に 'commands' フィールドがありません")
            elif config_type == 'scenarios':
                for scenario_name, scenario_config in config.items():
                    if 'devices' not in scenario_config or 'commands' not in scenario_config:
                        detailed_logs.append(f"シナリオ '{scenario_name}' に必須フィールドが不足しています")
    
    return render_template('config_validation.html', 
                         validation_results=validation_results,
                         config_summary=config_summary,
                         detailed_logs=detailed_logs)

# 設定再読み込み
@app.route('/config_reload', methods=['POST'])
def config_reload():
    """設定ファイルを再読み込み"""
    try:
        config_manager.reload_all_configs()
        flash('設定ファイルを再読み込みしました', 'success')
    except Exception as e:
        flash(f'設定ファイルの再読み込みに失敗しました: {str(e)}', 'danger')
    
    return redirect(url_for('config_validation'))

# ダッシュボード
@app.route('/')
def index():
    """ダッシュボード"""
    try:
        validation_results = validate_all_configs()
        config_summary = get_config_summary()
        
        return render_template('index.html', 
                             validation_results=validation_results,
                             config_summary=config_summary)
    except Exception as e:
        return f"Error: {str(e)}", 500

if __name__ == '__main__':
    import sys
    port = 5000 if len(sys.argv) > 1 and sys.argv[1] == '--port' else 5000
    app.run(host='0.0.0.0', port=port, debug=True, threaded=True)
