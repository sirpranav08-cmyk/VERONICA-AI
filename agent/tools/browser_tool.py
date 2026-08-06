"""
VERONICA Browser Control Tool
Full browser automation using Playwright (sync API run in a dedicated thread
to avoid conflicts with the agent's asyncio event loop)
"""
import threading
import queue
from playwright.sync_api import sync_playwright

_browser = None
_page = None
_playwright = None

_task_q = queue.Queue()
_worker_started = False
_worker_lock = threading.Lock()


def _ensure_page():
    global _browser, _page, _playwright
    needs_restart = False

    if _page is None or _browser is None:
        needs_restart = True
    else:
        try:
            if not _browser.is_connected():
                needs_restart = True
            elif _page.is_closed():
                needs_restart = True
        except Exception:
            needs_restart = True

    if needs_restart:
        try:
            if _playwright:
                _playwright.stop()
        except Exception:
            pass
        _browser = None
        _page = None
        _playwright = sync_playwright().start()
        _browser = _playwright.chromium.launch(headless=False)
        _page = _browser.new_page()

    return _page

def _worker_loop():
    while True:
        func, args, kwargs, result_q = _task_q.get()
        try:
            result = func(*args, **kwargs)
            result_q.put(("ok", result))
        except Exception as e:
            result_q.put(("error", str(e)))


def _start_worker():
    global _worker_started
    with _worker_lock:
        if not _worker_started:
            t = threading.Thread(target=_worker_loop, daemon=True)
            t.start()
            _worker_started = True


def _run_in_browser_thread(func, *args, **kwargs):
    """Submit a function to the dedicated Playwright thread and wait for result."""
    _start_worker()
    result_q = queue.Queue()
    _task_q.put((func, args, kwargs, result_q))
    status, value = result_q.get(timeout=30)
    if status == "error":
        return f"Error: {value}"
    return value


# ── Internal (run inside worker thread only) ─────────────────────────

def _open_url(url: str) -> str:
    if not url.startswith('http'):
        url = 'https://' + url
    page = _ensure_page()
    try:
        page.goto(url, timeout=15000)
    except Exception:
        # Browser may have died between check and use — force a fresh one and retry once
        global _browser, _page, _playwright
        _browser = None
        _page = None
        page = _ensure_page()
        page.goto(url, timeout=15000)
    return f"Opened: {url} — Title: {page.title()}"


def _click_element(selector: str) -> str:
    page = _ensure_page()
    page.click(selector, timeout=5000)
    return f"Clicked: {selector}"


def _type_text(selector: str, text: str) -> str:
    page = _ensure_page()
    page.fill(selector, text)
    return f"Typed '{text}' into {selector}"


def _get_page_text() -> str:
    page = _ensure_page()
    text = page.inner_text('body')
    return text[:2000]


def _search_google(query: str) -> str:
    page = _ensure_page()
    page.goto(f"https://www.google.com/search?q={query}&hl=en&gl=us")
    page.wait_for_timeout(2000)
    try:
        page.click("button:has-text('Accept all')", timeout=2000)
        page.wait_for_timeout(1000)
    except Exception:
        pass
    try:
        page.wait_for_selector('h3', timeout=8000)
    except Exception:
        pass
    results = page.query_selector_all('h3')
    texts = [r.inner_text() for r in results[:5] if r.inner_text()]
    if not texts:
        return f"No results found for '{query}' (page may not have loaded fully)"
    return f"Google results for '{query}':\n" + "\n".join(texts)


def _take_screenshot(path: str) -> str:
    page = _ensure_page()
    page.screenshot(path=path)
    return f"Screenshot saved to {path}"


def _get_current_url() -> str:
    page = _ensure_page()
    return f"Current URL: {page.url} | Title: {page.title()}"


def _close_browser() -> str:
    global _browser, _page, _playwright
    if _browser:
        _browser.close()
    if _playwright:
        _playwright.stop()
    _browser = None
    _page = None
    _playwright = None
    return "Browser closed"


def _scroll_page(direction: str) -> str:
    page = _ensure_page()
    if direction == "down":
        page.keyboard.press("PageDown")
    else:
        page.keyboard.press("PageUp")
    return f"Scrolled {direction}"


def _go_back() -> str:
    page = _ensure_page()
    page.go_back()
    return f"Went back to: {page.url}"


# ── Public API (safe to call from async code / any thread) ──────────

def open_url(url: str) -> str:
    return _run_in_browser_thread(_open_url, url)


def click_element(selector: str) -> str:
    return _run_in_browser_thread(_click_element, selector)


def type_text(selector: str, text: str) -> str:
    return _run_in_browser_thread(_type_text, selector, text)


def get_page_text() -> str:
    return _run_in_browser_thread(_get_page_text)


def search_google(query: str) -> str:
    return _run_in_browser_thread(_search_google, query)


def take_screenshot(path: str = "D:/jarvis-agent/agent/data/browser_screenshot.png") -> str:
    return _run_in_browser_thread(_take_screenshot, path)


def get_current_url() -> str:
    return _run_in_browser_thread(_get_current_url)


def close_browser() -> str:
    return _run_in_browser_thread(_close_browser)


def scroll_page(direction: str = "down") -> str:
    return _run_in_browser_thread(_scroll_page, direction)


def go_back() -> str:
    return _run_in_browser_thread(_go_back)


if __name__ == "__main__":
    print("Testing browser...")
    print(open_url("https://google.com"))
    print(search_google("VERONICA AI assistant"))