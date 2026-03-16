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
        this.reconnectTimer = null;
        this.isCapturing = false;
        this.localStream = null;
    }

    async init() {
        if (!this.videoObj || !this.canvas || !this.ctx) {
            console.error("Dashboard media elements are missing.");
            return;
        }

        if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
            return;
        }

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

        this.ws.onerror = () => {
            this.connStatus.innerHTML = '<span class="dot disconnected"></span>Network Error';
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
            if (this.reconnectTimer) {
                clearTimeout(this.reconnectTimer);
            }
            this.reconnectTimer = setTimeout(() => this.init(), 3000); // Reconnect loop
        };
    }

    async startMediaCapture() {
        if (this.isCapturing) return;

        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            this.connStatus.innerHTML = '<span class="dot disconnected"></span>Media API unsupported';
            alert("This browser cannot access camera APIs. Use a modern Chrome/Edge/Firefox build.");
            return;
        }

        // Camera APIs require secure origins. localhost is allowed, remote HTTP is blocked by browsers.
        const isLocalhost = ["localhost", "127.0.0.1"].includes(window.location.hostname);
        if (!window.isSecureContext && !isLocalhost) {
            this.connStatus.innerHTML = '<span class="dot disconnected"></span>HTTPS required for camera';
            alert("Camera is blocked because this page is not secure. Use HTTPS for online access, or open via http://localhost:8000 on the same machine.");
            return;
        }

        try {
            // Try full AV capture first.
            const stream = await navigator.mediaDevices.getUserMedia({
                video: { width: 1280, height: 720 },
                audio: true
            });
            await this.attachAndStartStream(stream);

        } catch (fullMediaErr) {
            console.warn("AV capture failed, retrying with video only.", fullMediaErr);

            try {
                const videoOnlyStream = await navigator.mediaDevices.getUserMedia({
                    video: { width: 1280, height: 720 },
                    audio: false
                });
                await this.attachAndStartStream(videoOnlyStream);
                this.audioStatus.innerText = "Mic unavailable";
                this.audioStatus.className = "status-warn";
            } catch (videoOnlyErr) {
                console.error("Critical Permission Error accessing local Device", videoOnlyErr);
                this.connStatus.innerHTML = '<span class="dot disconnected"></span>Camera blocked';
                const reason = this.getMediaErrorReason(videoOnlyErr);
                alert(`Camera access failed: ${reason}`);
            }
        }
    }

    getMediaErrorReason(err) {
        const name = err && err.name ? err.name : "UnknownError";

        if (name === "NotAllowedError" || name === "SecurityError") {
            return "permission denied. Allow camera access for this site in browser settings.";
        }
        if (name === "NotFoundError" || name === "DevicesNotFoundError") {
            return "no camera device detected. Connect a webcam and retry.";
        }
        if (name === "NotReadableError" || name === "TrackStartError") {
            return "camera is busy in another app (Zoom/Teams/OBS). Close other apps and retry.";
        }
        if (name === "OverconstrainedError" || name === "ConstraintNotSatisfiedError") {
            return "requested camera resolution is unsupported by this device.";
        }
        return `${name}. Check browser console for details.`;
    }

    stopMediaCapture() {
        if (this.captureTimer) {
            clearInterval(this.captureTimer);
            this.captureTimer = null;
        }

        if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
            this.mediaRecorder.stop();
        }
        this.mediaRecorder = null;

        if (this.localStream) {
            this.localStream.getTracks().forEach(track => track.stop());
        }
        this.localStream = null;
        this.isCapturing = false;
    }

    async attachAndStartStream(stream) {
        this.localStream = stream;

        this.videoObj.onloadedmetadata = async () => {
            try {
                await this.videoObj.play();
            } catch (_) {
                // Browser autoplay policy may block play in rare cases; user interaction will resume it.
            }

            this.canvas.width = this.videoObj.videoWidth || 1280;
            this.canvas.height = this.videoObj.videoHeight || 720;

            const resolutionDetail = document.getElementById('resolution-detail');
            if (resolutionDetail) {
                resolutionDetail.innerText = `(${this.canvas.width}x${this.canvas.height})`;
            }

            if (this.captureTimer) {
                clearInterval(this.captureTimer);
            }

            // Start sending specific frames to RT-DETR Vision service
            this.captureTimer = setInterval(() => this.sendVideoFrame(), CAPTURE_INTERVAL_MS);
            this.isCapturing = true;
        };

        this.videoObj.srcObject = stream;

        // Setup MediaRecorder for audio chunks to LSTM Acoustic service
        const audioTrack = stream.getAudioTracks()[0];
        if (audioTrack && typeof MediaRecorder !== 'undefined') {
            const audioStream = new MediaStream([audioTrack]);
            const preferredMime = 'audio/webm;codecs=opus';
            const options = MediaRecorder.isTypeSupported(preferredMime) ? { mimeType: preferredMime } : {};
            this.mediaRecorder = new MediaRecorder(audioStream, options);

            this.mediaRecorder.ondataavailable = (e) => {
                if (e.data.size > 0 && this.ws && this.ws.readyState === WebSocket.OPEN) {
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
    }

    sendVideoFrame() {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return;
        if (!this.ctx || !this.canvas.width || !this.canvas.height) return;
        if (this.videoObj.readyState < 2) return;

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

window.addEventListener('beforeunload', () => {
    if (window.GuardianApp) {
        window.GuardianApp.stopMediaCapture();
    }
});
