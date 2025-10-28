import sys
import time
import subprocess
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field

@dataclass
class PythonEnvironment:
    """Python环境配置"""
    min_version: Tuple[int, int] = (3, 8)
    required_packages: List[str] = field(default_factory=list)

@dataclass
class NodeEnvironment:
    """Node.js环境配置"""
    min_version: int = 16
    required_packages: Dict[str, List[str]] = field(default_factory=dict)

class EnvironmentError(Exception):
    """环境错误异常基类"""
    def __init__(self, message: Optional[str] = None, error_type: Optional[str] = None):
        super().__init__(message)
        self.error_type = error_type

class PackageNotFoundError(EnvironmentError):
    """包未找到错误"""
    def __init__(self, package_name: str):
        super().__init__(f"未找到包：{package_name}", "package_not_found")
        self.package_name = package_name

class VersionMismatchError(EnvironmentError):
    """版本不匹配错误"""
    def __init__(self, package_name: str, current_version: str, required_version: str):
        super().__init__(
            f"包版本不匹配：{package_name} (当前版本：{current_version}, 需要版本：{required_version})",
            "version_mismatch"
        )
        self.package_name = package_name
        self.current_version = current_version
        self.required_version = required_version

class EnvironmentNotFoundError(EnvironmentError):
    """环境未找到错误"""
    def __init__(self, env_type: str):
        super().__init__(f"未找到{env_type}环境", "environment_not_found")
        self.env_type = env_type

class ConfigurationError(EnvironmentError):
    """配置错误"""
    def __init__(self, config_name: str, reason: str):
        super().__init__(f"配置错误 {config_name}：{reason}", "configuration_error")
        self.config_name = config_name
        self.reason = reason

