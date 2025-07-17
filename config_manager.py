import os
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

@dataclass
class ServerConfig:
    host: str
    port: int

@dataclass
class TimeoutConfig:
    server_start: int
    health_check_interval: int

@dataclass
class EnvironmentConfig:
    python_min_version: List[int]
    node_min_version: int

@dataclass
class LoggingConfig:
    directory: str
    level: str
    max_size: int
    backup_count: int

@dataclass
class SecurityConfig:
    enable_process_check: bool
    encrypt_config: bool
    confirm_sensitive_operations: bool

@dataclass
class SystemConfig:
    django: ServerConfig
    frontend: ServerConfig
    timeout: TimeoutConfig
    environment: EnvironmentConfig
    logging: LoggingConfig
    security: SecurityConfig

class ConfigManager:
    def __init__(self, config_path: str = 'config.yaml'):
        self.config_path = Path(config_path)
        self.config: Optional[SystemConfig] = None
        self.load_config()

    def load_config(self) -> None:
        """加载配置文件"""
        try:
            if not self.config_path.exists():
                raise FileNotFoundError(f'配置文件不存在: {self.config_path}')

            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)

            # 验证配置
            self._validate_config(config_data)

            # 创建配置对象
            self.config = self._create_config_object(config_data)

        except Exception as e:
            raise ConfigError(f'加载配置文件失败: {str(e)}')

    def _validate_config(self, config: Dict[str, Any]) -> None:
        """验证配置数据的完整性和有效性"""
        required_fields = {
            'server': {'django': ['host', 'port'], 'frontend': ['host', 'port']},
            'timeout': ['server_start', 'health_check_interval'],
            'environment': {'python': ['min_version'], 'node': ['min_version']},
            'logging': ['directory', 'level', 'max_size', 'backup_count'],
            'security': ['enable_process_check', 'encrypt_config', 'confirm_sensitive_operations']
        }

        def check_fields(data: Dict[str, Any], fields: Dict[str, Any], path: str = ''):
            for key, value in fields.items():
                if key not in data:
                    raise ConfigError(f'缺少必需的配置项: {path}{key}')
                
                if isinstance(value, dict):
                    if not isinstance(data[key], dict):
                        raise ConfigError(f'配置项类型错误: {path}{key}')
                    check_fields(data[key], value, f'{path}{key}.')
                elif isinstance(value, list):
                    for field in value:
                        if field not in data[key]:
                            raise ConfigError(f'缺少必需的配置项: {path}{key}.{field}')

        check_fields(config, required_fields)

    def _create_config_object(self, config_data: Dict[str, Any]) -> SystemConfig:
        """创建配置对象"""
        try:
            django_config = ServerConfig(
                host=config_data['server']['django']['host'],
                port=config_data['server']['django']['port']
            )

            frontend_config = ServerConfig(
                host=config_data['server']['frontend']['host'],
                port=config_data['server']['frontend']['port']
            )

            timeout_config = TimeoutConfig(
                server_start=config_data['timeout']['server_start'],
                health_check_interval=config_data['timeout']['health_check_interval']
            )

            environment_config = EnvironmentConfig(
                python_min_version=config_data['environment']['python']['min_version'],
                node_min_version=config_data['environment']['node']['min_version']
            )

            logging_config = LoggingConfig(
                directory=config_data['logging']['directory'],
                level=config_data['logging']['level'],
                max_size=config_data['logging']['max_size'],
                backup_count=config_data['logging']['backup_count']
            )

            security_config = SecurityConfig(
                enable_process_check=config_data['security']['enable_process_check'],
                encrypt_config=config_data['security']['encrypt_config'],
                confirm_sensitive_operations=config_data['security']['confirm_sensitive_operations']
            )

            return SystemConfig(
                django=django_config,
                frontend=frontend_config,
                timeout=timeout_config,
                environment=environment_config,
                logging=logging_config,
                security=security_config
            )

        except Exception as e:
            raise ConfigError(f'创建配置对象失败: {str(e)}')

class ConfigError(Exception):
    """配置错误异常类"""
    pass