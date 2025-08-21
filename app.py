
from flask import Flask, render_template, request, redirect, url_for, send_file, flash
import yaml
import os
import subprocess
import threading
from datetime import datetime
import io

# 設定管理モジュールのインポート
from config_manager import config_manager, get_devices, get_command_groups, get_scenarios

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
                selected_group = request.form.get('device_group')
                if selected_group:
                    # グループに属するデバイスを取得
                    selected_devices = []
                    for device_name, device in devices.items():
                        if device.get('group') == selected_group:
                            selected_devices.append(device_name)
                    devices_list = selected_devices
                else:
                    devices_list = []
            else:
                # 個別デバイス選択の場合
                selected_device = request.form.get('individual_device')
                if selected_device:
                    devices_list = [selected_device]
                else:
                    devices_list = []
            
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
    return render_template('scenario_lists.html', scenarios=scenarios)

# 実行管理
@app.route('/execute')
def execute():
    """実行管理ページ"""
    devices = get_devices()
    command_groups = get_command_groups()
    scenarios = get_scenarios()
    return render_template('execute.html', devices=devices, command_groups=command_groups, scenarios=scenarios, scenario_lists=scenarios)

@app.route('/run_scenario', methods=['POST'])
def run_scenario():
    """シナリオを実行"""
    scenario_name = request.form['scenario_name']
    scenarios = get_scenarios()
    
    if scenario_name not in scenarios:
        flash('シナリオが見つかりません', 'danger')
        return redirect(url_for('execute'))
    
    scenario = scenarios[scenario_name]
    
    # 非同期で実行
    def execute_scenario():
        try:
            # ここで実際の実行処理を行う
            # 現在はダミーの実行結果を生成
            result = {
                'scenario_name': scenario_name,
                'devices': scenario['devices'],
                'commands': scenario['commands'],
                'status': 'success',
                'output': f'シナリオ "{scenario_name}" を実行しました',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # 結果を保存
            result_dir = os.path.join('results', datetime.now().strftime('%Y%m%d'))
            os.makedirs(result_dir, exist_ok=True)
            result_file = os.path.join(result_dir, f'{scenario_name}_{datetime.now().strftime("%H%M%S")}.yaml')
            
            with open(result_file, 'w', encoding='utf-8') as f:
                yaml.dump(result, f, default_flow_style=False, allow_unicode=True)
                
        except Exception as e:
            print(f"シナリオ実行エラー: {e}")
    
    # 別スレッドで実行
    thread = threading.Thread(target=execute_scenario)
    thread.start()
    
    flash(f'シナリオ "{scenario_name}" を実行中です...', 'info')
    return redirect(url_for('execute'))

# 追加のルート
@app.route('/execute_scenario/<scenario_name>', methods=['GET'])
def execute_scenario(scenario_name):
    """シナリオを実行（GET用）"""
    scenarios = get_scenarios()
    
    if scenario_name not in scenarios:
        flash('シナリオが見つかりません', 'danger')
        return redirect(url_for('execute'))
    
    scenario = scenarios[scenario_name]
    
    # 非同期で実行
    def execute_scenario():
        try:
            # ここで実際の実行処理を行う
            # 現在はダミーの実行結果を生成
            result = {
                'scenario_name': scenario_name,
                'devices': scenario['devices'],
                'commands': scenario['commands'],
                'status': 'success',
                'output': f'シナリオ "{scenario_name}" を実行しました',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # 結果を保存
            result_dir = os.path.join('results', datetime.now().strftime('%Y%m%d'))
            os.makedirs(result_dir, exist_ok=True)
            result_file = os.path.join(result_dir, f'{scenario_name}_{datetime.now().strftime("%H%M%S")}.yaml')
            
            with open(result_file, 'w', encoding='utf-8') as f:
                yaml.dump(result, f, default_flow_style=False, allow_unicode=True)
                
        except Exception as e:
            print(f"シナリオ実行エラー: {e}")
    
    # 別スレッドで実行
    thread = threading.Thread(target=execute_scenario)
    thread.start()
    
    flash(f'シナリオ "{scenario_name}" を実行中です...', 'info')
    return redirect(url_for('execute'))

@app.route('/execute_scenario_post', methods=['POST'])
def execute_scenario_post():
    """シナリオを実行（POST用）"""
    return run_scenario()

@app.route('/execute_scenario_list')
def execute_scenario_list():
    """シナリオ一覧を実行"""
    scenarios = get_scenarios()
    return render_template('scenario_lists.html', scenarios=scenarios)

# ダウンロード機能
@app.route('/download/<path:filename>')
def download_file(filename):
    return send_file(filename, as_attachment=True)

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
