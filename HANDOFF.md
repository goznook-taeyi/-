# 인수인계 — 솔팅기(hospital-shorts) 안에 유튜브 다운로드 버튼 넣기

이 문서는 **회원님 PC의 Claude Code(PowerShell)** 가 읽고 이어서 작업하기 위한 인수인계서입니다.
지금까지 클라우드 세션에서 진행한 내용과, 로컬에서 마무리해야 할 일을 정리했습니다.

---

## 최종 목표 (사용자 요청 원문)

> "솔팅기 내 골라낸 영상 우측에 버튼을 만들어서 그 버튼을 누르면 바로 다운로드 할 수 있도록 제작해줘"

즉, 사용자가 이미 쓰고 있는 **솔팅기 대시보드**의 영상 목록에서, 각 영상(특히 골라낸 영상) **우측에 ⬇ 다운로드 버튼**을 달고, 누르면 그 영상이 바로 mp4로 저장되게 만드는 것.

## 로컬 PC에 있는 두 프로젝트 (혼동 주의)

사용자 PC에는 이름이 비슷한 두 프로그램이 있는데, 버튼이 들어갈 곳은 **①번**이다.

**① `C:\Users\2taey\hospital-shorts` — 솔팅기 (← 이 작업의 대상)**
- 숏츠 트렌드를 수집·분석해 **골라낸 영상 목록 대시보드**를 만드는 파이썬 파이프라인.
- 실행: 바탕화면 아이콘 → `start_solting.vbs`(숨김) → `start_solting.bat`.
- `run_solting.py` = 파이프라인 실행기(CLI, 대시보드 아님). 확인 결과 마지막 단계에서
  **`src/build_site.py` 가 대시보드 화면을 생성**한다(빌드 순서: build_library → build_kb →
  build_playbooks → **build_site**). 즉 **영상 목록을 렌더링하는 곳은 `src/build_site.py`**.
- 데이터: SQLite DB(`src/db.py`, `src/common.py`), `data/knowledge_base.json`, `data/library`,
  `site/`(생성된 정적 사이트로 추정).
- **다운로드 버튼은 이 대시보드의 영상 항목 우측에 넣는다.**

**② `C:\ai-projects\shortform` — 콘텐츠마케터 키티 (버튼 대상 아님)**
- `mascot.py` = PySide6 바탕화면 마스코트 + 핑크 채팅창. 클릭하면 `claude -p`(로컬 Claude Code)를
  호출해 기획안을 만들고 구글 시트를 생성하는 도우미. **영상 목록이 없으므로 버튼 자리 없음.**
- 참고로 여기서 **로컬에 Claude Code가 설치돼 있음이 확인됨**: `C:\Users\2taey\.local\bin\claude.exe`,
  파이썬은 `C:\Users\2taey\AppData\Local\Programs\Python\Python312\python.exe`.

## 로컬에서 먼저 읽을 파일

`src/build_site.py`(대시보드 생성 = 버튼을 넣을 곳)와 `start_solting.bat`(실행/서빙 방식 확인,
다운로드 서버를 함께 켜지게 손볼 곳). 대시보드가 정적 HTML이면 백엔드가 없으므로,
아래 다운로드 로직을 담은 작은 로컬 서버를 만들어 `start_solting.bat`에서 함께 실행한다.

## 로컬에서 해야 할 작업

1. `run_solting.py`(및 필요 시 `site/`, `src/`, `templates/`, `static/` 등 대시보드 화면을 그리는 파일)를 읽어 **영상 목록을 렌더링하는 지점**을 찾는다.
2. 각 영상 항목 **우측에 ⬇ 다운로드 버튼**을 추가한다. 골라낸(선정된) 영상 목록이 따로 있으면 그쪽에도 추가.
3. 버튼 클릭 시 그 영상의 유튜브 URL을 **다운로드 엔드포인트로 전달**해 mp4로 저장한다.
4. 진행률/완료/실패 상태를 버튼이나 옆에 표시한다.
5. 골라낸 영상 전체를 한 번에 받는 "모두 다운로드" 버튼도 추가하면 좋다.

### 다운로드 구현 방법 (권장)

솔팅기가 이미 파이썬 서버이므로, **별도 서버를 띄우지 말고 솔팅기 서버 안에 다운로드 엔드포인트를 직접 추가**하는 게 가장 깔끔하다. 아래는 이 저장소(클라우드에서 만든 참고 구현)에서 그대로 가져다 쓸 수 있는 로직이다.

**필요 패키지:** `yt-dlp` (그리고 최고화질 병합을 원하면 `ffmpeg`). `pip install yt-dlp`

