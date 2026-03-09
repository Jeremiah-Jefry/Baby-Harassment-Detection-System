import os
import subprocess
import time
import sys
from pathlib import Path

def start_services():
    """
    Utility script to concurrently start the Guardianize Frontend & Backend 
    servers. It launches both in the background and consolidates their output.
    """
    
    root_dir = Path(__file__).resolve().parent
    frontend_dir = root_dir / "frontend"
    backend_dir = root_dir / "backend"
    
    print("Starting Guardianize Enterprise Architecture...\n")

    # 1. Start the HTTP Server for the Frontend Dashboard (Port 8080)
    print("Starting Frontend Server (Port 8080)...")
    frontend_process = subprocess.Popen(
        [sys.executable, "-m", "http.server", "8080"],
        cwd=frontend_dir
    )
    
    # Quick artificial delay to ensure frontend bounds to loopback properly
    time.sleep(1)
    
    # 2. Start the Uvicorn ASGI Server for the FastAPI Backend (Port 8000)
    print("Starting ASGI Backend (Port 8000)...")
    backend_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"],
        cwd=backend_dir
    )
    
    print("\nAll services running!")
    print("\nOpen your browser to: http://localhost:8080\n")
    print("Press CTRL+C at any time to gracefully terminate both servers.\n")
    
    try:
        # Keep main thread alive while subprocesses run in background
        while True:
            time.sleep(1)
            
            # Watchdog: Exit if either process unexpectedly crashes
            if frontend_process.poll() is not None or backend_process.poll() is not None:
                print("⚠️ A sub-process died unexpectedly. Shutting down system.")
                break
                
    except KeyboardInterrupt:
        print("\n\nShutting down Guardianize services gracefully...")
        
    finally:
        # Guarantee both processes are terminated immediately 
        frontend_process.terminate()
        backend_process.terminate()
        frontend_process.wait()
        backend_process.wait()
        print("Goodbye!")

if __name__ == "__main__":
    start_services()
