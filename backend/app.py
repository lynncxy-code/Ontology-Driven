import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from ontology import SharedState

app = Flask(__name__)
CORS(app)

# Serve static files from frontend directory
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))
app = Flask(__name__, static_folder=frontend_dir, static_url_path='')
CORS(app)

state = SharedState()

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/api/state', methods=['GET'])
def get_state():
    return jsonify(state.to_dict())

@app.route('/api/update', methods=['POST'])
def update_state():
    data = request.json
    state.update(data)
    return jsonify(state.to_dict())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
