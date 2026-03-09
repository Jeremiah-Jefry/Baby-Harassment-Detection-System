// JS Configuration Settings
export const CONFIG = {
    // Determine host dynamically or fallback
    HOST: window.location.hostname || 'localhost',
    PORT: 8000,

    // WebSocket Reconnect Settings
    WS: {
        MAX_RETRIES: 10,
        BASE_DELAY_MS: 1000,
        MAX_DELAY_MS: 30000, // 30 seconds max backoff
        PING_INTERVAL_MS: 5000, // Client side ping
    },

    // UI performance limits
    UI: {
        MAX_ALERTS_RENDERED: 50, // Avoid DOM bloating by clipping logs
        ALERT_FLASH_DURATION_MS: 8000, // How long card stays red
    }
};

// Computed base URL
export const WS_BASE_URL = `ws://${CONFIG.HOST}:${CONFIG.PORT}`;
