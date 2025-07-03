import { mount, flushPromises } from '@vue/test-utils';
import { nextTick } from 'vue';
import ModelConfig from '@/components/ModelConfig.vue';
import ApiService from '@/utils/api';
import { useToast } from 'vue-toast-notification';

// Mock the ApiService
jest.mock('@/utils/api', () => ({
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

// Mock vue-multiselect component
jest.mock('vue-multiselect', () => ({
  __esModule: true,
  default: {
    name: 'VueMultiselect',
    template: '<div class="mock-multiselect"><slot name="selection" :values="modelValue"></slot></div>',
    props: ['modelValue', 'options', 'multiple', 'label', 'trackBy']
  }
}));

describe('ModelConfig.vue', () => {
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
    jest.useRealTimers();
  });

  const createWrapper = (props = {}) => {
    return mount(ModelConfig, {
      props: {
        initialImages: [],
        ...props
      },
      global: {
        stubs: {
          VueMultiselect: true
        }
      }
    });
  };

  test('renders correctly with default props', async () => {
    wrapper = createWrapper();
    
    expect(wrapper.find('textarea[name="instruction"]').exists()).toBe(true);
    expect(wrapper.find('input[name="num_inference_step"]').exists()).toBe(true);
    expect(wrapper.find('select[name="height"]').exists()).toBe(true);
    expect(wrapper.find('select[name="width"]').exists()).toBe(true);
    expect(wrapper.find('input[name="guidance_scale"]').exists()).toBe(true);
  });

  test('validates form fields correctly', async () => {
    wrapper = createWrapper();
    
    // Submit form without filling required fields
    await wrapper.find('form').trigger('submit');
    await flushPromises();
    
    // Check validation errors
    expect(wrapper.text()).toContain('Instruction is required');
    expect(ApiService.executeScript).not.toHaveBeenCalled();
  });

  test('submits form successfully when valid', async () => {
    wrapper = createWrapper({
      initialImages: ['test-image.jpg']
    });
    
    // Fill required fields
    await wrapper.find('textarea[name="instruction"]').setValue('Test instruction');
    await wrapper.find('input[name="num_inference_step"]').setValue(30);
    await wrapper.find('select[name="height"]').setValue('512');
    await wrapper.find('select[name="width"]').setValue('512');
    await wrapper.find('input[name="guidance_scale"]').setValue(7.5);
    
    // Submit form
    await wrapper.find('form').trigger('submit');
    await flushPromises();
    
    // Check API call
    expect(ApiService.executeScript).toHaveBeenCalledWith({
      input_images: ['test-image.jpg'],
      instruction: 'Test instruction',
      num_inference_step: 30,
      height: 512,
      width: 512,
      guidance_scale: 7.5
    });
    
    // Check emitted events
    expect(wrapper.emitted('generation-started')).toBeTruthy();
  });

  test('handles API error on submit', async () => {
    // Mock API error
    ApiService.executeScript.mockRejectedValueOnce(new Error('API error'));
    
    wrapper = createWrapper({
      initialImages: ['test-image.jpg']
    });
    
    // Fill required fields
    await wrapper.find('textarea[name="instruction"]').setValue('Test instruction');
    
    // Submit form
    await wrapper.find('form').trigger('submit');
    await flushPromises();
    
    // Check error handling
    expect(mockToast.error).toHaveBeenCalled();
    expect(wrapper.emitted('generation-error')).toBeTruthy();
  });

  test('polls for status updates after submission', async () => {
    jest.useFakeTimers();
    
    wrapper = createWrapper({
      initialImages: ['test-image.jpg']
    });
    
    // Fill required fields
    await wrapper.find('textarea[name="instruction"]').setValue('Test instruction');
    
    // Submit form
    await wrapper.find('form').trigger('submit');
    await flushPromises();
    
    // Advance timers to trigger polling
    jest.advanceTimersByTime(2000);
    await flushPromises();
    
    // Check status polling
    expect(ApiService.getScriptStatus).toHaveBeenCalledWith('test-process-id');
    expect(wrapper.emitted('generation-progress')).toBeTruthy();
    
    // Mock completion
    ApiService.getScriptStatus.mockResolvedValueOnce({
      data: {
        status: 'completed',
        output_image: 'output-image.jpg'
      }
    });
    
    // Advance timers again
    jest.advanceTimersByTime(2000);
    await flushPromises();
    
    // Check completion handling
    expect(wrapper.emitted('generation-completed')).toBeTruthy();
  });

  test('cancels generation successfully', async () => {
    wrapper = createWrapper();
    
    // Set up generation in progress
    wrapper.vm.isGenerating = true;
    wrapper.vm.processId = 'test-process-id';
    await nextTick();
    
    // Click cancel button
    await wrapper.find('button.cancel-button').trigger('click');
    await flushPromises();
    
    // Check cancellation
    expect(ApiService.cancelScript).toHaveBeenCalledWith('test-process-id');
    expect(wrapper.emitted('generation-cancelled')).toBeTruthy();
  });

  test('exposes submitForm method for external triggering', async () => {
    wrapper = createWrapper({
      initialImages: ['test-image.jpg']
    });
    
    // Fill required fields
    await wrapper.find('textarea[name="instruction"]').setValue('Test instruction');
    
    // Call submitForm method directly
    wrapper.vm.submitForm();
    await flushPromises();
    
    // Check API call was made
    expect(ApiService.executeScript).toHaveBeenCalled();
  });
});
