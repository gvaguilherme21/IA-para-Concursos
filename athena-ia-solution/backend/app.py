from flask import Flask, request, jsonify
from flask_cors import CORS

# Assuming text_processor and bert_model are in the correct path
# For development, ensure PYTHONPATH includes the backend directory or use relative imports if structured as a package
try:
    from utils.text_processor import extract_topics
    from models.bert_model import generate_prompts
except ImportError:
    # Fallback for environments where the utils/models are not directly in PYTHONPATH
    # This might happen if 'backend' itself is not a package recognized by Python
    # or if the script is run from a different working directory.
    # For a robust solution, consider structuring 'backend' as a Python package.
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__)))
    from utils.text_processor import extract_topics
    from models.bert_model import generate_prompts

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes and origins

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint to verify API is running."""
    return jsonify({"status": "Healthy", "message": "Athena API is up and running!"}), 200

@app.route('/extract_topics', methods=['POST'])
def extract_topics_route():
    """
    Endpoint to extract topics from edital content.
    Expects JSON: {"edital_content": "text..."}
    Returns JSON: {"topics": ["topic1", "topic2", ...]}
    """
    data = request.get_json()
    if not data or "edital_content" not in data:
        return jsonify({"error": "Missing 'edital_content' in request body"}), 400

    edital_content = data["edital_content"]
    if not isinstance(edital_content, str) or not edital_content.strip():
        return jsonify({"error": "'edital_content' must be a non-empty string"}), 400

    try:
        topics = extract_topics(edital_content)
        return jsonify({"topics": topics}), 200
    except Exception as e:
        # Log the exception e for debugging
        print(f"Error in /extract_topics: {e}")
        return jsonify({"error": "Failed to extract topics", "details": str(e)}), 500

@app.route('/generate_prompts', methods=['POST'])
def generate_prompts_route():
    """
    Endpoint to generate study prompts.
    Expects JSON: {"edital_content": "text...", "knowledge_gaps": ["gap1", "gap2", ...]}
    Returns JSON: {"prompts": ["prompt1", "prompt2", ...]}
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body is missing or not JSON"}), 400

    edital_content = data.get("edital_content")
    knowledge_gaps = data.get("knowledge_gaps")

    if not edital_content or not isinstance(edital_content, str) or not edital_content.strip():
        return jsonify({"error": "'edital_content' must be a non-empty string"}), 400
    
    if knowledge_gaps is None or not isinstance(knowledge_gaps, list):
        # Allow empty list for knowledge_gaps, but it must be a list.
        return jsonify({"error": "'knowledge_gaps' must be a list (can be empty)"}), 400
    
    if not all(isinstance(gap, str) for gap in knowledge_gaps):
        return jsonify({"error": "All items in 'knowledge_gaps' must be strings"}), 400

    try:
        prompts = generate_prompts(edital_content, knowledge_gaps)
        return jsonify({"prompts": prompts}), 200
    except Exception as e:
        # Log the exception e for debugging
        print(f"Error in /generate_prompts: {e}")
        return jsonify({"error": "Failed to generate prompts", "details": str(e)}), 500

if __name__ == '__main__':
    # Note: For production, use a WSGI server like Gunicorn or Waitress
    app.run(debug=True, host='0.0.0.0', port=5000)
