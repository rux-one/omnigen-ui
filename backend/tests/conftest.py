import os
import pytest
import tempfile
import sys
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import the app
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
