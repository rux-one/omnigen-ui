from flask import Flask, request, jsonify, send_from_directory, abort, url_for
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import uuid
import logging
from datetime import datetime
import subprocess
import threading
import json
import signal
import shlex
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
log_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(pathname)s:%(lineno)d'
)

# File handler for all logs
file_handler = logging.FileHandler("api.log")
file_handler.setFormatter(log_formatter)

# Console handler for INFO and above
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
console_handler.setLevel(logging.INFO)

# Error file handler for ERROR and above
error_handler = logging.FileHandler("error.log")
error_handler.setFormatter(log_formatter)
error_handler.setLevel(logging.ERROR)

# Configure root logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(console_handler)
logger.addHandler(error_handler)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

# Configure CORS
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Configure upload folders
INPUT_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'input_images')
OUTPUT_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'output_images')

# Ensure directories exist
os.makedirs(INPUT_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Store active processes
active_processes = {}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Custom error handlers
@app.errorhandler(400)
def bad_request(error):
    request_data = request.get_json() if request.is_json else {}
    logger.error(f"Bad request: {error}, Route: {request.path}, Method: {request.method}, Data: {request_data}")
    return jsonify({
        "error": "Bad Request",
        "message": str(error),
        "path": request.path
    }), 400

@app.errorhandler(404)
def not_found(error):
    logger.error(f"Resource not found: {error}, Path: {request.path}, Method: {request.method}")
    return jsonify({
        "error": "Not Found",
        "message": f"The requested resource '{request.path}' was not found",
        "path": request.path
    }), 404

@app.errorhandler(405)
def method_not_allowed(error):
    logger.error(f"Method not allowed: {error}, Path: {request.path}, Method: {request.method}")
    return jsonify({
        "error": "Method Not Allowed",
        "message": f"The method {request.method} is not allowed for the requested URL",
        "path": request.path,
        "method": request.method
    }), 405

@app.errorhandler(413)
def request_entity_too_large(error):
    logger.error(f"Request entity too large: {error}, Path: {request.path}")
    return jsonify({
        "error": "Request Entity Too Large",
        "message": "The file you are trying to upload is too large. Maximum size is 16MB.",
        "path": request.path
    }), 413

@app.errorhandler(500)
def server_error(error):
    logger.error(f"Server error: {error}, Path: {request.path}, Method: {request.method}", exc_info=True)
    return jsonify({
        "error": "Internal Server Error",
        "message": "An unexpected error occurred",
        "path": request.path
    }), 500

@app.errorhandler(Exception)
def unhandled_exception(error):
    logger.error(f"Unhandled exception: {error}, Path: {request.path}, Method: {request.method}", exc_info=True)
    return jsonify({
        "error": "Internal Server Error",
        "message": "An unexpected error occurred",
        "path": request.path
    }), 500

# Health check endpoint
@app.route('/api/health', methods=['GET'])
def health_check():
    logger.info("Health check endpoint called")
    return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()})

# File upload endpoint
@app.route('/api/upload', methods=['POST'])
def upload_file():
    logger.info("Upload endpoint called")
    
    if 'file' not in request.files:
        logger.warning("No file part in the request")
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        logger.warning("No selected file")
        return jsonify({"error": "No selected file"}), 400
    
    if file and allowed_file(file.filename):
        # Generate a unique filename with UUID
        filename = str(uuid.uuid4()) + os.path.splitext(secure_filename(file.filename))[1]
        file_path = os.path.join(INPUT_FOLDER, filename)
        
        # Save the file
        file.save(file_path)
        
        # Get file metadata
        file_size = os.path.getsize(file_path)
        created_time = datetime.now().isoformat()
        
        # Generate URL for the file
        file_url = url_for('serve_image', folder='input', filename=filename, _external=True)
        
        logger.info(f"File uploaded successfully: {filename}")
        
        return jsonify({
            "filename": filename,
            "original_filename": secure_filename(file.filename),
            "path": file_path,
            "url": file_url,
            "size": file_size,
            "created": created_time
        })
    
    logger.warning(f"Invalid file type: {file.filename}")
    return jsonify({"error": "Invalid file type. Allowed types: png, jpg, jpeg, gif"}), 400

