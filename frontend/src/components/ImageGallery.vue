<template>
  <div class="gallery-container">
    <h2>Image Gallery</h2>
    
    <div class="gallery-tabs">
      <button 
        class="gallery-tab" 
        :class="{ active: activeTab === 'input' }" 
        @click="switchTab('input')"
      >
        Input Images
      </button>
      <button 
        class="gallery-tab" 
        :class="{ active: activeTab === 'output' }" 
        @click="switchTab('output')"
      >
        Generated Images
      </button>
    </div>
    
    <div class="gallery-content">
      <div v-if="loading" class="loading">
        <p>Loading images...</p>
      </div>
      
      <div v-else-if="images.length === 0" class="no-images">
        <p>No {{ activeTab === 'input' ? 'input' : 'generated' }} images found.</p>
        <button v-if="activeTab === 'input'" @click="goToUpload" class="action-button">
          Upload Images
        </button>
        <button v-else @click="goToGenerate" class="action-button">
          Generate Images
        </button>
      </div>
      
      <div v-else class="image-grid">
        <div v-for="image in images" :key="image.filename" class="image-card">
          <div class="image-container">
            <img :src="image.url" :alt="image.filename" @click="openImageViewer(image)" />
          </div>
          <div class="image-info">
            <div class="image-name" :title="image.filename">
              {{ truncateFilename(image.filename) }}
            </div>
            <div class="image-meta">
              <span>{{ formatFileSize(image.size) }}</span>
              <span>{{ formatDate(image.created) }}</span>
            </div>
            <div class="image-actions">
              <button class="delete-button" @click.stop="confirmDelete(image)" title="Delete image">
                Delete
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Image Viewer Modal -->
    <div v-if="selectedImage" class="image-viewer-overlay" @click="closeImageViewer">
      <div class="image-viewer-container" @click.stop>
        <div class="image-viewer-header">
          <h3>{{ selectedImage.filename }}</h3>
          <button class="close-button" @click="closeImageViewer">&times;</button>
        </div>
        <div class="image-viewer-content">
          <img :src="selectedImage.url" :alt="selectedImage.filename" />
        </div>
        <div class="image-viewer-footer">
          <div class="image-details">
            <p>Size: {{ formatFileSize(selectedImage.size) }}</p>
            <p>Created: {{ formatDate(selectedImage.created, true) }}</p>
          </div>
          <div class="image-action-buttons">
            <a :href="selectedImage.url" download class="download-button">Download</a>
            <button class="delete-button-modal" @click="confirmDelete(selectedImage)">Delete</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, watch, onMounted } from 'vue';
import { useToast } from 'vue-toast-notification';
import ApiService from '../utils/api';

export default {
  name: 'ImageGallery',
  emits: ['change-tab'],
  
  setup(props, { emit }) {
    const $toast = useToast();
    // Initialize with 'input' tab to show uploaded images first
    const activeTab = ref('input');
    const loading = ref(true);
    const images = ref([]);
    const selectedImage = ref(null);
    
    const fetchImages = async () => {
      loading.value = true;
      try {
        let response;
        if (activeTab.value === 'input') {
          response = await ApiService.getInputImages();
        } else {
          response = await ApiService.getOutputImages();
        }
        images.value = response.data.images || [];
      } catch (error) {
        console.error(`Error fetching ${activeTab.value} images:`, error);
        $toast.error(`Failed to load ${activeTab.value} images: ${error.message}`);
        images.value = [];
      } finally {
        loading.value = false;
      }
    };
    
    const truncateFilename = (filename) => {
      if (filename.length <= 20) return filename;
      return filename.substring(0, 8) + '...' + filename.substring(filename.length - 8);
    };
    
    const formatFileSize = (bytes) => {
      if (bytes < 1024) return bytes + ' B';
      else if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
      else return (bytes / 1048576).toFixed(1) + ' MB';
    };
    
    const formatDate = (dateString, detailed = false) => {
      const date = new Date(dateString);
      if (detailed) {
        return date.toLocaleString();
      } else {
        return date.toLocaleDateString();
      }
    };
    
    const openImageViewer = (image) => {
      selectedImage.value = image;
      document.body.style.overflow = 'hidden'; // Prevent scrolling when modal is open
    };
    
    const closeImageViewer = () => {
      selectedImage.value = null;
      document.body.style.overflow = ''; // Restore scrolling
    };
    
    const goToUpload = () => {
      emit('change-tab', 'upload');
    };
    
    const goToGenerate = () => {
      emit('change-tab', 'generate');
    };
    
    const confirmDelete = (image) => {
      if (confirm(`Are you sure you want to delete ${image.filename}?`)) {
        deleteImage(image);
      }
    };
    
    const deleteImage = async (image) => {
      try {
        if (activeTab.value === 'input') {
          await ApiService.deleteInputImage(image.filename);
        } else {
          await ApiService.deleteOutputImage(image.filename);
        }
        
        // Remove the image from the array
        images.value = images.value.filter(img => img.filename !== image.filename);
        
        // Close the viewer if the deleted image was being viewed
        if (selectedImage.value && selectedImage.value.filename === image.filename) {
          closeImageViewer();
        }
        
        $toast.success(`Image ${image.filename} deleted successfully`);
      } catch (error) {
        console.error(`Error deleting image:`, error);
        $toast.error(`Failed to delete image: ${error.message || 'Unknown error'}`);
      }
    };
    
    // Function to switch tabs and reload images
    const switchTab = (tab) => {
      activeTab.value = tab;
      fetchImages();
    };
    
    // Watch for tab changes to reload images
    watch(activeTab, () => {
      fetchImages();
    });
    
    onMounted(() => {
      fetchImages();
    });
    
    return {
      activeTab,
      loading,
      images,
      selectedImage,
      truncateFilename,
      formatFileSize,
      formatDate,
      openImageViewer,
      closeImageViewer,
      goToUpload,
      goToGenerate,
      confirmDelete,
      switchTab
    };
  }
};
</script>

