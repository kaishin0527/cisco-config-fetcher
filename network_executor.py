
"""
ネットワークデバイスコマンド実行モジュール
SSHとtelnet接続をサポートし、コマンド実行と結果取得を行う
"""
import paramiko
import telnetlib3
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import logging
from io import StringIO

# ログ管理モジュールのインポート
from logger_manager import get_log_manager

logger = logging.getLogger(__name__)

class NetworkDeviceExecutor:
    """ネットワークデバイスコマンド実行クラス"""
    
    def __init__(self, device_config: Dict[str, Any]):
        """
        デバイス設定で初期化
        
        Args:
            device_config: デバイス設定辞書
        """
        self.device_config = device_config
        self.connection = None
        self.lock = threading.Lock()
        
        # ログ管理インスタンスの取得
        self.log_manager = get_log_manager()
        
        # デバイス設定のバリデーション
        if not self.validate_device_config():
            raise ValueError("Invalid device configuration")
        
    def connect(self) -> bool:
        """
        デバイスに接続
        
        Returns:
            bool: 接続成功時True、失敗時False
        """
        try:
            connection_type = self.device_config.get('connection_type', 'ssh').lower()
            
            if connection_type == 'ssh':
                return self._connect_ssh()
            elif connection_type == 'telnet':
                return self._connect_telnet()
            else:
                logger.error(f"Unsupported connection type: {connection_type}")
                return False
                
        except Exception as e:
            logger.error(f"Connection error for {self.device_config.get('hostname', self.device_config.get('host', 'unknown'))}: {e}")
            return False
    
    def _connect_ssh(self) -> bool:
        """SSH接続を確立"""
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # 接続パラメータ取得
            host = self.device_config['host']
            username = self.device_config['username']
            password = self.device_config.get('password', '')
            
            # 接続
            client.connect(
                hostname=host,
                username=username,
                password=password,
                timeout=self.device_config.get('timeout', 30),
                port=self.device_config.get('port', 22)
            )
            
            # 特権モードへの昇格
            secret = self.device_config.get('secret')
            if secret:
                stdin, stdout, stderr = client.exec_command('enable')
                stdin.write(secret + '\n')
                stdin.flush()
                
                # 特権モードへの昇格確認
                output = stdout.read().decode('utf-8', errors='ignore')
                if '#' not in output:
                    logger.error("Failed to enter privileged mode")
                    client.close()
                    return False
            
            self.connection = client
            logger.info(f"SSH connection established to {host}")
            return True
            
        except Exception as e:
            logger.error(f"SSH connection failed to {host}: {e}")
            return False
    
    def _connect_telnet(self) -> bool:
        """Telnet接続を確立"""
        try:
            host = self.device_config['host']
            username = self.device_config['username']
            password = self.device_config.get('password', '')
            
            # Telnet接続（telnetlib3を使用）
            import asyncio
            
            async def _connect_async():
                tn = await telnetlib3.open_connection(
                    host, self.device_config.get('port', 23), 
                    encoding='ascii'
                )
                
                # ログインプロンプト待ち
                output = await tn.read_until(b"login:")
                if b"login:" not in output:
                    logger.error(f"Login prompt not found on {host}")
                    tn.close()
                    return False
                
                # ユーザー名送信
                await tn.write(username.encode('ascii') + b"\n")
                
                # パスワードプロンプト待ち
                output = await tn.read_until(b"Password:")
                if b"Password:" not in output:
                    logger.error(f"Password prompt not found on {host}")
                    tn.close()
                    return False
                
                # パスワード送信
                await tn.write(password.encode('ascii') + b"\n")
                
                # プロンプト待ち
                wait_string = self.device_config.get('wait_string', '#')
                output = await tn.read_until(wait_string.encode('ascii'))
                
                return tn
            
            # 同期処理として実行
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
            tn = loop.run_until_complete(_connect_async())
            
            self.connection = tn
            logger.info(f"Telnet connection established to {host}")
            return True
            
        except Exception as e:
            logger.error(f"Telnet connection failed to {host}: {e}")
            if 'tn' in locals():
                async def _cleanup():
                    await tn.close()
                loop = asyncio.get_event_loop()
                loop.run_until_complete(_cleanup())
            return False
    
    def execute_commands(self, commands: List[str]) -> Dict[str, Any]:
        """
        コマンドを実行し、結果を返す
        
        Args:
            commands: 実行するコマンドリスト
            
        Returns:
            Dict: 実行結果
        """
        if not self.connection:
            if not self.connect():
                return {
                    'success': False,
                    'error': 'Failed to establish connection',
                    'output': '',
                    'error_output': ''
                }
        
        result = {
            'success': True,
            'output': '',
            'error_output': '',
            'command_results': []
        }
        
        try:
            connection_type = self.device_config.get('connection_type', 'ssh').lower()
            device_name = self.device_config.get('hostname', self.device_config.get('host', 'unknown'))
            
            for command in commands:
                command_result = self._execute_single_command(command, connection_type)
                result['command_results'].append(command_result)
                
                if command_result['success']:
                    result['output'] += command_result['output'] + "\n"
                else:
                    result['success'] = False
                    result['error_output'] += command_result['error_output'] + "\n"
                
                # コマンド実行結果をログに記録
                self.log_manager.log_command_execution(device_name, command, command_result)
                    
        except Exception as e:
            error_msg = f"Command execution error: {e}"
            logger.error(error_msg)
            result['success'] = False
            result['error_output'] += error_msg + "\n"
            
        finally:
            self.disconnect()
            
        return result
    
    def _execute_single_command(self, command: str, connection_type: str) -> Dict[str, Any]:
        """
        単一のコマンドを実行
        
        Args:
            command: 実行するコマンド
            connection_type: 接続タイプ ('ssh' or 'telnet')
            
        Returns:
            Dict: コマンド実行結果
        """
        result = {
            'command': command,
            'success': True,
            'output': '',
            'error_output': '',
            'execution_time': 0
        }
        
        start_time = time.time()
        
        try:
            if connection_type == 'ssh':
                command_result = self._execute_ssh_command(command)
            elif connection_type == 'telnet':
                command_result = self._execute_telnet_command(command)
            else:
                raise ValueError(f"Unsupported connection type: {connection_type}")
            
            result.update(command_result)
            
        except Exception as e:
            result['success'] = False
            result['error_output'] = str(e)
            
        finally:
            result['execution_time'] = time.time() - start_time
            
        return result
    
    def _execute_ssh_command(self, command: str) -> Dict[str, Any]:
        """SSHでコマンドを実行"""
        try:
            stdin, stdout, stderr = self.connection.exec_command(command)
            
            # 出力を読み取る
            output = stdout.read().decode('utf-8', errors='ignore')
            error_output = stderr.read().decode('utf-8', errors='ignore')
            
            # プロンプトを待つ
            wait_string = self.device_config.get('wait_string', '#')
            if wait_string:
                # プロンプト待ちの実装（必要に応じて）
                pass
            
            return {
                'output': output,
                'error_output': error_output
            }
            
        except Exception as e:
            return {
                'output': '',
                'error_output': str(e)
            }
    
    def _execute_telnet_command(self, command: str) -> Dict[str, Any]:
        """Telnetでコマンドを実行"""
        try:
            # コマンド送信
            import asyncio
            
            async def _execute_command_async():
                # コマンド送信
                await self.connection.write(command.encode('ascii') + b"\n")
                
                # 出力待ち
                wait_string = self.device_config.get('wait_string', '#')
                output = await self.connection.read_until(wait_string.encode('ascii'))
                output = output.decode('utf-8', errors='ignore')
                
                # プロンプトを除去
                if wait_string and output.endswith(wait_string):
                    output = output[:-len(wait_string)].strip()
                
                return output
            
            # 同期処理として実行
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            output = loop.run_until_complete(_execute_command_async())
            loop.close()
            
            return {
                'output': output,
                'error_output': ''
            }
            
        except Exception as e:
            return {
                'output': '',
                'error_output': str(e)
            }
    
    def disconnect(self):
        """接続を切断"""
        try:
            if self.connection:
                if isinstance(self.connection, paramiko.SSHClient):
                    self.connection.close()
                elif hasattr(self.connection, 'close'):  # telnetlib3の場合
                    import asyncio
                    
                    async def _disconnect_async():
                        await self.connection.close()
                    
                    # 同期処理として実行
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                    loop.run_until_complete(_disconnect_async())
                    loop.close()
                self.connection = None
                logger.info("Connection closed")
        except Exception as e:
            logger.error(f"Error while disconnecting: {e}")
    
    def test_connection(self) -> Dict[str, Any]:
        """
        接続テストを実行
        
        Returns:
            Dict: 接続テスト結果
        """
        test_result = {
            'success': False,
            'message': '',
            'connection_time': 0
        }
        
        start_time = time.time()
        
        try:
            if self.connect():
                test_result['success'] = True
                test_result['message'] = 'Connection successful'
            else:
                test_result['message'] = 'Connection failed'
                
        except Exception as e:
            test_result['message'] = f"Connection error: {e}"
            
        finally:
            test_result['connection_time'] = time.time() - start_time
            self.disconnect()
            
        return test_result
    
    def execute_command_group(self, group_name: str, command_groups: Dict[str, Any]) -> Dict[str, Any]:
        """
        コマンドグループを実行
        
        Args:
            group_name: コマンドグループ名
            command_groups: コマンドグループ設定
            
        Returns:
            実行結果
        """
        if group_name not in command_groups:
            return {
                'success': False,
                'error': f'Command group "{group_name}" not found',
                'output': '',
                'error_output': ''
            }
        
        group_config = command_groups[group_name]
        commands = group_config.get('commands', [])
        
        return self.execute_commands(commands)
    
    def execute_scenario(self, scenario_config: Dict[str, Any], command_groups: Dict[str, Any]) -> Dict[str, Any]:
        """
        シナリオを実行
        
        Args:
            scenario_config: シナリオ設定
            command_groups: コマンドグループ設定
            
        Returns:
            実行結果
        """
        results = []
        commands = scenario_config.get('commands', [])
        
        device_name = self.device_config.get('hostname', self.device_config.get('host', 'unknown'))
        scenario_name = scenario_config.get('name', 'unknown_scenario')
        
        for command_item in commands:
            if isinstance(command_item, str) and command_item in command_groups:
                # コマンドグループの実行
                result = self.execute_command_group(command_item, command_groups)
            else:
                # 単一コマンドの実行
                result = self.execute_commands([command_item])
            
            results.append(result)
        
        # シナリオ実行結果を作成
        scenario_result = {
            'success': all(r.get('success', False) for r in results),
            'results': results,
            'output': '\n'.join(r.get('output', '') for r in results),
            'error_output': '\n'.join(r.get('error_output', '') for r in results),
            'total_commands': len(commands),
            'successful_commands': sum(1 for r in results if r.get('success', False)),
            'failed_commands': sum(1 for r in results if not r.get('success', False))
        }
        
        # シナリオ実行結果をログに記録
        self.log_manager.log_scenario_execution(device_name, scenario_name, scenario_result)
        
        return scenario_result
    
    def validate_device_config(self) -> bool:
        """
        デバイス設定のバリデーション
        
        Returns:
            bool: 設定が有効な場合True
        """
        required_fields = ['host', 'device_type', 'username']
        for field in required_fields:
            if field not in self.device_config:
                logger.error(f"Required field '{field}' is missing")
                return False
        
        # device_typeの検証
        valid_device_types = ['cisco_ios', 'cisco_asa']
        device_type = self.device_config.get('device_type')
        if device_type not in valid_device_types:
            logger.error(f"Invalid device_type: {device_type}")
            return False
        
        return True


