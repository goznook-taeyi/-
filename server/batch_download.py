"""골라낸 영상 URL 목록을 일괄 다운로드하는 CLI.

숏폼솔팅기 같은 외부 프로그램에서 서버 없이 바로 호출할 수 있다.

사용법:
    python batch_download.py urls.txt          # 한 줄에 URL 하나인 텍스트 파일
    python batch_download.py URL1 URL2 ...     # URL을 직접 나열

외부 파이썬 코드에서 임포트해서 쓸 수도 있다:
    from batch_download import download_all
    download_all(["https://www.youtube.com/shorts/...", ...])
"""

import sys
from pathlib import Path

import yt_dlp

from app import DOWNLOAD_DIR, build_format, is_youtube_url


def download_all(urls):
    """URL 목록을 순서대로 내려받고 (성공 목록, 실패 목록)을 반환한다."""
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    ydl_opts = {
        "format": build_format(),
        "outtmpl": str(DOWNLOAD_DIR / "%(title)s [%(id)s].%(ext)s"),
        "merge_output_format": "mp4",
        "noplaylist": True,
        "ignoreerrors": False,
    }
    done, failed = [], []
    for i, url in enumerate(urls, 1):
        print(f"[{i}/{len(urls)}] {url}")
        if not is_youtube_url(url):
            print("  건너뜀: 유튜브 URL이 아닙니다.")
            failed.append((url, "유튜브 URL이 아닙니다."))
            continue
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.extract_info(url, download=True)
            done.append(url)
        except Exception as exc:
            print(f"  실패: {exc}")
            failed.append((url, str(exc)))
    return done, failed


def read_urls(args):
    if len(args) == 1 and Path(args[0]).is_file():
        lines = Path(args[0]).read_text(encoding="utf-8").splitlines()
        return [line.strip() for line in lines if line.strip()]
    return args


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    urls = read_urls(sys.argv[1:])
    done, failed = download_all(urls)
    print(f"\n완료 {len(done)}개, 실패 {len(failed)}개 → 저장 위치: {DOWNLOAD_DIR}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
