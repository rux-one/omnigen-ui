import os
import json
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
from io import BytesIO
from flask import url_for

# Import the Flask app
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import app

@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test_secret_key'
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
    
    # Create temporary directories for test uploads
    with tempfile.TemporaryDirectory() as temp_input_dir, \
         tempfile.TemporaryDirectory() as temp_output_dir:
        
        # Override the upload directories
        app.config['UPLOAD_FOLDER_INPUT'] = temp_input_dir
        app.config['UPLOAD_FOLDER_OUTPUT'] = temp_output_dir
        
        # Create a test client
        with app.test_client() as client:
            yield client

@pytest.fixture
def mock_subprocess():
    """Mock subprocess for testing script execution."""
    with patch('subprocess.Popen') as mock_popen:
        # Configure the mock
        mock_process = MagicMock()
        mock_process.poll.return_value = None  # Process is running
        mock_process.stdout.readline.side_effect = [
            b'Starting OmniGen2...\n',
            b'Loading model...\n',
            b'progress: 25\n',
            b'progress: 50\n',
            b'progress: 75\n',
            b'progress: 100\n',
            b'Generation complete!\n',
            b''  # Empty string to simulate end of output
        ]
        mock_popen.return_value = mock_process
        
        yield mock_popen

def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get('/api/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'ok'
    assert 'timestamp' in data

def test_upload_file_success(client):
    """Test successful file upload."""
    # Create a test image
    test_image = BytesIO(b'fake image content')
    test_image.name = 'test.jpg'
    
    # Send the file to the upload endpoint
    response = client.post(
        '/api/upload',
        data={'file': (test_image, 'test.jpg')},
        content_type='multipart/form-data'
    )
    
    # Check the response
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'filename' in data
    assert 'url' in data
    assert 'size' in data
    assert 'created' in data
    
    # Verify the file was saved
    uploaded_files = os.listdir(app.config['UPLOAD_FOLDER_INPUT'])
    assert len(uploaded_files) == 1

def test_upload_file_invalid_extension(client):
    """Test file upload with invalid extension."""
    # Create a test file with invalid extension
    test_file = BytesIO(b'fake file content')
    test_file.name = 'test.txt'
    
    # Send the file to the upload endpoint
    response = client.post(
        '/api/upload',
        data={'file': (test_file, 'test.txt')},
        content_type='multipart/form-data'
    )
    
    # Check the response
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    assert 'Invalid file type' in data['message']

def test_upload_no_file(client):
    """Test file upload with no file."""
    # Send an empty request to the upload endpoint
    response = client.post(
        '/api/upload',
        data={},
        content_type='multipart/form-data'
    )
    
    # Check the response
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    assert 'No file part' in data['message']

def test_list_input_images(client):
    """Test listing input images."""
    # Create a test image in the input folder
    test_image_path = os.path.join(app.config['UPLOAD_FOLDER_INPUT'], 'test.jpg')
    with open(test_image_path, 'wb') as f:
        f.write(b'fake image content')
    
    # Set file modification time for testing
    os.utime(test_image_path, (1000000, 1000000))
    
    # Request the list of input images
    response = client.get('/api/images/input')
    
    # Check the response
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'images' in data
    assert len(data['images']) == 1
    assert data['images'][0]['filename'] == 'test.jpg'
    assert data['images'][0]['size'] == len(b'fake image content')

def test_list_output_images(client):
    """Test listing output images."""
    # Create a test image in the output folder
    test_image_path = os.path.join(app.config['UPLOAD_FOLDER_OUTPUT'], 'test_output.jpg')
    with open(test_image_path, 'wb') as f:
        f.write(b'fake output image content')
    
    # Set file modification time for testing
    os.utime(test_image_path, (1000000, 1000000))
    
    # Request the list of output images
    response = client.get('/api/images/output')
    
    # Check the response
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'images' in data
    assert len(data['images']) == 1
    assert data['images'][0]['filename'] == 'test_output.jpg'
    assert data['images'][0]['size'] == len(b'fake output image content')

def test_serve_image(client):
    """Test serving an image."""
    # Create a test image in the input folder
    test_image_path = os.path.join(app.config['UPLOAD_FOLDER_INPUT'], 'test.jpg')
    with open(test_image_path, 'wb') as f:
        f.write(b'fake image content')
    
    # Request the image
    response = client.get('/api/images/view/input/test.jpg')
    
    # Check the response
    assert response.status_code == 200
    assert response.data == b'fake image content'
    assert response.headers['Content-Type'] == 'image/jpeg'

def test_serve_nonexistent_image(client):
    """Test serving a nonexistent image."""
    # Request a nonexistent image
    response = client.get('/api/images/view/input/nonexistent.jpg')
    
    # Check the response
    assert response.status_code == 404
    data = json.loads(response.data)
    assert 'error' in data
    assert 'Not Found' in data['error']

def test_execute_script(client, mock_subprocess):
    """Test executing the OmniGen2 script."""
    # Prepare the request data
    request_data = {
        'input_images': ['test.jpg'],
        'instruction': 'Generate a landscape',
        'inference_steps': 30,
        'height': 512,
        'width': 512,
        'guidance_scale': 7.5
    }
    
    # Send the request to execute the script
    response = client.post(
        '/api/execute',
        data=json.dumps(request_data),
        content_type='application/json'
    )
    
    # Check the response
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'process_id' in data
    assert 'status' in data
    assert data['status'] == 'running'

def test_execute_script_missing_params(client):
    """Test executing the script with missing parameters."""
    # Prepare the request data with missing parameters
    request_data = {
        'input_images': ['test.jpg']
        # Missing required parameters
    }
    
    # Send the request to execute the script
    response = client.post(
        '/api/execute',
        data=json.dumps(request_data),
        content_type='application/json'
    )
    
    # Check the response
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    assert 'Missing required parameters' in data['message']

@patch('app.processes')
def test_get_script_status(mock_processes, client):
    """Test getting the status of a running script."""
    # Set up a mock process
    process_id = 'test-process-id'
    mock_processes[process_id] = {
        'status': 'running',
        'progress': 50,
        'output': ['Starting OmniGen2...', 'Loading model...', 'progress: 50'],
        'output_image': None,
        'error': None
    }
    
    # Request the status
    response = client.get(f'/api/status/{process_id}')
    
    # Check the response
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'running'
    assert data['progress'] == 50
    assert 'output' in data
    assert len(data['output']) == 3

@patch('app.processes')
def test_get_nonexistent_script_status(mock_processes, client):
    """Test getting the status of a nonexistent script."""
    # Request the status of a nonexistent process
    response = client.get('/api/status/nonexistent-id')
    
    # Check the response
    assert response.status_code == 404
    data = json.loads(response.data)
    assert 'error' in data
    assert 'Process not found' in data['message']

@patch('app.processes')
@patch('app.subprocess.Popen')
def test_cancel_script(mock_popen, mock_processes, client):
    """Test cancelling a running script."""
    # Set up a mock process
    process_id = 'test-process-id'
    mock_process = MagicMock()
    mock_processes[process_id] = {
        'status': 'running',
        'progress': 50,
        'output': ['Starting OmniGen2...', 'Loading model...', 'progress: 50'],
        'output_image': None,
        'error': None,
        'process': mock_process
    }
    
    # Send the cancel request
    response = client.post(f'/api/cancel/{process_id}')
    
    # Check the response
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'cancelled'
    
    # Verify the process was terminated
    mock_process.terminate.assert_called_once()

@patch('app.processes')
def test_cancel_nonexistent_script(mock_processes, client):
    """Test cancelling a nonexistent script."""
    # Send the cancel request for a nonexistent process
    response = client.post('/api/cancel/nonexistent-id')
    
    # Check the response
    assert response.status_code == 404
    data = json.loads(response.data)
    assert 'error' in data
    assert 'Process not found' in data['message']

def test_not_found(client):
    """Test 404 error handler."""
    # Request a nonexistent endpoint
    response = client.get('/api/nonexistent')
    
    # Check the response
    assert response.status_code == 404
    data = json.loads(response.data)
    assert 'error' in data
    assert 'Not Found' in data['error']

def test_method_not_allowed(client):
    """Test 405 error handler."""
    # Send a POST request to an endpoint that only accepts GET
    response = client.post('/api/health')
    
    # Check the response
    assert response.status_code == 405
    data = json.loads(response.data)
    assert 'error' in data
    assert 'Method Not Allowed' in data['error']