# List input images endpoint
@app.route('/api/images/input', methods=['GET'])
def list_input_images():
    logger.info("List input images endpoint called")
    
    images = []
    for filename in os.listdir(INPUT_FOLDER):
        if os.path.isfile(os.path.join(INPUT_FOLDER, filename)) and allowed_file(filename):
            file_path = os.path.join(INPUT_FOLDER, filename)
            file_size = os.path.getsize(file_path)
            created_time = datetime.fromtimestamp(os.path.getctime(file_path)).isoformat()
            file_url = url_for('serve_image', folder='input', filename=filename, _external=True)
            
            images.append({
                "filename": filename,
                "path": file_path,
                "url": file_url,
                "size": file_size,
                "created": created_time
            })
    
    # Sort by creation time (newest first)
    images.sort(key=lambda x: x["created"], reverse=True)
    
    return jsonify({"images": images})

# List output images endpoint
@app.route('/api/images/output', methods=['GET'])
def list_output_images():
    logger.info("List output images endpoint called")
    
    images = []
    for filename in os.listdir(OUTPUT_FOLDER):
        if os.path.isfile(os.path.join(OUTPUT_FOLDER, filename)) and allowed_file(filename):
            file_path = os.path.join(OUTPUT_FOLDER, filename)
            file_size = os.path.getsize(file_path)
            created_time = datetime.fromtimestamp(os.path.getctime(file_path)).isoformat()
            file_url = url_for('serve_image', folder='output', filename=filename, _external=True)
            
            images.append({
                "filename": filename,
                "path": file_path,
                "url": file_url,
                "size": file_size,
                "created": created_time
            })
    
    # Sort by creation time (newest first)
    images.sort(key=lambda x: x["created"], reverse=True)
    
    return jsonify({"images": images})

# Serve image files
@app.route('/api/images/view/<folder>/<filename>', methods=['GET'])
def serve_image(folder, filename):
    logger.info(f"Serve image endpoint called for: {folder}/{filename}")
    
    if folder == 'input':
        return send_from_directory(INPUT_FOLDER, filename)
    elif folder == 'output':
        return send_from_directory(OUTPUT_FOLDER, filename)
    else:
        logger.warning(f"Invalid folder: {folder}")
        return jsonify({"error": "Invalid folder"}), 400

# Function to monitor process and update progress
def monitor_process(process_id):
    process_info = active_processes[process_id]
    process = process_info['process']
    
    try:
        # Read output line by line
        for line in iter(process.stdout.readline, ''):
            if not line:
                break
                
            line_str = line.decode('utf-8') if isinstance(line, bytes) else line
            process_info['output'].append(line_str.strip())
                
            # Parse progress information from the output
            if 'progress:' in line_str.lower():
                try:
                    progress = int(line_str.split('progress:')[1].strip().rstrip('%'))
                    process_info['progress'] = progress
                    # Progress update
                    logger.info(f"Progress update for {process_id}: {progress}%")
                except ValueError:
                    pass
        
        # Wait for process to complete
        return_code = process.poll()
        
        # Update process status
        if return_code == 0:
            process_info['status'] = 'completed'
            logger.info(f"Process completed successfully: {process_id}")
            # Process completed
            logger.info(f"Process {process_id} completed with output: {process_info['output_path']}")
        else:
            process_info['status'] = 'failed'
            error_output = '\n'.join(process_info['output'])
            process_info['error'] = error_output
            logger.error(f"Process failed: {process_id}, Error: {error_output}")
            # Process error
            logger.error(f"Process {process_id} failed with error: {error_output}")
    except Exception as e:
        process_info['status'] = 'failed'
        process_info['error'] = str(e)
        logger.error(f"Error monitoring process: {process_id}, Error: {str(e)}")
        # Process error
        logger.error(f"Error monitoring process {process_id}: {str(e)}")

