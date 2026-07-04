// 로컬 서버(127.0.0.1:8756)와의 통신은 전부 여기서 한다.
// 페이지(content script) 컨텍스트에서 로컬 주소로 fetch하면 Chrome의
// Local Network Access 정책에 막히지만, 확장 서비스 워커는
// host_permissions 덕분에 제약 없이 요청할 수 있다.

const SERVER = "http://127.0.0.1:8756";

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  (async () => {
    try {
      let res;
      if (message.type === "download") {
        res = await fetch(`${SERVER}/download`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ url: message.url }),
        });
      } else if (message.type === "status") {
        res = await fetch(`${SERVER}/status/${message.jobId}`);
      } else {
        sendResponse({ ok: false, error: "알 수 없는 요청" });
        return;
      }
      const data = await res.json();
      sendResponse({ ok: res.ok, data });
    } catch {
      sendResponse({
        ok: false,
        serverDown: true,
        error: "로컬 서버를 먼저 실행하세요: python server/app.py",
      });
    }
  })();
  return true; // sendResponse를 비동기로 사용
});
