import { mount } from '@vue/test-utils';
import { h } from 'vue';
import ErrorBoundary from '@/components/ErrorBoundary.vue';
import { useToast } from 'vue-toast-notification';

// Mock the toast notification
jest.mock('vue-toast-notification', () => ({
  useToast: jest.fn().mockReturnValue({
    error: jest.fn(),
  })
}));

// Create a component that will throw an error
const ErrorComponent = {
  render() {
    throw new Error('Test error');
  }
};

// Create a normal component
const NormalComponent = {
  template: '<div>Normal component</div>'
};

describe('ErrorBoundary.vue', () => {
  let wrapper;
  let mockToast;
  
  beforeEach(() => {
    // Reset mocks
    jest.clearAllMocks();
    
    // Setup toast mock
    mockToast = {
      error: jest.fn()
    };
    useToast.mockReturnValue(mockToast);
  });
  
  it('renders the default slot when no error occurs', () => {
    wrapper = mount(ErrorBoundary, {
      slots: {
        default: NormalComponent
      }
    });
    
    expect(wrapper.text()).toContain('Normal component');
    expect(wrapper.find('.error-container').exists()).toBe(false);
  });
  
  it('displays error UI when an error occurs in a child component', async () => {
    // We need to mock console.error to prevent test output pollution
    const originalConsoleError = console.error;
    console.error = jest.fn();
    
    // Mount with component that will throw
    wrapper = mount(ErrorBoundary, {
      slots: {
        default: ErrorComponent
      }
    });
    
    // Error boundary should have caught the error
    expect(wrapper.find('.error-container').exists()).toBe(true);
    expect(wrapper.find('h3').text()).toContain('Something went wrong');
    expect(wrapper.find('.error-message').text()).toContain('Test error');
    
    // Toast should have been called
    expect(mockToast.error).toHaveBeenCalledWith(
      expect.stringContaining('Test error'),
      expect.objectContaining({ duration: 5000 })
    );
    
    // Restore console.error
    console.error = originalConsoleError;
  });
  
  it('provides retry functionality', async () => {
    // Mock console.error
    const originalConsoleError = console.error;
    console.error = jest.fn();
    
    // Create a component that throws only on first render
    let renderCount = 0;
    const ThrowOnceComponent = {
      render() {
        renderCount++;
        if (renderCount === 1) {
          throw new Error('First render error');
        }
        return h('div', 'Success after retry');
      }
    };
    
    // Mount with component that will throw once
    wrapper = mount(ErrorBoundary, {
      slots: {
        default: ThrowOnceComponent
      }
    });
    
    // Error boundary should have caught the error
    expect(wrapper.find('.error-container').exists()).toBe(true);
    
    // Click retry button
    await wrapper.find('.retry-button').trigger('click');
    
    // Component should now render successfully
    expect(wrapper.find('.error-container').exists()).toBe(false);
    expect(wrapper.text()).toContain('Success after retry');
    
    // Restore console.error
    console.error = originalConsoleError;
  });
  
  it('provides reload functionality', async () => {
    // Mock window.location.reload
    const originalReload = window.location.reload;
    window.location.reload = jest.fn();
    
    // Mock console.error
    const originalConsoleError = console.error;
    console.error = jest.fn();
    
    // Mount with component that will throw
    wrapper = mount(ErrorBoundary, {
      slots: {
        default: ErrorComponent
      }
    });
    
    // Click reload button
    await wrapper.find('.reload-button').trigger('click');
    
    // Reload should have been called
    expect(window.location.reload).toHaveBeenCalled();
    
    // Restore mocks
    window.location.reload = originalReload;
    console.error = originalConsoleError;
  });
});
