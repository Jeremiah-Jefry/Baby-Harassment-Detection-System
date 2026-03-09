import { AlertStreamManager } from './ws-manager.js';
import { UIRenderer } from './ui-renderer.js';
import { MediaCaptureService } from './media-capture.js';

/**
 * Enterprise Main Application Entry Point
 * Wires the UI Renderer, Media Capture, and WebSocket services together.
 */
document.addEventListener('DOMContentLoaded', () => {
    // 1. Initialize UI Renderer to listen to state changes
    const renderer = new UIRenderer();

    // 2. Instantiate and connect WebSocket managers for AI Alerts
    const alertStream = new AlertStreamManager();
    alertStream.connect();

    // 3. Initialize real-time Media Capture (requests mic/camera and handles video WS sending)
    const mediaCapture = new MediaCaptureService();
    mediaCapture.init();
});
