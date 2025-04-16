from flask import Flask, request, jsonify
import os
import json
import datetime
import shutil
import portalocker
import threading
from PIL import Image, ImageDraw
import pystray

app = Flask(__name__)

# Directories
STORAGE_DIR = "data_storage"
HISTORY_DIR = "history_storage"
LOG_FILE = "requests.log"

os.makedirs(STORAGE_DIR, exist_ok=True)
os.makedirs(HISTORY_DIR, exist_ok=True)

# IP to username mapping
IP_TO_NAME = {
    "127.0.0.1": "localhost",
    "192.168.1.168": "localhost",
    "192.168.1.5": "Person A",
    "10.0.0.42": "Person B",
}

if os.path.exists("ipnamemap.json"):
    with open("ipnamemap.json", "r", encoding="utf-8") as f:
        IP_TO_NAME = json.load(f)

def log_request(method, path, user):
    timestamp = current_timestamp()
    log_entry = f"{timestamp} | {user} | {method} | {path}\n"
    with open(LOG_FILE, "a") as log:
        portalocker.lock(log, portalocker.LOCK_EX)
        log.write(log_entry)
        portalocker.unlock(log)

def get_user(ip):
    return IP_TO_NAME.get(ip, ip)

def fs_path(path, base_dir=STORAGE_DIR):
    return os.path.join(base_dir, *path.split('/')) + '.json'

def ensure_dirs(file_path):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

def current_timestamp():
    return datetime.datetime.now().isoformat()

def update_history(path, data):
    history_path = fs_path(path, HISTORY_DIR)
    ensure_dirs(history_path)
    history = []
    if os.path.exists(history_path):
        with open(history_path, 'r') as f:
            portalocker.lock(f, portalocker.LOCK_SH)
            history = json.load(f)
            portalocker.unlock(f)
    history.append(data)
    with open(history_path, 'w') as f:
        portalocker.lock(f, portalocker.LOCK_EX)
        json.dump(history, f, indent=2)
        portalocker.unlock(f)

def read_directory_recursively(dir_path):
    """Recursively reads all .json files in a directory and returns a nested dict."""
    data = {}
    for item in os.listdir(dir_path):
        item_path = os.path.join(dir_path, item)
        if os.path.isdir(item_path):
            data[item] = read_directory_recursively(item_path)
        elif item.endswith('.json'):
            file_name_without_ext = os.path.splitext(item)[0]
            try:
                with open(item_path, 'r') as f:
                    portalocker.lock(f, portalocker.LOCK_SH)
                    content = json.load(f)
                    portalocker.unlock(f)
                data[file_name_without_ext] = content
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error reading {item_path}: {e}")
                data[file_name_without_ext] = {"error": f"Could not read file: {e}"}
    return data

@app.route('/read/<path:path>', methods=['GET'])
def read(path):
    file_path = fs_path(path)
    dir_path = os.path.join(STORAGE_DIR, *path.split('/'))
    user = get_user(request.remote_addr)
    log_request("READ", path, user)

    # check file
    if os.path.exists(file_path) and os.path.isfile(file_path):
        with open(file_path, 'r') as f:
            portalocker.lock(f, portalocker.LOCK_SH)
            try:
                data = json.load(f)
                portalocker.unlock(f)
                return jsonify(data)
            except json.JSONDecodeError as e:
                portalocker.unlock(f)
                return jsonify({"error": f"Error decoding JSON from file: {e}"}), 500

    # check folder
    elif os.path.exists(dir_path) and os.path.isdir(dir_path):
        data = read_directory_recursively(dir_path)
        return jsonify(data)

    else:
        return jsonify({"error": "Not found"}), 404

@app.route('/write/<path:path>', methods=['PUT'])
def write(path):
    file_path = fs_path(path)
    user = get_user(request.remote_addr)
    log_request("WRITE", path, user)

    value = request.json.get('value')
    if value is None:
        return jsonify({"error": "Missing 'value'"}), 400

    ensure_dirs(file_path)
    timestamp = current_timestamp()

    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            portalocker.lock(f, portalocker.LOCK_SH)
            existing = json.load(f)
            portalocker.unlock(f)
        created_at = existing["created_at"]
        created_by = existing["created_by"]
    else:
        created_at = timestamp
        created_by = user

    data = {
        "value": value,
        "created_at": created_at,
        "created_by": created_by,
        "updated_at": timestamp,
        "updated_by": user
    }

    with open(file_path, 'w') as f:
        portalocker.lock(f, portalocker.LOCK_EX)
        json.dump(data, f, indent=2)
        portalocker.unlock(f)

    history_entry = {
        "value": value,
        "timestamp": timestamp,
        "user": user
    }
    update_history(path, history_entry)

    return jsonify({"success": True, "metadata": data})

@app.route('/delete_value/<path:path>', methods=['DELETE'])
def delete_value(path):
    file_path = fs_path(path)
    user = get_user(request.remote_addr)
    log_request("DELETE_VALUE", path, user)

    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        return jsonify({"error": "Value not found"}), 404

    try:
        with open(file_path, 'r') as f:
            portalocker.lock(f, portalocker.LOCK_SH)
            data = json.load(f)
            portalocker.unlock(f)
    except (json.JSONDecodeError, IOError) as e:
        os.remove(file_path)
        return jsonify({"success": True, "warning": f"Deleted but could not read content: {e}"}), 200

    history_entry = {
        "is_deleted": True,
        "timestamp": current_timestamp(),
        "user": user
    }
    update_history(path, history_entry)

    os.remove(file_path)
    return jsonify(data)

@app.route('/delete_folder/<path:path>', methods=['DELETE'])
def delete_folder(path):
    dir_path = os.path.join(STORAGE_DIR, *path.split('/'))
    user = get_user(request.remote_addr)
    log_request("DELETE_FOLDER", path, user)

    if not os.path.exists(dir_path) or not os.path.isdir(dir_path):
        return jsonify({"error": "Folder not found"}), 404

    deleted_content = read_directory_recursively(dir_path)

    history_entry = {
        "is_deleted": True,
        "timestamp": current_timestamp(),
        "user": user
    }
    update_history(path, history_entry)

    shutil.rmtree(dir_path)
    return jsonify(deleted_content)

def run_server():
    app.run(host='0.0.0.0', port=6924, debug=False, use_reloader=False)

def create_image(width, height, color1, color2):
    image = Image.new('RGB', (width, height), color1)
    dc = ImageDraw.Draw(image)
    dc.rectangle(
        (width // 2, 0, width, height // 2),
        fill=color2)
    dc.rectangle(
        (0, height // 2, width // 2, height),
        fill=color2)
    return image

def quit_action(icon, item):
    print("Stopping server...")
    icon.stop()
    os._exit(0)

def open_folder_action(icon, item):
    folder_path = os.path.abspath(STORAGE_DIR)
    print(f"Opening folder: {folder_path}")
    try:
        os.startfile(folder_path)
    except Exception as e:
        print(f"Error opening folder: {e}")

if __name__ == '__main__':
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    print("Server started in background thread.")

    icon_image = create_image(64, 64, 'black', 'blue')
    menu = (
        pystray.MenuItem('Open Data Folder', open_folder_action),
        pystray.MenuItem('Quit', quit_action)
    )
    tray_icon = pystray.Icon("SimpleDB Server", icon_image, "SimpleDB Server", menu)

    print("Starting system tray icon...")
    tray_icon.run()