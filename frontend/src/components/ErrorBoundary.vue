<template>
  <div>
    <div v-if="error" class="error-boundary">
      <div class="error-content">
        <h3>Something went wrong</h3>
        <p>{{ errorMessage }}</p>
        <div class="error-actions">
          <button @click="resetError" class="retry-button">Try Again</button>
          <button @click="reloadPage" class="reload-button">Reload Page</button>
        </div>
      </div>
    </div>
    <slot v-else></slot>
  </div>
</template>

<script>
import { ref, onErrorCaptured } from 'vue';
import { useToast } from 'vue-toast-notification';

export default {
  name: 'ErrorBoundary',
  props: {
    component: {
      type: String,
      default: 'Component'
    }
  },
  
  setup(props) {
    const $toast = useToast();
    const error = ref(null);
    const errorMessage = ref('');
    
    onErrorCaptured((err, instance, info) => {
      error.value = err;
      errorMessage.value = `${err.message || 'An unexpected error occurred'}`;
      
      // Log the error
      console.error(`Error in ${props.component}:`, err);
      console.error('Component:', instance);
      console.error('Error Info:', info);
      
      // Show toast notification
      $toast.error(`Error in ${props.component}: ${err.message || 'An unexpected error occurred'}`);
      
      // Prevent error from propagating further
      return false;
    });
    
    const resetError = () => {
      error.value = null;
      errorMessage.value = '';
    };
    
    const reloadPage = () => {
      window.location.reload();
    };
    
    return {
      error,
      errorMessage,
      resetError,
      reloadPage
    };
  }
};
</script>

<style scoped>
.error-boundary {
  background-color: #fff0f0;
  border: 1px solid #ffcccc;
  border-radius: 8px;
  padding: 20px;
  margin: 20px 0;
  box-shadow: 0 2px 10px rgba(255, 0, 0, 0.1);
}

.error-content {
  text-align: center;
}

.error-content h3 {
  color: #e74c3c;
  margin-bottom: 10px;
}

.error-content p {
  color: #333;
  margin-bottom: 20px;
  white-space: pre-wrap;
}

.error-actions {
  display: flex;
  justify-content: center;
  gap: 10px;
}

.retry-button, .reload-button {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.3s;
}

.retry-button {
  background-color: #3498db;
  color: white;
}

.retry-button:hover {
  background-color: #2980b9;
}

.reload-button {
  background-color: #95a5a6;
  color: white;
}

.reload-button:hover {
  background-color: #7f8c8d;
}
</style>
