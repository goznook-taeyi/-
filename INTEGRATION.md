# 숏폼솔팅기 연동 가이드 — 골라낸 영상 옆에 다운로드 버튼 달기

숏폼솔팅기(예: `C:\ai-projects\shortform`)의 영상 목록에서 **각 영상 우측에 ⬇ 버튼**을 달고,
누르면 이 저장소의 다운로드 서버가 바로 mp4로 저장하게 만드는 방법입니다.

## 준비물

다운로드 서버가 켜져 있어야 합니다.

```bash
pip install -r server/requirements.txt
python server/app.py
```

## API 계약 (솔팅기가 호출할 주소)

| 요청 | 내용 |
|---|---|
| `POST http://127.0.0.1:8756/download` | 본문 `{"url": "<유튜브 URL>"}` → 응답 `{"job_id": "..."}` |
| `POST http://127.0.0.1:8756/download/batch` | 본문 `{"urls": [...]}` → 응답 `{"jobs": [...]}` |
| `GET http://127.0.0.1:8756/status/<job_id>` | `{"status": "downloading"/"done"/"error", "progress": 0~100, ...}` |
| `GET http://127.0.0.1:8756/health` | 서버 실행 확인 `{"ok": true}` |

CORS가 허용되어 있어 로컬 웹앱에서 바로 `fetch` 할 수 있고, 저장 위치는 `~/Downloads/YouTube/` 입니다.

## 방법 A — 가장 쉬움: 솔팅기 작업하는 클로드 세션에 맡기기

숏폼솔팅기를 만들었던 클로드 세션(또는 그 저장소로 새 세션)을 열고, 아래 프롬프트를 그대로 붙여넣으세요.

> 영상 목록에서 각 영상(또는 골라낸 영상) 우측에 ⬇ 다운로드 버튼을 추가해줘.
> 버튼을 누르면 `http://127.0.0.1:8756/download` 로 `{"url": "<그 영상의 유튜브 URL>"}` 을 POST 하고,
> 응답의 `job_id` 로 `http://127.0.0.1:8756/status/<job_id>` 를 1초마다 폴링해서
> 버튼에 진행률(%)을 표시하고, `status`가 `done`이면 "완료", `error`면 오류 메시지를 보여줘.
> 요청 자체가 실패하면 "다운로드 서버를 먼저 실행하세요 (python server/app.py)" 라고 안내해줘.
> 골라낸 영상 전체를 한 번에 받는 버튼도 하나 추가해줘 —
> `http://127.0.0.1:8756/download/batch` 에 `{"urls": [...]}` 를 POST 하면 돼.
> CORS는 서버에서 이미 허용돼 있어.

## 방법 B — 웹 UI(HTML/JS)에 직접 붙이기

솔팅기가 브라우저 화면이라면, 아래 함수를 스크립트에 추가하고
영상 항목을 그리는 곳에서 `makeDownloadButton(영상URL)` 을 만들어 행 우측에 붙이면 끝입니다.

```javascript
const DOWNLOADER = "http://127.0.0.1:8756";

function makeDownloadButton(videoUrl) {
  const btn = document.createElement("button");
  btn.textContent = "⬇ 다운로드";
  btn.onclick = async () => {
    btn.disabled = true;
    try {
      const res = await fetch(`${DOWNLOADER}/download`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: videoUrl }),
      }).catch(() => { throw new Error("다운로드 서버를 먼저 실행하세요 (python server/app.py)"); });
      const { job_id, error } = await res.json();
      if (!res.ok) throw new Error(error);
      for (;;) {                                   // 1초마다 진행률 폴링
        await new Promise(r => setTimeout(r, 1000));
        const job = await (await fetch(`${DOWNLOADER}/status/${job_id}`)).json();
        if (job.status === "done") { btn.textContent = "✅ 완료"; return; }
        if (job.status === "error") throw new Error(job.error);
        btn.textContent = `${Math.floor(job.progress || 0)}%`;
      }
    } catch (e) {
      btn.textContent = "⬇ 다운로드";
      btn.disabled = false;
      alert(e.message);
    }
  };
  return btn;
}

// 사용 예: 영상 행을 만드는 곳에서
// row.appendChild(makeDownloadButton(video.url));
```

## 방법 C — 파이썬 GUI(tkinter 등)에 직접 붙이기

```python
import threading
import requests  # pip install requests

DOWNLOADER = "http://127.0.0.1:8756"

def download_video(video_url, on_update):
    """버튼 클릭 핸들러에서 호출. on_update(문구)로 버튼/라벨 글자를 갱신한다."""
    def worker():
        try:
            res = requests.post(f"{DOWNLOADER}/download", json={"url": video_url}, timeout=5)
        except requests.ConnectionError:
            on_update("서버를 먼저 실행하세요")
            return
        job_id = res.json().get("job_id")
        while True:
            job = requests.get(f"{DOWNLOADER}/status/{job_id}").json()
            if job["status"] == "done":
                on_update("✅ 완료")
                return
            if job["status"] == "error":
                on_update("실패")
                return
            on_update(f"{int(job.get('progress', 0))}%")
            import time; time.sleep(1)
    threading.Thread(target=worker, daemon=True).start()

# tkinter 사용 예 — 영상 행마다:
# btn = tk.Button(row, text="⬇")
# btn.config(command=lambda u=video_url, b=btn: download_video(u, lambda t: b.config(text=t)))
```

서버 없이 쓰고 싶으면 `server/batch_download.py` 의 `download_all(urls)` 를 임포트해도 됩니다 (README 참고).
