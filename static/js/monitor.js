const CAPTURE_INTERVAL_MS = 100;
const MAX_LOGS = 50;

class GuardianMonitor {
    constructor() {
        this.ws = null;
        this.videoObj = document.getElementById('local-video');
        this.canvas = document.getElementById('hidden-canvas');
        this.ctx = this.canvas ? this.canvas.getContext('2d') : null;

        this.logsContainer = document.getElementById('alerts-container');
        this.connStatus = document.getElementById('conn-status');
        this.visionStatus = document.getElementById('vision-status');
        this.audioStatus = document.getElementById('audio-status');

        this.captureTimer = null;
        this.reconnectTimer = null;
        this.isCapturing = false;
        this.localStream = null;
    }

    async init() {
        if (!this.videoObj || !this.canvas || !this.ctx) {
            console.error('Dashboard media elements are missing.');
            return;
        }

        await this.loadAlertHistory();
        await this.startMediaCapture();
        this.connectSocket();
    }

    connectSocket() {
        if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
            return;
        }

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const socketHost = window.location.hostname === '0.0.0.0'
            ? `127.0.0.1${window.location.port ? `:${window.location.port}` : ''}`
            : window.location.host;
        this.connStatus.innerHTML = '<span class="dot disconnected"></span>Connecting...';
        this.ws = new WebSocket(`${protocol}//${socketHost}/ws/monitor`);

        this.ws.onopen = () => {
            this.connStatus.innerHTML = '<span class="dot connected"></span>System Active';
        };

        this.ws.onerror = () => {
            this.connStatus.innerHTML = '<span class="dot disconnected"></span>Network Error';
        };

        this.ws.onmessage = (event) => {
            try {
                const payload = JSON.parse(event.data);
                if (payload.event === 'status') {
                    this.connStatus.innerHTML = '<span class="dot connected"></span>System Active';
                    return;
                }
                this.renderAlert(payload);
            } catch (error) {
                console.error('Malformed AI Alert', error);
            }
        };

        this.ws.onclose = () => {
            this.connStatus.innerHTML = '<span class="dot disconnected"></span>Disconnected/Reconnecting...';
            if (this.reconnectTimer) {
                clearTimeout(this.reconnectTimer);
            }
            this.reconnectTimer = setTimeout(() => this.connectSocket(), 3000);
        };

