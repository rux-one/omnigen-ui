<template>
  <div class="image-generation-container">
    <h2>Generate Images with OmniGen2</h2>
    
    <div class="section">
      <h3>1. Select Input Images</h3>
      <div v-if="loading" class="loading">Loading images...</div>
      <div v-else-if="inputImages.length === 0" class="no-images">
        No input images available. Please upload images first.
      </div>
      <div v-else class="image-selection">
        <div 
          v-for="image in inputImages" 
          :key="image.filename" 
          class="image-item"
          :class="{ selected: selectedImages.includes(image.filename) }"
          @click="toggleImageSelection(image.filename)"
        >
          <img :src="image.url" :alt="image.filename" />
          <div class="image-info">
            <span class="image-name">{{ image.filename.substring(0, 8) }}...</span>
          </div>
          <div class="selection-overlay" v-if="selectedImages.includes(image.filename)">
            <span class="selection-number">{{ selectedImages.indexOf(image.filename) + 1 }}</span>
          </div>
        </div>
      </div>
      <div class="selection-info" v-if="selectedImages.length > 0">
        <p>{{ selectedImages.length }} image(s) selected</p>
        <button @click="clearSelection" class="secondary-button">Clear Selection</button>
      </div>
    </div>
    
    <div class="section">
      <h3>2. Configure Model Parameters</h3>
      <ModelConfig 
        ref="modelConfigRef"
        :initialImages="selectedImages" 
        @generation-started="onGenerationStarted"
        @generation-progress="onGenerationProgress"
        @generation-completed="onGenerationCompleted"
        @generation-error="onGenerationError"
        @generation-cancelled="onGenerationCancelled"
      />
    </div>
    
    <div class="section">
      <h3>3. Generate Image</h3>
      <button 
        @click="startGeneration" 
        :disabled="selectedImages.length === 0 || isGenerating"
        class="generate-button"
      >
        {{ isGenerating ? 'Generating...' : 'Generate Image' }}
      </button>
    </div>
    
    <div class="section" v-if="isGenerating || generationResult">
      <h3>4. Generation Status</h3>
      <div v-if="isGenerating" class="generation-status">
        <div class="progress-container">
          <div class="progress-bar" :style="{ width: `${generationProgress}%` }"></div>
        </div>
        <p>{{ generationProgress }}% complete</p>
        <button @click="cancelGeneration" class="cancel-button">Cancel Generation</button>
      </div>
      <div v-else-if="generationResult" class="generation-result">
        <div v-if="generationResult.status === 'completed'" class="result-success">
          <h4>Generation Completed!</h4>
          <div class="result-image">
            <img :src="generationResult.output_url" alt="Generated image" />
          </div>
        </div>
        <div v-else-if="generationResult.status === 'failed'" class="result-error">
          <h4>Generation Failed</h4>
          <p class="error-message">{{ generationResult.error || 'Unknown error occurred' }}</p>
        </div>
        <div v-else-if="generationResult.status === 'cancelled'" class="result-cancelled">
          <h4>Generation Cancelled</h4>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue';
import { useToast } from 'vue-toast-notification';
import ApiService from '../utils/api';
import ModelConfig from './ModelConfig.vue';