def execute_scenario_on_device(device_config: Dict[str, Any], command_groups: Dict[str, List[str]], 
                             scenario_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    シナリオをデバイスで実行
    
    Args:
        device_config: デバイス設定
        command_groups: コマンドグループ設定
        scenario_config: シナリオ設定
        
    Returns:
        Dict: 実行結果
    """
    executor = NetworkDeviceExecutor(device_config)
    
    # 実行結果
    result = {
        'device_name': device_config.get('hostname', device_config.get('host', 'unknown')),
        'device_host': device_config.get('host', 'unknown'),
        'success': False,
        'start_time': datetime.now().isoformat(),
        'end_time': '',
        'total_commands': 0,
        'successful_commands': 0,
        'failed_commands': 0,
        'command_results': [],
        'error_message': ''
    }
    
    try:
        # 実行するコマンドを収集
        commands_to_execute = []
        for command_group_name in scenario_config.get('commands', []):
            if command_group_name in command_groups:
                commands_to_execute.extend(command_groups[command_group_name])
        
        result['total_commands'] = len(commands_to_execute)
        
        if not commands_to_execute:
            result['error_message'] = 'No commands to execute'
            return result
        
        # コマンド実行
        execution_result = executor.execute_commands(commands_to_execute)
        
        # 結果集計
        result['success'] = execution_result['success']
        result['end_time'] = datetime.now().isoformat()
        
        for cmd_result in execution_result.get('command_results', []):
            if cmd_result['success']:
                result['successful_commands'] += 1
            else:
                result['failed_commands'] += 1
            result['command_results'].append(cmd_result)
            
        if not execution_result['success']:
            result['error_message'] = execution_result.get('error_output', 'Unknown error')
            
    except Exception as e:
        result['success'] = False
        result['error_message'] = str(e)
        result['end_time'] = datetime.now().isoformat()
        
    return result


# 便利な関数
def test_device_connection(device_config: Dict[str, Any]) -> Dict[str, Any]:
    """デバイス接続をテスト"""
    executor = NetworkDeviceExecutor(device_config)
    return executor.test_connection()


def get_supported_device_types() -> List[str]:
    """サポートするデバイスタイプを返す"""
    return ['cisco_ios', 'cisco_asa', 'cisco_nxos', 'juniper_junos']


def get_supported_connection_types() -> List[str]:
    """サポートする接続タイプを返す"""
    return ['ssh', 'telnet']
