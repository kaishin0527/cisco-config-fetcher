
"""
設定管理モジュール
複数のYAML設定ファイルを一元管理し、キャッシュ機能を提供
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class ConfigManager:
    """設定管理シングルトンクラス"""
    
    _instance = None
    _configs: Dict[str, Dict[str, Any]] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.config_dir = Path(__file__).parent
            self._initialized = True
    
    def load_config(self, config_type: str, force_reload: bool = False) -> Dict[str, Any]:
        """
        設定ファイルを読み込み、キャッシュを返す
        
        Args:
            config_type: 設定タイプ ('devices', 'command_groups', 'scenarios')
            force_reload: 強制的に再読み込みするかどうか
            
        Returns:
            設定データの辞書
        """
        if config_type not in self._configs or force_reload:
            config_file = self.config_dir / f"{config_type}.yaml"
            
            if not config_file.exists():
                logger.warning(f"設定ファイルが存在しません: {config_file}")
                self._configs[config_type] = {}
            else:
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        self._configs[config_type] = yaml.safe_load(f) or {}
                    logger.info(f"設定ファイルを読み込みました: {config_file}")
                except Exception as e:
                    logger.error(f"設定ファイルの読み込みに失敗しました: {config_file}, エラー: {e}")
                    self._configs[config_type] = {}
        
        return self._configs[config_type]
    
    def get_devices(self) -> Dict[str, Any]:
        """デバイス設定を取得"""
        return self.load_config('devices')
    
    def get_command_groups(self) -> Dict[str, Any]:
        """コマンドグループ設定を取得"""
        return self.load_config('command_groups')
    
    def get_scenarios(self) -> Dict[str, Any]:
        """シナリオ設定を取得"""
        return self.load_config('scenarios')
    
    def get_device(self, device_name: str) -> Optional[Dict[str, Any]]:
        """特定のデバイス設定を取得"""
        devices = self.get_devices()
        return devices.get(device_name)
    
    def get_command_group(self, group_name: str) -> Optional[Dict[str, Any]]:
        """特定のコマンドグループを取得"""
        groups = self.get_command_groups()
        return groups.get(group_name)
    
    def get_scenario(self, scenario_name: str) -> Optional[Dict[str, Any]]:
        """特定のシナリオを取得"""
        scenarios = self.get_scenarios()
        return scenarios.get(scenario_name)
    
    def save_config(self, config_type: str, config_data: Dict[str, Any]):
        """
        設定データをファイルに保存
        
        Args:
            config_type: 設定タイプ ('devices', 'command_groups', 'scenarios')
            config_data: 保存する設定データ
        """
        config_file = self.config_dir / f"{config_type}.yaml"
        
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
            
            # キャッシュを更新
            self._configs[config_type] = config_data
            
            logger.info(f"設定ファイルを保存しました: {config_file}")
        except Exception as e:
            logger.error(f"設定ファイルの保存に失敗しました: {config_file}, エラー: {e}")
            raise
    
    def validate_config(self, config_type: str) -> bool:
        """設定ファイルのバリデーション"""
        config = self.load_config(config_type)
        
        if config_type == 'devices':
            required_fields = ['host', 'device_type', 'username']
            for device_name, device_config in config.items():
                for field in required_fields:
                    if field not in device_config:
                        logger.error(f"デバイス '{device_name}' に必須フィールド '{field}' がありません")
                        return False
                # 環境変数の参照をチェック
                if 'password' in device_config and isinstance(device_config['password'], str):
                    if device_config['password'].startswith('!ENV ${') and device_config['password'].endswith('}'):
                        env_var = device_config['password'][6:-1]
                        if env_var not in os.environ:
                            logger.warning(f"デバイス '{device_name}' で参照されている環境変数 '{env_var}' が設定されていません")
                if 'secret' in device_config and isinstance(device_config['secret'], str):
                    if device_config['secret'].startswith('!ENV ${') and device_config['secret'].endswith('}'):
                        env_var = device_config['secret'][6:-1]
                        if env_var not in os.environ:
                            logger.warning(f"デバイス '{device_name}' で参照されている環境変数 '{env_var}' が設定されていません")
        elif config_type == 'command_groups':
            for group_name, group_config in config.items():
                if 'commands' not in group_config:
                    logger.error(f"コマンドグループ '{group_name}' に 'commands' フィールドがありません")
                    return False
                if not isinstance(group_config['commands'], list):
                    logger.error(f"コマンドグループ '{group_name}' の 'commands' はリストである必要があります")
                    return False
        elif config_type == 'scenarios':
            for scenario_name, scenario_config in config.items():
                if 'devices' not in scenario_config or 'commands' not in scenario_config:
                    logger.error(f"シナリオ '{scenario_name}' に必須フィールドが不足しています")
                    return False
                if not isinstance(scenario_config['devices'], list):
                    logger.error(f"シナリオ '{scenario_name}' の 'devices' はリストである必要があります")
                    return False
                if not isinstance(scenario_config['commands'], list):
                    logger.error(f"シナリオ '{scenario_name}' の 'commands' はリストである必要があります")
                    return False
        
        return True
    
    def validate_all_configs(self) -> Dict[str, bool]:
        """すべての設定ファイルをバリデーション"""
        results = {}
        for config_type in ['devices', 'command_groups', 'scenarios']:
            results[config_type] = self.validate_config(config_type)
        return results
    
    def get_config_summary(self) -> Dict[str, Any]:
        """設定のサマリーを取得"""
        summary = {}
        for config_type in ['devices', 'command_groups', 'scenarios']:
            config = self.load_config(config_type)
            summary[config_type] = {
                'count': len(config),
                'items': list(config.keys())
            }
        return summary
    
    def reload_all_configs(self):
        """すべての設定を再読み込み"""
        self._configs.clear()
        logger.info("すべての設定を再読み込みしました")

# グローバルインスタンス
config_manager = ConfigManager()

# 便利な関数
def get_devices() -> Dict[str, Any]:
    """デバイス設定を取得する便利関数"""
    return config_manager.get_devices()

def get_command_groups() -> Dict[str, Any]:
    """コマンドグループ設定を取得する便利関数"""
    return config_manager.get_command_groups()

def get_scenarios() -> Dict[str, Any]:
    """シナリオ設定を取得する便利関数"""
    return config_manager.get_scenarios()
