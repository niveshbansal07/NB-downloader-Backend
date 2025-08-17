import os
import tempfile
import yt_dlp
import ffmpeg
import logging
import shutil
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

class VideoProcessor:
    def __init__(self, temp_dir: str = None, max_file_size: int = 2 * 1024 * 1024 * 1024):
        self.temp_dir = temp_dir or tempfile.gettempdir()
        self.max_file_size = max_file_size

    # ---------- Get Video Info ----------
    async def get_video_info(self, url: str) -> Dict:
        try:
            ydl_opts = {"quiet": True, "no_warnings": True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

            return {
                "title": info.get("title", "Unknown Title"),
                "thumbnail": info.get("thumbnail"),
                "duration": self._format_duration(info.get("duration", 0)),
                "duration_seconds": info.get("duration", 0),
                "formats": self._extract_qualities(info.get("formats", [])),
                "uploader": info.get("uploader", "Unknown"),
                "view_count": info.get("view_count", 0),
                "like_count": info.get("like_count", 0),
                "webpage_url": info.get("webpage_url", url),
            }

        except Exception as e:
            logger.error(f"Video info error: {str(e)}")
            raise ValueError(f"Failed to extract video information: {str(e)}")

    # ---------- Download & Merge ----------
    async def download_and_merge(self, url: str, progress_callback=None) -> Tuple[str, str]:
        temp_dir = tempfile.mkdtemp(dir=self.temp_dir)
        video_file = os.path.join(temp_dir, "video.mp4")
        audio_file = os.path.join(temp_dir, "audio.m4a")
        output_file = os.path.join(temp_dir, "merged_video.mp4")

        try:
            # Video Download
            v_opts = {
                "format": "bestvideo[ext=mp4]/bestvideo",
                "outtmpl": video_file,
                "progress_hooks": [progress_callback] if progress_callback else None,
            }
            with yt_dlp.YoutubeDL(v_opts) as ydl:
                ydl.download([url])

            if not os.path.exists(video_file):
                raise FileNotFoundError("Video file was not downloaded.")

            # Audio Download
            a_opts = {
                "format": "bestaudio[ext=m4a]/bestaudio",
                "outtmpl": audio_file,
                "progress_hooks": [progress_callback] if progress_callback else None,
            }
            with yt_dlp.YoutubeDL(a_opts) as ydl:
                ydl.download([url])

            if not os.path.exists(audio_file):
                raise FileNotFoundError("Audio file was not downloaded.")

            # Merge with ffmpeg
            ffmpeg.input(video_file).output(
                ffmpeg.input(audio_file),
                output_file,
                vcodec="copy",
                acodec="aac",
                strict="experimental"
            ).overwrite_output().run(capture_stdout=True, capture_stderr=True)

            if not os.path.exists(output_file):
                raise FileNotFoundError("Failed to create merged file.")

            return output_file, self._get_filename_from_url(url)

        except Exception as e:
            logger.error(f"Download/Merge error: {str(e)}")
            self._cleanup_temp_files(temp_dir)
            raise ValueError(f"Failed to download video: {str(e)}")

    # ---------- Helper Functions ----------
    def _format_duration(self, seconds: int) -> str:
        if not seconds:
            return "Unknown"
        h, m, s = seconds // 3600, (seconds % 3600) // 60, seconds % 60
        return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"

    def _extract_qualities(self, formats: List[Dict]) -> List[str]:
        qualities = {f"{fmt['height']}p" for fmt in formats if fmt.get("height")}
        return sorted(qualities, key=lambda x: int(x[:-1]), reverse=True)

    def _get_filename_from_url(self, url: str) -> str:
        try:
            with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info.get("title", "video")
                return "".join(c for c in title if c.isalnum() or c in " -_") + ".mp4"
        except Exception:
            return "downloaded_video.mp4"

    def _cleanup_temp_files(self, temp_dir: str):
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
