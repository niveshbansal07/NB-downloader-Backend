import os
import tempfile
import asyncio
import yt_dlp
import ffmpeg
from typing import Dict, List, Optional, Tuple
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class VideoProcessor:
    def __init__(self, temp_dir: str = None, max_file_size: int = 2 * 1024 * 1024 * 1024):  # 2GB default
        self.temp_dir = temp_dir or tempfile.gettempdir()
        self.max_file_size = max_file_size
        
    async def get_video_info(self, url: str) -> Dict:
        """Extract video information without downloading"""
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # Get best thumbnail
                thumbnails = info.get('thumbnails', [])
                best_thumbnail = None
                if thumbnails:
                    # Prefer high quality thumbnails
                    for thumb in thumbnails:
                        if thumb.get('width', 0) >= 480:
                            best_thumbnail = thumb.get('url')
                            break
                    if not best_thumbnail and thumbnails:
                        best_thumbnail = thumbnails[0].get('url')
                
                # Format duration
                duration = info.get('duration', 0)
                duration_str = self._format_duration(duration)
                
                # Get available formats
                formats = info.get('formats', [])
                available_qualities = self._extract_qualities(formats)
                
                return {
                    'title': info.get('title', 'Unknown Title'),
                    'thumbnail': best_thumbnail,
                    'duration': duration_str,
                    'duration_seconds': duration,
                    'formats': available_qualities,
                    'uploader': info.get('uploader', 'Unknown'),
                    'view_count': info.get('view_count', 0),
                    'like_count': info.get('like_count', 0),
                    'webpage_url': info.get('webpage_url', url)
                }
                
        except Exception as e:
            logger.error(f"Error extracting video info: {str(e)}")
            raise ValueError(f"Failed to extract video information: {str(e)}")
    
    async def download_and_merge(self, url: str, progress_callback=None) -> Tuple[str, str]:
        """Download best video and audio, then merge them"""
        temp_dir = tempfile.mkdtemp(dir=self.temp_dir)
        
        try:
            # Download best video and audio separately
            video_file, audio_file = await self._download_separate_streams(url, temp_dir, progress_callback)
            
            # Merge video and audio
            output_file = await self._merge_video_audio(video_file, audio_file, temp_dir)
            
            # Clean up individual files
            if os.path.exists(video_file):
                os.remove(video_file)
            if os.path.exists(audio_file):
                os.remove(audio_file)
                
            return output_file, self._get_filename_from_url(url)
            
        except Exception as e:
            # Clean up on error
            self._cleanup_temp_files(temp_dir)
            raise e
    
    async def _download_separate_streams(self, url: str, temp_dir: str, progress_callback=None) -> Tuple[str, str]:
        """Download best video and audio streams separately"""
        video_file = os.path.join(temp_dir, "video.mp4")
        audio_file = os.path.join(temp_dir, "audio.m4a")
        
        ydl_opts = {
            'outtmpl': {
                'video': video_file,
                'audio': audio_file
            },
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'merge_output_format': None,  # Don't merge automatically
            'writesubtitles': False,
            'writeautomaticsub': False,
            'progress_hooks': [progress_callback] if progress_callback else None,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        # Check if files exist and have content
        if not os.path.exists(video_file) or os.path.getsize(video_file) == 0:
            raise ValueError("Failed to download video stream")
        
        if not os.path.exists(audio_file) or os.path.getsize(audio_file) == 0:
            raise ValueError("Failed to download audio stream")
        
        return video_file, audio_file
    
    async def _merge_video_audio(self, video_file: str, audio_file: str, temp_dir: str) -> str:
        """Merge video and audio using ffmpeg"""
        output_file = os.path.join(temp_dir, "merged_video.mp4")
        
        try:
            # Use ffmpeg to merge video and audio
            stream = ffmpeg.input(video_file)
            audio = ffmpeg.input(audio_file)
            
            ffmpeg.output(
                stream, audio,
                output_file,
                vcodec='copy',  # Copy video codec (no re-encoding)
                acodec='aac',   # Use AAC for audio
                strict='experimental'
            ).overwrite_output().run(capture_stdout=True, capture_stderr=True)
            
            # Check if output file was created successfully
            if not os.path.exists(output_file) or os.path.getsize(output_file) == 0:
                raise ValueError("Failed to merge video and audio")
            
            return output_file
            
        except ffmpeg.Error as e:
            logger.error(f"FFmpeg error: {e.stderr.decode()}")
            raise ValueError(f"Failed to merge video and audio: {str(e)}")
    
    def _format_duration(self, seconds: int) -> str:
        """Format duration in seconds to HH:MM:SS or MM:SS"""
        if not seconds:
            return "Unknown"
        
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"
    
    def _extract_qualities(self, formats: List[Dict]) -> List[str]:
        """Extract available video qualities from formats"""
        qualities = set()
        
        for fmt in formats:
            height = fmt.get('height')
            if height:
                if height >= 1440:
                    qualities.add('1440p')
                elif height >= 1080:
                    qualities.add('1080p')
                elif height >= 720:
                    qualities.add('720p')
                elif height >= 480:
                    qualities.add('480p')
                elif height >= 360:
                    qualities.add('360p')
        
        return sorted(list(qualities), key=lambda x: int(x.replace('p', '')), reverse=True)
    
    def _get_filename_from_url(self, url: str) -> str:
        """Generate a safe filename from URL"""
        try:
            ydl_opts = {'quiet': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info.get('title', 'video')
                # Clean filename
                safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
                return f"{safe_title}.mp4"
        except:
            return "downloaded_video.mp4"
    
    def _cleanup_temp_files(self, temp_dir: str):
        """Clean up temporary files"""
        try:
            import shutil
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
        except Exception as e:
            logger.error(f"Error cleaning up temp files: {str(e)}")
    
    def cleanup_file(self, file_path: str):
        """Clean up a specific file"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            logger.error(f"Error cleaning up file {file_path}: {str(e)}")
