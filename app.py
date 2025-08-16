from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import os
import tempfile
import asyncio
import logging
from typing import Optional
import aiofiles
from pathlib import Path

from utils.video_processor import VideoProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="NB Downloader API",
    description="A professional YouTube video downloader API",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize video processor
video_processor = VideoProcessor()

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "NB Downloader API",
        "version": "1.0.0",
        "endpoints": {
            "preview": "/preview?url={youtube_url}",
            "download": "/download?url={youtube_url}"
        }
    }

@app.get("/preview")
async def preview_video(url: str = Query(..., description="YouTube video URL")):
    """Get video preview information"""
    try:
        # Validate URL
        if not url or "youtube.com" not in url and "youtu.be" not in url:
            raise HTTPException(status_code=400, detail="Invalid YouTube URL")
        
        # Get video information
        video_info = video_processor.get_video_info(url)
        
        return {
            "success": True,
            "data": video_info
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in preview endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get video preview")

@app.get("/download")
async def download_video(
    url: str = Query(..., description="YouTube video URL"),
    background_tasks: BackgroundTasks = None
):
    """Download and stream video file"""
    try:
        # Validate URL
        if not url or "youtube.com" not in url and "youtu.be" not in url:
            raise HTTPException(status_code=400, detail="Invalid YouTube URL")
        
        # Get video info first to validate
        video_info = video_processor.get_video_info(url)
        
        # Download and merge video
        output_file, filename = await asyncio.to_thread(video_processor.download_and_merge, url)
        
        # Check file size
        file_size = os.path.getsize(output_file)
        if file_size > video_processor.max_file_size:
            video_processor.cleanup_file(output_file)
            raise HTTPException(status_code=413, detail="File too large")
        
        # Add cleanup task
        if background_tasks:
            background_tasks.add_task(video_processor.cleanup_file, output_file)
        
        # Return file as streaming response
        return FileResponse(
            path=output_file,
            filename=filename,
            media_type='video/mp4',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"',
                'Content-Length': str(file_size)
            }
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in download endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to download video")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "NB Downloader API"}

@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Handle 404 errors"""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Endpoint not found",
            "message": "The requested endpoint does not exist"
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "Something went wrong on our end"
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
    # uvicorn.run(app, host="127.0.0.1", port=8000)
