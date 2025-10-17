# yt_audio_backend/main.py
import os
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from utils.downloader import download_audio_async, extract_video_id
from utils.cleaner import auto_cleanup

app = FastAPI(title="YouTube Audio Service", version="1.0")

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


@app.on_event("startup")
async def startup_event():
    # 启动自动清理协程（每小时执行一次）
    asyncio.create_task(auto_cleanup(DOWNLOAD_DIR))


@app.post("/download")
async def download_audio(url: str):
    """下载并转换 YouTube 音频"""
    try:
        vid = extract_video_id(url)
        if vid:
            mp3_path = os.path.join(DOWNLOAD_DIR, f"{vid}.mp3")
            if os.path.exists(mp3_path):
                return {"status": "exists", "url": url, "video_id": vid}
        asyncio.create_task(download_audio_async(url, DOWNLOAD_DIR))
        return {"status": "downloading", "url": url, "video_id": vid}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/audio/{video_id}")
async def get_audio(video_id: str):
    """获取音频文件"""
    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.mp3")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, media_type="audio/mpeg")


@app.delete("/audio/{video_id}")
async def delete_audio(video_id: str):
    """删除指定音频文件"""
    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.mp3")
    if os.path.exists(file_path):
        os.remove(file_path)
        return {"deleted": video_id}
    raise HTTPException(status_code=404, detail="File not found")


@app.delete("/audio")
async def clear_all_audios():
    """清空音频目录"""
    count = 0
    for f in os.listdir(DOWNLOAD_DIR):
        if f.endswith(".mp3"):
            os.remove(os.path.join(DOWNLOAD_DIR, f))
            count += 1
    return {"cleared": count}
