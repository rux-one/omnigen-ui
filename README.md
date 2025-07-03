# OmniGen2 UI

A web application for generating images with the OmniGen2 model.

## Project Overview

This application provides a user-friendly interface to interact with the OmniGen2 image generation model. It allows users to upload images, configure model parameters, and generate new images based on instructions. The application features a modern Vue 3 frontend with a Flask backend API.

## Features

- Upload and manage input images
- Configure OmniGen2 model parameters
- Generate images with custom instructions
- Track generation progress in real-time
- View and download generated images
- Cancel ongoing generation processes

## Project Structure

```
omnigen-ui/
├── frontend/                # Vue 3 frontend application
│   ├── src/                 # Source files
│   │   ├── components/      # Vue components
│   │   │   ├── ImageUpload.vue      # Image upload component
│   │   │   ├── ImageGeneration.vue  # Image generation component
│   │   │   ├── ImageGallery.vue     # Gallery component
│   │   │   └── ErrorBoundary.vue    # Error handling component
│   │   ├── utils/          # Utility functions
│   │   │   └── api.js      # API service for backend communication
│   │   └── App.vue         # Main application component
├── backend/                # Python Flask backend
│   ├── app.py              # Main application file
│   ├── requirements.txt    # Python dependencies
│   └── venv/               # Python virtual environment
├── input_images/           # Directory for uploaded input images
├── output_images/          # Directory for generated output images
└── docs/                   # Project documentation
```

## Setup Instructions

### Environment Variables

#### Frontend (.env file in frontend directory)

```
VUE_APP_API_BASE_URL=http://localhost:5000/api
```

#### Backend (.env file in backend directory)

```
INFERENCE_SCRIPT_PATH=inference.py
```

You can create these .env files based on the provided .env.example files in each directory.

### Backend Setup

1. Navigate to the backend directory:
   ```
   cd backend
   ```

2. Create a .env file (copy from .env.example and modify as needed):
   ```
   cp .env.example .env
   ```

3. Activate the virtual environment:
   ```
   # On Linux/Mac
   source venv/bin/activate
   
   # On Windows
   venv\Scripts\activate
   ```

4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

5. Run the Flask application:
   ```
   python app.py
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```
   cd frontend
   ```

2. Install dependencies:
   ```
   npm install
   ```

3. Run the development server:
   ```
   npm run serve
   ```

4. Build for production:
   ```
   npm run build
   ```

## Usage

1. Start both the backend and frontend servers
2. Open your browser and navigate to http://localhost:8080
3. Upload input images
4. Configure model parameters
5. Generate images with custom instructions
6. View and download the results

## Technologies Used

- **Frontend**: Vue 3 (Composition API), Axios, vue-toast-notification
- **Backend**: Python, Flask 2.0.3, Flask-CORS 4.0.0
- **Image Processing**: OmniGen2 model

## API Endpoints

### Backend API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check endpoint |
| `/api/upload` | POST | Upload an image file |
| `/api/images/input` | GET | List all uploaded input images |
| `/api/images/output` | GET | List all generated output images |
| `/api/images/view/<folder>/<filename>` | GET | View a specific image |
| `/api/execute` | POST | Execute the OmniGen2 script with parameters |
| `/api/status/<process_id>` | GET | Check the status of a running process |
| `/api/cancel/<process_id>` | POST | Cancel a running process |
