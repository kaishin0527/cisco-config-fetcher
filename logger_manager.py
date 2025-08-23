

"""
ログ管理モジュール
ネットワークデバイス操作のログを永続的に保管し、閲覧機能を提供
"""
import os
import json
import logging
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import threading
from logging.handlers import RotatingFileHandler

class LogManager:
    """ログ管理クラス"""
    
    def __init__(self, log_dir: str = "logs"):
        """
        ログ管理クラスを初期化
        
        Args:
            log_dir: ログファイルを保存するディレクトリ
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # ログ設定
        self.setup_logging()
        
        # ログインデックス
        self.log_index_file = self.log_dir / "log_index.json"
        self.log_index = self.load_log_index()
        
        # ログロック
        self.lock = threading.Lock()
    
    def setup_logging(self):
        """ログ設定を初期化"""
        # ログフォーマット
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # ファイルハンドラー（ローテーション付き）
        file_handler = RotatingFileHandler(
            self.log_dir / "network_executor.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        
        # コンソールハンドラー
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        # ロガー設定
        self.logger = logging.getLogger('NetworkExecutor')
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def load_log_index(self) -> Dict[str, Any]:
        """ログインデックスを読み込む"""
        if self.log_index_file.exists():
            try:
                with open(self.log_index_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"ログインデックスの読み込みに失敗: {e}")
        
        return {
            'sessions': [],
            'devices': {},
            'commands': {}
        }
    
    def save_log_index(self):
        """ログインデックスを保存"""
        try:
            with open(self.log_index_file, 'w', encoding='utf-8') as f:
                json.dump(self.log_index, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"ログインデックスの保存に失敗: {e}")
    
    def log_command_execution(self, device_name: str, command: str, result: Dict[str, Any]):
        """
        コマンド実行をログに記録
        
        Args:
            device_name: デバイス名
            command: 実行したコマンド
            result: 実行結果
        """
        with self.lock:
            # セッションID生成
            session_id = f"{device_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # ログエントリー作成
            log_entry = {
                'session_id': session_id,
                'timestamp': datetime.now().isoformat(),
                'device_name': device_name,
                'command': command,
                'success': result.get('success', False),
                'execution_time': result.get('execution_time', 0),
                'output': result.get('output', ''),
                'error_output': result.get('error_output', ''),
                'command_type': self._get_command_type(command)
            }
            
            # ログファイルに保存
            log_file = self.log_dir / f"{device_name}_{datetime.now().strftime('%Y%m%d')}.log"
            try:
                with open(log_file, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
            except Exception as e:
                self.logger.error(f"ログファイルの書き込みに失敗: {e}")
            
            # インデックス更新
            self._update_log_index(log_entry)
            
            # ログ出力
            if result.get('success'):
                self.logger.info(f"Command executed successfully: {device_name} > {command}")
            else:
                self.logger.error(f"Command execution failed: {device_name} > {command}")
                self.logger.error(f"Error: {result.get('error_output', 'Unknown error')}")
    
    def log_scenario_execution(self, device_name: str, scenario_name: str, result: Dict[str, Any]):
        """
        シナリオ実行をログに記録
        
        Args:
            device_name: デバイス名
            scenario_name: シナリオ名
            result: 実行結果
        """
        with self.lock:
            session_id = f"scenario_{device_name}_{scenario_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            log_entry = {
                'session_id': session_id,
                'timestamp': datetime.now().isoformat(),
                'device_name': device_name,
                'scenario_name': scenario_name,
                'success': result.get('success', False),
                'total_commands': result.get('total_commands', 0),
                'successful_commands': result.get('successful_commands', 0),
                'failed_commands': result.get('failed_commands', 0),
                'output': result.get('output', ''),
                'error_output': result.get('error_output', ''),
                'command_results': result.get('command_results', [])
            }
            
            # ログファイルに保存
            log_file = self.log_dir / f"scenario_{datetime.now().strftime('%Y%m%d')}.log"
            try:
                with open(log_file, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
            except Exception as e:
                self.logger.error(f"シナリオログの書き込みに失敗: {e}")
            
            # インデックス更新
            self._update_scenario_index(log_entry)
            
            # ログ出力
            if result.get('success'):
                self.logger.info(f"Scenario executed successfully: {device_name} > {scenario_name}")
            else:
                self.logger.error(f"Scenario execution failed: {device_name} > {scenario_name}")
    
    def _get_command_type(self, command: str) -> str:
        """コマンドタイプを判定"""
        command_lower = command.lower()
        if 'show' in command_lower:
            return 'show'
        elif 'configure' in command_lower or 'conf' in command_lower:
            return 'configure'
        elif 'ping' in command_lower:
            return 'ping'
        elif 'traceroute' in command_lower or 'tracert' in command_lower:
            return 'traceroute'
        else:
            return 'other'
    
    def _update_log_index(self, log_entry: Dict[str, Any]):
        """ログインデックスを更新"""
        session_id = log_entry['session_id']
        
        # セッションリストに追加
        if session_id not in [s['session_id'] for s in self.log_index['sessions']]:
            self.log_index['sessions'].append({
                'session_id': session_id,
                'timestamp': log_entry['timestamp'],
                'device_name': log_entry['device_name'],
                'command': log_entry['command'],
                'success': log_entry['success']
            })
        
        # デバイスインデックス更新
        device_name = log_entry['device_name']
        if device_name not in self.log_index['devices']:
            self.log_index['devices'][device_name] = []
        
        device_session = {
            'session_id': session_id,
            'timestamp': log_entry['timestamp'],
            'command': log_entry['command'],
            'success': log_entry['success'],
            'execution_time': log_entry['execution_time']
        }
        
        # 重複チェック
        if not any(s['session_id'] == session_id for s in self.log_index['devices'][device_name]):
            self.log_index['devices'][device_name].append(device_session)
        
        # コマンドインデックス更新
        command_key = f"{log_entry['device_name']}_{log_entry['command']}"
        if command_key not in self.log_index['commands']:
            self.log_index['commands'][command_key] = []
        
        command_session = {
            'session_id': session_id,
            'timestamp': log_entry['timestamp'],
            'success': log_entry['success'],
            'execution_time': log_entry['execution_time']
        }
        
        self.log_index['commands'][command_key].append(command_session)
        
        # インデックス保存
        self.save_log_index()
    
    def _update_scenario_index(self, log_entry: Dict[str, Any]):
        """シナリオログインデックスを更新"""
        session_id = log_entry['session_id']
        
        # セッションリストに追加
        scenario_session = {
            'session_id': session_id,
            'timestamp': log_entry['timestamp'],
            'device_name': log_entry['device_name'],
            'scenario_name': log_entry['scenario_name'],
            'success': log_entry['success'],
            'total_commands': log_entry['total_commands'],
            'successful_commands': log_entry['successful_commands'],
            'failed_commands': log_entry['failed_commands']
        }
        
        self.log_index['sessions'].append(scenario_session)
        
        # インデックス保存
        self.save_log_index()
    
    def get_logs(self, device_name: Optional[str] = None, 
                 command: Optional[str] = None,
                 start_date: Optional[str] = None,
                 end_date: Optional[str] = None,
                 limit: int = 100) -> List[Dict[str, Any]]:
        """
        ログを取得
        
        Args:
            device_name: デバイス名（フィルタ）
            command: コマンド（フィルタ）
            start_date: 開始日（YYYY-MM-DD）
            end_date: 終了日（YYYY-MM-DD）
            limit: 取得件数制限
            
        Returns:
            ログリスト
        """
        logs = []
        
        # ログファイルを検索
        for log_file in self.log_dir.glob("*.log"):
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            log_entry = json.loads(line.strip())
                            
                            # フィルタリング
                            if device_name and log_entry.get('device_name') != device_name:
                                continue
                            
                            if command and log_entry.get('command') != command:
                                continue
                            
                            if start_date:
                                log_date = log_entry.get('timestamp', '').split('T')[0]
                                if log_date < start_date:
                                    continue
                            
                            if end_date:
                                log_date = log_entry.get('timestamp', '').split('T')[0]
                                if log_date > end_date:
                                    continue
                            
                            logs.append(log_entry)
                            
                        except json.JSONDecodeError:
                            continue
                            
            except Exception as e:
                self.logger.error(f"ログファイルの読み込みに失敗: {log_file} - {e}")
        
        # タイムスタンプでソート
        logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # 件数制限
        return logs[:limit]
    
    def get_device_logs(self, device_name: str, limit: int = 50) -> List[Dict[str, Any]]:
        """デバイスのログを取得"""
        return self.get_logs(device_name=device_name, limit=limit)
    
    def get_command_logs(self, command: str, limit: int = 50) -> List[Dict[str, Any]]:
        """コマンドのログを取得"""
        return self.get_logs(command=command, limit=limit)
    
    def get_scenario_logs(self, device_name: str, scenario_name: str) -> List[Dict[str, Any]]:
        """シナリオのログを取得"""
        logs = self.get_logs(device_name=device_name)
        return [log for log in logs if log.get('scenario_name') == scenario_name]
    
    def get_log_summary(self) -> Dict[str, Any]:
        """ログサマリーを取得"""
        total_sessions = len(self.log_index['sessions'])
        successful_sessions = sum(1 for s in self.log_index['sessions'] if s.get('success'))
        failed_sessions = total_sessions - successful_sessions
        
        device_count = len(self.log_index['devices'])
        command_count = len(self.log_index['commands'])
        
        return {
            'total_sessions': total_sessions,
            'successful_sessions': successful_sessions,
            'failed_sessions': failed_sessions,
            'device_count': device_count,
            'command_count': command_count,
            'log_directory': str(self.log_dir),
            'last_updated': datetime.now().isoformat()
        }
    
    def clear_logs(self, device_name: Optional[str] = None, older_than_days: Optional[int] = None):
        """
        ログをクリア
        
        Args:
            device_name: デバイス名（指定したデバイスのログのみクリア）
            older_than_days: 指定日数より古いログをクリア
        """
        with self.lock:
            if older_than_days:
                # 古いログファイルを削除
                cutoff_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                cutoff_date = cutoff_date.replace(day=cutoff_date.day - older_than_days)
                
                for log_file in self.log_dir.glob("*.log"):
                    if log_file.stat().st_mtime < cutoff_date.timestamp():
                        try:
                            log_file.unlink()
                            self.logger.info(f"古いログファイルを削除: {log_file}")
                        except Exception as e:
                            self.logger.error(f"ログファイルの削除に失敗: {log_file} - {e}")
            
            # インデックスを再構築
            self.log_index = {
                'sessions': [],
                'devices': {},
                'commands': {}
            }
            self.save_log_index()
            
            self.logger.info("ログインデックスをクリアしました")

# グローバルインスタンス
log_manager = LogManager()

def get_log_manager() -> LogManager:
    """ログ管理インスタンスを取得"""
    return log_manager