<style scoped>
.gallery-container {
  max-width: 100%;
}

h2 {
  color: var(--primary-color);
  margin-bottom: 20px;
}

.gallery-tabs {
  display: flex;
  margin-bottom: 20px;
  border-bottom: 1px solid #eee;
}

.gallery-tab {
  padding: 12px 24px;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 16px;
  font-weight: bold;
  color: var(--text-color);
  border-bottom: 3px solid transparent;
  transition: all 0.3s ease;
  flex: 1;
  text-align: center;
}

.gallery-tab:hover {
  color: var(--primary-color);
}

.gallery-tab.active {
  color: var(--primary-color);
  border-bottom-color: var(--primary-color);
}

.loading, .no-images {
  text-align: center;
  padding: 40px;
  color: #666;
}

.action-button {
  margin-top: 15px;
  padding: 10px 20px;
  background-color: var(--primary-color);
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
}

.action-button:hover {
  background-color: #2980b9;
}

.image-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 20px;
}

.image-card {
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s, box-shadow 0.2s;
  background-color: white;
}

.image-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.15);
}

.image-container {
  height: 200px;
  overflow: hidden;
  cursor: pointer;
}

.image-container img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s ease;
}

.image-container img:hover {
  transform: scale(1.05);
}

.image-info {
  padding: 15px;
}

.image-name {
  font-weight: bold;
  margin-bottom: 5px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.image-meta {
  display: flex;
  justify-content: space-between;
  font-size: 0.8rem;
  color: #666;
}

.image-actions {
  display: flex;
  justify-content: center;
  margin-top: 8px;
  width: 100%;
}

.delete-button {
  background-color: #e74c3c;
  border: none;
  color: white;
  cursor: pointer;
  padding: 6px 12px;
  border-radius: 4px;
  transition: background-color 0.2s;
  width: 100%;
  font-size: 0.9rem;
}

.delete-button:hover {
  background-color: #c0392b;
}

/* Image Viewer Modal */
.image-viewer-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.image-viewer-container {
  background-color: white;
  border-radius: 8px;
  width: 90%;
  max-width: 1000px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.image-viewer-header {
  padding: 15px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #eee;
}

.image-viewer-header h3 {
  margin: 0;
  font-size: 1.2rem;
  color: var(--secondary-color);
}

.close-button {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #666;
}

.image-viewer-content {
  flex: 1;
  overflow: auto;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.image-viewer-content img {
  max-width: 100%;
  max-height: 60vh;
  object-fit: contain;
}

.image-viewer-footer {
  padding: 15px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-top: 1px solid #eee;
}

.image-details {
  font-size: 0.9rem;
  color: #666;
}

.image-details p {
  margin: 5px 0;
}

.download-button {
  padding: 8px 15px;
  background-color: var(--primary-color);
  color: white;
  text-decoration: none;
  border-radius: 4px;
  font-size: 0.9rem;
  transition: background-color 0.3s;
}

.download-button:hover {
  background-color: #2980b9;
}

.image-action-buttons {
  display: flex;
  gap: 10px;
}

.delete-button-modal {
  padding: 8px 15px;
  background-color: #e74c3c;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 0.9rem;
  cursor: pointer;
  transition: background-color 0.3s;
}

.delete-button-modal:hover {
  background-color: #c0392b;
}
</style>
