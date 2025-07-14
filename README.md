
### 依赖管理策略
- **全局虚拟环境**：所有模块共用项目根目录下的`.venv`虚拟环境
- **统一依赖文件**：在根目录维护一个总的`requirements.txt`文件
- **依赖安装流程**：
  ```bash
  # 创建并激活虚拟环境
  python -m venv .venv
  
  # Windows激活虚拟环境
  .venv\Scripts\activate
  
  # Linux/Mac激活虚拟环境
  source .venv/bin/activate
  
  # 安装所有依赖
  pip install -r requirements.txt
  ```

## 依赖自动安装机制

PH&RL 启动器和主控台支持自动安装依赖，采用如下两步策略：

1. **优先使用官方 PyPI 源安装依赖**：
   - 地址：https://pypi.org/simple/
2. **如官方源安装失败，自动切换到清华大学镜像源**：
   - 地址：https://pypi.tuna.tsinghua.edu.cn/simple/

> 该机制已集成在新版 `start_system.py` 启动器中，无需手动干预。

### 手动安装依赖（如自动安装失败）

如果自动安装依赖失败，可手动执行如下命令：

```bash
# 官方源
pip install flask pandas openpyxl pillow requests -i https://pypi.org/simple/

# 或使用清华镜像源
pip install flask pandas openpyxl pillow requests -i https://pypi.tuna.tsinghua.edu.cn/simple/
```

如需单独安装某个包，只需将包名替换即可。


1. 为特定模块创建独立的虚拟环境：
   ```bash
   # 在模块目录下创建虚拟环境
   cd question_bank_web
   python -m venv venv_qb
   
   # 激活虚拟环境
   .\venv_qb\Scripts\activate  # Windows
   source venv_qb/bin/activate  # Linux/Mac
   
   # 安装依赖
   pip install -r requirements.txt
   ```

2. 确保在激活虚拟环境后运行模块：
   ```bash
   # 激活虚拟环境
   .\venv_qb\Scripts\activate  # Windows
   
   # 运行模块
   python run.py
   ```

## 🎯 使用指南

### 首次使用
1. 克隆或下载项目代码
2. 创建并激活虚拟环境：
   ```bash
   # 创建虚拟环境
   python -m venv .venv
   
   # Windows激活虚拟环境
   .venv\Scripts\activate
   
   # Linux/Mac激活虚拟环境
   source .venv/bin/activate
   ```
3. 安装依赖：`pip install -r requirements.txt`
4. 运行启动器：`python start_system.py`

### 开发指南
1. **添加新依赖**：
   ```bash
   pip install new_package
   pip freeze > requirements.txt
   ```
2. **模块开发**：在对应模块目录下开发，遵循模块化设计原则
3. **共享代码**：将多模块共用的代码放在`common`目录
4. **文档更新**：及时更新模块README和项目总文档

## 📞 联系方式

如有问题或建议，请联系开发团队。

### 技术支持
- 📧 Email: support@phrl.com
- 🐛 Bug报告: [GitHub Issues](https://github.com/your-org/phrl-exam-system/issues)
- 📖 文档: [在线文档](https://docs.phrl.com)

### 贡献指南
欢迎提交Pull Request和Issue，请遵循以下规范：
1. Fork项目并创建feature分支
2. 编写测试用例
3. 确保所有测试通过
4. 提交Pull Request

最后更新：2025-07-03
