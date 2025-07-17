import os
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from config_manager import LoggingConfig

class LogManager:
    """日志管理类，实现结构化日志记录"""
    def __init__(self, name: str, config: LoggingConfig):
        self.name = name
        self.config = config
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        # 创建日志目录
        log_dir = Path(self.config.directory)
        log_dir.mkdir(exist_ok=True)

        # 创建日志记录器
        logger = logging.getLogger(self.name)
        logger.setLevel(self._get_log_level())

        # 创建文件处理器
        log_file = log_dir / f"{self.name}_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=self.config.max_size,
            backupCount=self.config.backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(self._get_log_level())

        # 创建格式化器
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] [%(name)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)

        # 添加处理器
        logger.addHandler(file_handler)

        return logger

    def _get_log_level(self) -> int:
        """获取日志级别"""
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        return level_map.get(self.config.level.upper(), logging.INFO)

    def set_level(self, level: str) -> None:
        """动态设置日志级别"""
        new_level = self._get_log_level()
        self.logger.setLevel(new_level)
        for handler in self.logger.handlers:
            handler.setLevel(new_level)

    def _format_extra(self, extra: Optional[Dict[str, Any]] = None) -> str:
        """格式化额外信息"""
        if not extra:
            return ''
        return ' '.join(f'{k}={v}' for k, v in extra.items())

    def debug(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """记录调试级别日志"""
        extra_str = self._format_extra(extra)
        self.logger.debug(f'{message} {extra_str}'.strip())

    def info(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """记录信息级别日志"""
        extra_str = self._format_extra(extra)
        self.logger.info(f'{message} {extra_str}'.strip())

    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """记录警告级别日志"""
        extra_str = self._format_extra(extra)
        self.logger.warning(f'{message} {extra_str}'.strip())

    def error(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """记录错误级别日志"""
        extra_str = self._format_extra(extra)
        self.logger.error(f'{message} {extra_str}'.strip())

    def critical(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """记录严重错误级别日志"""
        extra_str = self._format_extra(extra)
        self.logger.critical(f'{message} {extra_str}'.strip())

    def get_logger(self) -> logging.Logger:
        """获取日志记录器"""
        return self.logger