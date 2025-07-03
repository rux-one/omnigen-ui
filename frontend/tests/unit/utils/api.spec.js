import axios from 'axios';
import MockAdapter from 'axios-mock-adapter';
import ApiService from '@/utils/api';

describe('ApiService', () => {
  let mock;
  
  beforeEach(() => {
    // Create a new instance of axios-mock-adapter
    mock = new MockAdapter(axios);
  });
  
  afterEach(() => {
    // Reset the mock
    mock.reset();
  });
  
  it('should get input images', async () => {
    const mockImages = {
      images: [
        {
          filename: 'test1.jpg',
          url: 'http://localhost:5000/api/images/view/input/test1.jpg',
          size: 1024,
          created: '2025-07-03T10:00:00Z'
        }
      ]
    };
    
    // Mock the API response
    mock.onGet('http://localhost:5000/api/images/input').reply(200, mockImages);
    
    // Call the method
    const response = await ApiService.getInputImages();
    
    // Assert the response
    expect(response.data).toEqual(mockImages);
  });
  
  it('should get output images', async () => {
    const mockImages = {
      images: [
        {
          filename: 'output1.jpg',
          url: 'http://localhost:5000/api/images/view/output/output1.jpg',
          size: 1024,
          created: '2025-07-03T10:00:00Z'
        }
      ]
    };
    
    // Mock the API response
    mock.onGet('http://localhost:5000/api/images/output').reply(200, mockImages);
    
    // Call the method
    const response = await ApiService.getOutputImages();
    
    // Assert the response
    expect(response.data).toEqual(mockImages);
  });
  
  it('should upload an image', async () => {
    const mockResponse = {
      filename: 'test1.jpg',
      url: 'http://localhost:5000/api/images/view/input/test1.jpg',
      size: 1024,
      created: '2025-07-03T10:00:00Z'
    };
    
    // Mock the API response
    mock.onPost('http://localhost:5000/api/upload').reply(200, mockResponse);
    
    // Create a mock file
    const file = new File(['test'], 'test1.jpg', { type: 'image/jpeg' });
    
    // Create a mock progress callback
    const onUploadProgress = jest.fn();
    
    // Call the method
    const response = await ApiService.uploadImage(file, onUploadProgress);
    
    // Assert the response
    expect(response.data).toEqual(mockResponse);
  });
  
  it('should execute the script', async () => {
    const mockParams = {
      input_images: ['test1.jpg'],
      instruction: 'Generate a landscape',
      inference_steps: 30,
      height: 512,
      width: 512,
      guidance_scale: 7.5
    };
    
    const mockResponse = {
      process_id: 'test-process-id',
      status: 'running'
    };
    
    // Mock the API response
    mock.onPost('http://localhost:5000/api/execute').reply(200, mockResponse);
    
    // Call the method
    const response = await ApiService.executeScript(mockParams);
    
    // Assert the response
    expect(response.data).toEqual(mockResponse);
  });
  
  it('should get script status', async () => {
    const processId = 'test-process-id';
    const mockResponse = {
      status: 'running',
      progress: 50,
      output: ['Starting OmniGen2...', 'Loading model...', 'progress: 50']
    };
    
    // Mock the API response
    mock.onGet(`http://localhost:5000/api/status/${processId}`).reply(200, mockResponse);
    
    // Call the method
    const response = await ApiService.getScriptStatus(processId);
    
    // Assert the response
    expect(response.data).toEqual(mockResponse);
  });
  
  it('should cancel script execution', async () => {
    const processId = 'test-process-id';
    const mockResponse = {
      status: 'cancelled'
    };
    
    // Mock the API response
    mock.onPost(`http://localhost:5000/api/cancel/${processId}`).reply(200, mockResponse);
    
    // Call the method
    const response = await ApiService.cancelScript(processId);
    
    // Assert the response
    expect(response.data).toEqual(mockResponse);
  });
  
  it('should handle API errors', async () => {
    // Mock a 500 server error
    mock.onGet('http://localhost:5000/api/images/input').reply(500, {
      error: 'Internal Server Error',
      message: 'Something went wrong',
      path: '/api/images/input',
      method: 'GET'
    });
    
    // Call the method and expect it to throw
    await expect(ApiService.getInputImages()).rejects.toThrow();
  });
});
