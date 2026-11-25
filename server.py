@app.post("/download")
def download_video(req: VideoRequest):
    COOKIE_FILE = "cookies.txt" if os.path.exists("cookies.txt") else (
        "/etc/secrets/cookies.txt" if os.path.exists("/etc/secrets/cookies.txt") else None
    )
    file_id = str(uuid.uuid4())
    output_template = os.path.join(DOWNLOAD_DIR, f"{file_id}.%(ext)s")

    if req.format == "mp3":
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": output_template,
            "cookiefile": COOKIE_FILE,
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
            "cookiefile": COOKIE_FILE,
        }
        final_ext = "mp4"

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(req.url, download=True)
            safe_title = "".join(c for c in info.get("title", "video") if c.isalnum() or c in " -_").strip() or "video"
            final_file = os.path.join(DOWNLOAD_DIR, f"{file_id}.{final_ext}")

        return FileResponse(
            path=final_file,
            filename=f"{safe_title}.{final_ext}",
            media_type="application/octet-stream"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
