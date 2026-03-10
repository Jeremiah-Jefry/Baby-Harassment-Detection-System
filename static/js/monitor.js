// WebSocket Client Orchestrator & Live Media Capture
const CAPTURE_INTERVAL_MS = 2000; // Match the python backend's 2.0s rule
const MAX_LOGS = 50;

class GuardianMonitor {
    constructor() {
        this.ws = null;
        this.videoObj = document.getElementById('local-video');
        this.canvas = document.getElementById('hidden-canvas');
        this.ctx = this.canvas ? this.canvas.getContext('2d') : null;

        // DOM Elements
        this.logsContainer = document.getElementById('alerts-container');
        this.connStatus = document.getElementById('conn-status');
        this.visionStatus = document.getElementById('vision-status');
        this.audioStatus = document.getElementById('audio-status');

        this.mediaRecorder = null;
        this.captureTimer = null;
    }

    async init() {
        if (!this.videoObj) return;

        // 1. Establish Secure WebSocket to FastAPI Backend Monitor endpoint
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        this.ws = new WebSocket(`${protocol}//${window.location.host}/ws/monitor`);

        // Load SQL Alert History Before Live Feed Connects
        await this.loadAlertHistory();

        this.ws.onopen = () => {
            console.log("Enterprise WS Connected.");
            this.connStatus.innerHTML = '<span class="dot connected"></span>System Active';
            this.startMediaCapture();
        };

        this.ws.onmessage = (event) => {
            if (event.data === 'pong') return;
            try {
                const payload = JSON.parse(event.data);
                this.renderAlert(payload);
            } catch (e) {
                console.error("Malformed AI Alert", e);
            }
        };

        this.ws.onclose = () => {
            this.connStatus.innerHTML = '<span class="dot disconnected"></span>Disconnected/Reconnecting...';
            setTimeout(() => this.init(), 3000); // Reconnect loop
        };
    }

    async startMediaCapture() {
        try {
            // Get local camera & microphone streams
            const stream = await navigator.mediaDevices.getUserMedia({
                video: { width: 1280, height: 720 },
                audio: true
            });
            this.videoObj.srcObject = stream;

            // Wait for video mapping
            this.videoObj.onloadedmetadata = () => {
                this.canvas.width = this.videoObj.videoWidth;
                this.canvas.height = this.videoObj.videoHeight;
                document.getElementById('resolution-detail').innerText = `(${this.videoObj.videoWidth}x${this.videoObj.videoHeight})`;

                // Start sending specific frames to RT-DETR Vision service
                this.captureTimer = setInterval(() => this.sendVideoFrame(), CAPTURE_INTERVAL_MS);
            };

            // Setup MediaRecorder for audio chunks to LSTM Acoustic service
            const audioTrack = stream.getAudioTracks()[0];
            if (audioTrack) {
                const audioStream = new MediaStream([audioTrack]);
                this.mediaRecorder = new MediaRecorder(audioStream, { mimeType: 'audio/webm;codecs=opus' });

                this.mediaRecorder.ondataavailable = (e) => {
                    if (e.data.size > 0 && this.ws.readyState === WebSocket.OPEN) {
                        const reader = new FileReader();
                        reader.readAsDataURL(e.data);
                        reader.onloadend = () => {
                            this.ws.send(JSON.stringify({
                                type: "audio_chunk",
                                data: reader.result
                            }));
                        };
                    }
                };

                // Chunk every 1 second (1000ms) to bypass audio buffer backlogs
                this.mediaRecorder.start(1000);
            }

        } catch (err) {
            console.error("Critical Permission Error accessing local Device", err);
            alert("Error: Camera or Microphone access denied / hardware disconnected. Guardianize cannot proceed.");
        }
    }

    sendVideoFrame() {
        if (this.ws.readyState !== WebSocket.OPEN) return;

        // Draw to hidden canvas to obtain raw JPEG base64 payload
        this.ctx.drawImage(this.videoObj, 0, 0, this.canvas.width, this.canvas.height);
        const dataUrl = this.canvas.toDataURL('image/jpeg', 0.8);

        this.ws.send(JSON.stringify({
            type: "video_frame",
            data: dataUrl
        }));
    }

    renderAlert(alertData, fromHistory = false) {
        // Clear empty state text
        const emptyState = document.querySelector('.empty-state');
        if (emptyState) emptyState.remove();

        // Map colors & classes
        let typeClass = alertData.type || 'info';

        // Build the Log Layout Segment
        const log = document.createElement('div');
        log.className = `log-item ${typeClass}`;
        if (fromHistory) {
            log.style.opacity = '0.7'; // Indicate it's an old DB fetch visually
        }

        const timestamp = fromHistory ? alertData.timestamp : new Date().toLocaleTimeString();
        const source = alertData.model_source || (alertData.target === 'baby' ? 'Vision' : 'Audio');

        log.innerHTML = `
            <div class="log-header">
                <span class="log-source">[${source}]</span>
                <span class="log-time">${timestamp}</span>
            </div>
            <div class="log-msg">${alertData.message}</div>
        `;

        this.logsContainer.prepend(log); // newest top

        // Trim logs to prevent memory overflow
        if (this.logsContainer.children.length > MAX_LOGS) {
            this.logsContainer.removeChild(this.logsContainer.lastChild);
        }

        // Trigger flash animations on the system widget cards to capture attention
        if (!fromHistory) {
            this.triggerFlash(typeClass, alertData.target);
        }
    }

    triggerFlash(severity, target) {
        const isVision = target === 'baby';
        const widgetCard = document.getElementById(isVision ? 'vision-status-card' : 'audio-status-card');
        const widgetText = document.getElementById(isVision ? 'vision-status' : 'audio-status');

        if (severity === 'critical' || severity === 'urgent' || severity === 'danger') {
            widgetCard.classList.remove('flash-critical', 'flash-warning');
            void widgetCard.offsetWidth; // hard reflow
            widgetCard.classList.add('flash-critical');
            widgetText.innerText = "HAZARD DETECTED";
            widgetText.className = "status-critical";
        } else if (severity === 'warning' || severity === 'alert') {
            widgetCard.classList.remove('flash-critical', 'flash-warning');
            void widgetCard.offsetWidth;
            widgetCard.classList.add('flash-warning');
            widgetText.innerText = "Warning Alert";
            widgetText.className = "status-warn";
        }

        // Return to normal 5s later
        setTimeout(() => {
            widgetText.innerText = isVision ? "Active" : "Monitoring";
            widgetText.className = "status-normal";
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

                // Append reverse to simulate timeline loading correctly
                pastAlerts.reverse().forEach(alert => {
                    this.renderAlert(alert, true);
                });
            }
        } catch (e) {
            console.error("Failed to fetch history table", e);
        }
    }
}

// Bootstrap application once browser completes CSS/DOM load
window.addEventListener('load', () => {
    window.GuardianApp = new GuardianMonitor();
    window.GuardianApp.init();
});
