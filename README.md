# Guardianize - Intelligent Monitoring System


##  Executive Summary

**Guardianize** is an enterprise-grade, AI-powered monitoring application designed specifically to ensure the safety and well-being of infants and children under supervision. Utilizing state-of-the-art computer vision and acoustic anomaly detection paradigms, the system analyzes real-time environmental data to autonomously identify hazards, erratic physical handling, and auditory distress signals.

This repository serves as the official monolithic architecture implementation, integrating a dynamic, multi-page frontend dashboard with a robust, computationally optimized AI inference backend.

##  System Architecture

The project is structured as a streamlined, bare-metal monolithic web application, completely negating the need for complex containerization orchestration like Docker.

### Core Technology Stack

*   **Backend Framework:** FastAPI (ASGI) for asynchronous high-performance routing.
*   **Database Layer:** SQLite powered by SQLAlchemy ORM with Pydantic for rigorous data validation.
*   **Artificial Intelligence:** Hugging Face `transformers` ecosystem.
    *   **Vision Engine:** `facebook/detr-resnet-50` (RT-DETR proxy for precise spatial object tracking and heuristic movement analysis).
    *   **Acoustic Engine:** `MIT/ast-finetuned-audioset-10-10-0.4593` (Audio Spectrogram Transformer for nuanced distress classification).
*   **Frontend Interface:** Pure HTML5, CSS3, and Vanilla JavaScript for maximum performance and direct DOM manipulation.
*   **Communication Protocol:** Native Full-Duplex WebSockets (`ws://`) for uninhibited, low-latency telemetry streaming.

### Functional Paradigms

1.  **Unified Routing:** FastAPI concurrently serves RESTful API endpoints, WebSockets interfaces, and Jinja2-templated HTML views from a single Python instance.
2.  **Asynchronous ML Pipelines:** Heavy inference tasks are offloaded via `asyncio.to_thread` utilizing intelligent temporal frame-skipping, ensuring the primary event loop remains non-blocking on standard computing hardware.
3.  **Persistent Audit Trails:** All anomalous events detected by the AI models are immediately serialized and permanently committed to the local `guardianize.db` ledger for historical auditing.

---

##  Deployment & Installation Guide

This system is configured for exclusive local execution leveraging standard Python virtual environments. Please follow these instructions sequentially.

### Prerequisites

*   **Python:** Version 3.11 or greater must be installed and accessible within your system's `PATH`.
*   **Hardware:** An integrated webcam and microphone are required for edge telemetry capture.

### Environment Initialization

1.  **Acquire Repository:** Navigate to your desired installation directory via your preferred command-line interface (e.g., PowerShell).
    ```powershell
    cd path\to\Baby-Harassment-Detection-System
    ```

2.  **Initialize Virtual Environment:** Generate a localized Python environment to sandbox project dependencies.
    ```powershell
    python -m venv venv
    ```

3.  **Activate Environment:**
    ```powershell
    .\venv\Scripts\activate
    ```
    *(A `(venv)` indicator should now prefix your terminal prompt).*

### Dependency Resolution

Install the required library matrix. Due to the inclusion of PyTorch and deep learning model binaries, this process may require several minutes based on network bandwidth.

```powershell
pip install -r requirements.txt
```

### Application Bootstrapping

Initialize the Uvicorn ASGI server to orchestrate the application lifecycle.

```powershell
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Automated Startup Procedures:**
> *   **Database Hydration:** The SQLite engine will automatically instatiate `guardianize.db` and scaffold all required SQL tables on the initial run.
> *   **Model Caching:** The Hugging Face inference models will be automatically fetched from remote repositories and cached locally during the first initialization.

---

##  User Guide

Once the terminal confirms the successful loading of the **DETR Pipeline** and **Audio Pipeline**, the system is operational.

1.  **Access the Platform:** Navigate your modern web browser (Google Chrome, Microsoft Edge) to [`http://localhost:8000`](http://localhost:8000).
2.  **Authentication:** Proceed to the Login portal. For this MVP iteration, mock authentication is enabled. You may register any structurally valid email profile; the system will autonomously hash the credentials and provision a new entry within the database.
3.  **Live Telemetry:** Upon accessing the Dashboard Command Center, authorize the browser's request for Camera and Microphone access.
4.  **Monitoring:** The system will immediately begin extracting physical frames and acoustic signatures, transmitting them over secure WebSockets mapping directly into the AI heuristic engines. Detected anomalies will populate the "Alert History" ledger in real-time.

### Camera Access Requirement (Important)

- Browsers allow webcam/mic capture only on secure origins: `https://...` or `http://localhost`.
- If you open this app from another device using plain `http://<LAN-IP>:8000`, camera access will be blocked by browser policy.
- For local testing, use `http://localhost:8000` on the same machine running the server.
- For online/LAN access with camera enabled, expose the app over HTTPS (for example with a reverse proxy or HTTPS tunnel).

---

*Guardianize Internal Development Documentation. Unauthorized structural deviation from this architecture is unsupported in the current MVP phase.*
