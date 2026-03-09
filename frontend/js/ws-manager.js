import { CONFIG, WS_BASE_URL } from './config.js';
import { state } from './state.js';

export class WebSocketManager {
    constructor(endpoint) {
        this.endpoint = endpoint;
        this.url = `${WS_BASE_URL}${endpoint}`;
        this.socket = null;
        this.retryCount = 0;
        this.pingInterval = null;
    }

    connect() {
        this.socket = new WebSocket(this.url);

        this.socket.onopen = () => {
            console.log(`[WS] Connected to ${this.endpoint}`);
            this.retryCount = 0;
            state.setConnectionState(true);
            this.startPing();
            this.onOpen();
        };

        this.socket.onmessage = (event) => {
            this.onMessage(event);
        };

        this.socket.onclose = () => {
            console.warn(`[WS] Disconnected from ${this.endpoint}`);
            this.stopPing();
            state.setConnectionState(false);
            this.attemptReconnect();
        };

        this.socket.onerror = (error) => {
            console.error(`[WS Error] ${this.endpoint}:`, error);
            // Socket will close and trigger onclose reconnect logic
        };
    }

    startPing() {
        if (this.pingInterval) clearInterval(this.pingInterval);
        this.pingInterval = setInterval(() => {
            if (this.socket && this.socket.readyState === WebSocket.OPEN) {
                this.socket.send("ping");
            }
        }, CONFIG.WS.PING_INTERVAL_MS);
    }

    stopPing() {
        if (this.pingInterval) clearInterval(this.pingInterval);
    }

    attemptReconnect() {
        if (this.retryCount >= CONFIG.WS.MAX_RETRIES) {
            console.error(`[WS] Max retries reached for ${this.endpoint}`);
            return;
        }

        // Exponential backoff with a cap
        const delay = Math.min(
            CONFIG.WS.BASE_DELAY_MS * Math.pow(2, this.retryCount),
            CONFIG.WS.MAX_DELAY_MS
        );

        console.log(`[WS] Reconnecting ${this.endpoint} in ${delay}ms... (Attempt ${this.retryCount + 1})`);

        setTimeout(() => {
            this.retryCount++;
            this.connect();
        }, delay);
    }

    // Override Hooks for Subclasses mapping to specific domains
    onOpen() { }
    onMessage(event) { }
}

/**
 * Service for sending live Media frames/chunks to Backend
 */
export class MediaStreamManager extends WebSocketManager {
    constructor() {
        super('/ws/media');
    }

    sendMediaPayload(type, base64Data) {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            const payload = JSON.stringify({
                type: type,
                data: base64Data
            });
            this.socket.send(payload);
        }
    }

    onMessage(event) {
        // Ignore pong heartbeats or anything else sent back from ingest WS
        if (event.data === "pong") return;
    }
}

/**
 * Service specifically for Real-time inference alerts
 */
export class AlertStreamManager extends WebSocketManager {
    constructor() {
        super('/ws/alerts');
    }
    onMessage(event) {
        // Filter out 'pong' heartbeat responses
        if (event.data === "pong") return;

        try {
            const data = JSON.parse(event.data);
            if (data.timestamp) {
                state.pushAlert(data);
            }
        } catch (e) {
            console.error("Failed to parse alert stream data", e);
        }
    }
}
