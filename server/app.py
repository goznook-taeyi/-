"""유튜브 숏츠/영상 다운로드 로컬 서버.

크롬 확장에서 보낸 유튜브 URL을 받아 yt-dlp로 mp4를 내려받는다.
127.0.0.1 에서만 리슨하므로 외부에서는 접근할 수 없다.

실행:
    pip install -r requirements.txt
    python app.py
"""

import shutil
import threading
import uuid
from pathlib import Path
from urllib.parse import urlparse

import yt_dlp
from flask import Flask, jsonify, request

HOST = "127.0.0.1"
PORT = 8756
DOWNLOAD_DIR = Path.home() / "Downloads" / "YouTube"

ALLOWED_HOSTS = {
    "www.youtube.com",
    "youtube.com",
    "m.youtube.com",
    "youtu.be",
}

app = Flask(__name__)


@app.after_request
def add_cors_headers(resp):
    # 크롬 확장(서비스 워커)은 host_permissions 덕분에 CORS가 필요 없지만,
    # 숏폼솔팅기 같은 로컬 웹앱이 이 API를 호출할 때는 필요하다.
    # 서버가 127.0.0.1에만 바인딩되어 같은 PC에서만 접근 가능하므로 * 허용은 안전하다.
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return resp

# job_id -> {"status": "downloading"|"done"|"error", "progress": float, ...}
jobs = {}
jobs_lock = threading.Lock()


def is_youtube_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    return parsed.scheme in ("http", "https") and parsed.hostname in ALLOWED_HOSTS


def build_format() -> str:
    # ffmpeg이 있으면 최고 화질 영상+오디오를 mp4로 병합, 없으면 단일 mp4 스트림
    if shutil.which("ffmpeg"):
        return "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/best"
    return "b[ext=mp4]/best"


def update_job(job_id: str, **fields):
    with jobs_lock:
        if job_id in jobs:
            jobs[job_id].update(fields)


def run_download(job_id: str, url: str):
    def progress_hook(d):
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            downloaded = d.get("downloaded_bytes", 0)
            if total:
                update_job(job_id, progress=round(downloaded / total * 100, 1))
        elif d["status"] == "finished":
            update_job(job_id, progress=100.0)

    ydl_opts = {
        "format": build_format(),
        "outtmpl": str(DOWNLOAD_DIR / "%(title)s [%(id)s].%(ext)s"),
        "merge_output_format": "mp4",
        "noplaylist": True,
        "progress_hooks": [progress_hook],
        "quiet": True,
        "no_warnings": True,
    }
    try:
        DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
        filename = Path(ydl.prepare_filename(info)).name
        update_job(job_id, status="done", progress=100.0, filename=filename)
    except Exception as exc:  # yt-dlp는 다양한 예외를 던진다
        update_job(job_id, status="error", error=str(exc))


def start_job(url: str) -> str:
    job_id = uuid.uuid4().hex
    with jobs_lock:
        jobs[job_id] = {"status": "downloading", "progress": 0.0, "url": url}
    threading.Thread(target=run_download, args=(job_id, url), daemon=True).start()
    return job_id


@app.get("/")
def index():
    """숏폼 솔팅기 웹 UI — URL을 모아 골라내고 바로 다운로드하는 페이지."""
    return app.send_static_file("index.html")


@app.get("/health")
def health():
    return jsonify({"ok": True})


@app.post("/download")
def download():
    data = request.get_json(silent=True) or {}
    url = data.get("url", "")
    if not is_youtube_url(url):
        return jsonify({"error": "유튜브 URL이 아닙니다."}), 400
    return jsonify({"job_id": start_job(url)})


@app.post("/download/batch")
def download_batch():
    """숏폼솔팅기 같은 외부 프로그램이 골라낸 영상 목록을 일괄 다운로드한다.

    요청:  {"urls": ["https://www.youtube.com/shorts/...", ...]}
    응답:  {"jobs": [{"url": ..., "job_id": ...} 또는 {"url": ..., "error": ...}]}
    """
    data = request.get_json(silent=True) or {}
    urls = data.get("urls")
    if not isinstance(urls, list) or not urls:
        return jsonify({"error": "urls 목록이 필요합니다."}), 400

    results = []
    for url in urls:
        if not isinstance(url, str) or not is_youtube_url(url):
            results.append({"url": url, "error": "유튜브 URL이 아닙니다."})
        else:
            results.append({"url": url, "job_id": start_job(url)})
    return jsonify({"jobs": results})


@app.get("/jobs")
def list_jobs():
    with jobs_lock:
        return jsonify(jobs)


@app.get("/status/<job_id>")
def status(job_id):
    with jobs_lock:
        job = jobs.get(job_id)
        if job is None:
            return jsonify({"error": "존재하지 않는 작업입니다."}), 404
        return jsonify(job)


if __name__ == "__main__":
    print(f"저장 위치: {DOWNLOAD_DIR}")
    if not shutil.which("ffmpeg"):
        print("안내: ffmpeg이 없어 단일 mp4 스트림으로 받습니다. "
              "최고 화질을 원하면 ffmpeg을 설치하세요.")
    app.run(host=HOST, port=PORT)
