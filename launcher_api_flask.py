import threading
from flask import Flask, jsonify, request
from flask_cors import CORS
from launcher import SystemLauncherGUI

app = Flask(__name__)
CORS(app)

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

@app.route('/api/launcher/check_virtual_env', methods=['GET'])
@launcher_op
def check_virtual_env():
    result = get_launcher().env_manager.check_virtual_env()
    return jsonify({'result': result})

@app.route('/api/launcher/check_python_env', methods=['GET'])
@launcher_op
def check_python_env():
    result = get_launcher().env_manager.check_python_environment()
    return jsonify({'result': result})

@app.route('/api/launcher/install_python_deps', methods=['POST'])
@launcher_op
def install_python_deps():
    result = get_launcher().env_manager.install_python_dependencies()
    return jsonify({'success': result})

@app.route('/api/launcher/start_django', methods=['POST'])
@launcher_op
def start_django():
    result = get_launcher().start_django_server()
    return jsonify({'success': result})

@app.route('/api/launcher/start_frontend', methods=['POST'])
@launcher_op
def start_frontend():
    result = get_launcher().start_frontend_server()
    return jsonify({'success': result})

@app.route('/api/launcher/stop_all', methods=['POST'])
@launcher_op
def stop_all():
    result = get_launcher().stop_all_servers()
    return jsonify({'success': result})

@app.route('/api/launcher/status', methods=['GET'])
@launcher_op
def status():
    launcher = get_launcher()
    return jsonify({
        'django': launcher.django_server.is_running(),
        'frontend': launcher.frontend_server.is_running(),
        'postgres': launcher.env_manager.check_postgresql_connection(),
        'redis': launcher.env_manager.check_redis_connection(),
        'websocket': launcher.env_manager.check_websocket_connection(),
    })

@app.route('/api/launcher/log', methods=['GET'])
@launcher_op
def log():
    log_content = ''
    try:
        with open('system_launcher.log', 'r', encoding='utf-8') as f:
            log_content = f.read()[-5000:]
    except Exception:
        pass
    return jsonify({'log': log_content})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8008, debug=True) 