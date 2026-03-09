# Guardianize Web Development MVP

Guardianize is an AI-powered baby and babysitter monitoring system designed to detect mistreatment, abuse, and hazards. This project contains the boilerplate MVP for the Web Development side, specifically simulating real-time AI alerts and video feeds over WebSockets.

## Requirements

- Python 3.8+
- Any modern web browser

## Setup Instructions

### 1. Install Backend Dependencies
Open your terminal, navigate to the `backend` directory, and install the required Python packages.

```bash
cd backend
pip install -r requirements.txt
```

### 2. Run the FastAPI Server
Start the Uvicorn server to serve the WebSocket endpoints.

```bash
uvicorn main:app --reload
```
You should see output indicating that the server is running on `http://127.0.0.1:8000`.

### 3. Open the Dashboard
- Open the `frontend/index.html` file directly in your web browser (you can typically just double-click it).
- Or, if you use an IDE like VS Code, use the "Live Server" extension to serve the `frontend` folder.

## Features

- **Real-Time Video Feed Simulation**: The frontend connects to `ws://localhost:8000/ws/video` and receives constant pseudo-frames representing the camera feed.
- **AI Alert Simulation**: The frontend connects to `ws://localhost:8000/ws/alerts`. The FastAPI backend runs mock `process_yolo_frame()` and `process_lstm_audio()` functions that randomly generate alerts (like "Abnormal Movement Detected") every 10-15 seconds.
- **Dynamic Status Updates**: When alerts are received, the corresponding status panel (Baby or Babysitter) updates instantly and visually flashes.

## Connecting Your Actual AI Models

When you are ready to plug in the actual AI models:
1. Navigate to `backend/main.py`.
2. Locate the `process_yolo_frame()` and `process_lstm_audio()` functions.
3. Replace the mock randomized returns with your actual model inference logic.
4. Update the `/ws/video` endpoint to transmit actual base64 encoded JPEG strings or stream data instead of text JSON.
5. Update `frontend/js/app.js` to render the received image stream instead of the text placeholder.