# Script execution endpoint
@app.route('/api/execute', methods=['POST'])
def execute_script():
    logger.info("Execute script endpoint called")
    
    try:
        # Parse request data
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Extract parameters
        input_images = data.get('input_images', [])
        if not input_images or not isinstance(input_images, list) or len(input_images) == 0:
            return jsonify({"error": "At least one input image is required"}), 400
        
        # Validate input images exist
        for img in input_images:
            if not os.path.exists(os.path.join(INPUT_FOLDER, img)):
                return jsonify({"error": f"Input image not found: {img}"}), 404
        
        # Generate output filename with UUID
        output_filename = f"{str(uuid.uuid4())}.png"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
        
        # Build command with parameters
        model_path = data.get('model_path', "OmniGen2/OmniGen2")
        num_inference_step = data.get('num_inference_step', 50)
        height = data.get('height', 1024)
        width = data.get('width', 1024)
        text_guidance_scale = data.get('text_guidance_scale', 5.0)
        image_guidance_scale = data.get('image_guidance_scale', 2.0)
        instruction = data.get('instruction', "Put the animal from the second picture into the street depicted by the first picture.")
        
        # Build input image paths string
        input_image_paths = " ".join([os.path.join(INPUT_FOLDER, img) for img in input_images])
        
        # Get inference script path from environment variable or use default
        inference_script = os.environ.get('INFERENCE_SCRIPT_PATH', 'inference.py')
        
        # Build the command
        cmd = f"python {inference_script} \
            --model_path {model_path} \
            --num_inference_step {num_inference_step} \
            --height {height} \
            --width {width} \
            --text_guidance_scale {text_guidance_scale} \
            --image_guidance_scale {image_guidance_scale} \
            --instruction \"{instruction}\" \
            --input_image_path {input_image_paths} \
            --output_image_path {output_path}"
        
        # Create a unique process ID
        process_id = str(uuid.uuid4())
        
        # Start the process
        logger.info(f"Starting process: {process_id} with command: {cmd}")
        process = subprocess.Popen(
            shlex.split(cmd),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        
        # Store process information
        active_processes[process_id] = {
            'process': process,
            'status': 'running',
            'progress': 0,
            'start_time': datetime.now().isoformat(),
            'output_path': output_path,
            'output_filename': output_filename,
            'output': [],
            'command': cmd
        }
        
        # Start monitoring thread
        monitor_thread = threading.Thread(target=monitor_process, args=(process_id,))
        monitor_thread.daemon = True
        monitor_thread.start()
        
        return jsonify({
            "process_id": process_id,
            "status": "started",
            "output_filename": output_filename
        })
    
    except Exception as e:
        logger.error(f"Error executing script: {str(e)}")
        return jsonify({"error": f"Error executing script: {str(e)}"}), 500

# Script status endpoint
@app.route('/api/status/<process_id>', methods=['GET'])
def script_status(process_id):
    logger.info(f"Status endpoint called for process: {process_id}")
    
    if process_id not in active_processes:
        return jsonify({"error": "Process not found"}), 404
    
    process_info = active_processes[process_id]
    
    # Check if process is still running
    if process_info['status'] == 'running':
        return_code = process_info['process'].poll()
        if return_code is not None:
            if return_code == 0:
                process_info['status'] = 'completed'
            else:
                process_info['status'] = 'failed'
    
    # Prepare response
    response = {
        "process_id": process_id,
        "status": process_info['status'],
        "progress": process_info['progress'],
        "start_time": process_info['start_time']
    }
    
    # Add output path if completed
    if process_info['status'] == 'completed':
        file_url = url_for('serve_image', folder='output', filename=process_info['output_filename'], _external=True)
        response["output_url"] = file_url
    
    # Add error if failed
    if process_info['status'] == 'failed' and 'error' in process_info:
        response["error"] = process_info['error']
    
    return jsonify(response)

# Script cancellation endpoint
@app.route('/api/cancel/<process_id>', methods=['POST'])
def cancel_script(process_id):
    logger.info(f"Cancel endpoint called for process: {process_id}")
    
    if process_id not in active_processes:
        return jsonify({"error": "Process not found"}), 404
    
    process_info = active_processes[process_id]
    
    # Check if process is still running
    if process_info['status'] == 'running':
        try:
            # Try to terminate the process
            process_info['process'].terminate()
            
            # Wait a bit and check if it terminated
            try:
                process_info['process'].wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force kill if it didn't terminate
                process_info['process'].kill()
            
            process_info['status'] = 'cancelled'
            logger.info(f"Process cancelled: {process_id}")
            
            return jsonify({
                "process_id": process_id,
                "status": "cancelled"
            })
        except Exception as e:
            logger.error(f"Error cancelling process: {process_id}, Error: {str(e)}")
            return jsonify({"error": f"Error cancelling process: {str(e)}"}), 500
    else:
        # Process is not running
        return jsonify({
            "process_id": process_id,
            "status": process_info['status'],
            "message": "Process is not running"
        })

if __name__ == '__main__':
    # Get port from environment variable or use default
    port = int(os.environ.get('BACKEND_PORT', 5000))
    logger.info(f"Starting OmniGen2 UI backend server on port {port}")
    app.run(debug=True, host='0.0.0.0', port=port)
