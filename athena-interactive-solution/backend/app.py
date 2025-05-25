from flask import Flask, request, jsonify
from flask_cors import CORS

# Adjusted import paths for the new project structure
try:
    from utils.text_processor import extract_topics
    from models.mock_bert_model import generate_prompts
except ImportError:
    # Fallback for environments where the utils/models are not directly in PYTHONPATH
    import sys
    import os
    # Adds the 'backend' directory to sys.path, assuming app.py is in 'backend'
    sys.path.append(os.path.dirname(__file__)) 
    from utils.text_processor import extract_topics
    from models.mock_bert_model import generate_prompts

app = Flask(__name__)
# Enable CORS for all routes and origins, essential for local Streamlit development
CORS(app) 

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint to verify API is running."""
    return jsonify({"status": "Healthy", "message": "Athena Backend API is up and running!"}), 200

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
        # Basic validation for edital_content
        return jsonify({"error": "'edital_content' must be a non-empty string"}), 400

    try:
        # Call the text processing function
        topics = extract_topics(edital_content)
        app.logger.info(f"Extracted topics: {topics} for content: {edital_content[:100]}...") # Log snippet
        return jsonify({"topics": topics}), 200
    except Exception as e:
        app.logger.error(f"Error in /extract_topics: {e}", exc_info=True) # Log exception details
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

    # Validate inputs
    if not edital_content or not isinstance(edital_content, str) or not edital_content.strip():
        return jsonify({"error": "'edital_content' must be a non-empty string"}), 400
    
    if knowledge_gaps is None or not isinstance(knowledge_gaps, list):
        # knowledge_gaps must be a list, can be empty.
        return jsonify({"error": "'knowledge_gaps' must be a list (it can be empty)"}), 400
    
    if not all(isinstance(gap, str) for gap in knowledge_gaps):
        return jsonify({"error": "All items in 'knowledge_gaps' must be strings"}), 400

    try:
        # Call the prompt generation function
        prompts = generate_prompts(edital_content, knowledge_gaps)
        app.logger.info(f"Generated prompts: {prompts} for content: {edital_content[:100]}... and gaps: {knowledge_gaps}")
        return jsonify({"prompts": prompts}), 200
    except Exception as e:
        app.logger.error(f"Error in /generate_prompts: {e}", exc_info=True)
        return jsonify({"error": "Failed to generate prompts", "details": str(e)}), 500

if __name__ == '__main__':
    # For development server
    # For production, use a WSGI server like Gunicorn: gunicorn -w 4 -b 0.0.0.0:5000 app:app
    app.run(debug=True, host='0.0.0.0', port=5000)
