# YouTube Shorts Downloader

유튜브에서 숏츠나 영상을 보다가 마음에 드는 영상이 있으면 **페이지 안의 다운로드 버튼**을 눌러 바로 mp4로 저장할 수 있는 도구입니다.

두 부분으로 구성됩니다.

| 구성 요소 | 역할 |
|---|---|
| `extension/` (크롬 확장) | 유튜브 페이지에 다운로드 버튼을 추가하고, 클릭 시 영상 URL을 로컬 서버로 전송 |
| `server/` (Python 로컬 서버) | [yt-dlp](https://github.com/yt-dlp/yt-dlp)로 영상을 내려받아 `~/Downloads/YouTube/` 에 mp4로 저장 |

## 설치

### 1. 로컬 서버

Python 3.9 이상이 필요합니다.

```bash
pip install -r server/requirements.txt
python server/app.py
```

서버는 `127.0.0.1:8756` 에서만 동작하며 외부에서는 접근할 수 없습니다.

> **선택:** 최고 화질(1080p 이상)로 받으려면 [ffmpeg](https://ffmpeg.org/download.html)을 설치하세요.
> ffmpeg이 없으면 영상+오디오가 합쳐진 단일 mp4 스트림(보통 720p)으로 자동 폴백됩니다.

### 2. 크롬 확장

1. 크롬에서 `chrome://extensions` 접속
2. 우측 상단 **개발자 모드** 켜기
3. **압축해제된 확장 프로그램을 로드합니다** 클릭 → 이 저장소의 `extension/` 폴더 선택

## 사용법

1. 로컬 서버를 실행한 상태에서 유튜브를 엽니다.
2. 버튼 위치:
   - **숏츠** (`youtube.com/shorts/...`): 좋아요/댓글 버튼이 있는 우측 액션 바 맨 위의 ⬇ 원형 버튼
   - **일반 영상** (`youtube.com/watch?v=...`): 좋아요/공유 버튼 옆의 "다운로드" 버튼
3. 버튼을 누르면 진행률이 표시되고, 완료되면 `~/Downloads/YouTube/제목 [영상ID].mp4` 로 저장됩니다.

서버가 꺼져 있으면 "로컬 서버를 먼저 실행하세요" 안내가 표시됩니다.

## 외부 프로그램 연동 (예: 숏폼솔팅기)

숏폼솔팅기처럼 영상을 골라내는 프로그램에서 선택된 URL 목록을 넘겨 일괄 다운로드할 수 있습니다. 두 가지 방법을 제공합니다.

### 방법 1 — HTTP API (서버 실행 중일 때)

```python
import requests

selected = [
    "https://www.youtube.com/shorts/AAAA",
    "https://www.youtube.com/shorts/BBBB",
]
res = requests.post("http://127.0.0.1:8756/download/batch", json={"urls": selected})
print(res.json())   # 각 URL의 job_id (진행률은 GET /status/<job_id> 또는 GET /jobs 로 확인)
```

### 방법 2 — CLI / 파이썬 임포트 (서버 없이)

```bash
# 한 줄에 URL 하나인 텍스트 파일로
python server/batch_download.py 골라낸영상들.txt

# 또는 URL을 직접 나열
python server/batch_download.py https://www.youtube.com/shorts/AAAA https://www.youtube.com/shorts/BBBB
```

숏폼솔팅기가 파이썬 프로젝트라면 함수로 바로 불러 쓸 수도 있습니다.

```python
import sys
sys.path.insert(0, r"이_저장소_경로\server")   # 예: C:\ai-projects 쪽 코드에서

from batch_download import download_all
done, failed = download_all(selected)
```

다운로드 결과는 모두 `~/Downloads/YouTube/` 에 저장됩니다.

## 주의

이 도구는 **본인이 시청 권한을 가진 영상을 개인 소장 용도로** 저장하기 위한 것입니다.
저작권이 있는 콘텐츠의 재배포는 YouTube 서비스 약관 및 저작권법에 위배될 수 있습니다.
