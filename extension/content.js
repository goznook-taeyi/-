// 유튜브 숏츠/시청 페이지에 다운로드 버튼을 주입한다.
// 로컬 서버와의 통신은 background.js(서비스 워커)가 대신한다 —
// 페이지 컨텍스트에서 127.0.0.1로 직접 fetch하면 Chrome의
// Local Network Access 정책에 막히기 때문.

const BUTTON_CLASS = "ysd-download-btn";

const ICON_SVG = `
<svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor" aria-hidden="true">
  <path d="M12 3a1 1 0 0 1 1 1v9.59l3.3-3.3a1 1 0 1 1 1.4 1.42l-5 5a1 1 0 0 1-1.4 0l-5-5a1 1 0 1 1 1.4-1.42l3.3 3.3V4a1 1 0 0 1 1-1z"/>
  <path d="M5 19a1 1 0 0 1 1-1h12a1 1 0 1 1 0 2H6a1 1 0 0 1-1-1z"/>
</svg>`;

function showToast(message, isError = false) {
  const existing = document.querySelector(".ysd-toast");
  if (existing) existing.remove();
  const toast = document.createElement("div");
  toast.className = "ysd-toast" + (isError ? " ysd-toast-error" : "");
  toast.textContent = message;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 4000);
}

// 숏츠는 스크롤로 영상이 바뀌어도 location.href가 갱신되므로 항상 현재 주소를 쓴다.
function currentVideoUrl() {
  return location.href;
}

function sendToBackground(message) {
  return new Promise((resolve) => chrome.runtime.sendMessage(message, resolve));
}

async function pollStatus(jobId, button) {
  for (;;) {
    await new Promise((r) => setTimeout(r, 1000));
    const res = await sendToBackground({ type: "status", jobId });
    if (!res || !res.ok) {
      throw new Error(res?.error || "서버와 연결이 끊어졌습니다.");
    }
    const job = res.data;
    if (job.status === "done") return job;
    if (job.status === "error") throw new Error(job.error || "다운로드 실패");
    const label = button.querySelector(".ysd-progress");
    if (label) label.textContent = `${Math.floor(job.progress || 0)}%`;
  }
}

async function startDownload(button) {
  if (button.dataset.busy === "1") return;
  button.dataset.busy = "1";
  button.classList.add("ysd-busy");
  const icon = button.querySelector(".ysd-icon");
  const progress = document.createElement("span");
  progress.className = "ysd-progress";
  progress.textContent = "0%";
  icon.style.display = "none";
  button.appendChild(progress);

  try {
    const res = await sendToBackground({ type: "download", url: currentVideoUrl() });
    if (!res || !res.ok) {
      throw new Error(res?.error || res?.data?.error || "다운로드 요청 실패");
    }
    const job = await pollStatus(res.data.job_id, button);
    showToast(`다운로드 완료: ${job.filename || "저장됨"} (Downloads/YouTube)`);
  } catch (err) {
    showToast(err.message, true);
  } finally {
    button.dataset.busy = "0";
    button.classList.remove("ysd-busy");
    progress.remove();
    icon.style.display = "";
  }
}

function createButton(shape) {
  const button = document.createElement("button");
  button.className = `${BUTTON_CLASS} ysd-${shape}`;
  button.title = "이 영상 다운로드 (mp4)";
  button.innerHTML = `<span class="ysd-icon">${ICON_SVG}</span>` +
    (shape === "pill" ? '<span class="ysd-label">다운로드</span>' : "");
  button.addEventListener("click", (e) => {
    e.preventDefault();
    e.stopPropagation();
    startDownload(button);
  });
  return button;
}

// 숏츠: 현재 화면에 보이는 영상의 액션 바(좋아요/댓글 열)에 원형 버튼 추가
function injectShortsButton() {
  const renderers = document.querySelectorAll(
    "ytd-reel-video-renderer, ytd-shorts [is-active]"
  );
  for (const renderer of renderers) {
    const actions = renderer.querySelector(
      "#actions, ytd-reel-player-overlay-renderer #actions"
    );
    if (actions && !actions.querySelector(`.${BUTTON_CLASS}`)) {
      actions.prepend(createButton("circle"));
    }
  }
}

// 일반 시청 페이지: 좋아요/공유 버튼이 있는 상단 액션 영역에 알약형 버튼 추가
function injectWatchButton() {
  const menu = document.querySelector(
    "#above-the-fold #top-level-buttons-computed, ytd-watch-metadata #actions-inner #top-level-buttons-computed"
  );
  if (menu && !menu.querySelector(`.${BUTTON_CLASS}`)) {
    menu.appendChild(createButton("pill"));
  }
}

function inject() {
  if (location.pathname.startsWith("/shorts/")) {
    injectShortsButton();
  } else if (location.pathname === "/watch") {
    injectWatchButton();
  }
}

// 유튜브는 SPA라서 페이지 이동/숏츠 스크롤 시 DOM이 갈아끼워진다.
document.addEventListener("yt-navigate-finish", inject);
new MutationObserver(() => inject()).observe(document.body, {
  childList: true,
  subtree: true,
});
inject();
