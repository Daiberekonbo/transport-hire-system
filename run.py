import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn

app = FastAPI(title="My App")

FRONTEND_DIR = Path(__file__).parent / "frontend"


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/api/info")
async def info():
    return {
        "app": "My App",
        "version": "1.0.0",
        "framework": "FastAPI",
        "python": "3.11",
    }


@app.get("/service-worker.js")
async def service_worker():
    return FileResponse(FRONTEND_DIR / "service-worker.js", media_type="application/javascript")


@app.get("/manifest.json")
async def manifest():
    return FileResponse(FRONTEND_DIR / "manifest.json", media_type="application/json")


@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    file_path = FRONTEND_DIR / full_path
    if file_path.exists() and file_path.is_file():
        return FileResponse(file_path)
    return FileResponse(FRONTEND_DIR / "index.html")


if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "5000"))
    uvicorn.run("run:app", host=host, port=port, reload=True)
