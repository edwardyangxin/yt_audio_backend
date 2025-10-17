# yt_audio_backend/utils/downloader.py
import asyncio
import os
import logging
from urllib.parse import urlparse, parse_qs
import yt_dlp


logger = logging.getLogger(__name__)


def extract_video_id(url: str) -> str | None:
    """从 YouTube URL 提取视频 ID，支持 youtube.com 和 youtu.be 链接。"""
    try:
        parsed = urlparse(url)
        # youtu.be/<id>
        if parsed.netloc.endswith("youtu.be"):
            vid = parsed.path.lstrip("/")
            return vid or None
        # youtube.com/watch?v=<id>
        if parsed.netloc.endswith("youtube.com") or parsed.netloc.endswith("youtube-nocookie.com"):
            qs = parse_qs(parsed.query)
            vid_list = qs.get("v")
            if vid_list:
                return vid_list[0]
        return None
    except Exception:
        return None


async def run_blocking(func, *args, **kwargs):
    """在异步环境中执行阻塞函数"""
    return await asyncio.to_thread(func, *args, **kwargs)


async def download_audio_async(url: str, download_dir: str):
    """异步下载并转换为 MP3"""
    video_id = extract_video_id(url)
    if video_id:
        logger.info("[Downloader] Start downloading video_id=%s", video_id)
    else:
        logger.info("[Downloader] Start downloading from URL with unknown id: %s", url)

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(download_dir, "%(id)s.%(ext)s"),
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "quiet": True,
    }

    def _download():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return info.get("id")

    try:
        result_id = await run_blocking(_download)
        logger.info("[Downloader] Finished downloading video_id=%s", result_id)
        return result_id
    except Exception as e:
        logger.exception("[Downloader] Download failed for URL=%s error=%s", url, e)
        raise
