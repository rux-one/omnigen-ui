<template>
  <div class="model-config-container">
    <h2>Model Configuration</h2>
    
    <form @submit.prevent="submitForm" class="config-form">
      <!-- Image Selection -->
      <div class="form-group">
        <label for="input-images">Input Images</label>
        <div class="multiselect-container">
          <Multiselect
            v-model="form.input_images"
            mode="tags"
            :searchable="true"
            :createTag="false"
            :options="availableImages"
            :classes="{
              container: 'multiselect-custom',
              tag: 'multiselect-tag',
              remove: 'multiselect-tag-remove'
            }"
            placeholder="Select input images"
            label="filename"
            valueProp="filename"
            track-by="filename"
          >
            <template #tag="{ option, handleTagRemove, disabled }">
              <div class="multiselect-tag">
                {{ option.filename }}
                <span
                  v-if="!disabled"
                  class="multiselect-tag-remove"
                  @click.stop="handleTagRemove(option, $event)"
                >
                  ×
                </span>
              </div>
            </template>
            <template #option="{ option }">
              <div class="multiselect-option">
                <img 
                  :src="option.url" 
                  :alt="option.filename" 
                  class="multiselect-option-image"
                />
                <span class="multiselect-option-text">{{ option.filename }}</span>
              </div>
            </template>
          </Multiselect>
        </div>
        <small class="error-text" v-if="v$.input_images.$error">
          {{ v$.input_images.$errors[0].$message }}
        </small>
      </div>

      <!-- Instruction -->
      <div class="form-group">
        <label for="instruction">Instruction</label>
        <textarea
          id="instruction"
          v-model="form.instruction"
          class="form-control"
          :class="{ 'is-invalid': v$.instruction.$error }"
          placeholder="Enter instructions for image generation"
          rows="3"
        ></textarea>
        <small class="error-text" v-if="v$.instruction.$error">
          {{ v$.instruction.$errors[0].$message }}
        </small>
      </div>

      <!-- Inference Steps -->
      <div class="form-group">
        <label for="inference-steps">Inference Steps ({{ form.inference_steps }})</label>
        <div class="slider-container">
          <input
            id="inference-steps"
            v-model="form.inference_steps"
            type="range"
            min="10"
            max="100"
            step="1"
            class="slider"
            :class="{ 'is-invalid': v$.inference_steps.$error }"
          />
          <span class="slider-value">{{ form.inference_steps }}</span>
        </div>
        <small class="hint-text">Higher values produce better quality but take longer</small>
        <small class="error-text" v-if="v$.inference_steps.$error">
          {{ v$.inference_steps.$errors[0].$message }}
        </small>
      </div>

      <!-- Height -->
      <div class="form-group">
        <label for="height">Height (pixels)</label>
        <select
          id="height"
          v-model="form.height"
          class="form-control"
          :class="{ 'is-invalid': v$.height.$error }"
        >
          <option value="256">256</option>
          <option value="512">512</option>
          <option value="768">768</option>
          <option value="1024">1024</option>
        </select>
        <small class="error-text" v-if="v$.height.$error">
          {{ v$.height.$errors[0].$message }}
        </small>
      </div>

      <!-- Width -->
      <div class="form-group">
        <label for="width">Width (pixels)</label>
        <select
          id="width"
          v-model="form.width"
          class="form-control"
          :class="{ 'is-invalid': v$.width.$error }"
        >
          <option value="256">256</option>
          <option value="512">512</option>
          <option value="768">768</option>
          <option value="1024">1024</option>
        </select>
        <small class="error-text" v-if="v$.width.$error">
          {{ v$.width.$errors[0].$message }}
        </small>
      </div>

      <!-- Guidance Scale -->
      <div class="form-group">
        <label for="guidance-scale">Guidance Scale ({{ form.guidance_scale }})</label>
        <div class="slider-container">
          <input
            id="guidance-scale"
            v-model="form.guidance_scale"
            type="range"
            min="1"
            max="20"
            step="0.1"
            class="slider"
            :class="{ 'is-invalid': v$.guidance_scale.$error }"
          />
          <span class="slider-value">{{ form.guidance_scale }}</span>
        </div>
        <small class="hint-text">Controls how closely the image follows the prompt</small>
        <small class="error-text" v-if="v$.guidance_scale.$error">
          {{ v$.guidance_scale.$errors[0].$message }}
        </small>
      </div>

      <!-- Submit Button -->
      <div class="form-actions">
        <button 
          type="submit" 
          class="submit-button" 
          :disabled="isSubmitting || v$.$invalid"
        >
          <span v-if="isSubmitting">
            <span class="spinner"></span> Generating...
          </span>
          <span v-else>Generate Image</span>
        </button>
      </div>
    </form>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted, watch } from 'vue';