export default {
  name: 'ImageGeneration',
  components: {
    ModelConfig
  },
  setup() {
    const $toast = useToast();
    const inputImages = ref([]);
    const selectedImages = ref([]);
    const loading = ref(true);
    const isGenerating = ref(false);
    const generationProgress = ref(0);
    const generationResult = ref(null);
    const currentProcessId = ref(null);
    const statusCheckInterval = ref(null);
    const modelConfigRef = ref(null);

    // Fetch input images on component mount
    onMounted(() => {
      fetchInputImages();
    });

    // Fetch input images from API
    const fetchInputImages = async () => {
      loading.value = true;
      try {
        const response = await ApiService.getInputImages();
        inputImages.value = response.data.images;
      } catch (error) {
        console.error('Error fetching input images:', error);
        $toast.error(`Failed to load input images: ${error.message}`);
      } finally {
        loading.value = false;
      }
    };

    // Toggle image selection
    const toggleImageSelection = (filename) => {
      const index = selectedImages.value.indexOf(filename);
      if (index === -1) {
        selectedImages.value.push(filename);
      } else {
        selectedImages.value.splice(index, 1);
      }
    };

    // Clear image selection
    const clearSelection = () => {
      selectedImages.value = [];
    };
    
    // Start generation using the ModelConfig component
    const startGeneration = () => {
      if (selectedImages.value.length === 0) {
        $toast.error('Please select at least one input image');
        return;
      }
      
      // Trigger the form submission in the ModelConfig component
      if (modelConfigRef.value && typeof modelConfigRef.value.submitForm === 'function') {
        modelConfigRef.value.submitForm();
      } else {
        $toast.error('Model configuration component not ready');
      }
    };
    
    // Event handlers for ModelConfig component
    const onGenerationStarted = () => {
      isGenerating.value = true;
      generationProgress.value = 0;
      generationResult.value = null;
    };

    const onGenerationProgress = (data) => {
      if (data.progress) {
        generationProgress.value = data.progress;
      }
      if (data.processId) {
        currentProcessId.value = data.processId;
      }
    };

    const onGenerationCompleted = (outputImage) => {
      isGenerating.value = false;
      if (outputImage) {
        generationResult.value = {
          status: 'completed',
          output_url: `http://localhost:5000/api/images/view/output/${outputImage}`
        };
      }
    };

    const onGenerationError = (err) => {
      isGenerating.value = false;
      generationResult.value = {
        status: 'failed',
        error: typeof err === 'string' ? err : 'Unknown error occurred'
      };
    };

    const onGenerationCancelled = () => {
      isGenerating.value = false;
      generationResult.value = {
        status: 'cancelled'
      };
    };

    const cancelGeneration = async () => {
      if (!currentProcessId.value || !isGenerating.value) return;
      
      try {
        await ApiService.cancelScript(currentProcessId.value);
        clearInterval(statusCheckInterval.value);
        isGenerating.value = false;
        generationResult.value = {
          status: 'cancelled'
        };
        $toast.info('Image generation cancelled');
      } catch (error) {
        console.error('Error cancelling generation:', error);
        $toast.error(`Failed to cancel generation: ${error.message}`);
      }
    };
    
    return {
      inputImages,
      selectedImages,
      loading,
      isGenerating,
      generationProgress,
      generationResult,
      toggleImageSelection,
      clearSelection,
      startGeneration,
      onGenerationStarted,
      onGenerationProgress,
      onGenerationCompleted,
      onGenerationError,
      onGenerationCancelled,
      cancelGeneration,
      modelConfigRef
    };
  }
};
</script>

<style scoped>
.image-generation-container {
  max-width: 100%;
}

.section {
  margin-bottom: 30px;
  padding: 20px;
  background-color: #f9f9f9;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

h2 {
  color: var(--primary-color);
  margin-bottom: 20px;
}

h3 {
  color: var(--secondary-color);
  margin-bottom: 15px;
  font-size: 1.2rem;
  border-bottom: 1px solid #eee;
  padding-bottom: 10px;
}

.loading, .no-images {
  text-align: center;
  padding: 20px;
  color: #666;
}

.image-selection {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 15px;
  margin-top: 15px;
}

.image-item {
  position: relative;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.image-item:hover {
  transform: translateY(-3px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.image-item.selected {
  border: 3px solid var(--primary-color);
}

.image-item img {
  width: 100%;
  height: 120px;
  object-fit: cover;
  display: block;
}

.image-info {
  padding: 8px;
  background-color: rgba(0, 0, 0, 0.03);
  font-size: 0.8rem;
}

.selection-overlay {
  position: absolute;
  top: 5px;
  right: 5px;
  background-color: var(--primary-color);
  color: white;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 0.8rem;
}

.selection-info {
  margin-top: 15px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
  color: var(--secondary-color);
}

.form-group input, .form-group textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
}

.parameters-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 15px;
}

.generate-button {
  background-color: var(--accent-color);
  color: white;
  padding: 12px 24px;
  font-size: 1.1rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.generate-button:hover:not(:disabled) {
  background-color: #c0392b;
}

.generate-button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

.secondary-button {
  background-color: #95a5a6;
  color: white;
  padding: 8px 16px;
  font-size: 0.9rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.secondary-button:hover {
  background-color: #7f8c8d;
}

.cancel-button {
  background-color: #e74c3c;
  color: white;
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  margin-top: 10px;
}

.cancel-button:hover {
  background-color: #c0392b;
}

.progress-container {
  width: 100%;
  height: 20px;
  background-color: #eee;
  border-radius: 10px;
  overflow: hidden;
  margin-bottom: 10px;
}

.progress-bar {
  height: 100%;
  background-color: var(--primary-color);
  transition: width 0.3s ease;
}

.generation-status {
  padding: 15px;
  background-color: #f5f5f5;
  border-radius: 8px;
}

.generation-result {
  padding: 15px;
  border-radius: 8px;
}

.result-success {
  color: #2ecc71;
}

.result-error {
  color: #e74c3c;
}

.result-cancelled {
  color: #f39c12;
}

.error-message {
  background-color: #ffecec;
  padding: 10px;
  border-radius: 4px;
  color: #e74c3c;
  margin-top: 10px;
  white-space: pre-wrap;
}

.result-image {
  margin-top: 15px;
  text-align: center;
}

.result-image img {
  max-width: 100%;
  max-height: 500px;
  border-radius: 8px;
  box-shadow: 0 3px 10px rgba(0, 0, 0, 0.1);
}
</style>
