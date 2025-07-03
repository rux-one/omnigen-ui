<template>
  <div class="image-upload-container">
    <h2>Image Upload</h2>
    
    <div 
      class="dropzone-container"
      :class="{ 'active-dropzone': isDragging }"
      @dragenter.prevent="onDragEnter"
      @dragleave.prevent="onDragLeave"
      @dragover.prevent
      @drop.prevent="onDrop"
      @click="triggerFileInput"
    >
      <input 
        type="file" 
        ref="fileInput" 
        @change="onFileSelected" 
        accept="image/*" 
        multiple
        class="file-input"
      />
      
      <div v-if="!isUploading" class="dropzone-content">
        <div class="icon">
          <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
            <polyline points="17 8 12 3 7 8"></polyline>
            <line x1="12" y1="3" x2="12" y2="15"></line>
          </svg>
        </div>
        <p class="dropzone-text">Drag and drop images here or click to browse</p>
        <p class="dropzone-hint">Supported formats: JPG, PNG, GIF</p>
      </div>
      
      <div v-else class="upload-progress">
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: uploadProgress + '%' }"></div>
        </div>
        <p>Uploading: {{ uploadProgress }}%</p>
      </div>
    </div>
    
    <div v-if="uploadedImages.length > 0" class="uploaded-images">
      <h3>Uploaded Images</h3>
      <div class="image-grid">
        <div v-for="image in uploadedImages" :key="image.filename" class="image-item">
          <img :src="image.url" :alt="image.filename" class="thumbnail" />
          <div class="image-info">
            <p class="image-name">{{ image.filename }}</p>
            <p class="image-size">{{ formatFileSize(image.size) }}</p>
            <p class="image-date">{{ formatDate(image.created) }}</p>
          </div>
        </div>
      </div>
    </div>
    
    <div v-if="errorMessage" class="error-message">
      {{ errorMessage }}
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue';
import { useToast } from 'vue-toast-notification';
import ApiService from '../utils/api';

export default {
  name: 'ImageUpload',
  setup() {
    const $toast = useToast();
    const fileInput = ref(null);
    const isDragging = ref(false);
    const isUploading = ref(false);
    const uploadProgress = ref(0);
    const uploadedImages = ref([]);
    const errorMessage = ref('');
    const loading = ref(false);
    
    // Fetch already uploaded images on component mount
    const fetchUploadedImages = async () => {
      loading.value = true;
      try {
        const response = await ApiService.getInputImages();
        uploadedImages.value = response.data.images || [];
      } catch (error) {
        console.error('Error fetching images:', error);
        $toast.error(`Failed to load uploaded images: ${error.message}`);
      } finally {
        loading.value = false;
      }
    };
    
    onMounted(() => {
      fetchUploadedImages();
    });
    
    const triggerFileInput = () => {
      fileInput.value.click();
    };
    
    const onDragEnter = () => {
      isDragging.value = true;
    };
    
    const onDragLeave = () => {
      isDragging.value = false;
    };
    
    const onDrop = (event) => {
      isDragging.value = false;
      const files = event.dataTransfer.files;
      if (files.length) {
        uploadFiles(files);
      }
    };
    
    const onFileSelected = (event) => {
      const files = event.target.files;
      if (files.length) {
        uploadFiles(files);
      }
    };
    
    const uploadFiles = async (files) => {
      // Reset state
      errorMessage.value = '';
      isUploading.value = true;
      uploadProgress.value = 0;
      
      // Validate files
      const validFiles = Array.from(files).filter(file => {
        const validTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/jpg'];
        if (!validTypes.includes(file.type)) {
          errorMessage.value = `Invalid file type: ${file.name}. Only JPG, PNG, and GIF are allowed.`;
          return false;
        }
        return true;
      });
      
      if (validFiles.length === 0) {
        isUploading.value = false;
        return;
      }
      
      // Upload each file
      for (let i = 0; i < validFiles.length; i++) {
        const file = validFiles[i];
        try {
          await uploadFile(file);
        } catch (error) {
          console.error('Upload error:', error);
          $toast.error(`Failed to upload ${file.name}: ${error.message}`);
        }
      }
      
      // Reset upload state
      isUploading.value = false;
      uploadProgress.value = 100;
      
      // Reset file input
      fileInput.value.value = '';
    };
    
    const formatFileSize = (bytes) => {
      if (bytes < 1024) return bytes + ' B';
      else if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
      else return (bytes / 1048576).toFixed(1) + ' MB';
    };
    
    const uploadFile = async (file) => {
      if (!file) return;
      
      try {
        // Update progress for current file
        await ApiService.uploadImage(file, (progressEvent) => {
          uploadProgress.value = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        });
        
        $toast.success(`${file.name} uploaded successfully!`);
        await fetchUploadedImages(); // Refresh the image list
      } catch (error) {
        console.error('Upload failed:', error);
        throw error; // Propagate error to be handled by the caller
      }
    };
    
    const formatDate = (dateString) => {
      const date = new Date(dateString);
      return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    };
    
    return {
      fileInput,
      isDragging,
      isUploading,
      uploadProgress,
      uploadedImages,
      errorMessage,
      triggerFileInput,
      onDragEnter,
      onDragLeave,
      onDrop,
      onFileSelected,
      formatFileSize,
      formatDate
    };
  }
};
</script>

<style scoped>
.image-upload-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.dropzone-container {
  border: 2px dashed #ccc;
  border-radius: 8px;
  padding: 40px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-bottom: 20px;
}

.active-dropzone {
  border-color: #4caf50;
  background-color: rgba(76, 175, 80, 0.1);
}

.dropzone-content {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.icon {
  color: #666;
  margin-bottom: 15px;
}

.dropzone-text {
  font-size: 18px;
  margin-bottom: 10px;
}

.dropzone-hint {
  font-size: 14px;
  color: #666;
}

.file-input {
  display: none;
}

.upload-progress {
  width: 100%;
}

.progress-bar {
  height: 10px;
  background-color: #eee;
  border-radius: 5px;
  overflow: hidden;
  margin-bottom: 10px;
}

.progress-fill {
  height: 100%;
  background-color: #4caf50;
  transition: width 0.3s ease;
}

.uploaded-images {
  margin-top: 30px;
}

.image-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 15px;
  margin-top: 15px;
}

.image-item {
  border: 1px solid #eee;
  border-radius: 8px;
  overflow: hidden;
  transition: transform 0.2s ease;
}

.image-item:hover {
  transform: translateY(-5px);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
}

.thumbnail {
  width: 100%;
  height: 150px;
  object-fit: cover;
}

.image-info {
  padding: 10px;
}

.image-name {
  font-size: 14px;
  font-weight: bold;
  margin: 0 0 5px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.image-size, .image-date {
  font-size: 12px;
  color: #666;
  margin: 0;
}

.error-message {
  background-color: #ffebee;
  color: #c62828;
  padding: 10px;
  border-radius: 4px;
  margin-top: 20px;
}
</style>