import { useVuelidate } from '@vuelidate/core';
import { required, minValue, maxValue, minLength } from '@vuelidate/validators';
import Multiselect from 'vue-multiselect';
import { useToast } from 'vue-toast-notification';
import ApiService from '../utils/api';

export default {
  name: 'ModelConfig',
  components: {
    Multiselect
  },
  props: {
    initialImages: {
      type: Array,
      default: () => []
    }
  },
  emits: ['generation-started', 'generation-progress', 'generation-completed', 'generation-error', 'generation-cancelled'],
  setup(props, { emit }) {
    const toast = useToast();
    const availableImages = ref([]);
    const isSubmitting = ref(false);
    const processId = ref(null);
    const statusCheckInterval = ref(null);

    // Form data
    const form = reactive({
      input_images: [],
      instruction: '',
      inference_steps: 30,
      height: 512,
      width: 512,
      guidance_scale: 7.5
    });

    // Validation rules
    const rules = computed(() => ({
      input_images: { 
        required, 
        minLength: minLength(1) 
      },
      instruction: { 
        required, 
        minLength: minLength(3) 
      },
      inference_steps: { 
        required, 
        minValue: minValue(10), 
        maxValue: maxValue(100) 
      },
      height: { 
        required 
      },
      width: { 
        required 
      },
      guidance_scale: { 
        required, 
        minValue: minValue(1), 
        maxValue: maxValue(20) 
      }
    }));

    const v$ = useVuelidate(rules, form);

    // Load available images
    const loadAvailableImages = async () => {
      try {
        const response = await ApiService.getInputImages();
        availableImages.value = response.data.images;
        
        // Pre-select images if provided
        if (props.initialImages && props.initialImages.length > 0) {
          // Map string filenames to image objects
          form.input_images = props.initialImages.map(filename => {
            // Find the corresponding image object
            const imageObj = availableImages.value.find(img => img.filename === filename);
            return imageObj || filename; // Return the object if found, otherwise the filename
          });
        }
      } catch (error) {
        console.error('Failed to load input images:', error);
        toast.error('Failed to load input images. Please try again later.');
      }
    };

    // Submit form
    const submitForm = async () => {
      const isValid = await v$.value.$validate();
      if (!isValid) return;

      isSubmitting.value = true;
      emit('generation-started');

      try {
        // Handle case where input_images might not be an array or might be empty
        const imageFilenames = Array.isArray(form.input_images) 
          ? form.input_images.map(img => typeof img === 'string' ? img : img.filename)
          : [];

        // Prepare parameters for the API
        const params = {
          input_images: imageFilenames,
          instruction: form.instruction,
          inference_steps: parseInt(form.inference_steps),
          height: parseInt(form.height),
          width: parseInt(form.width),
          guidance_scale: parseFloat(form.guidance_scale)
        };

        // Call the API to execute the script
        const response = await ApiService.executeScript(params);
        processId.value = response.data.process_id;
        
        toast.success('Image generation started successfully!');
        
        // Start polling for status
        startStatusPolling();
      } catch (error) {
        console.error('Failed to start image generation:', error);
        toast.error('Failed to start image generation: ' + (error.message || 'Unknown error'));
        isSubmitting.value = false;
        emit('generation-error', error);
      }
    };

    // Poll for generation status
    const startStatusPolling = () => {
      if (!processId.value) return;
      
      statusCheckInterval.value = setInterval(async () => {
        try {
          const response = await ApiService.getScriptStatus(processId.value);
          const status = response.data;
          
          // Emit progress updates
          emit('generation-progress', {
            status: status.status,
            progress: status.progress,
            output: status.output
          });
          
          // Check if process is complete
          if (status.status === 'completed') {
            clearInterval(statusCheckInterval.value);
            isSubmitting.value = false;
            toast.success('Image generation completed successfully!');
            emit('generation-completed', status.output_image);
          } 
          // Check if process failed
          else if (status.status === 'failed') {
            clearInterval(statusCheckInterval.value);
            isSubmitting.value = false;
            toast.error('Image generation failed: ' + (status.error || 'Unknown error'));
            emit('generation-error', status.error);
          }
        } catch (error) {
          console.error('Failed to check generation status:', error);
          clearInterval(statusCheckInterval.value);
          isSubmitting.value = false;
          toast.error('Failed to check generation status: ' + (error.message || 'Unknown error'));
          emit('generation-error', error);
        }
      }, 2000); // Check every 2 seconds
    };

    // Cancel generation
    const cancelGeneration = async () => {
      if (!processId.value || !isSubmitting.value) return;
      
      try {
        await ApiService.cancelScript(processId.value);
        toast.info('Image generation cancelled');
        clearInterval(statusCheckInterval.value);
        isSubmitting.value = false;
        emit('generation-cancelled');
      } catch (error) {
        console.error('Failed to cancel generation:', error);
        toast.error('Failed to cancel generation: ' + (error.message || 'Unknown error'));
      }
    };

    // Clean up on component unmount
    onMounted(() => {
      loadAvailableImages();
    });

    // Watch for changes in initialImages prop
    watch(() => props.initialImages, (newImages) => {
      if (newImages && newImages.length > 0 && availableImages.value.length > 0) {
        // Map string filenames to image objects
        form.input_images = newImages.map(filename => {
          // Find the corresponding image object
          const imageObj = availableImages.value.find(img => img.filename === filename);
          return imageObj || filename; // Return the object if found, otherwise the filename
        });
      } else {
        form.input_images = [];
      }
    }, { deep: true });

    return {
      form,
      v$,
      availableImages,
      isSubmitting,
      submitForm,
      cancelGeneration
    };
  }
};
</script>

