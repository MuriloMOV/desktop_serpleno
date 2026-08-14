import asyncio
import json
import logging
import threading
from collections.abc import Callable
from typing import Any

try:
    import websockets
except Exception:
    websockets = None  # type: ignore

logger = logging.getLogger(__name__)


class WebSocketChatClient:
    def __init__(self, base_url: str, auth_service=None):
        self.base_url = base_url.rstrip("/")
        self.auth_service = auth_service
        self._connected = False
        self._connecting = False
        self._callbacks: dict[str, list] = {}
        self._thread: threading.Thread | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._ws: Any = None
        self._should_run = False
        self._room_name: str | None = None
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 5
        self._reconnect_base_delay = 1.0

    def _get_ws_url(self) -> str:
        api_url = self.base_url
        if api_url.startswith("https://"):
            ws_url = "wss://" + api_url[len("https://"):]
        elif api_url.startswith("http://"):
            ws_url = "ws://" + api_url[len("http://"):]
        else:
            ws_url = "ws://" + api_url
        return f"{ws_url}/ws/chat/{self._room_name}/"

    def _get_session_cookie_header(self) -> str | None:
        try:
            if self.auth_service and hasattr(self.auth_service, "session"):
                cookies = self.auth_service.session.cookies
                sessionid = cookies.get("sessionid")
                if sessionid:
                    return f"sessionid={sessionid}"
        except Exception:
            pass
        return None

    def on(self, event: str, callback: Callable):
        self._callbacks.setdefault(event, []).append(callback)

    def off(self, event: str, callback: Callable):
        if event in self._callbacks:
            self._callbacks[event] = [
                cb for cb in self._callbacks[event] if cb != callback
            ]

    def _notify(self, event: str, *args):
        for cb in list(self._callbacks.get(event, [])):
            try:
                cb(*args)
            except Exception:
                pass

    def is_connected(self) -> bool:
        return self._connected

    def connect(self, user_a_id: int, user_b_id: int) -> bool:
        if not websockets:
            return False
        with threading.Lock():
            if self._connected or self._connecting:
                return self._connected
            self._room_name = (
                f"{min(user_a_id, user_b_id)}-{max(user_a_id, user_b_id)}"
            )
            self._connecting = True
            self._should_run = True
            self._reconnect_attempts = 0
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()
        return True

    def connect_group(self, user_id: int) -> bool:
        if not websockets:
            return False
        with threading.Lock():
            if self._connected or self._connecting:
                return self._connected
            self._room_name = f"group-{user_id}"
            self._connecting = True
            self._should_run = True
            self._reconnect_attempts = 0
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()
        return True

    def _run(self):
        loop = None
        try:
            loop = asyncio.new_event_loop()
            self._loop = loop
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._connect_and_listen())
        except Exception as exc:
            logger.error("WebSocket loop error: %s", exc)
        finally:
            self._connected = False
            self._connecting = False
            try:
                self._notify("close")
            except Exception:
                pass
            if loop is not None and not loop.is_closed():
                loop.close()
            self._loop = None

    async def _connect_and_listen(self):
        while self._should_run and self._reconnect_attempts < self._max_reconnect_attempts:
            try:
                ws_url = self._get_ws_url()
                cookie_header = self._get_session_cookie_header()
                extra_headers = {}
                if cookie_header:
                    extra_headers["Cookie"] = cookie_header

                async with websockets.connect(
                    ws_url,
                    additional_headers=extra_headers,
                    ping_interval=20,
                    ping_timeout=20,
                    close_timeout=5,
                ) as ws:
                    self._ws = ws
                    self._connected = True
                    self._connecting = False
                    self._reconnect_attempts = 0
                    self._notify("open")

                    async for raw_msg in ws:
                        if not self._should_run:
                            break
                        try:
                            msg = json.loads(raw_msg)
                            self._notify("message", msg)
                        except Exception:
                            pass

                    if self._should_run:
                        self._connected = False
                        self._notify("close")
                        continue
                    break

            except Exception as exc:
                self._connected = False
                self._connecting = False
                logger.warning("WebSocket connection failed: %s", exc)
                if self._should_run:
                    self._notify("error", exc)
                    delay = min(
                        self._reconnect_base_delay * (2 ** self._reconnect_attempts),
                        30,
                    )
                    self._reconnect_attempts += 1
                    await asyncio.sleep(delay)
                else:
                    break

    def send(self, data: dict) -> bool:
        if not self._connected or not self._ws:
            return False
        try:
            if self._loop and self._loop.is_running():
                fut = asyncio.run_coroutine_threadsafe(
                    self._ws.send(json.dumps(data)), self._loop
                )
                fut.result(timeout=5)
                return True
        except Exception as exc:
            logger.error("WebSocket send failed: %s", exc)
        return False

    def disconnect(self):
        self._should_run = False
        self._connected = False
        self._connecting = False
        try:
            if self._loop and self._loop.is_running() and self._ws:
                asyncio.run_coroutine_threadsafe(self._ws.close(), self._loop).result(
                    timeout=5
                )
        except Exception:
            pass
        self._ws = None
        self._room_name = None
        self._notify("close")
        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=5)
        self._thread = None
