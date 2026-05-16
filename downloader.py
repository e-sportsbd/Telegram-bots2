import yt_dlp
import os
import tempfile

# Quality format map
QUALITY_FORMATS = {
    "audio": "bestaudio/best",
    "360":   "bestvideo[height<=360]+bestaudio/best[height<=360]",
    "720":   "bestvideo[height<=720]+bestaudio/best[height<=720]",
    "1080":  "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
}

def get_video_info(url: str) -> dict:
    """Fetch video metadata without downloading."""
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return {
            "title": info.get("title", "Unknown"),
            "duration": info.get("duration", 0),
            "thumbnail": info.get("thumbnail", ""),
            "uploader": info.get("uploader", "Unknown"),
        }

def download_video(url: str, quality: str) -> str:
    """Download video/audio and return the output file path."""
    fmt = QUALITY_FORMATS.get(quality, QUALITY_FORMATS["720"])
    tmpdir = tempfile.mkdtemp()

    if quality == "audio":
        ydl_opts = {
            "format": fmt,
            "outtmpl": os.path.join(tmpdir, "%(title)s.%(ext)s"),
            "quiet": True,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        }
    else:
        ydl_opts = {
            "format": fmt,
            "outtmpl": os.path.join(tmpdir, "%(title)s.%(ext)s"),
            "quiet": True,
            "merge_output_format": "mp4",
            "postprocessors": [{
                "key": "FFmpegVideoConvertor",
                "preferedformat": "mp4",
            }],
        }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    # Find the downloaded file
    files = os.listdir(tmpdir)
    if not files:
        raise FileNotFoundError("Download produced no output file.")

    return os.path.join(tmpdir, files[0])
