# yt_audio_backend/utils/cleaner.py
import os
import asyncio
import time

async def auto_cleanup(directory: str, expire_hours: int = 24):
    """自动清理超过指定小时的旧音频"""
    while True:
        now = time.time()
        expired = 0
        for file in os.listdir(directory):
            if file.endswith(".mp3"):
                file_path = os.path.join(directory, file)
                if now - os.path.getmtime(file_path) > expire_hours * 3600:
                    os.remove(file_path)
                    expired += 1
        if expired:
            print(f"[Cleaner] Deleted {expired} old files")
        await asyncio.sleep(3600)  # 每小时检查一次
