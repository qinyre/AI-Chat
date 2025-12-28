from flask import Flask, render_template, request, Response, stream_with_context, jsonify, send_from_directory
from llm_wrapper import LLMWrapper
import os

app = Flask(__name__)
llm = LLMWrapper()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/assets/icons/<filename>')
def serve_icon(filename):
    """Serve local icon files from assets/icons/"""
    icons_dir = os.path.join(os.path.dirname(__file__), 'assets', 'icons')
    return send_from_directory(icons_dir, filename)

@app.route('/api/models')
def get_models():
    return jsonify(llm.get_models())

@app.route('/api/chat', methods=['POST'])
def chat():
    print("Received chat request", flush=True) # Debug log
    data = request.json
    model_id = data.get('model')
    messages = data.get('messages')
    print(f"Model: {model_id}, Messages: {len(messages)}", flush=True)

    if not model_id or not messages:
        return "Missing arguments", 400

    def generate():
        for chunk in llm.chat_stream(model_id, messages):
            yield chunk

    return Response(stream_with_context(generate()), mimetype='text/plain')

if __name__ == '__main__':
    print("Starting Web Chat on http://127.0.0.1:5000")
    app.run(debug=True, port=5000)
