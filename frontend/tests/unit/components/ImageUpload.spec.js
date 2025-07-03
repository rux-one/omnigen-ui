import { shallowMount, mount } from '@vue/test-utils';
import { nextTick } from 'vue';
import ImageUpload from '@/components/ImageUpload.vue';
import ApiService from '@/utils/api';
import { useToast } from 'vue-toast-notification';

// Mock the API service
jest.mock('@/utils/api', () => ({
  getInputImages: jest.fn(),
  uploadImage: jest.fn()
}));

// Mock the toast notification
jest.mock('vue-toast-notification', () => ({
  useToast: jest.fn().mockReturnValue({
    success: jest.fn(),
    error: jest.fn(),
    info: jest.fn()
  })
}));

describe('ImageUpload.vue', () => {
  let wrapper;
  let mockToast;
  
  beforeEach(() => {
    // Reset mocks
    jest.clearAllMocks();
    
    // Setup toast mock
    mockToast = {
      success: jest.fn(),
      error: jest.fn(),
      info: jest.fn()
    };
    useToast.mockReturnValue(mockToast);
    
    // Mock API responses
    ApiService.getInputImages.mockResolvedValue({
      data: {
        images: [
          {
            filename: 'test1.jpg',
            url: 'http://localhost:5000/api/images/view/input/test1.jpg',
            size: 1024,
            created: '2025-07-03T10:00:00Z'
          },
          {
            filename: 'test2.png',
            url: 'http://localhost:5000/api/images/view/input/test2.png',
            size: 2048,
            created: '2025-07-03T11:00:00Z'
          }
        ]
      }
    });
    
    // Mount the component
    wrapper = shallowMount(ImageUpload);
  });
  
  it('renders the component correctly', () => {
    expect(wrapper.find('.image-upload-container').exists()).toBe(true);
    expect(wrapper.find('h2').text()).toBe('Image Upload');
    expect(wrapper.find('.dropzone-container').exists()).toBe(true);
  });
  
  it('fetches images on mount', async () => {
    expect(ApiService.getInputImages).toHaveBeenCalledTimes(1);
    await nextTick();
    expect(wrapper.vm.uploadedImages.length).toBe(2);
  });
  
  it('handles drag and drop events', async () => {
    // Test drag enter
    await wrapper.find('.dropzone-container').trigger('dragenter');
    expect(wrapper.vm.isDragging).toBe(true);
    
    // Test drag leave
    await wrapper.find('.dropzone-container').trigger('dragleave');
    expect(wrapper.vm.isDragging).toBe(false);
  });
  
  it('formats file size correctly', () => {
    expect(wrapper.vm.formatFileSize(500)).toBe('500 B');
    expect(wrapper.vm.formatFileSize(1500)).toBe('1.5 KB');
    expect(wrapper.vm.formatFileSize(1500000)).toBe('1.4 MB');
  });
  
  it('formats date correctly', () => {
    const date = new Date('2025-07-03T10:00:00Z');
    const formatted = wrapper.vm.formatDate('2025-07-03T10:00:00Z');
    expect(formatted).toContain(date.toLocaleDateString());
  });
  
  it('validates file types', async () => {
    // Create a mock file with invalid type
    const invalidFile = new File(['test'], 'test.txt', { type: 'text/plain' });
    
    // Mock the FileList
    const dataTransfer = {
      files: [invalidFile]
    };
    
    // Trigger drop event
    await wrapper.find('.dropzone-container').trigger('drop', { dataTransfer });
    
    // Check error message
    expect(wrapper.vm.errorMessage).toContain('Invalid file type');
    expect(ApiService.uploadImage).not.toHaveBeenCalled();
  });
  
  it('uploads valid files', async () => {
    // Setup successful upload mock
    ApiService.uploadImage.mockResolvedValue({
      data: {
        filename: 'test3.jpg',
        url: 'http://localhost:5000/api/images/view/input/test3.jpg',
        size: 3072,
        created: '2025-07-03T12:00:00Z'
      }
    });
    
    // Create a mock file with valid type
    const validFile = new File(['test'], 'test3.jpg', { type: 'image/jpeg' });
    
    // Call the uploadFile method directly
    await wrapper.vm.uploadFile(validFile);
    
    // Verify API was called
    expect(ApiService.uploadImage).toHaveBeenCalledWith(validFile, expect.any(Function));
    expect(mockToast.success).toHaveBeenCalled();
    expect(ApiService.getInputImages).toHaveBeenCalledTimes(2); // Initial + after upload
  });
  
  it('handles upload errors', async () => {
    // Setup failed upload mock
    const errorMessage = 'Network error';
    ApiService.uploadImage.mockRejectedValue({ message: errorMessage });
    
    // Create a mock file with valid type
    const validFile = new File(['test'], 'test3.jpg', { type: 'image/jpeg' });
    
    // Call the uploadFile method and catch the error
    try {
      await wrapper.vm.uploadFile(validFile);
    } catch (error) {
      expect(error.message).toBe(errorMessage);
    }
    
    // Verify error was logged
    expect(ApiService.uploadImage).toHaveBeenCalledWith(validFile, expect.any(Function));
    expect(mockToast.success).not.toHaveBeenCalled();
  });
});
