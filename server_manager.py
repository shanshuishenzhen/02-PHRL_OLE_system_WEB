import os
import sys
import socket
import subprocess
import time
import requests
import logging
import threading
from abc import ABC, abstractmethod
from typing import Optional, Tuple
from pathlib import Path
from config_manager import ServerConfig, ConfigError

class ServerError(Exception):
    """服务器错误异常类"""
    pass

class ServerManager(ABC):
    """服务器管理基类"""
    def __init__(self, server_config: ServerConfig, project_root: Path, logger: logging.Logger):
        self.config = server_config
        self.project_root = project_root
        self.logger = logger
        self.process: Optional[subprocess.Popen] = None
        self.health_check_thread: Optional[threading.Thread] = None

    @abstractmethod
    def start(self) -> bool:
        """启动服务器"""
        pass

    @abstractmethod
    def stop(self) -> bool:
        """停止服务器"""
        pass

    def is_running(self) -> bool:
        """检查服务器是否正在运行"""
        return self.process is not None and self.process.poll() is None

    def check_port_available(self) -> bool:
        """检查端口是否可用"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                try:
                    s.bind(('0.0.0.0', self.config.port))
                    s.listen(1)
                    return True
                except socket.error:
                    return False
        except Exception:
            return False

    def terminate_port_process(self) -> bool:
        """终止占用端口的进程"""
        try:
            result = subprocess.run(
                ['powershell', '-NoProfile', '-Command',
                 f'Stop-Process -Id (Get-NetTCPConnection -LocalPort {self.config.port}).OwningProcess -Force'],
                capture_output=True
            )
            return result.returncode == 0
        except Exception:
            return False

    def wait_for_server(self, url: str, timeout: int = 180) -> bool:
        """等待服务器响应"""
        start_time = time.time()
        retry_interval = 5  # 重试间隔（秒）
        max_retries = 3  # 单次检查的最大重试次数
        connection_timeout = 10  # 连接超时时间（秒）

        while time.time() - start_time < timeout:
            for retry in range(max_retries):
                try:
                    response = requests.get(
                        url,
                        timeout=connection_timeout,
                        headers={'Cache-Control': 'no-cache'}
                    )
                    
                    if response.status_code == 200:
                        self.logger.info(f'服务器在 {url} 已就绪')
                        return True
                    elif response.status_code >= 500:
                        self.logger.warning(
                            f'服务器返回错误状态码: {response.status_code}，'
                            f'重试次数: {retry + 1}/{max_retries}'
                        )
                        break
                    else:
                        self.logger.warning(
                            f'服务器返回非预期状态码: {response.status_code}，'
                            f'重试次数: {retry + 1}/{max_retries}'
                        )
                except requests.Timeout:
                    self.logger.warning(
                        f'服务器响应超时（{connection_timeout}秒），'
                        f'重试次数: {retry + 1}/{max_retries}'
                    )
                except requests.ConnectionError:
                    self.logger.warning(
                        f'无法连接到服务器，'
                        f'重试次数: {retry + 1}/{max_retries}'
                    )
                except requests.RequestException as e:
                    self.logger.warning(
                        f'检查服务器状态时出错: {str(e)}，'
                        f'重试次数: {retry + 1}/{max_retries}'
                    )
                
                if retry < max_retries - 1:
                    self.logger.info(f'等待 {retry_interval} 秒后进行下一次重试...')
                    time.sleep(retry_interval)
            
            # 一轮重试结束，检查进程状态
            if self.process and self.process.poll() is not None:
                stdout, stderr = self.process.communicate()
                self.logger.error(
                    f'服务器进程已退出，退出码: {self.process.returncode}\n'
                    f'标准输出: {stdout}\n'
                    f'错误输出: {stderr}'
                )
                return False
            
            # 等待更长时间后继续下一轮检查
            self.logger.info(f'当前轮次检查失败，等待 {retry_interval * 2} 秒后进行下一轮检查...')
            time.sleep(retry_interval * 2)

        elapsed_time = time.time() - start_time
        self.logger.error(
            f'等待服务器启动超时（{int(elapsed_time)}秒），'
            f'目标地址: {url}'
        )
        return False

    def monitor_process_output(self) -> None:
        """监控进程输出"""
        if not self.process:
            return

        while self.process.poll() is None:
            if self.process.stdout:
                try:
                    line = self.process.stdout.readline()
                    if line:
                        self.logger.info(f'[{self.__class__.__name__}] {line.strip()}')
                except UnicodeDecodeError:
                    self.logger.warning(f'[{self.__class__.__name__}] 无法解码标准输出内容')

            if self.process.stderr:
                try:
                    line = self.process.stderr.readline()
                    if line:
                        self.logger.error(f'[{self.__class__.__name__}] {line.strip()}')
                except UnicodeDecodeError:
                    self.logger.warning(f'[{self.__class__.__name__}] 无法解码错误输出内容')

class DjangoServerManager(ServerManager):
    """Django服务器管理类"""
    def __init__(self, server_config: ServerConfig, project_root: Path, logger: logging.Logger):
        super().__init__(server_config, project_root, logger)
        self.backend_dir = project_root / 'backend'

    def start(self) -> bool:
        if self.is_running():
            self.logger.warning('Django服务器已在运行')
            return True

        if not self.check_port_available():
            if not self.terminate_port_process():
                raise ServerError(f'端口{self.config.port}被占用且无法释放')

        try:
            self.process = subprocess.Popen(
                [sys.executable, 'manage.py', 'runserver',
                 f'{self.config.host}:{self.config.port}'],
                cwd=str(self.backend_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8'
            )

            if self.process.poll() is not None:
                stdout, stderr = self.process.communicate()
                raise ServerError(f'Django服务器启动失败:\n{stderr if stderr else stdout}')

            server_url = f'http://{self.config.host}:{self.config.port}/admin/'
            if not self.wait_for_server(server_url):
                raise ServerError('Django服务器启动超时')

            threading.Thread(target=self.monitor_process_output, daemon=True).start()
            return True

        except Exception as e:
            raise ServerError(f'启动Django服务器失败: {str(e)}')

    def stop(self) -> bool:
        if not self.process:
            return True

        try:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None
            return True
        except Exception as e:
            self.logger.error(f'停止Django服务器失败: {str(e)}')
            return False

class ViteServerManager(ServerManager):
    """Vite服务器管理类"""
    def __init__(self, server_config: ServerConfig, project_root: Path, logger: logging.Logger):
        super().__init__(server_config, project_root, logger)
        self.frontend_dir = project_root / 'frontend'

    def check_dependencies(self) -> bool:
        """检查前端项目依赖"""
        try:
            # 检查 node_modules 目录是否存在
            if not (self.frontend_dir / 'node_modules').exists():
                self.logger.info('正在安装前端依赖...')
                result = subprocess.run(
                    ['npm', 'install'],
                    cwd=str(self.frontend_dir),
                    capture_output=True,
                    text=True,
                    encoding='utf-8'
                )
                if result.returncode != 0:
                    raise ServerError(f'安装前端依赖失败:\n{result.stderr}')
                self.logger.info('前端依赖安装完成')
            return True
        except Exception as e:
            raise ServerError(f'检查前端依赖失败: {str(e)}')

    def start(self) -> bool:
        if self.is_running():
            self.logger.warning('Vite服务器已在运行')
            return True

        if not self.check_port_available():
            if not self.terminate_port_process():
                raise ServerError(f'端口{self.config.port}被占用且无法释放')

        try:
            # 检查并安装依赖
            self.check_dependencies()

            # 设置环境变量
            env = os.environ.copy()
            env['VITE_HOST'] = 'localhost'
            env['VITE_PORT'] = '5182'
            env['NODE_ENV'] = 'development'

            # 启动开发服务器
            self.process = subprocess.Popen(
                ['npm', 'run', 'dev'],
                cwd=str(self.frontend_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                env=env,
                shell=True
            )

            # 启动输出监控线程
            threading.Thread(target=self.monitor_process_output, daemon=True).start()

            # 等待服务器就绪
            server_url = f'http://{self.config.host}:{self.config.port}/debug-dashboard'
            start_time = time.time()
            max_wait_time = 180  # 最大等待时间（秒）

            while time.time() - start_time < max_wait_time:
                if self.process.poll() is not None:
                    stdout, stderr = self.process.communicate()
                    raise ServerError(f'Vite服务器启动失败:\n{stderr if stderr else stdout}')

                try:
                    response = requests.get(server_url, timeout=5)
                    if response.status_code == 200:
                        self.logger.info(f'Vite服务器已在 {server_url} 启动')
                        return True
                except requests.RequestException:
                    time.sleep(2)
                    continue

            self.stop()
            raise ServerError('Vite服务器启动超时')

        except Exception as e:
            if self.process:
                self.stop()
            raise ServerError(f'启动Vite服务器失败: {str(e)}')

    def stop(self) -> bool:
        if not self.process:
            return True

        try:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None
            return True
        except Exception as e:
            self.logger.error(f'停止Vite服务器失败: {str(e)}')
            return False