**핵심 다운로드 로직 (yt-dlp):**
```python
import shutil, threading, uuid
from pathlib import Path
import yt_dlp

DOWNLOAD_DIR = Path.home() / "Downloads" / "YouTube"
ALLOWED_HOSTS = {"www.youtube.com", "youtube.com", "m.youtube.com", "youtu.be"}
jobs = {}  # job_id -> {"status": "downloading"/"done"/"error", "progress": float, ...}

def build_format():
    # ffmpeg 있으면 최고화질 영상+오디오 mp4 병합, 없으면 단일 mp4 스트림
    if shutil.which("ffmpeg"):
        return "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/best"
    return "b[ext=mp4]/best"

def run_download(job_id, url):
    def hook(d):
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            if total:
                jobs[job_id]["progress"] = round(d.get("downloaded_bytes", 0)/total*100, 1)
        elif d["status"] == "finished":
            jobs[job_id]["progress"] = 100.0
    opts = {
        "format": build_format(),
        "outtmpl": str(DOWNLOAD_DIR / "%(title)s [%(id)s].%(ext)s"),
        "merge_output_format": "mp4", "noplaylist": True,
        "progress_hooks": [hook], "quiet": True, "no_warnings": True,
    }
    try:
        DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
        jobs[job_id].update(status="done", progress=100.0,
                            filename=Path(ydl.prepare_filename(info)).name)
    except Exception as e:
        jobs[job_id].update(status="error", error=str(e))

def start_job(url):
    job_id = uuid.uuid4().hex
    jobs[job_id] = {"status": "downloading", "progress": 0.0, "url": url}
    threading.Thread(target=run_download, args=(job_id, url), daemon=True).start()
    return job_id
```

**엔드포인트 (솔팅기가 Flask면 그대로, FastAPI/기타면 형태만 맞춰 이식):**
```python
# POST /download        {"url": "..."}          -> {"job_id": "..."}
# POST /download/batch  {"urls": [...]}          -> {"jobs": [{"url","job_id"} | {"url","error"}]}
# GET  /status/<job_id>                          -> {"status","progress",...}
```
`url`은 `urlparse(url).hostname in ALLOWED_HOSTS` 로 유튜브 도메인인지 검증할 것.

### 프론트(대시보드 화면) 버튼 스니펫

솔팅기 화면이 서버사이드 템플릿이든 순수 JS든, 각 영상 행에 아래 버튼을 붙이면 된다.
(서버 통신을 같은 서버에서 하므로 CORS 불필요. 다른 포트면 서버에 CORS 허용 헤더 추가.)

```javascript
async function downloadVideo(videoUrl, btn) {
  btn.disabled = true;
  try {
    const r = await fetch("/download", {
      method: "POST", headers: {"Content-Type": "application/json"},
      body: JSON.stringify({ url: videoUrl }),
    });
    const { job_id, error } = await r.json();
    if (!r.ok) throw new Error(error);
    for (;;) {
      await new Promise(s => setTimeout(s, 1000));
      const job = await (await fetch(`/status/${job_id}`)).json();
      if (job.status === "done")  { btn.textContent = "✅ 완료"; return; }
      if (job.status === "error") throw new Error(job.error);
      btn.textContent = `${Math.floor(job.progress || 0)}%`;
    }
  } catch (e) { btn.textContent = "다시 시도"; btn.disabled = false; alert(e.message); }
}
// 각 영상 행 우측에: <button onclick="downloadVideo('영상URL', this)">⬇ 다운로드</button>
```

## 검증 방법 (로컬)

1. 솔팅기를 실행하고 대시보드를 연다.
2. 영상 목록에서 ⬇ 버튼이 각 항목 우측에 보이는지 확인.
3. 실제 유튜브 숏츠 하나로 눌러 → 진행률 표시 → `~/Downloads/YouTube/` 에 mp4 생성 확인.
   (로그인 필요한 영상이면 `.env`/`ig_cookies` 처럼 쿠키를 쓰는지 확인. yt-dlp는 `cookiesfrombrowser` 옵션으로 브라우저 쿠키 사용 가능.)
4. "모두 다운로드"로 골라낸 여러 개 일괄 저장 확인.

---

## 참고: 클라우드 세션에서 이미 만들어 둔 것

이 저장소(`goznook-taeyi/-`, 브랜치 `claude/youtube-shorts-download-xpjup0`, PR #1)에는 독립 실행형 참고 구현이 들어 있다. 로컬 작업 시 코드를 그대로 참고/복사하면 된다.

- `server/app.py` — Flask 다운로드 서버(위 로직의 완성본). `/download`, `/download/batch`, `/status/<id>`, `/jobs`, `/health`, `/`(솔팅기 UI)
- `server/static/index.html` — 참고용 솔팅기 대시보드 UI (URL 추가 → 골라내기 → 우측 ⬇ 버튼 다운로드). **이 버튼/폴링 UX를 그대로 hospital-shorts 화면에 이식하면 됨.**
- `server/batch_download.py` — 서버 없이 쓰는 일괄 다운로드 CLI / `download_all(urls)` 함수
- `extension/` — 유튜브 페이지 자체에 버튼을 다는 크롬 확장 (참고용, 이번 작업과는 별개)
- `INTEGRATION.md` — 외부 프로그램에 버튼 다는 스니펫 모음

로컬에서 이 저장소를 함께 참고하려면:
```
git clone https://github.com/goznook-taeyi/-.git ref-downloader
cd ref-downloader && git checkout claude/youtube-shorts-download-xpjup0
```
