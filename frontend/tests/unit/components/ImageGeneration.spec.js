import { mount, flushPromises } from '@vue/test-utils';
import { nextTick } from 'vue';
import ImageGeneration from '@/components/ImageGeneration.vue';
import ModelConfig from '@/components/ModelConfig.vue';
import ApiService from '@/utils/api';
import { useToast } from 'vue-toast-notification';

// Mock the ApiService
jest.mock('@/utils/api', () => ({
  getInputImages: jest.fn(),
  executeScript: jest.fn(),
  getScriptStatus: jest.fn(),
  cancelScript: jest.fn()
}));

// Mock vue-toast-notification
jest.mock('vue-toast-notification', () => ({
  useToast: jest.fn(() => ({
    success: jest.fn(),
    error: jest.fn(),
    info: jest.fn()
  }))
}));

// Mock ModelConfig component
jest.mock('@/components/ModelConfig.vue', () => ({
  name: 'ModelConfig',
  template: '<div class="mock-model-config"></div>',
  props: ['initialImages'],
  methods: {
    submitForm: jest.fn()
  }
}));

describe('ImageGeneration.vue', () => {
  let wrapper;
  let mockToast;

  beforeEach(() => {
    jest.clearAllMocks();
    mockToast = {
      success: jest.fn(),
      error: jest.fn(),
      info: jest.fn()
    };
    useToast.mockReturnValue(mockToast);

    // Default mock implementations
    ApiService.getInputImages.mockResolvedValue({
      data: {
        images: [
          { filename: 'test1.jpg', url: 'http://localhost:5000/api/images/view/input/test1.jpg' },
          { filename: 'test2.jpg', url: 'http://localhost:5000/api/images/view/input/test2.jpg' }
        ]
      }
    });
    ApiService.executeScript.mockResolvedValue({ data: { process_id: 'test-process-id' } });
    ApiService.getScriptStatus.mockResolvedValue({ 
      data: { 
        status: 'running', 
        progress: 50, 
        output: ['Processing...'] 
      } 
    });
  });

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount();
    }
  });

  const createWrapper = () => {
    return mount(ImageGeneration, {
      global: {
        stubs: {
          ModelConfig: true
        }
      }
    });
  };

  test('fetches input images on mount', async () => {
    wrapper = createWrapper();
    await flushPromises();
    
    expect(ApiService.getInputImages).toHaveBeenCalled();
    expect(wrapper.vm.inputImages.length).toBe(2);
    expect(wrapper.vm.loading).toBe(false);
  });

  test('handles image selection correctly', async () => {
    wrapper = createWrapper();
    await flushPromises();
    
    // Select an image
    await wrapper.vm.toggleImageSelection('test1.jpg');
    expect(wrapper.vm.selectedImages).toContain('test1.jpg');
    
    // Select another image
    await wrapper.vm.toggleImageSelection('test2.jpg');
    expect(wrapper.vm.selectedImages).toContain('test2.jpg');
    
    // Deselect an image
    await wrapper.vm.toggleImageSelection('test1.jpg');
    expect(wrapper.vm.selectedImages).not.toContain('test1.jpg');
    
    // Clear selection
    await wrapper.vm.clearSelection();
    expect(wrapper.vm.selectedImages.length).toBe(0);
  });

  test('starts generation when button is clicked', async () => {
    wrapper = createWrapper();
    await flushPromises();
    
    // Select an image
    await wrapper.vm.toggleImageSelection('test1.jpg');
    
    // Mock the ModelConfig ref
    wrapper.vm.modelConfigRef = {
      submitForm: jest.fn()
    };
    
    // Click generate button
    await wrapper.find('button.generate-button').trigger('click');
    
    // Check if ModelConfig submitForm was called
    expect(wrapper.vm.modelConfigRef.submitForm).toHaveBeenCalled();
  });

  test('shows error toast when no images are selected', async () => {
    wrapper = createWrapper();
    await flushPromises();
    
    // Click generate button without selecting images
    await wrapper.find('button.generate-button').trigger('click');
    
    // Check error toast
    expect(mockToast.error).toHaveBeenCalledWith('Please select at least one input image');
  });

  test('handles generation events correctly', async () => {
    wrapper = createWrapper();
    await flushPromises();
    
    // Test onGenerationStarted
    wrapper.vm.onGenerationStarted();
    expect(wrapper.vm.isGenerating).toBe(true);
    expect(wrapper.vm.generationProgress).toBe(0);
    expect(wrapper.vm.generationResult).toBe(null);
    
    // Test onGenerationProgress
    wrapper.vm.onGenerationProgress({ progress: 75, processId: 'test-process-id' });
    expect(wrapper.vm.generationProgress).toBe(75);
    expect(wrapper.vm.currentProcessId).toBe('test-process-id');
    
    // Test onGenerationCompleted
    wrapper.vm.onGenerationCompleted('output-test.jpg');
    expect(wrapper.vm.isGenerating).toBe(false);
    expect(wrapper.vm.generationResult.status).toBe('completed');
    expect(wrapper.vm.generationResult.output_url).toContain('output-test.jpg');
    
    // Test onGenerationError
    wrapper.vm.onGenerationError('Test error');
    expect(wrapper.vm.isGenerating).toBe(false);
    expect(wrapper.vm.generationResult.status).toBe('failed');
    expect(wrapper.vm.generationResult.error).toBe('Test error');
    
    // Test onGenerationCancelled
    wrapper.vm.onGenerationCancelled();
    expect(wrapper.vm.isGenerating).toBe(false);
    expect(wrapper.vm.generationResult.status).toBe('cancelled');
  });

  test('cancels generation successfully', async () => {
    wrapper = createWrapper();
    await flushPromises();
    
    // Set up generation in progress
    wrapper.vm.isGenerating = true;
    wrapper.vm.currentProcessId = 'test-process-id';
    await nextTick();
    
    // Call cancel generation
    await wrapper.vm.cancelGeneration();
    
    // Check cancellation
    expect(ApiService.cancelScript).toHaveBeenCalledWith('test-process-id');
    expect(wrapper.vm.isGenerating).toBe(false);
    expect(wrapper.vm.generationResult.status).toBe('cancelled');
  });
});
