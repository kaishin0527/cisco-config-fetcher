




from flask import Flask, render_template, request, redirect, url_for, send_file, flash
import yaml
import os
import subprocess
import threading
from datetime import datetime

# 設定管理モジュールのインポート
from config_manager import config_manager, get_devices, get_command_groups, get_scenarios

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.secret_key = 'supersecretkey'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 設定ファイルパス（互換性のため）
DEVICES_FILE = 'devices_updated.yaml'
COMMAND_GROUPS_FILE = 'command_groups.yaml'
SCENARIO_LIST_FILE = 'scenario_list.yaml'

def load_yaml(file_path):
    """YAMLファイルを読み込む（互換性のため）"""
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return yaml.safe_load(f)
    return {}

def save_yaml(data, file_path):
    """YAMLファイルに保存（互換性のため）"""
    with open(file_path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False)

def get_all_devices():
    """すべてのデバイスを取得（config_manager経由）"""
    return get_devices()

def get_all_command_groups():
    """すべてのコマンドグループを取得（config_manager経由）"""
    return get_command_groups()

def get_all_scenarios():
    """すべてのシナリオを取得（config_manager経由）"""
    return get_scenarios()

def validate_all_configs():
    """すべての設定をバリデーション（config_manager経由）"""
    return config_manager.validate_all_configs()

def get_config_summary():
    """設定のサマリーを取得（config_manager経由）"""
    return config_manager.get_config_summary()

# ダッシュボード
@app.route('/')
def index():
    """ダッシュボード"""
    # config_managerの統合情報を取得
    config_summary = get_config_summary()
    validation_results = validate_all_configs()
    
    return render_template('index.html', 
                         config_summary=config_summary, 
                         validation_results=validation_results)

# デバイス管理
@app.route('/devices')
def devices():
    devices_data = get_all_devices()
    return render_template('devices.html', devices=devices_data)

@app.route('/device/add', methods=['GET', 'POST'])
def add_device():
    if request.method == 'POST':
        name = request.form['name']
        device_config = {
            'host': request.form['host'],
            'device_type': request.form['device_type'],
            'username': request.form['username'],
            'password': request.form['password'],
            'secret': request.form['secret'],
            'group': request.form['group'],
            'prompt_pattern': request.form['prompt_pattern']
        }
        
        # config_managerを使用してデバイスを追加
        devices = get_all_devices()
        devices[name] = device_config
        
        # YAMLファイルに保存
        devices_data = {'devices': devices}
        save_yaml(devices_data, DEVICES_FILE)
        
        flash(f'デバイス {name} を追加しました', 'success')
        return redirect(url_for('devices'))
    return render_template('device_form.html')

@app.route('/device/edit/<name>', methods=['GET', 'POST'])
def edit_device(name):
    device = get_all_devices().get(name)
    if not device:
        flash('デバイスが見つかりません', 'danger')
        return redirect(url_for('devices'))
        
    if request.method == 'POST':
        device['host'] = request.form['host']
        device['device_type'] = request.form['device_type']
        device['username'] = request.form['username']
        device['password'] = request.form['password']
        device['secret'] = request.form['secret']
        device['group'] = request.form['group']
        device['prompt_pattern'] = request.form['prompt_pattern']
        
        # config_managerを使用してデバイスを更新
        devices = get_all_devices()
        devices[name] = device
        
        # YAMLファイルに保存
        devices_data = {'devices': devices}
        save_yaml(devices_data, DEVICES_FILE)
        
        flash(f'デバイス {name} を更新しました', 'success')
        return redirect(url_for('devices'))
    return render_template('device_form.html', device=device, name=name)

@app.route('/device/delete/<name>')
def delete_device(name):
    devices = get_all_devices()
    if name in devices:
        del devices[name]
        
        # YAMLファイルに保存
        devices_data = {'devices': devices}
        save_yaml(devices_data, DEVICES_FILE)
        
        flash(f'デバイス {name} を削除しました', 'success')
    else:
        flash('デバイスが見つかりません', 'danger')
    return redirect(url_for('devices'))

# コマンドグループ管理
@app.route('/command_groups')
def command_groups():
    command_groups_data = get_all_command_groups()
    return render_template('command_groups.html', command_groups=command_groups_data)

