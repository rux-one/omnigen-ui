<template>
  <div class="app-container">
    <header class="app-header">
      <h1>OmniGen2 UI</h1>
      <p>Image Generation with OmniGen2 Model</p>
    </header>

    <main class="app-content">
      <div class="tabs">
        <button 
          class="tab-button" 
          :class="{ active: activeTab === 'upload' }" 
          @click="activeTab = 'upload'"
        >
          Upload Images
        </button>
        <button 
          class="tab-button" 
          :class="{ active: activeTab === 'generate' }" 
          @click="activeTab = 'generate'"
        >
          Generate Images
        </button>
        <button 
          class="tab-button" 
          :class="{ active: activeTab === 'gallery' }" 
          @click="activeTab = 'gallery'"
        >
          Gallery
        </button>
      </div>

      <div class="tab-content">
        <div v-if="activeTab === 'upload'">
          <ErrorBoundary component="ImageUpload">
            <ImageUpload />
          </ErrorBoundary>
        </div>
        <div v-else-if="activeTab === 'generate'">
          <ErrorBoundary component="ImageGeneration">
            <ImageGeneration />
          </ErrorBoundary>
        </div>
        <div v-else-if="activeTab === 'gallery'">
          <ErrorBoundary component="ImageGallery">
            <ImageGallery @change-tab="activeTab = $event" />
          </ErrorBoundary>
        </div>
      </div>
    </main>

    <footer class="app-footer">
      <p>&copy; {{ new Date().getFullYear() }} OmniGen2 UI</p>
    </footer>
  </div>
</template>

<script>
import { ref } from 'vue';
import ImageUpload from './components/ImageUpload.vue';
import ImageGeneration from './components/ImageGeneration.vue';
import ImageGallery from './components/ImageGallery.vue';
import ErrorBoundary from './components/ErrorBoundary.vue';

export default {
  name: 'App',
  components: {
    ImageUpload,
    ImageGeneration,
    ImageGallery,
    ErrorBoundary
  },
  setup() {
    const activeTab = ref('upload');
    
    return {
      activeTab
    };
  }
}
</script>

<style>
:root {
  --primary-color: #3498db;
  --secondary-color: #2c3e50;
  --accent-color: #e74c3c;
  --light-gray: #f5f5f5;
  --dark-gray: #333;
  --text-color: #2c3e50;
  --border-radius: 8px;
}

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  background-color: var(--light-gray);
  color: var(--text-color);
  line-height: 1.6;
}

#app {
  font-family: 'Avenir', Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.app-header {
  text-align: center;
  margin-bottom: 30px;
  padding: 20px 0;
  border-bottom: 1px solid #eee;
}

.app-header h1 {
  color: var(--primary-color);
  font-size: 2.5rem;
  margin-bottom: 10px;
}

.app-content {
  flex: 1;
  background-color: white;
  border-radius: var(--border-radius);
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
  padding: 20px;
  margin-bottom: 20px;
}

.tabs {
  display: flex;
  margin-bottom: 20px;
  border-bottom: 1px solid #eee;
}

.tab-button {
  padding: 10px 20px;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 16px;
  color: var(--text-color);
  border-bottom: 3px solid transparent;
  transition: all 0.3s ease;
}

.tab-button:hover {
  color: var(--primary-color);
}

.tab-button.active {
  color: var(--primary-color);
  border-bottom-color: var(--primary-color);
}

.tab-content {
  padding: 20px 0;
}

.placeholder {
  text-align: center;
  padding: 40px;
  color: #999;
  font-style: italic;
}

.app-footer {
  text-align: center;
  padding: 20px 0;
  color: #666;
  font-size: 14px;
}

button {
  background-color: var(--primary-color);
  color: white;
  border: none;
  padding: 10px 15px;
  border-radius: var(--border-radius);
  cursor: pointer;
  transition: background-color 0.3s ease;
}

button:hover {
  background-color: #2980b9;
}

button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}
</style>
