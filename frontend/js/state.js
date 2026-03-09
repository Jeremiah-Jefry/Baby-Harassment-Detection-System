import { CONFIG } from './config.js';

/**
 * State Management using a rudimentary PubSub pattern.
 * Decouples logic (WebSockets) from the View (DOM Rendering).
 */
class AppState {
    constructor() {
        this.systemConnected = false;
        this.alerts = [];
        this.listeners = {
            'connection_change': [],
            'new_alert': [],
            'video_frame': []
        };
    }

    // PubSub Subscribe
    on(event, callback) {
        if (!this.listeners[event]) return;
        this.listeners[event].push(callback);
    }

    // PubSub Trigger
    emit(event, data) {
        if (!this.listeners[event]) return;
        this.listeners[event].forEach(cb => cb(data));
    }

    setConnectionState(isConnected) {
        if (this.systemConnected !== isConnected) {
            this.systemConnected = isConnected;
            this.emit('connection_change', isConnected);
        }
    }

    pushAlert(alertData) {
        // Prevent array growth memory leak
        if (this.alerts.length > CONFIG.UI.MAX_ALERTS_RENDERED) {
            this.alerts.shift();
        }

        this.alerts.push(alertData);
        this.emit('new_alert', alertData);
    }

    pushVideoFrame(frameData) {
        this.emit('video_frame', frameData);
    }
}

// Singleton State instance
export const state = new AppState();