@app.route('/command_group/add', methods=['GET', 'POST'])
def add_command_group():
    if request.method == 'POST':
        name = request.form['name']
        commands = [cmd.strip() for cmd in request.form['commands'].split('\n') if cmd.strip()]
        config_mode = 'config_mode' in request.form
        
        command_group_config = {
            'commands': commands,
            'config_mode': config_mode
        }
        
        # config_managerを使用してコマンドグループを追加
        command_groups = get_all_command_groups()
        command_groups[name] = command_group_config
        
        # YAMLファイルに保存
        command_groups_data = {'command_groups': command_groups}
        save_yaml(command_groups_data, COMMAND_GROUPS_FILE)
        
        flash(f'コマンドグループ {name} を追加しました', 'success')
        return redirect(url_for('command_groups'))
    return render_template('command_group_form.html')

@app.route('/command_group/edit/<name>', methods=['GET', 'POST'])
def edit_command_group(name):
    group = get_all_command_groups().get(name)
    if not group:
        flash('コマンドグループが見つかりません', 'danger')
        return redirect(url_for('command_groups'))
        
    if request.method == 'POST':
        commands = [cmd.strip() for cmd in request.form['commands'].split('\n') if cmd.strip()]
        config_mode = 'config_mode' in request.form
        
        group['commands'] = commands
        group['config_mode'] = config_mode
        
        # config_managerを使用してコマンドグループを更新
        command_groups = get_all_command_groups()
        command_groups[name] = group
        
        # YAMLファイルに保存
        command_groups_data = {'command_groups': command_groups}
        save_yaml(command_groups_data, COMMAND_GROUPS_FILE)
        
        flash(f'コマンドグループ {name} を更新しました', 'success')
        return redirect(url_for('command_groups'))
    return render_template('command_group_form.html', group=group, name=name)

@app.route('/command_group/delete/<name>')
def delete_command_group(name):
    command_groups = get_all_command_groups()
    if name in command_groups:
        del command_groups[name]
        
        # YAMLファイルに保存
        command_groups_data = {'command_groups': command_groups}
        save_yaml(command_groups_data, COMMAND_GROUPS_FILE)
        
        flash(f'コマンドグループ {name} を削除しました', 'success')
    else:
        flash('コマンドグループが見つかりません', 'danger')
    return redirect(url_for('command_groups'))

# シナリオ管理
@app.route('/scenarios')
def scenarios():
    scenarios_data = get_all_scenarios()
    return render_template('scenarios.html', scenarios=scenarios_data)

@app.route('/scenario/add', methods=['GET', 'POST'])
def add_scenario():
    if request.method == 'POST':
        name = request.form['name']
        scenario_config = {
            'name': name,
            'description': request.form['description'],
            'devices': request.form.getlist('devices'),
            'commands': request.form.getlist('commands'),
            'steps': []
        }
        
        # config_managerを使用してシナリオを追加
        scenarios = get_all_scenarios()
        scenarios[name] = scenario_config
        
        # YAMLファイルに保存
        scenarios_data = {'scenarios': scenarios}
        save_yaml(scenarios_data, SCENARIO_LIST_FILE)
        
        flash(f'シナリオ {name} を追加しました', 'success')
        return redirect(url_for('scenarios'))
    return render_template('scenario_form.html')

# シナリオリスト管理
@app.route('/scenario_lists')
def scenario_lists():
    scenario_lists_data = get_all_scenarios()
    return render_template('scenario_lists.html', scenario_lists=scenario_lists_data)

# 実行管理
@app.route('/execute')
def execute():
    scenarios_data = get_all_scenarios()
    scenario_lists_data = get_all_scenarios()
    return render_template('execute.html', scenarios=scenarios_data, scenario_lists=scenario_lists_data)

def run_scenario_list(scenario_list_name):
    """バックグラウンドでシナリオリストを実行"""
    subprocess.run(['python3', 'cisco_config_fetcher_parallel.py'])
    print(f"シナリオリスト {scenario_list_name} の実行が完了しました")

@app.route('/execute/scenario_list', methods=['POST'])
def execute_scenario_list():
    scenario_list_name = request.form['scenario_list']
    # バックグラウンドで実行
    thread = threading.Thread(target=run_scenario_list, args=(scenario_list_name,))
    thread.start()
    flash(f'シナリオリスト {scenario_list_name} の実行を開始しました', 'success')
    return redirect(url_for('execute'))

@app.route('/execute/scenario', methods=['POST'])
def execute_scenario():
    scenario_name = request.form['scenario']
    # 簡易実装（実際には個別シナリオ実行機能を実装する必要あり）
    flash(f'シナリオ {scenario_name} の実行を開始しました', 'success')
    return redirect(url_for('execute'))

# 静的ファイル提供
@app.route('/download/<path:filename>')
def download_file(filename):
    return send_file(filename, as_attachment=True)

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=51361, debug=True)




