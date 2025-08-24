
#!/usr/bin/env python3
"""
Cisco Config Fetcher API Server
REST APIを提供し、外部アプリケーションからシナリオ実行やログ取得が可能になる
"""

import yaml
import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import time
from concurrent.futures import ThreadPoolExecutor
import uuid

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # CORSを有効にして外部アクセスを許可

# グローバル変数
scenarios = {}
scenario_results = {}
scenario_lock = threading.Lock()

class APIServer:
    """APIサーバークラス"""
    
    def __init__(self, config_fetcher_module):
        self.config_fetcher = config_fetcher_module
        self.executor = ThreadPoolExecutor(max_workers=5)
        
    def load_config(self) -> Dict[str, Any]:
        """設定ファイルを読み込む"""
        config_path = 'config.yaml'
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return {}
    
    def save_config(self, config: Dict[str, Any]) -> None:
        """設定ファイルを保存する"""
        with open('config.yaml', 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True, indent=2)

# APIエンドポイント
@app.route('/api/v1/health', methods=['GET'])
def health_check():
    """ヘルスチェック"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'cisco-config-fetcher-api'
    })

@app.route('/api/v1/scenarios', methods=['GET'])
def get_scenarios():
    """シナリオ一覧を取得"""
    try:
        config = api_server.load_config()
        scenarios = config.get('scenarios', {})
        
        scenario_list = []
        for name, scenario in scenarios.items():
            scenario_list.append({
                'name': name,
                'description': scenario.get('description', ''),
                'devices': list(scenario.get('devices', {}).keys()),
                'created_at': scenario.get('created_at', ''),
                'updated_at': scenario.get('updated_at', '')
            })
        
        return jsonify({
            'scenarios': scenario_list,
            'count': len(scenario_list)
        })
    except Exception as e:
        logger.error(f"シナリオ一覧取得エラー: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/scenarios/<scenario_name>', methods=['GET'])
def get_scenario(scenario_name):
    """特定のシナリオを取得"""
    try:
        config = api_server.load_config()
        scenarios = config.get('scenarios', {})
        
        if scenario_name not in scenarios:
            return jsonify({'error': 'Scenario not found'}), 404
        
        scenario = scenarios[scenario_name]
        return jsonify({
            'name': scenario_name,
            'description': scenario.get('description', ''),
            'devices': scenario.get('devices', {}),
            'created_at': scenario.get('created_at', ''),
            'updated_at': scenario.get('updated_at', '')
        })
    except Exception as e:
        logger.error(f"シナリオ取得エラー: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/scenarios', methods=['POST'])
def create_scenario():
    """新しいシナリオを作成"""
    try:
        data = request.get_json()
        
        if not data or 'name' not in data:
            return jsonify({'error': 'Scenario name is required'}), 400
        
        scenario_name = data['name']
        description = data.get('description', '')
        devices = data.get('devices', {})
        
        # シナリオ名のバリデーション
        if not scenario_name.replace('_', '').replace('-', '').isalnum():
            return jsonify({'error': 'Invalid scenario name'}), 400
        
        config = api_server.load_config()
        scenarios = config.get('scenarios', {})
        
        if scenario_name in scenarios:
            return jsonify({'error': 'Scenario already exists'}), 409
        
        # 新しいシナリオを作成
        scenarios[scenario_name] = {
            'description': description,
            'devices': devices,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        config['scenarios'] = scenarios
        api_server.save_config(config)
        
        logger.info(f"シナリオを作成: {scenario_name}")
        return jsonify({
            'message': 'Scenario created successfully',
            'scenario': {
                'name': scenario_name,
                'description': description,
                'devices': devices
            }
        }), 201
        
    except Exception as e:
        logger.error(f"シナリオ作成エラー: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/scenarios/<scenario_name>', methods=['PUT'])
def update_scenario(scenario_name):
    """シナリオを更新"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        config = api_server.load_config()
        scenarios = config.get('scenarios', {})
        
        if scenario_name not in scenarios:
            return jsonify({'error': 'Scenario not found'}), 404
        
        # シナリオを更新
        scenarios[scenario_name].update({
            'description': data.get('description', scenarios[scenario_name].get('description', '')),
            'devices': data.get('devices', scenarios[scenario_name].get('devices', {})),
            'updated_at': datetime.now().isoformat()
        })
        
        config['scenarios'] = scenarios
        api_server.save_config(config)
        
        logger.info(f"シナリオを更新: {scenario_name}")
        return jsonify({
            'message': 'Scenario updated successfully',
            'scenario': scenarios[scenario_name]
        })
        
    except Exception as e:
        logger.error(f"シナリオ更新エラー: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/scenarios/<scenario_name>', methods=['DELETE'])
def delete_scenario(scenario_name):
    """シナリオを削除"""
    try:
        config = api_server.load_config()
        scenarios = config.get('scenarios', {})
        
        if scenario_name not in scenarios:
            return jsonify({'error': 'Scenario not found'}), 404
        
        del scenarios[scenario_name]
        config['scenarios'] = scenarios
        api_server.save_config(config)
        
        logger.info(f"シナリオを削除: {scenario_name}")
        return jsonify({'message': 'Scenario deleted successfully'})
        
    except Exception as e:
        logger.error(f"シナリオ削除エラー: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/scenarios/<scenario_name>/execute', methods=['POST'])
def execute_scenario(scenario_name):
    """シナリオを実行"""
    try:
        # 非同期実行のためのジョブIDを生成
        job_id = str(uuid.uuid4())
        
        # リクエストデータを取得
        data = request.get_json() or {}
        options = data.get('options', {})
        
        # シナリオ実行をバックグラウンドで開始
        future = api_server.executor.submit(
            _run_scenario_background,
            scenario_name,
            job_id,
            options
        )
        
        # ジョブIDを返す
        return jsonify({
            'message': 'Scenario execution started',
            'job_id': job_id,
            'scenario_name': scenario_name
        }), 202
        
    except Exception as e:
        logger.error(f"シナリオ実行開始エラー: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/jobs/<job_id>', methods=['GET'])
def get_job_status(job_id):
    """ジョブの状態を取得"""
    try:
        with scenario_lock:
            if job_id not in scenario_results:
                return jsonify({'error': 'Job not found'}), 404
            
            result = scenario_results[job_id]
            return jsonify({
                'job_id': job_id,
                'status': result['status'],
                'scenario_name': result['scenario_name'],
                'started_at': result['started_at'],
                'completed_at': result.get('completed_at'),
                'progress': result.get('progress', 0),
                'message': result.get('message', ''),
                'results': result.get('results', {}),
                'logs': result.get('logs', [])
            })
            
    except Exception as e:
        logger.error(f"ジョブ状態取得エラー: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/jobs/<job_id>/logs', methods=['GET'])
def get_job_logs(job_id):
    """ジョブのログを取得"""
    try:
        with scenario_lock:
            if job_id not in scenario_results:
                return jsonify({'error': 'Job not found'}), 404
            
            result = scenario_results[job_id]
            return jsonify({
                'job_id': job_id,
                'logs': result.get('logs', []),
                'total_logs': len(result.get('logs', []))
            })
            
    except Exception as e:
        logger.error(f"ジョブログ取得エラー: {e}")
        return jsonify({'error': str(e)}), 500

def _run_scenario_background(scenario_name: str, job_id: str, options: Dict[str, Any]):
    """シナリオをバックグラウンドで実行"""
    started_at = datetime.now().isoformat()
    
    with scenario_lock:
        scenario_results[job_id] = {
            'status': 'running',
            'scenario_name': scenario_name,
            'started_at': started_at,
            'progress': 0,
            'message': 'Scenario execution started',
            'logs': [],
            'results': {}
        }
    
    try:
        # ここで実際のシナリオ実行処理を行う
        # 現在はモック実装
        logger.info(f"シナリオ実行開始: {scenario_name} (Job ID: {job_id})")
        
        # プログレス更新
        with scenario_lock:
            scenario_results[job_id]['progress'] = 10
            scenario_results[job_id]['message'] = 'Loading scenario configuration'
            scenario_results[job_id]['logs'].append(f"[{started_at}] Starting scenario: {scenario_name}")
        
        # シナリオ設定の読み込み（モック）
        time.sleep(1)
        
        with scenario_lock:
            scenario_results[job_id]['progress'] = 30
            scenario_results[job_id]['message'] = 'Connecting to devices'
            scenario_results[job_id]['logs'].append(f"[{datetime.now().isoformat()}] Connecting to devices...")
        
        # デバイス接続（モック）
        time.sleep(2)
        
        with scenario_lock:
            scenario_results[job_id]['progress'] = 50
            scenario_results[job_id]['message'] = 'Executing commands'
            scenario_results[job_id]['logs'].append(f"[{datetime.now().isoformat()}] Executing commands...")
        
        # コマンド実行（モック）
        time.sleep(3)
        
        with scenario_lock:
            scenario_results[job_id]['progress'] = 80
            scenario_results[job_id]['message'] = 'Collecting results'
            scenario_results[job_id]['logs'].append(f"[{datetime.now().isoformat()}] Collecting results...")
        
        # 結果収集（モック）
        time.sleep(1)
        
        completed_at = datetime.now().isoformat()
        
        with scenario_lock:
            scenario_results[job_id].update({
                'status': 'completed',
                'completed_at': completed_at,
                'progress': 100,
                'message': 'Scenario execution completed successfully',
                'logs': scenario_results[job_id]['logs'] + [f"[{completed_at}] Scenario completed successfully"],
                'results': {
                    'total_devices': 5,
                    'successful_devices': 5,
                    'failed_devices': 0,
                    'output_files': ['config_backup_20241201.zip', 'show_commands_20241201.json']
                }
            })
        
        logger.info(f"シナリオ実行完了: {scenario_name} (Job ID: {job_id})")
        
    except Exception as e:
        completed_at = datetime.now().isoformat()
        
        with scenario_lock:
            scenario_results[job_id].update({
                'status': 'failed',
                'completed_at': completed_at,
                'progress': scenario_results[job_id].get('progress', 0),
                'message': f'Scenario execution failed: {str(e)}',
                'logs': scenario_results[job_id].logs + [f"[{completed_at}] Error: {str(e)}"],
                'results': {}
            })
        
        logger.error(f"シナリオ実行失敗: {scenario_name} (Job ID: {job_id}) - {e}")

@app.route('/api/v1/devices', methods=['GET'])
def get_devices():
    """デバイス一覧を取得"""
    try:
        config = api_server.load_config()
        devices = config.get('devices', {})
        
        device_list = []
        for name, device in devices.items():
            device_list.append({
                'name': name,
                'host': device.get('host', ''),
                'username': device.get('username', ''),
                'device_group': device.get('device_group', 'default'),
                'command_group': device.get('command_group', 'default'),
                'status': 'unknown'
            })
        
        return jsonify({
            'devices': device_list,
            'count': len(device_list)
        })
    except Exception as e:
        logger.error(f"デバイス一覧取得エラー: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/logs', methods=['GET'])
def get_logs():
    """システムログを取得"""
    try:
        # ログファイルの読み込み（モック）
        logs = [
            {'timestamp': '2024-12-01T10:00:00', 'level': 'INFO', 'message': 'System started'},
            {'timestamp': '2024-12-01T10:01:00', 'level': 'INFO', 'message': 'Scenario executed successfully'},
            {'timestamp': '2024-12-01T10:02:00', 'level': 'WARNING', 'message': 'Device connection timeout'},
            {'timestamp': '2024-12-01T10:03:00', 'level': 'INFO', 'message': 'Backup completed'}
        ]
        
        return jsonify({
            'logs': logs,
            'count': len(logs)
        })
    except Exception as e:
        logger.error(f"ログ取得エラー: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/config', methods=['GET'])
def get_config():
    """設定情報を取得"""
    try:
        config = api_server.load_config()
        return jsonify(config)
    except Exception as e:
        logger.error(f"設定取得エラー: {e}")
        return jsonify({'error': str(e)}), 500

# グローバルインスタンス
api_server = None

def run_api_server(host='0.0.0.0', port=5000, debug=False):
    """APIサーバーを起動"""
    global api_server
    
    # APIサーバー初期化
    api_server = APIServer(None)  # config_fetcherモジュールは不要に変更
    
    logger.info(f"APIサーバーを起動: http://{host}:{port}")
    app.run(host=host, port=port, debug=debug, threaded=True)

if __name__ == '__main__':
    run_api_server(debug=True)