<style scoped>
.model-config-container {
  background-color: #f8f9fa;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

h2 {
  margin-top: 0;
  margin-bottom: 20px;
  color: #333;
  font-size: 1.5rem;
}

.config-form {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.form-group {
  margin-bottom: 15px;
}

label {
  display: block;
  margin-bottom: 5px;
  font-weight: 600;
  color: #555;
}

.form-control {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
  transition: border-color 0.2s;
}

.form-control:focus {
  border-color: #4a90e2;
  outline: none;
}

.form-control.is-invalid {
  border-color: #dc3545;
}

textarea.form-control {
  resize: vertical;
  min-height: 80px;
}

.error-text {
  display: block;
  color: #dc3545;
  font-size: 0.85rem;
  margin-top: 5px;
}

.hint-text {
  display: block;
  color: #6c757d;
  font-size: 0.85rem;
  margin-top: 5px;
}

.slider-container {
  display: flex;
  align-items: center;
  gap: 15px;
}

.slider {
  flex: 1;
  height: 5px;
  background: #ddd;
  outline: none;
  -webkit-appearance: none;
  border-radius: 5px;
}

.slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #4a90e2;
  cursor: pointer;
}

.slider::-moz-range-thumb {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #4a90e2;
  cursor: pointer;
  border: none;
}

.slider-value {
  min-width: 40px;
  text-align: center;
  font-weight: 600;
  color: #4a90e2;
}

.form-actions {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.submit-button {
  background-color: #4a90e2;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 10px 20px;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.submit-button:hover:not(:disabled) {
  background-color: #3a80d2;
}

.submit-button:disabled {
  background-color: #a0c0e8;
  cursor: not-allowed;
}

.spinner {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: white;
  animation: spin 1s ease-in-out infinite;
  margin-right: 8px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Multiselect styling */
.multiselect-container {
  width: 100%;
}

.multiselect-custom {
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
}

.multiselect-tag {
  background-color: #4a90e2;
  color: white;
  border-radius: 4px;
  padding: 2px 8px;
  margin: 2px;
  display: inline-flex;
  align-items: center;
}

.multiselect-tag-remove {
  margin-left: 5px;
  cursor: pointer;
  font-weight: bold;
}

.multiselect-option {
  display: flex;
  align-items: center;
  padding: 5px;
}

.multiselect-option-image {
  width: 40px;
  height: 40px;
  object-fit: cover;
  margin-right: 10px;
  border-radius: 4px;
}

.multiselect-option-text {
  font-size: 0.9rem;
}
</style>

<style src="vue-multiselect/dist/vue-multiselect.css"></style>
