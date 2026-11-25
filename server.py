import os
import uuid
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import yt_dlp

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

class VideoRequest(BaseModel):
    url: str
    format: str = "mp4"
    quality: str = "1080p"

# Serve a página inicial (index.html) ao acessar o link no celular
@app.get("/")
def serve_frontend():
    return FileResponse("index.html")

@app.post("/analyze")
def analyze_video(req: VideoRequest):
    ydl_opts = {"quiet": True, "no_warnings": True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(req.url, download=False)
            duration_sec = info.get("duration", 0)
            mins, secs = divmod(duration_sec, 60)
            return {
                "title": info.get("title", "Vídeo sem título"),
                "duration": f"{int(mins):02d}:{int(secs):02d}",
                "thumbnail": info.get("thumbnail", ""),
                "source": info.get("extractor_key", "Web")
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/download")
def download_video(req: VideoRequest):
    file_id = str(uuid.uuid4())
    output_template = os.path.join(DOWNLOAD_DIR, f"{file_id}.%(ext)s")

    if req.format == "mp3":
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": output_template,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": req.quality.replace("k", ""),
            }],
        }
        final_ext = "mp3"
    else:
        height = req.quality.replace("p", "")
        ydl_opts = {
            "format": f"bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "outtmpl": output_template,
            "merge_output_format": "mp4",
        }
        final_ext = "mp4"

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(req.url, download=True)
            safe_title = "".join(c for c in info.get("title", "video") if c.isalnum() or c in " -_").strip()
            final_file = os.path.join(DOWNLOAD_DIR, f"{file_id}.{final_ext}")

        return FileResponse(
            path=final_file,
            filename=f"{safe_title}.{final_ext}",
            media_type="application/octet-stream"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