class EnvironmentManager:
    """环境管理器"""
    def __init__(self, project_root: Path, logger, config_path: Optional[Path] = None):
        self.project_root = project_root
        self.backend_dir = project_root / 'backend'
        self.frontend_dir = project_root / 'frontend'
        self.logger = logger
        self.config_path = config_path or (project_root / 'config.yaml')

        # 加载环境配置
        self._load_environment_config()

    def _load_environment_config(self):
        """从配置文件加载环境配置"""
        try:
            if not self.config_path.exists():
                self.logger.warning(f"配置文件 {self.config_path} 不存在，使用默认配置")
                self._use_default_config()
                return

            import yaml
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
            except yaml.YAMLError as e:
                raise ConfigurationError('config.yaml', f'YAML解析错误：{str(e)}')

            # 验证配置结构
            if not isinstance(config, dict):
                raise ConfigurationError('config.yaml', '配置文件格式错误')

            env_config = config.get('environment', {})
            python_config = env_config.get('python', {})
            node_config = env_config.get('node', {})

            # 初始化Python环境配置
            self.python_env = PythonEnvironment(
                min_version=tuple(python_config.get('min_version', (3, 8))),
                required_packages=python_config.get('required_packages', [
                    'django',
                    'djangorestframework',
                    'django-cors-headers',
                    'channels',
                    'daphne',
                    'mysqlclient',
                    'pillow',
                    'python-dotenv',
                    'requests'
                ])
            )

            # 初始化Node.js环境配置
            self.node_env = NodeEnvironment(
                min_version=node_config.get('min_version', 16),
                required_packages=node_config.get('required_packages', {
                    'dependencies': [
                        'react',
                        'react-dom',
                        'react-router-dom',
                        'antd',
                        '@ant-design/icons',
                        'axios'
                    ],
                    'devDependencies': [
                        'vite',
                        '@vitejs/plugin-react',
                        'typescript',
                        '@types/react',
                        '@types/react-dom'
                    ]
                })
            )

            self.logger.info('环境配置加载成功')

        except Exception as e:
            self.logger.error(f'加载环境配置失败：{str(e)}')
            self.logger.info('使用默认配置')
            self._use_default_config()

    def _use_default_config(self):
        """使用默认环境配置"""
        self.python_env = PythonEnvironment(
            min_version=(3, 8),
            required_packages=[
                'django',
                'djangorestframework',
                'django-cors-headers',
                'channels',
                'daphne',
                'mysqlclient',
                'pillow',
                'python-dotenv',
                'requests'
            ]
        )

        self.node_env = NodeEnvironment(
            min_version=16,
            required_packages={
                'dependencies': [
                    'react',
                    'react-dom',
                    'react-router-dom',
                    'antd',
                    '@ant-design/icons',
                    'axios'
                ],
                'devDependencies': [
                    'vite',
                    '@vitejs/plugin-react',
                    'typescript',
                    '@types/react',
                    '@types/react-dom'
                ]
            }
        )

    def check_virtual_env(self) -> bool:
        """检查虚拟环境"""
        try:
            if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
                self.logger.info(f"虚拟环境已激活: {sys.prefix}")
                return True
            else:
                self.logger.error("虚拟环境未激活")
                return False
        except Exception as e:
            self.logger.error(f"检查虚拟环境失败: {str(e)}")
            return False

    def check_python_environment(self, max_retries: int = 3) -> bool:
        """检查Python环境"""
        retry_count = 0
        while retry_count < max_retries:
            try:
                # 检查Python版本
                version = sys.version_info
                if version.major < self.python_env.min_version[0] or \
                   (version.major == self.python_env.min_version[0] and \
                    version.minor < self.python_env.min_version[1]):
                    raise VersionMismatchError(
                        'Python',
                        f"{version.major}.{version.minor}.{version.micro}",
                        f"{self.python_env.min_version[0]}.{self.python_env.min_version[1]}"
                    )

                # 检查pip是否可用
                result = subprocess.run(
                    [sys.executable, '-m', 'pip', '--version'],
                    capture_output=True,
                    text=True,
                    encoding='utf-8'
                )
                if result.returncode != 0:
                    raise EnvironmentNotFoundError('pip')

                # 检查必要的Python包
                installed_packages = subprocess.run(
                    [sys.executable, '-m', 'pip', 'list', '--format=json'],
                    capture_output=True,
                    text=True,
                    encoding='utf-8'
                )

                if installed_packages.returncode != 0:
                    raise ConfigurationError('pip', '无法获取已安装的包信息')

                try:
                    installed = {pkg['name'].lower(): pkg['version'] 
                               for pkg in json.loads(installed_packages.stdout)}
                except json.JSONDecodeError:
                    raise ConfigurationError('pip', '解析已安装包信息失败')

                # 检查包版本兼容性
                missing_packages = []
                version_mismatch = []
                compatible_packages = []
                for pkg in self.python_env.required_packages:
                    pkg_name = pkg.split('==')[0].strip().lower()
                    if pkg_name not in installed:
                        # 检查是否可以安装指定版本
                        try:
                            pkg_info = subprocess.run(
                                [sys.executable, '-m', 'pip', 'install', pkg, '--dry-run'],
                                capture_output=True,
                                text=True,
                                encoding='utf-8'
                            )
                            if pkg_info.returncode == 0:
                                missing_packages.append(pkg)
                            else:
                                # 尝试获取兼容版本
                                pkg_info = subprocess.run(
                                    [sys.executable, '-m', 'pip', 'install', pkg_name, '--dry-run'],
                                    capture_output=True,
                                    text=True,
                                    encoding='utf-8'
                                )
                                if pkg_info.returncode == 0:
                                    compatible_packages.append(pkg_name)
                                else:
                                    missing_packages.append(pkg)
                        except Exception:
                            missing_packages.append(pkg)
                    elif '==' in pkg:
                        required_version = pkg.split('==')[1].strip()
                        current_version = installed[pkg_name]
                        from packaging.version import parse as parse_version
                        if parse_version(current_version) != parse_version(required_version):
                            # 检查是否有兼容版本
                            try:
                                pkg_info = subprocess.run(
                                    [sys.executable, '-m', 'pip', 'install', pkg_name, '--dry-run'],
                                    capture_output=True,
                                    text=True,
                                    encoding='utf-8'
                                )
                                if pkg_info.returncode == 0:
                                    compatible_packages.append(pkg_name)
                                else:
                                    version_mismatch.append((pkg_name, current_version, required_version))
                            except Exception:
                                version_mismatch.append((pkg_name, current_version, required_version))

                if missing_packages or version_mismatch:
                    error_msg = ""
                    if missing_packages:
                        error_msg += f"缺失的包: {', '.join(missing_packages)}\n"
                    if version_mismatch:
                        mismatch_info = '\n'.join(
                            f"  - {pkg}: 当前版本 {current} 与要求版本 {required} 不兼容"
                            for pkg, current, required in version_mismatch
                        )
                        error_msg += f"版本不匹配的包:\n{mismatch_info}"
                    if compatible_packages:
                        error_msg += f"\n以下包将使用兼容版本安装: {', '.join(compatible_packages)}"
                    raise PackageNotFoundError(error_msg.strip())

                self.logger.info("✅ Python环境检查通过")
                self.logger.debug("已安装的包版本信息：")
                for pkg in self.python_env.required_packages:
                    pkg_name = pkg.split('==')[0].strip().lower()
                    self.logger.debug(f"  - {pkg_name}: {installed[pkg_name]}")
                return True

            except (EnvironmentNotFoundError, VersionMismatchError, 
                    PackageNotFoundError, ConfigurationError) as e:
                self.logger.error(f"❌ {str(e)}")
                return False
            except Exception as e:
                self.logger.warning(f"⚠️ 检查失败 (尝试 {retry_count + 1}/{max_retries}): {str(e)}")
                retry_count += 1
                if retry_count < max_retries:
                    self.logger.info(f"等待 {retry_count * 2} 秒后重试...")
                    time.sleep(retry_count * 2)
                continue

        self.logger.error(f"❌ Python环境检查失败，已重试 {max_retries} 次")
        return False

    def check_node_environment(self, max_retries: int = 3) -> bool:
        """检查Node.js环境和前端依赖

        Args:
            max_retries: 最大重试次数，默认为3次

        Returns:
            bool: 环境检查是否通过

        Raises:
            EnvironmentNotFoundError: Node.js环境未找到
            VersionMismatchError: Node.js版本不匹配
            PackageNotFoundError: 包未找到
            ConfigurationError: 配置错误
        """
        retry_count = 0
        while retry_count < max_retries:
            try:
                # 检查node是否安装
                node_version = subprocess.run(
                    ['powershell', '-Command', '(Get-Command node).Path; node --version'],
                    capture_output=True,
                    text=True,
                    encoding='utf-8'
                )
                if node_version.returncode != 0:
                    raise EnvironmentNotFoundError('Node.js')

                # 检查node版本
                output_lines = node_version.stdout.strip().split('\n')
                if len(output_lines) < 2:
                    raise ConfigurationError('Node.js', '无法获取版本信息')

                # 第二行是版本信息
                version_str = output_lines[1].strip().lstrip('v').split('.')
                current_version = int(version_str[0])
                if current_version < self.node_env.min_version:
                    raise VersionMismatchError(
                        'Node.js',
                        f"v{'.'.join(version_str)}",
                        f"v{self.node_env.min_version}.0.0"
                    )

                # 检查npm是否可用
                npm_version = subprocess.run(
                    ['powershell', '-Command', '(Get-Command npm).Path; npm --version'],
                    capture_output=True,
                    text=True,
                    encoding='utf-8'
                )
                if npm_version.returncode != 0:
                    raise EnvironmentNotFoundError('npm')

                # 记录环境信息
                node_path = output_lines[0].strip()
                node_version_str = output_lines[1].strip()
                self.logger.debug(f"Node.js路径: {node_path}")
                self.logger.debug(f"Node.js版本: {node_version_str}")

                # 处理npm版本信息
                npm_output_lines = npm_version.stdout.strip().split('\n')
                if len(npm_output_lines) < 2:
                    raise ConfigurationError('npm', '无法获取版本信息')

                npm_path = npm_output_lines[0].strip()
                npm_version_str = npm_output_lines[1].strip()
                self.logger.debug(f"npm路径: {npm_path}")
                self.logger.debug(f"npm版本: {npm_version_str}")

                # 检查前端目录是否存在package.json
                package_json_path = self.frontend_dir / 'package.json'
                if not package_json_path.is_file():
                    raise ConfigurationError('frontend', '未找到package.json')

                try:
                    # 读取package.json
                    with open(package_json_path, 'r', encoding='utf-8') as f:
                        package_data = json.load(f)
                except json.JSONDecodeError:
                    raise ConfigurationError('package.json', '解析失败')

                # 检查必要的依赖包
                missing_deps = []
                version_mismatch = []
                for dep_type, packages in self.node_env.required_packages.items():
                    if dep_type not in package_data:
                        missing_deps.extend(packages)
                        continue

                    installed = package_data[dep_type]
                    for pkg in packages:
                        if pkg not in installed:
                            missing_deps.append(pkg)
                        elif installed[pkg].startswith('^') or installed[pkg].startswith('~'):
                            # 检查版本兼容性
                            required_version = installed[pkg].lstrip('^~')
                            try:
                                # 获取已安装的实际版本
                                npm_command = 'npm.cmd' if sys.platform == 'win32' else 'npm'
                                pkg_info = subprocess.run(
                                    [npm_command, 'list', pkg, '--depth=0', '--json'],
                                    cwd=str(self.frontend_dir),
                                    capture_output=True,
                                    text=True,
                                    encoding='utf-8'
                                )
                                if pkg_info.returncode == 0:
                                    pkg_data = json.loads(pkg_info.stdout)
                                    if 'dependencies' in pkg_data and pkg in pkg_data['dependencies']:
                                        actual_version = pkg_data['dependencies'][pkg]['version']
                                        if not self._is_version_compatible(actual_version, required_version):
                                            version_mismatch.append((pkg, actual_version, required_version))
                            except Exception:
                                self.logger.warning(f"⚠️ 无法获取 {pkg} 的实际版本信息")

                if missing_deps:
                    raise PackageNotFoundError(f"Node.js包: {', '.join(missing_deps)}")

                if version_mismatch:
                    mismatch_info = '\n'.join(
                        f"  - {pkg}: 当前版本 {current} 与要求版本 {required} 不兼容"
                        for pkg, current, required in version_mismatch
                    )
                    raise VersionMismatchError('Node.js包', '多个包版本不兼容', f"\n{mismatch_info}")

                self.logger.info("✅ Node.js环境检查通过")
                return True

            except (EnvironmentNotFoundError, VersionMismatchError,
                    PackageNotFoundError, ConfigurationError) as e:
                self.logger.error(f"❌ {str(e)}")
                return False
            except Exception as e:
                self.logger.warning(f"⚠️ 检查失败 (尝试 {retry_count + 1}/{max_retries}): {str(e)}")
                retry_count += 1
                if retry_count < max_retries:
                    self.logger.info(f"等待 {retry_count * 2} 秒后重试...")
                    time.sleep(retry_count * 2)
                continue

        self.logger.error(f"❌ Node.js环境检查失败，已重试 {max_retries} 次")
        return False

    def _is_version_compatible(self, actual_version: str, required_version: str) -> bool:
        """检查版本兼容性

        Args:
            actual_version: 实际版本号
            required_version: 要求的版本号

        Returns:
            bool: 版本是否兼容
        """
        try:
            from packaging.version import parse as parse_version
            actual = parse_version(actual_version)
            required = parse_version(required_version)

            # 主版本号必须相同
            actual_parts = actual_version.split('.')
            required_parts = required_version.split('.')
            if actual_parts[0] != required_parts[0]:
                return False

            # 次版本号和修订号可以更高
            return actual >= required
        except Exception:
            return False

    def install_python_dependencies(self, max_retries: int = 3, parallel_install: bool = True) -> bool:
        """安装Python依赖

        Args:
            max_retries: 最大重试次数，默认为3次
            parallel_install: 是否启用并行安装，默认为True

        Returns:
            bool: 安装是否成功
        """
        retry_count = 0
        while retry_count < max_retries:
            try:
                # 检查requirements.txt
                requirements_path = self.backend_dir / 'requirements.txt'
                if not requirements_path.exists():
                    self.logger.error("❌ requirements.txt 文件不存在")
                    return False

                # 读取并处理依赖列表
                with open(requirements_path, 'r', encoding='utf-8') as f:
                    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

                # 获取当前Python版本
                current_version = f"{sys.version_info.major}.{sys.version_info.minor}"
                self.logger.info(f"📌 当前Python版本: {current_version}")

                # 检查每个包的版本兼容性
                compatible_requirements = []
                incompatible_requirements = []
                for req in requirements:
                    try:
                        # 解析包名和版本要求
                        if '>=' in req:
                            pkg_name, version = req.split('>=', 1)
                            pkg_name = pkg_name.strip()
                            version = version.strip()
                            compatible_requirements.append(f"{pkg_name}>={version}")
                        elif '==' in req:
                            pkg_name, version = req.split('==', 1)
                            pkg_name = pkg_name.strip()
                            version = version.strip()
                            # 检查版本兼容性
                            try:
                                pkg_info = subprocess.run(
                                    [sys.executable, '-m', 'pip', 'install', f"{pkg_name}=={version}", '--dry-run'],
                                    capture_output=True,
                                    text=True,
                                    encoding='utf-8'
                                )
                                if pkg_info.returncode == 0:
                                    compatible_requirements.append(f"{pkg_name}=={version}")
                                else:
                                    # 尝试获取兼容版本
                                    pkg_info = subprocess.run(
                                        [sys.executable, '-m', 'pip', 'install', pkg_name, '--dry-run'],
                                        capture_output=True,
                                        text=True,
                                        encoding='utf-8'
                                    )
                                    if pkg_info.returncode == 0:
                                        compatible_requirements.append(pkg_name)
                                    else:
                                        incompatible_requirements.append(req)
                            except Exception:
                                incompatible_requirements.append(req)
                        else:
                            compatible_requirements.append(req)
                    except Exception as e:
                        self.logger.warning(f"⚠️ 解析依赖 {req} 失败: {str(e)}")
                        incompatible_requirements.append(req)

                if incompatible_requirements:
                    self.logger.warning("⚠️ 以下依赖包可能与当前Python版本不兼容，将尝试安装最新兼容版本：")
                    for req in incompatible_requirements:
                        self.logger.warning(f"  - {req}")

                # 清理pip缓存
                self.logger.info("🧹 清理pip缓存...")
                subprocess.run(
                    [sys.executable, '-m', 'pip', 'cache', 'purge'],
                    capture_output=True,
                    text=True,
                    encoding='utf-8'
                )

                # 创建临时requirements文件
                temp_requirements = requirements_path.parent / 'requirements.temp.txt'
                with open(temp_requirements, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(compatible_requirements))

                try:
                    # 安装依赖
                    self.logger.info("📦 开始安装Python依赖...")
                    install_cmd = [sys.executable, '-m', 'pip', 'install']
                    if parallel_install:
                        install_cmd.extend(['--no-cache-dir', '-r', str(temp_requirements)])
                    else:
                        install_cmd.extend(['-r', str(temp_requirements)])

                    # 启动安装进程并实时显示进度
                    process = subprocess.Popen(
                        install_cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        encoding='utf-8'
                    )

                    # 实时显示安装进度
                    while True:
                        if process.stdout is not None:
                            output = process.stdout.readline()
                            if output == '' and process.poll() is not None:
                                break
                            if output:
                                line = output.strip()
                                if 'error' in line.lower():
                                    self.logger.error(f"❌ {line}")
                                elif 'warning' in line.lower():
                                    self.logger.warning(f"⚠️ {line}")
                                elif any(keyword in line.lower() for keyword in ['collecting', 'downloading', 'installing']):
                                    self.logger.info(f"📥 {line}")
                                else:
                                    self.logger.debug(f"ℹ️ {line}")
                        else:
                            break

                    # 获取最终结果
                    return_code = process.poll()
                    if return_code != 0:
                        error_output = process.stderr.read() if process.stderr is not None else ''
                        raise RuntimeError(f"安装失败: {error_output}")

                    # 验证安装结果
                    self.logger.info("🔍 验证安装结果...")
                    missing_packages = self._get_missing_python_packages()
                    if missing_packages:
                        raise RuntimeError(f"以下包安装失败: {', '.join(missing_packages)}")

                    self.logger.info("✅ Python依赖安装完成")
                    return True

                finally:
                    # 清理临时文件
                    if temp_requirements.exists():
                        temp_requirements.unlink()

            except Exception as e:
                self.logger.error(f"❌ 安装失败 (尝试 {retry_count + 1}/{max_retries}): {str(e)}")
                retry_count += 1
                if retry_count < max_retries:
                    wait_time = retry_count * 5
                    self.logger.info(f"⏳ 等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                continue

        self.logger.error(f"❌ Python依赖安装失败，已重试 {max_retries} 次")
        return False

    def install_node_dependencies(self, max_retries: int = 3, parallel_install: bool = True) -> bool:
        """安装Node.js依赖

        Args:
            max_retries: 最大重试次数，默认为3次
            parallel_install: 是否启用并行安装，默认为True

        Returns:
            bool: 安装是否成功
        """
        retry_count = 0
        while retry_count < max_retries:
            try:
                # 检查package.json
                package_json_path = self.frontend_dir / 'package.json'
                if not package_json_path.exists():
                    self.logger.error("❌ package.json 文件不存在")
                    return False

                # 清理npm缓存
                self.logger.info("🧹 清理npm缓存...")
                clean_cache = subprocess.run(
                    ['powershell', '-NoProfile', '-Command', 'npm cache clean --force'],
                    cwd=str(self.frontend_dir),
                    capture_output=True,
                    text=True,
                    encoding='utf-8'
                )
                if clean_cache.returncode != 0:
                    self.logger.warning(f"⚠️ 清理缓存失败: {clean_cache.stderr}")

                # 删除node_modules和package-lock.json
                self.logger.info("🗑️ 正在删除旧的依赖文件...")
                subprocess.run(
                    ['powershell', '-NoProfile', '-Command',
                     'Remove-Item -Recurse -Force node_modules,package-lock.json -ErrorAction SilentlyContinue'],
                    cwd=str(self.frontend_dir),
                    capture_output=True,
                    text=True,
                    encoding='utf-8'
                )

                # 安装依赖
                self.logger.info("📦 开始安装前端依赖...")
                install_cmd = ['powershell', '-NoProfile', '-Command']
                if parallel_install:
                    install_cmd.append('npm ci --prefer-offline')
                else:
                    install_cmd.append('npm install')

                # 启动安装进程并实时显示进度
                process = subprocess.Popen(
                    install_cmd,
                    cwd=str(self.frontend_dir),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding='utf-8'
                )

                while True:
                    if process.stdout is not None:
                        output = process.stdout.readline()
                        if output == '' and process.poll() is not None:
                            break
                        if output:
                            line = output.strip()
                            if 'npm' in line.lower():
                                if 'err' in line.lower():
                                    self.logger.error(f"❌ {line}")
                                elif 'warn' in line.lower():
                                    self.logger.warning(f"⚠️ {line}")
                                else:
                                    self.logger.info(f"ℹ️ {line}")
                    else:
                        break

                return_code = process.poll()
                if return_code != 0:
                    error_output = process.stderr.read() if process.stderr is not None else ''
                    raise RuntimeError(f"安装失败: {error_output}")

                self.logger.info("✅ 前端依赖安装完成")
                return True

            except Exception as e:
                self.logger.error(f"❌ 安装失败 (尝试 {retry_count + 1}/{max_retries}): {str(e)}")
                retry_count += 1
                if retry_count < max_retries:
                    wait_time = retry_count * 5
                    self.logger.info(f"⏳ 等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                continue

        self.logger.error(f"❌ 前端依赖安装失败，已重试 {max_retries} 次")
        return False

    def _get_missing_python_packages(self) -> List[str]:
        """获取缺失的Python包列表"""
        try:
            with open(self.backend_dir / 'requirements.txt', 'r', encoding='utf-8') as f:
                required = [line.strip() for line in f if line.strip() and not line.startswith('#')]

            # 获取已安装的包信息
            installed_packages = subprocess.run(
                [sys.executable, '-m', 'pip', 'list', '--format=json'],
                capture_output=True,
                text=True,
                encoding='utf-8'
            )

            if installed_packages.returncode != 0:
                return required

            try:
                installed = {pkg['name'].lower(): pkg['version'] 
                           for pkg in json.loads(installed_packages.stdout)}
                missing = []

                for req in required:
                    if '>=' in req:
                        pkg_name, req_version = req.split('>=', 1)
                        pkg_name = pkg_name.strip().lower()
                        req_version = req_version.strip()

                        if pkg_name not in installed:
                            missing.append(req)
                        else:
                            from packaging.version import parse as parse_version
                            if parse_version(installed[pkg_name]) < parse_version(req_version):
                                missing.append(req)
                    else:
                        pkg_name = req.split('==')[0].strip().lower()
                        if pkg_name not in installed:
                            missing.append(req)

                return missing

            except json.JSONDecodeError:
                return required

        except Exception:
            return []

    def check_postgresql_connection(self) -> bool:
        """检测PostgreSQL数据库连接状态（通过Django配置自动适配）"""
        try:
            import importlib
            import socket
            # 读取Django settings
            settings_path = self.backend_dir / 'exam_system' / 'settings.py'
            db_host = 'localhost'
            db_port = 5432
            db_engine = None
            db_name = ''
            db_user = ''
            db_password = ''
            # 解析settings.py
            with open(settings_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            for i, line in enumerate(lines):
                if "'ENGINE'" in line and 'postgresql' in line:
                    db_engine = 'postgresql'
                if "'HOST'" in line:
                    db_host = line.split(':')[-1].replace("'", '').replace(',', '').strip()
                if "'PORT'" in line:
                    db_port = int(line.split(':')[-1].replace("'", '').replace(',', '').strip())
                if "'NAME'" in line:
                    db_name = line.split(':')[-1].replace("'", '').replace(',', '').strip()
                if "'USER'" in line:
                    db_user = line.split(':')[-1].replace("'", '').replace(',', '').strip()
                if "'PASSWORD'" in line:
                    db_password = line.split(':')[-1].replace("'", '').replace(',', '').strip()
            # 仅检测端口可达性
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            try:
                sock.connect((db_host, db_port))
                sock.close()
                self.logger.info(f"✅ PostgreSQL数据库({db_host}:{db_port})连接正常")
                return True
            except Exception as e:
                self.logger.error(f"❌ PostgreSQL数据库({db_host}:{db_port})无法连接: {str(e)}")
                return False
        except Exception as e:
            self.logger.error(f"❌ 检查PostgreSQL连接时发生错误: {str(e)}")
            return False

    def check_redis_connection(self) -> bool:
        """检测Redis服务连接状态（通过settings.py自动适配）"""
        try:
            import socket
            redis_host = 'localhost'
            redis_port = 6379
            # 读取settings.py
            settings_path = self.backend_dir / 'exam_system' / 'settings.py'
            with open(settings_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            for line in lines:
                if 'REDIS_HOST' in line:
                    redis_host = line.split(',')[0].split('"')[-2]
                if 'REDIS_PORT' in line:
                    redis_port = int(line.split(',')[0].split('"')[-2])
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            try:
                sock.connect((redis_host, redis_port))
                sock.close()
                self.logger.info(f"✅ Redis服务({redis_host}:{redis_port})连接正常")
                return True
            except Exception as e:
                self.logger.error(f"❌ Redis服务({redis_host}:{redis_port})无法连接: {str(e)}")
                return False
        except Exception as e:
            self.logger.error(f"❌ 检查Redis连接时发生错误: {str(e)}")
            return False

    def check_websocket_connection(self) -> bool:
        """检测WebSocket服务端口可用性（假定为Django Channels默认端口）"""
        try:
            import socket
            ws_host = 'localhost'
            ws_port = 8001  # 假定Daphne/Channels默认端口
            # 可根据实际配置调整
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            try:
                sock.connect((ws_host, ws_port))
                sock.close()
                self.logger.info(f"✅ WebSocket服务({ws_host}:{ws_port})端口可用")
                return True
            except Exception as e:
                self.logger.error(f"❌ WebSocket服务({ws_host}:{ws_port})端口不可用: {str(e)}")
                return False
        except Exception as e:
            self.logger.error(f"❌ 检查WebSocket端口时发生错误: {str(e)}")
            return False