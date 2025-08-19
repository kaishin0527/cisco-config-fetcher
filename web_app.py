



from flask import Flask, render_template, request, redirect, url_for, send_file
import yaml
import os
import subprocess
from datetime import datetime

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 設定ファイルパス
DEVICES_FILE = 'devices_updated.yaml'
COMMAND_GROUPS_FILE = 'command_groups.yaml'
SCENARIO_LIST_FILE = 'scenario_list.yaml'

def load_yaml(file_path):
    """YAMLファイルを読み込む"""
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return yaml.safe_load(f)
    return {}

def save_yaml(data, file_path):
    """YAMLファイルに保存"""
    with open(file_path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False)

@app.route('/')
def index():
    """ダッシュボード"""
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=51361, debug=True)



