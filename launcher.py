import os
import sys
import subprocess
import webbrowser
import time
import requests
import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
from pathlib import Path
from typing import Optional, Dict, Any, List

from config_manager import ConfigManager, ConfigError
from server_manager import DjangoServerManager, ViteServerManager, ServerError
from log_manager import LogManager
from environment_manager import EnvironmentManager, EnvironmentError

class SystemLauncherGUI:
    def __init__(self):
        try:
            # 初始化配置管理器
            self.config_manager = ConfigManager('config.yaml')
            if self.config_manager.config is None:
                raise RuntimeError('配置文件加载失败，config为None，请检查config.yaml')
            
            # 初始化日志管理器
            self.logger = LogManager('system_launcher', self.config_manager.config.logging)
            
            # 设置项目路径
            self.project_root = Path(__file__).parent
            self.backend_dir = self.project_root / 'backend'
            self.frontend_dir = self.project_root / 'frontend'
            
            # 初始化环境管理器
            self.env_manager = EnvironmentManager(
                self.project_root,
                self.logger.get_logger()
            )
            
            # 初始化服务器管理器
            self.django_server = DjangoServerManager(
                self.config_manager.config.django,
                self.project_root,
                self.logger.get_logger()
            )
            self.frontend_server = ViteServerManager(
                self.config_manager.config.frontend,
                self.project_root,
                self.logger.get_logger()
            )
            
            # 初始化GUI
            self._init_gui()
            
            self.logger.info('系统启动器初始化完成')
            
            # 检查工作目录
            self._check_working_directory()
            
        except Exception as e:
            # 如果在初始化过程中发生错误，确保显示错误信息
            if hasattr(self, 'log'):
                self.log(f'❌ 初始化失败: {str(e)}')
            raise

    def _init_gui(self):
        """初始化GUI界面"""
        # 创建主窗口
        self.root = tk.Tk()
        self.root.title("PHRL OLE System 启动器")
        self.root.geometry("800x600")

        # 设置样式
        style = ttk.Style()
        style.configure('Success.TButton', background='green')
        style.configure('Warning.TButton', background='orange')

        # 创建主框架
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky="nsew")

        # 创建日志文本框
        self.log_text = scrolledtext.ScrolledText(self.main_frame, height=20)
        self.log_text.grid(row=4, column=0, columnspan=3, pady=10, sticky="ew")

        # 创建按钮组
        self.create_button_groups()

        # 配置窗口大小调整
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=1)

    def create_button_groups(self):
        """创建按钮组"""
        # 环境检查组
        env_group = ttk.LabelFrame(self.main_frame, text="环境检查", padding="5")
        env_group.grid(row=0, column=0, columnspan=3, pady=5, sticky="ew")

        ttk.Button(env_group, text="检查虚拟环境",
                   command=lambda: self.run_in_thread(self.env_manager.check_virtual_env)).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(env_group, text="检查依赖包",
                   command=lambda: self.run_in_thread(self.env_manager.check_python_environment)).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(env_group, text="安装缺失依赖",
                   command=lambda: self.run_in_thread(self.env_manager.install_python_dependencies)).grid(row=0, column=2, padx=5, pady=5)

        # 服务管理组
        service_group = ttk.LabelFrame(self.main_frame, text="服务管理", padding="5")
        service_group.grid(row=1, column=0, columnspan=3, pady=5, sticky="ew")

        ttk.Button(service_group, text="启动Django服务器",
                   command=lambda: self.run_in_thread(self.start_django_server)).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(service_group, text="启动前端服务器",
                   command=lambda: self.run_in_thread(self.start_frontend_server)).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(service_group, text="停止所有服务器",
                   command=lambda: self.run_in_thread(self.stop_all_servers)).grid(row=0, column=2, padx=5, pady=5)

        # 快速访问组
        access_group = ttk.LabelFrame(self.main_frame, text="快速访问", padding="5")
        access_group.grid(row=2, column=0, columnspan=3, pady=5, sticky="ew")

        ttk.Button(access_group, text="打开调试主页",
                   command=self.open_debug_dashboard).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(access_group, text="打开API测试工具",
                   command=self.open_api_tester).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(access_group, text="打开Swagger文档",
                   command=self.open_swagger_docs).grid(row=0, column=2, padx=5, pady=5)

        # 调试工具组
        debug_group = ttk.LabelFrame(self.main_frame, text="调试工具", padding="5")
        debug_group.grid(row=3, column=0, columnspan=3, pady=5, sticky="ew")

        ttk.Button(debug_group, text="Django服务器信息",
                   command=lambda: self.show_server_info('django')).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(debug_group, text="前端服务器信息",
                   command=lambda: self.show_server_info('frontend')).grid(row=0, column=1, padx=5, pady=5)

    def log(self, message: str) -> None:
        """显示日志消息到GUI"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)

    def run_in_thread(self, func) -> None:
        """在新线程中运行函数"""
        thread = threading.Thread(target=func)
        thread.daemon = True
        thread.start()

    def _check_working_directory(self) -> bool:
        """检查工作目录和项目文件完整性"""
        try:
            # 检查backend目录
            if not self.backend_dir.is_dir():
                self.log("❌ 未找到backend目录")
                return False

            # 检查frontend目录
            if not self.frontend_dir.is_dir():
                self.log("❌ 未找到frontend目录")
                return False

            # 检查关键文件
            required_files = {
                self.backend_dir / 'manage.py': '后端入口文件',
                self.frontend_dir / 'package.json': '前端配置文件',
                self.frontend_dir / 'vite.config.ts': '前端构建配置文件'
            }

            for file_path, description in required_files.items():
                if not file_path.is_file():
                    self.log(f"❌ 未找到{description}: {file_path}")
                    return False

            self.log("✅ 项目文件检查完成")
            return True

        except Exception as e:
            self.log(f"❌ 检查工作目录失败: {str(e)}")
            return False

    def start_django_server(self) -> bool:
        """启动Django服务器"""
        try:
            if not self._check_working_directory():
                return False

            # 检查 Python 环境
            env_manager = EnvironmentManager(self.project_root, self.logger.get_logger())
            if not env_manager.check_python_environment():
                return False

            self.log("🚀 正在启动Django服务器...")
            if self.django_server.start():
                self.log("✅ Django服务器启动成功")
                return True
            else:
                self.log("❌ Django服务器启动失败")
                return False

        except ServerError as e:
            self.log(f"❌ {str(e)}")
            return False
        except Exception as e:
            self.log(f"❌ 启动Django服务器时发生错误: {str(e)}")
            return False

    def start_frontend_server(self) -> bool:
        """启动前端服务器"""
        try:
            if not self._check_working_directory():
                return False

            # 检查 Node.js 环境
            env_manager = EnvironmentManager(self.project_root, self.logger.get_logger())
            if not env_manager.check_node_environment():
                return False

            self.log("🚀 正在启动前端服务器...")
            if self.frontend_server.start():
                self.log("✅ 前端服务器启动成功")
                return True
            else:
                self.log("❌ 前端服务器启动失败")
                return False

        except ServerError as e:
            self.log(f"❌ {str(e)}")
            return False
        except Exception as e:
            self.log(f"❌ 启动前端服务器时发生错误: {str(e)}")
            return False

    def stop_all_servers(self) -> bool:
        """停止所有服务器"""
        success = True

        if self.django_server.stop():
            self.log("✅ Django服务器已停止")
        else:
            self.log("❌ 停止Django服务器失败")
            success = False

        if self.frontend_server.stop():
            self.log("✅ 前端服务器已停止")
        else:
            self.log("❌ 停止前端服务器失败")
            success = False

        return success

    def open_debug_dashboard(self) -> None:
        """打开调试主页（强制只打开debug-dashboard.html）"""
        try:
            url = 'http://localhost:5182/debug-dashboard.html'
            webbrowser.open(url)
            self.log("🌐 正在打开调试主页...")
            self.logger.debug(f"成功打开调试主页: {url}")
        except Exception as e:
            self.log(f"❌ 打开浏览器失败: {str(e)}")

    def open_api_tester(self) -> None:
        """打开API测试工具"""
        try:
            if self.config_manager.config is None:
                self.log("❌ 配置未加载，无法打开API测试工具")
                return
            url = f'http://{self.config_manager.config.django.host}:{self.config_manager.config.django.port}/api-tester.html'
            webbrowser.open(url)
            self.log("🌐 正在打开API测试工具...")
            self.logger.debug(f"打开API测试工具: {url}")
        except Exception as e:
            self.log(f"❌ 打开API测试工具失败: {str(e)}")

    def open_swagger_docs(self) -> None:
        """打开Swagger文档"""
        try:
            if self.config_manager.config is None:
                self.log("❌ 配置未加载，无法打开Swagger文档")
                return
            url = f'http://{self.config_manager.config.django.host}:{self.config_manager.config.django.port}/swagger/'
            webbrowser.open(url)
            self.log("🌐 正在打开Swagger文档...")
            self.logger.debug(f"打开Swagger文档: {url}")
        except Exception as e:
            self.log(f"❌ 打开Swagger文档失败: {str(e)}")

    def show_server_info(self, server_type: str) -> None:
        """显示服务器信息"""
        try:
            if self.config_manager.config is None:
                self.log("❌ 配置未加载，无法显示服务器信息")
                return
            # 获取服务器状态
            if server_type == 'django':
                server = self.django_server
                config = self.config_manager.config.django
            else:
                server = self.frontend_server
                config = self.config_manager.config.frontend
            info = {
                '服务器类型': server_type.title(),
                '运行状态': '运行中' if server.is_running() else '已停止',
                '主机地址': config.host,
                '端口': config.port,
                'PID': server.process.pid if server.process else 'N/A'
            }
            # 创建新窗口显示信息
            info_window = tk.Toplevel(self.root)
            info_window.title(f"{server_type.title()}服务器信息")
            info_window.geometry("400x300")
            # 创建文本区域
            info_text = scrolledtext.ScrolledText(info_window, wrap=tk.WORD)
            info_text.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
            # 显示信息
            for key, value in info.items():
                info_text.insert(tk.END, f"{key}: {value}\n")
            # 禁用编辑
            info_text.configure(state='disabled')
            # 刷新按钮
            ttk.Button(info_window, text="刷新",
                      command=lambda: self._refresh_server_info(info_text, server_type)).pack(pady=5)
            self.logger.debug(f"显示{server_type}服务器信息窗口")
        except Exception as e:
            self.log(f"❌ 获取服务器信息失败: {str(e)}")

    def _refresh_server_info(self, info_text: scrolledtext.ScrolledText, server_type: str) -> None:
        """刷新服务器信息"""
        try:
            info_text.configure(state='normal')
            info_text.delete(1.0, tk.END)
            self.show_server_info(server_type)
            info_text.configure(state='disabled')
        except Exception as e:
            self.log(f"❌ 刷新服务器信息失败: {str(e)}")

if __name__ == '__main__':
    try:
        app = SystemLauncherGUI()
        app.root.mainloop()
    except Exception as e:
        print(f"❌ 程序启动失败: {str(e)}")
        sys.exit(1)