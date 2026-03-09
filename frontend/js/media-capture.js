import { MediaStreamManager } from './ws-manager.js';

/**
 * Handles WebRTC getUserMedia capture, renders it locally to a 
 * `<video>` element, and periodically pushes frames and audio chunks
 * to the backend WebSocket for AI analysis.
 */
export class MediaCaptureService {
    constructor() {
        this.videoElement = document.getElementById('local-video');
        this.canvas = document.getElementById('frame-canvas');
        if (this.canvas) {
            this.ctx = this.canvas.getContext('2d', { willReadFrequently: true });
        }

        this.streamManager = new MediaStreamManager();
        this.streamManager.connect();

        this.mediaStream = null;
        this.mediaRecorder = null;
        this.frameIntervalId = null;

        // Frame rate config (e.g. 5 FPS for AI processing to save bandwidth)
        this.FPS = 5;
        // Audio chunk config (send audio every 1 second)
        this.AUDIO_CHUNK_MS = 1000;
    }

    async init() {
        try {
            console.log("Requesting camera and microphone permissions...");
            this.mediaStream = await navigator.mediaDevices.getUserMedia({
                video: { width: { ideal: 640 }, height: { ideal: 480 } },
                audio: true
            });

            // Connect the stream to the local video element so user can see it
            if (this.videoElement) {
                this.videoElement.srcObject = this.mediaStream;
            }

            // Start sending frames and audio once WebSocket is ready
            // We wait slightly to ensure WS connection is established
            setTimeout(() => {
                this.startVideoFrameExtraction();
                this.startAudioChunking();
            }, 1000);

        } catch (error) {
            console.error("Error accessing media devices:", error);
            alert("Could not access camera/microphone. Please ensure permissions are granted.");
        }
    }

    startVideoFrameExtraction() {
        if (!this.canvas || !this.videoElement) return;

        // Set canvas dimensions to match video
        this.canvas.width = 640;
        this.canvas.height = 480;

        const intervalMs = 1000 / this.FPS;

        this.frameIntervalId = setInterval(() => {
            if (this.videoElement.readyState >= 2) {
                // Draw current video frame to hidden canvas
                this.ctx.drawImage(this.videoElement, 0, 0, this.canvas.width, this.canvas.height);

                // Convert to compressed jpeg base64
                const base64Frame = this.canvas.toDataURL('image/jpeg', 0.6);

                // Route through the WS Manager
                this.streamManager.sendMediaPayload("video_frame", base64Frame);
            }
        }, intervalMs);
    }

    startAudioChunking() {
        if (!this.mediaStream) return;

        // We only want the audio tracks for the MediaRecorder
        const audioTracks = this.mediaStream.getAudioTracks();
        if (audioTracks.length === 0) return;

        const audioStream = new MediaStream(audioTracks);

        try {
            this.mediaRecorder = new MediaRecorder(audioStream, {
                // Highly compressed audio type supported by most browsers
                mimeType: 'audio/webm;codecs=opus'
            });

            this.mediaRecorder.ondataavailable = async (event) => {
                if (event.data.size > 0) {
                    // Convert Blob to Base64 to send via standard WS text frame
                    const reader = new FileReader();
                    reader.onloadend = () => {
                        const base64Audio = reader.result;
                        this.streamManager.sendMediaPayload("audio_chunk", base64Audio);
                    };
                    reader.readAsDataURL(event.data);
                }
            };

            this.mediaRecorder.start(this.AUDIO_CHUNK_MS);
            console.log(`Started audio chunking every ${this.AUDIO_CHUNK_MS}ms`);
        } catch (e) {
            console.error("MediaRecorder error:", e);
        }
    }
}