        setTimeout(() => {
            if (this.ws && this.ws.readyState !== WebSocket.OPEN) {
                this.connStatus.innerHTML = '<span class="dot disconnected"></span>Reconnecting...';
            }
        }, 2500);
    }

    async startMediaCapture() {
        if (this.isCapturing) {
            return;
        }

        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            this.connStatus.innerHTML = '<span class="dot disconnected"></span>Media API unsupported';
            alert('This browser cannot access camera APIs. Use a modern Chrome/Edge/Firefox build.');
            return;
        }

        const isLocalhost = ['localhost', '127.0.0.1'].includes(window.location.hostname);
        if (!window.isSecureContext && !isLocalhost) {
            this.connStatus.innerHTML = '<span class="dot disconnected"></span>HTTPS required for camera';
            alert('Camera access requires HTTPS on non-localhost hosts. Use https://... or open via localhost.');
            return;
        }

        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: { width: 1280, height: 720 },
                audio: false
            });
            await this.attachAndStartStream(stream);
        } catch (error) {
            console.error(error);
            this.connStatus.innerHTML = '<span class="dot disconnected"></span>Camera blocked';
            let reason = 'Allow webcam permission for this site and retry.';
            if (error && error.name === 'NotReadableError') {
                reason = 'Camera is currently used by another app (Zoom/Meet/Teams).';
            } else if (error && error.name === 'NotFoundError') {
                reason = 'No camera device detected.';
            } else if (error && error.name === 'NotAllowedError') {
                reason = 'Permission denied. Please allow camera access in the browser.';
            }
            alert(`Camera access failed: ${reason}`);
        }
    }

    stopMediaCapture() {
        if (this.captureTimer) {
            clearInterval(this.captureTimer);
            this.captureTimer = null;
        }

        if (this.localStream) {
            this.localStream.getTracks().forEach((track) => track.stop());
        }
        this.localStream = null;
        this.isCapturing = false;
    }

    async attachAndStartStream(stream) {
        this.localStream = stream;

        this.videoObj.onloadedmetadata = async () => {
            try {
                await this.videoObj.play();
            } catch (error) {
                console.error(error);
            }

            this.canvas.width = this.videoObj.videoWidth || 224;
            this.canvas.height = this.videoObj.videoHeight || 224;

            const resolutionDetail = document.getElementById('resolution-detail');
            if (resolutionDetail) {
                resolutionDetail.innerText = `(${this.canvas.width}x${this.canvas.height})`;
            }

            if (this.captureTimer) {
                clearInterval(this.captureTimer);
            }
            this.captureTimer = setInterval(() => this.sendVideoFrame(), CAPTURE_INTERVAL_MS);
            this.isCapturing = true;
        };

        this.videoObj.srcObject = stream;
        if (this.audioStatus) {
            this.audioStatus.innerText = 'Inactive';
        }
    }

    sendVideoFrame() {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return;
        if (!this.ctx || !this.canvas.width || !this.canvas.height) return;
        if (this.videoObj.readyState < 2) return;

        this.ctx.drawImage(this.videoObj, 0, 0, this.canvas.width, this.canvas.height);
        const dataUrl = this.canvas.toDataURL('image/jpeg', 0.75);
        this.ws.send(JSON.stringify({
            type: 'frame',
            frame: dataUrl
        }));
    }

    renderAlert(alertData, fromHistory = false) {
        const emptyState = document.querySelector('.empty-state');
        if (emptyState) emptyState.remove();

        const typeClass = alertData.type || alertData.severity || 'info';
        const log = document.createElement('div');
        log.className = `log-item ${typeClass}`;
        if (fromHistory) {
            log.style.opacity = '0.7';
        }

        const timestamp = fromHistory ? this.formatTimestamp(alertData.timestamp) : new Date().toLocaleTimeString();
        const source = alertData.model_source || '3D CNN';

        log.innerHTML = `
            <div class="log-header">
                <span class="log-source">[${source}]</span>
                <span class="log-time">${timestamp}</span>
            </div>
            <div class="log-msg">${alertData.message}</div>
        `;

        this.logsContainer.prepend(log);
        if (this.logsContainer.children.length > MAX_LOGS) {
            this.logsContainer.removeChild(this.logsContainer.lastChild);
        }

        if (!fromHistory) {
            this.triggerFlash(typeClass);
        }
    }

    triggerFlash(severity) {
        const widgetCard = document.getElementById('vision-status-card');
        const widgetText = document.getElementById('vision-status');

        if (severity === 'critical' || severity === 'urgent' || severity === 'danger') {
            widgetCard.classList.remove('flash-critical', 'flash-warning');
            void widgetCard.offsetWidth;
            widgetCard.classList.add('flash-critical');
            widgetText.innerText = 'HAZARD DETECTED';
            widgetText.className = 'status-critical';
        } else if (severity === 'warning' || severity === 'alert') {
            widgetCard.classList.remove('flash-critical', 'flash-warning');
            void widgetCard.offsetWidth;
            widgetCard.classList.add('flash-warning');
            widgetText.innerText = 'Warning Alert';
            widgetText.className = 'status-warn';
        }

        setTimeout(() => {
            widgetText.innerText = 'Active';
            widgetText.className = 'status-normal';
        }, 5000);
    }

    async loadAlertHistory() {
        try {
            const res = await fetch('/api/alerts/history');
            if (res.ok) {
                const pastAlerts = await res.json();

                if (pastAlerts.length > 0) {
                    const emptyState = document.querySelector('.empty-state');
                    if (emptyState) emptyState.remove();
                }

                pastAlerts.reverse().forEach((alert) => {
                    this.renderAlert(alert, true);
                });
            }
        } catch (error) {
            console.error('Failed to fetch history table', error);
        }
    }

    formatTimestamp(value) {
        const timestamp = new Date(value);
        if (Number.isNaN(timestamp.getTime())) {
            return value;
        }
        return timestamp.toLocaleString();
    }
}

window.addEventListener('load', () => {
    window.GuardianApp = new GuardianMonitor();
    window.GuardianApp.init();
});

window.addEventListener('beforeunload', () => {
    if (window.GuardianApp) {
        window.GuardianApp.stopMediaCapture();
    }
});
