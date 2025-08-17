import os
import tempfile
import asyncio
import yt_dlp
import ffmpeg
from typing import Dict, List, Optional, Tuple
import logging
from pathlib import Path
import shutil

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

            thumbnails = info.get('thumbnails', [])
            best_thumbnail = None
            if thumbnails:
                # Prefer high quality thumbnails
                thumbnails_sorted = sorted(thumbnails, key=lambda t: t.get('width', 0), reverse=True)
                best_thumbnail = thumbnails_sorted[0].get('url')

            duration = info.get('duration', 0)
            duration_str = self._format_duration(duration)

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
            video_file, audio_file = await self._download_separate_streams(url, temp_dir, progress_callback)

            output_file = await self._merge_video_audio(video_file, audio_file, temp_dir)

            # Clean up
            self._safe_remove(video_file)
            self._safe_remove(audio_file)

            return output_file, self._get_filename_from_url(url)

        except Exception as e:
            self._cleanup_temp_files(temp_dir)
            raise e

    async def _download_separate_streams(self, url: str, temp_dir: str, progress_callback=None) -> Tuple[str, str]:
        """Download best video and audio streams separately"""
        video_file = os.path.join(temp_dir, "video.mp4")
        audio_file = os.path.join(temp_dir, "audio.m4a")

        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]',
            'outtmpl': os.path.join(temp_dir, '%(id)s.%(ext)s'),
            'progress_hooks': [progress_callback] if progress_callback else None,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

            # Find actual downloaded files
            vid_ext = 'mp4'
            aud_ext = 'm4a'

            video_file = os.path.join(temp_dir, f"{info['id']}.{vid_ext}")
            audio_file = os.path.join(temp_dir, f"{info['id']}.{aud_ext}")

        if not os.path.exists(video_file):
            raise ValueError("Failed to download video stream")
        if not os.path.exists(audio_file):
            raise ValueError("Failed to download audio stream")

        return video_file, audio_file

    async def _merge_video_audio(self, video_file: str, audio_file: str, temp_dir: str) -> str:
        """Merge video and audio using ffmpeg"""
        output_file = os.path.join(temp_dir, "merged_video.mp4")

        try:
            (
                ffmpeg
                .output(ffmpeg.input(video_file), ffmpeg.input(audio_file), output_file,
                        vcodec='copy', acodec='aac', strict='experimental')
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )

            if not os.path.exists(output_file):
                raise ValueError("Failed to merge video and audio")

            return output_file

        except ffmpeg.Error as e:
            logger.error(f"FFmpeg error: {e.stderr.decode()}")
            raise ValueError("FFmpeg merging failed")

    def _format_duration(self, seconds: int) -> str:
        if not seconds:
            return "Unknown"
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}" if hours else f"{minutes:02d}:{secs:02d}"

    def _extract_qualities(self, formats: List[Dict]) -> List[str]:
        qualities = set()
        for fmt in formats:
            h = fmt.get('height')
            if h:
                if h >= 2160: qualities.add("2160p")
                elif h >= 1440: qualities.add("1440p")
                elif h >= 1080: qualities.add("1080p")
                elif h >= 720: qualities.add("720p")
                elif h >= 480: qualities.add("480p")
                elif h >= 360: qualities.add("360p")
        return sorted(list(qualities), key=lambda x: int(x.replace("p", "")), reverse=True)

    def _get_filename_from_url(self, url: str) -> str:
        try:
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info.get('title', 'video')
                safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
                return f"{safe_title}.mp4"
        except:
            return "downloaded_video.mp4"

    def _cleanup_temp_files(self, temp_dir: str):
        try:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
        except Exception as e:
            logger.error(f"Error cleaning temp files: {str(e)}")

    def _safe_remove(self, path: str):
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception as e:
            logger.warning(f"Could not delete {path}: {e}")
