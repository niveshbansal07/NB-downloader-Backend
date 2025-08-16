from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
import os
import asyncio
import logging
from utils.video_processor import VideoProcessor

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="NB Downloader API",
    description="A professional YouTube video downloader API",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Video processor
video_processor = VideoProcessor()

# Root
@app.get("/")
async def root():
    return {
        "message": "NB Downloader API",
        "version": "1.0.0",
        "endpoints": {
            "preview": "/preview?url={youtube_url}",
            "download": "/download?url={youtube_url}"
        }
    }

# Preview endpoint
@app.get("/preview")
async def preview_video(url: str = Query(..., description="YouTube video URL")):
    if not url or ("youtube.com" not in url and "youtu.be" not in url):
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")
    try:
        video_info = video_processor.get_video_info(url)
        return {"success": True, "data": video_info}
    except Exception as e:
        logger.error(f"Preview error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get video preview")

# Download endpoint
@app.get("/download")
async def download_video(url: str = Query(...), background_tasks: BackgroundTasks = None):
    if not url or ("youtube.com" not in url and "youtu.be" not in url):
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")
    try:
        output_file, filename = await asyncio.to_thread(video_processor.download_and_merge, url)
        file_size = os.path.getsize(output_file)
        if file_size > video_processor.max_file_size:
            video_processor.cleanup_file(output_file)
            raise HTTPException(status_code=413, detail="File too large")
        if background_tasks:
            background_tasks.add_task(video_processor.cleanup_file, output_file)
        return FileResponse(
            path=output_file,
            filename=filename,
            media_type='video/mp4',
            headers={"Content-Length": str(file_size)}
        )
    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to download video")

# Health
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "NB Downloader API"}

# 404 handler
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(status_code=404, content={"error": "Endpoint not found", "message": "The requested endpoint does not exist"})

# 500 handler
@app.exception_handler(500)
async def internal_error_handler(request, exc):
    logger.error(f"Internal server error: {str(exc)}")
    return JSONResponse(status_code=500, content={"error": "Internal server error", "message": "Something went wrong on our end"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
