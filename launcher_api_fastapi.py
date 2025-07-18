import threading
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from launcher import SystemLauncherGUI
from typing import Any

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_launcher = None
_launcher_lock = threading.Lock()

def get_launcher():
    global _launcher
    with _launcher_lock:
        if _launcher is None:
            _launcher = SystemLauncherGUI()
    return _launcher

def launcher_op(func):
    def wrapper(*args, **kwargs):
        with _launcher_lock:
            return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

@app.get('/api/launcher/check_virtual_env')
@launcher_op
def check_virtual_env() -> Any:
    result = get_launcher().env_manager.check_virtual_env()
    return {'result': result}

@app.get('/api/launcher/check_python_env')
@launcher_op
def check_python_env() -> Any:
    result = get_launcher().env_manager.check_python_environment()
    return {'result': result}

@app.post('/api/launcher/install_python_deps')
@launcher_op
def install_python_deps() -> Any:
    result = get_launcher().env_manager.install_python_dependencies()
    return {'success': result}

@app.post('/api/launcher/start_django')
@launcher_op
def start_django() -> Any:
    result = get_launcher().start_django_server()
    return {'success': result}

@app.post('/api/launcher/start_frontend')
@launcher_op
def start_frontend() -> Any:
    result = get_launcher().start_frontend_server()
    return {'success': result}

@app.post('/api/launcher/stop_all')
@launcher_op
def stop_all() -> Any:
    result = get_launcher().stop_all_servers()
    return {'success': result}

@app.get('/api/launcher/status')
@launcher_op
def status() -> Any:
    launcher = get_launcher()
    return {
        'django': launcher.django_server.is_running(),
        'frontend': launcher.frontend_server.is_running(),
        'postgres': launcher.env_manager.check_postgresql_connection(),
        'redis': launcher.env_manager.check_redis_connection(),
        'websocket': launcher.env_manager.check_websocket_connection(),
    }

@app.get('/api/launcher/log')
@launcher_op
def log() -> Any:
    log_content = ''
    try:
        with open('system_launcher.log', 'r', encoding='utf-8') as f:
            log_content = f.read()[-5000:]
    except Exception:
        pass
    return {'log': log_content}

# 启动命令：uvicorn launcher_api_fastapi:app --host 0.0.0.0 --port 8008 --reload 