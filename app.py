from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import yt_dlp

app = FastAPI(title="YouTube Downloader API")

# Allow all origins (for testing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

@app.get("/")
def home():
    return {"status": "ok", "message": "YouTube Downloader API running!"}

@app.get("/download")
def download(
    url: str = Query(..., description="YouTube video URL"),
    type: str = Query("video", description="Choose 'video', 'audio', or 'thumbnail'")
):
    """
    Download YouTube video/audio/thumbnail and return direct file link.
    """

    if not url:
        raise HTTPException(status_code=400, detail="Missing URL parameter")

    try:
        # Options based on type
        if type == "audio":
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": f"{DOWNLOAD_DIR}/%(title)s.%(ext)s",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
            }
        elif type == "video":
            ydl_opts = {
                "format": "best",
                "outtmpl": f"{DOWNLOAD_DIR}/%(title)s.%(ext)s",
            }
        elif type == "thumbnail":
            ydl_opts = {
                "skip_download": True,
                "writethumbnail": True,
                "outtmpl": f"{DOWNLOAD_DIR}/%(title)s.%(ext)s",
            }
        else:
            raise HTTPException(status_code=400, detail="Invalid type. Use 'video', 'audio', or 'thumbnail'")

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if type == "thumbnail":
                thumb_url = info.get("thumbnail")
                return {"thumbnail_url": thumb_url}

            filename = ydl.prepare_filename(info)
            if type == "audio":
                filename = os.path.splitext(filename)[0] + ".mp3"

        download_url = f"/file/{os.path.basename(filename)}"
        return {"title": info.get("title"), "download_url": download_url}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading: {str(e)}")

@app.get("/file/{filename}")
def serve_file(filename: str):
    """
    Serve downloaded file directly.
    """
    file_path = os.path.join(DOWNLOAD_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path=file_path, filename=filename, media_type="application/octet-stream")
