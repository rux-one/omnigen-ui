import unittest
import os
import json
import tempfile
import shutil
from app import app, INPUT_FOLDER, OUTPUT_FOLDER
from io import BytesIO

class FlaskAppTestCase(unittest.TestCase):
    def setUp(self):
        # Create temporary directories for testing
        self.test_input_folder = tempfile.mkdtemp()
        self.test_output_folder = tempfile.mkdtemp()
        
        # Store original paths
        self.original_input_folder = INPUT_FOLDER
        self.original_output_folder = OUTPUT_FOLDER
        
        # Override paths for testing
        app.config['INPUT_FOLDER'] = self.test_input_folder
        app.config['OUTPUT_FOLDER'] = self.test_output_folder
        
        # Configure the app for testing
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()
        
    def tearDown(self):
        # Remove test directories
        shutil.rmtree(self.test_input_folder)
        shutil.rmtree(self.test_output_folder)
        
    def test_health_check(self):
        """Test the health check endpoint"""
        response = self.client.get('/api/health')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'ok')
        self.assertIn('timestamp', data)
        
    def test_upload_file_no_file(self):
        """Test upload endpoint with no file"""
        response = self.client.post('/api/upload')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
        
    def test_upload_file_empty_filename(self):
        """Test upload endpoint with empty filename"""
        response = self.client.post(
            '/api/upload',
            data={'file': (BytesIO(b''), '')},
            content_type='multipart/form-data'
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
        
    def test_upload_file_invalid_type(self):
        """Test upload endpoint with invalid file type"""
        response = self.client.post(
            '/api/upload',
            data={'file': (BytesIO(b'test data'), 'test.txt')},
            content_type='multipart/form-data'
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn('Invalid file type', data['error'])
        
    def test_upload_file_success(self):
        """Test successful file upload"""
        # Create a test image (just bytes, not a real image but sufficient for test)
        test_image = BytesIO(b'fake image content')
        
        response = self.client.post(
            '/api/upload',
            data={'file': (test_image, 'test.jpg')},
            content_type='multipart/form-data'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('filename', data)
        self.assertIn('path', data)
        self.assertIn('message', data)
        self.assertEqual(data['message'], 'File uploaded successfully')
        
    def test_list_input_images_empty(self):
        """Test listing input images when directory is empty"""
        response = self.client.get('/api/images/input')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('images', data)
        self.assertEqual(len(data['images']), 0)
        
    def test_list_output_images_empty(self):
        """Test listing output images when directory is empty"""
        response = self.client.get('/api/images/output')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('images', data)
        self.assertEqual(len(data['images']), 0)
        
    def test_list_input_images_with_files(self):
        """Test listing input images with files present"""
        # Create a test file in the input directory
        with open(os.path.join(self.test_input_folder, 'test.jpg'), 'wb') as f:
            f.write(b'test image content')
            
        response = self.client.get('/api/images/input')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('images', data)
        self.assertEqual(len(data['images']), 1)
        self.assertEqual(data['images'][0]['filename'], 'test.jpg')
        
    def test_serve_image_not_found(self):
        """Test serving an image that doesn't exist"""
        response = self.client.get('/api/images/view/input/nonexistent.jpg')
        self.assertEqual(response.status_code, 404)
        
    def test_serve_image_invalid_folder(self):
        """Test serving an image with invalid folder"""
        response = self.client.get('/api/images/view/invalid/test.jpg')
        self.assertEqual(response.status_code, 404)
        
    def test_serve_image_success(self):
        """Test successfully serving an image"""
        # Create a test file in the input directory
        test_content = b'test image content'
        with open(os.path.join(self.test_input_folder, 'test.jpg'), 'wb') as f:
            f.write(test_content)
            
        response = self.client.get('/api/images/view/input/test.jpg')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, test_content)
        
    def test_execute_script_invalid_data(self):
        """Test execute endpoint with invalid data"""
        response = self.client.post(
            '/api/execute',
            json={},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
        
    def test_check_status_not_found(self):
        """Test checking status of nonexistent process"""
        response = self.client.get('/api/status/nonexistent-id')
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertIn('error', data)
        
    def test_cancel_execution_not_found(self):
        """Test cancelling nonexistent process"""
        response = self.client.post('/api/cancel/nonexistent-id')
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertIn('error', data)
        
if __name__ == '__main__':
    unittest.main()
