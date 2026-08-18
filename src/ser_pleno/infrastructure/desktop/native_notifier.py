"""Notificador desktop nativo para Windows."""

from __future__ import annotations

import logging
import threading

logger = logging.getLogger(__name__)

_IS_WINDOWS = False
try:
    import winsound

    _IS_WINDOWS = True
except Exception:  # pragma: no cover
    winsound = None  # type: ignore

try:
    from plyer import notification as _plyer_notification

    _PLYER_AVAILABLE = True
except Exception:  # pragma: no cover
    _PLYER_AVAILABLE = False

try:
    from win10toast import ToastNotifier

    _WIN10TOAST_AVAILABLE = True
except Exception:  # pragma: no cover
    _WIN10TOAST_AVAILABLE = False


class DesktopNotifier:
    """Envia notificações nativas do Windows e atualiza badge na taskbar."""

    def __init__(
        self,
        app_name: str = "SerPleno",
        enabled: bool = True,
        sound_enabled: bool = True,
        sound_path: str = "",
        window: Any | None = None,
    ):
        self.app_name = app_name
        self.enabled = enabled
        self.sound_enabled = sound_enabled
        self.sound_path = sound_path
        self._window = window
        self._last_count = 0
        self._lock = threading.Lock()
        self._toast = ToastNotifier() if _WIN10TOAST_AVAILABLE else None

    def set_window(self, window: Any | None) -> None:
        self._window = window

    def set_sound_path(self, sound_path: str) -> None:
        with self._lock:
            self.sound_path = sound_path

    def set_enabled(self, enabled: bool) -> None:
        with self._lock:
            self.enabled = enabled

    def set_sound_enabled(self, sound_enabled: bool) -> None:
        with self._lock:
            self.sound_enabled = sound_enabled

    def notify(self, title: str, message: str, duration: int = 5) -> bool:
        with self._lock:
            if not self.enabled:
                return False

        success = False
        try:
            if _PLYER_AVAILABLE:
                _plyer_notification.notify(
                    title=title,
                    message=message,
                    app_name=self.app_name,
                    timeout=duration,
                )
                success = True
        except Exception as exc:
            logger.debug("Falha ao notificar via plyer: %s", exc)

        if not success and _WIN10TOAST_AVAILABLE:
            try:
                self._toast.show_toast(
                    title,
                    message,
                    icon_path=None,
                    duration=duration,
                    threaded=True,
                )
                success = True
            except Exception as exc:
                logger.debug("Falha ao notificar via win10toast: %s", exc)

        if not success:
            try:
                self._windows_fallback(title, message)
                success = True
            except Exception as exc:
                logger.debug("Falha ao notificar via fallback: %s", exc)

        if success:
            self._play_sound()

        return success

    def update_unread_badge(self, count: int) -> None:
        with self._lock:
            if not self.enabled:
                return
            self._last_count = count
        try:
            self._update_taskbar_overlay(count)
            self._update_window_title(count)
        except Exception as exc:
            logger.debug("Falha ao atualizar badge da taskbar: %s", exc)

    def clear_badge(self) -> None:
        self.update_unread_badge(0)

    def _play_sound(self) -> None:
        with self._lock:
            if not self.sound_enabled:
                return
        if not _IS_WINDOWS:
            return
        try:
            if self.sound_path:
                winsound.PlaySound(self.sound_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
            else:
                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        except Exception as exc:
            logger.debug("Falha ao reproduzir som de notificação: %s", exc)

    def _windows_fallback(self, title: str, message: str) -> None:
        if not _IS_WINDOWS:
            return
        try:
            import ctypes

            ctypes.windll.user32.MessageBoxW(0, message, title, 0x00000040)
        except Exception as exc:
            logger.debug("Falha no fallback de notificação: %s", exc)

    def _update_taskbar_overlay(self, count: int) -> None:
        if count <= 0:
            self._clear_taskbar_overlay()
            return
        hwnd = self._get_window_hwnd()
        if not hwnd or not _IS_WINDOWS:
            return
        try:
            import ctypes
            from ctypes import wintypes

            user32 = ctypes.windll.user32

            try:
                import pythoncom  # type: ignore

                pythoncom.CoInitialize()
            except Exception:
                pass

            taskbar = ctypes.POINTER(wintypes.IUnknown)()
            CLSID_TaskbarList = "{56FDF344-FD6D-11d0-958A-006097C9A090}"
            IID_ITaskbarList3 = "{56FDF344-FD6D-11d0-958A-006097C9A090}"
            try:
                ctypes.oledll.ole32.CoCreateInstance(
                    ctypes.c_char_p(CLSID_TaskbarList.encode("utf-8")),
                    None,
                    1,
                    ctypes.c_char_p(IID_ITaskbarList3.encode("utf-8")),
                    ctypes.byref(taskbar),
                )
            except Exception:
                return

            if not taskbar:
                return

            try:
                TBPF_NOPROGRESS = 0
                taskbar.contents[0].lpVtbl.contents[4](taskbar, TBPF_NOPROGRESS)
                taskbar.contents[0].lpVtbl.contents[8](taskbar, hwnd, 1, count, 0)
            except Exception as exc:
                logger.debug("Falha ao definir overlay via ITaskbarList3: %s", exc)
        except Exception as exc:
            logger.debug("Falha ao atualizar overlay da taskbar: %s", exc)

    def _clear_taskbar_overlay(self) -> None:
        hwnd = self._get_window_hwnd()
        if not hwnd or not _IS_WINDOWS:
            return
        try:
            import ctypes
            from ctypes import wintypes

            try:
                import pythoncom  # type: ignore

                pythoncom.CoInitialize()
            except Exception:
                pass

            taskbar = ctypes.POINTER(wintypes.IUnknown)()
            CLSID_TaskbarList = "{56FDF344-FD6D-11d0-958A-006097C9A090}"
            IID_ITaskbarList3 = "{56FDF344-FD6D-11d0-958A-006097C9A090}"
            try:
                ctypes.oledll.ole32.CoCreateInstance(
                    ctypes.c_char_p(CLSID_TaskbarList.encode("utf-8")),
                    None,
                    1,
                    ctypes.c_char_p(IID_ITaskbarList3.encode("utf-8")),
                    ctypes.byref(taskbar),
                )
            except Exception:
                return

            if not taskbar:
                return

            try:
                TBPF_NOPROGRESS = 0
                taskbar.contents[0].lpVtbl.contents[4](taskbar, TBPF_NOPROGRESS)
                taskbar.contents[0].lpVtbl.contents[9](taskbar, hwnd)
            except Exception as exc:
                logger.debug("Falha ao limpar overlay via ITaskbarList3: %s", exc)
        except Exception as exc:
            logger.debug("Falha ao limpar overlay da taskbar: %s", exc)

    def _update_window_title(self, count: int) -> None:
        window = self._window
        if window is None or not hasattr(window, "title"):
            return
        try:
            base_title = getattr(window, "_original_title", None) or window.title()
            if getattr(window, "_original_title", None) is None:
                window._original_title = base_title
            if count > 0:
                window.title(f"{base_title} ({count})")
            else:
                window.title(base_title)
        except Exception as exc:
            logger.debug("Falha ao atualizar título da janela: %s", exc)

    def _get_window_hwnd(self) -> int | None:
        window = self._window
        if window is None:
            return None
        try:
            if hasattr(window, "winfo_id"):
                return int(window.winfo_id())
        except Exception:
            pass
        return None


_notifier: DesktopNotifier | None = None


def get_desktop_notifier() -> DesktopNotifier:
    global _notifier
    if _notifier is None:
        _notifier = DesktopNotifier()
    return _notifier
