import { state } from './state.js';
import { CONFIG } from './config.js';

export class UIRenderer {
    constructor() {
        this.cacheDOM();
        this.bindEvents();

        // Timeout storage to manage card CSS flashing
        this.flashTimeouts = {
            baby: null,
            babysitter: null
        };
    }

    cacheDOM() {
        this.dom = {
            connDot: document.querySelector('.status-dot'),
            connText: document.getElementById('conn-text'),
            videoFrame: document.getElementById('video-frame'),

            babyCard: document.getElementById('baby-status-card'),
            babyStatusText: document.getElementById('baby-status'),
            sitterCard: document.getElementById('sitter-status-card'),
            sitterStatusText: document.getElementById('sitter-status'),

            babyAlertsList: document.getElementById('baby-alerts-list'),
            sitterAlertsList: document.getElementById('sitter-alerts-list'),
            alertCountNum: document.getElementById('alert-count')
        };
    }

    bindEvents() {
        state.on('connection_change', this.updateConnectionStatus.bind(this));
        state.on('new_alert', this.renderNewAlert.bind(this));
        state.on('video_frame', this.renderVideoFrame.bind(this));
    }

    updateConnectionStatus(isConnected) {
        if (isConnected) {
            this.dom.connDot.className = 'status-dot connected';
            this.dom.connText.textContent = 'System Active';
        } else {
            this.dom.connDot.className = 'status-dot disconnected';
            this.dom.connText.textContent = 'Disconnected';
            this.dom.videoFrame.innerHTML = `
                <div class="video-placeholder">
                    <span class="loader" style="animation: none;"></span>
                    <p>Connection lost. Reconnecting...</p>
                </div>
            `;
        }
    }

    renderVideoFrame(frameData) {
        // Only inject mock overlay if it doesn't exist to prevent full DOM reflows
        let mockCamera = this.dom.videoFrame.querySelector('.mock-camera-overlay');
        if (!mockCamera) {
            this.dom.videoFrame.innerHTML = `
                <div class="mock-camera-overlay">CAM 01 - NURSERY RT-DETR</div>
                <div class="mock-video-feed"></div>
            `;
        }

        const feedContainer = this.dom.videoFrame.querySelector('.mock-video-feed');
        if (feedContainer) {
            feedContainer.innerHTML = `
                <p style="font-size: 1.5rem; margin-bottom: 8px; color: #fff;">${frameData.content}</p>
                <p style="opacity: 0.5;">[Event: ${frameData.timestamp}]</p>
            `;
        }
    }

    renderNewAlert(alertData) {
        // Update Total Count
        this.dom.alertCountNum.textContent = state.alerts.length;

        // Build fragment for performance
        const fragment = document.createDocumentFragment();
        const alertEl = document.createElement('div');
        alertEl.className = `alert-item ${alertData.type}`;

        const time = alertData.timestamp.split(' ')[1] || "Just now";

        alertEl.innerHTML = `
            <div class="alert-header">
                <span class="alert-model">${alertData.model_source || 'AI'}</span>
                <span class="alert-time">${time}</span>
            </div>
            <div class="alert-message">${alertData.message}</div>
        `;
        fragment.appendChild(alertEl);

        // Append to correct list and flash status
        if (alertData.target === 'baby') {
            this.pruneList(this.dom.babyAlertsList);
            this.dom.babyAlertsList.appendChild(fragment);
            this.dom.babyAlertsList.scrollTop = this.dom.babyAlertsList.scrollHeight;
            this.updateStatusPanel('baby', alertData.type);
        } else {
            this.pruneList(this.dom.sitterAlertsList);
            this.dom.sitterAlertsList.appendChild(fragment);
            this.dom.sitterAlertsList.scrollTop = this.dom.sitterAlertsList.scrollHeight;
            this.updateStatusPanel('babysitter', alertData.type);
        }
    }

    pruneList(listElement) {
        // Remove empty state text
        const emptyState = listElement.querySelector('.empty-alerts');
        if (emptyState) emptyState.remove();

        // Prevent memory leak by removing old DOM nodes
        while (listElement.children.length >= CONFIG.UI.MAX_ALERTS_RENDERED) {
            listElement.removeChild(listElement.firstChild);
        }
    }

    updateStatusPanel(target, type) {
        const card = target === 'baby' ? this.dom.babyCard : this.dom.sitterCard;
        const textElement = target === 'baby' ? this.dom.babyStatusText : this.dom.sitterStatusText;

        let label = 'Info';
        if (['danger', 'critical', 'urgent'].includes(type)) label = 'Hazard';
        else if (['warning', 'alert'].includes(type)) label = 'Warning';

        textElement.textContent = label;
        textElement.className = `status-value ${type}`;

        // Reset animation by triggering reflow
        card.classList.remove('alert-danger', 'alert-warning', 'alert-critical', 'alert-urgent', 'alert-alert');
        void card.offsetWidth;
        card.classList.add(`alert-${type}`);

        // Set timeout to return to normal
        if (this.flashTimeouts[target]) clearTimeout(this.flashTimeouts[target]);

        this.flashTimeouts[target] = setTimeout(() => {
            textElement.textContent = target === 'baby' ? 'Safe' : 'Normal';
            textElement.className = 'status-value safe';
            card.classList.remove(`alert-${type}`);
        }, CONFIG.UI.ALERT_FLASH_DURATION_MS);
    }
}
