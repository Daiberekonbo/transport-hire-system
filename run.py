import os
import sys
import threading
import time
import webbrowser
import ctypes
from pathlib import Path
from typing import Optional

from backend import create_app

LOCAL_URL = "http://127.0.0.1:5000"
BROWSER_DELAY_SECONDS = 2.0
MUTEX_NAME = "Global\\THMS_Desktop_App_Instance_Mutex"
instance_mutex = None


def is_windows() -> bool:
    return os.name == "nt"


def hide_console_window() -> None:
    if not is_windows():
        return
    try:
        kernel32 = ctypes.windll.kernel32
        user32 = ctypes.windll.user32
        hwnd = kernel32.GetConsoleWindow()
        if hwnd:
            SW_HIDE = 0
            user32.ShowWindow(hwnd, SW_HIDE)
    except Exception:
        pass


def show_error_message(title: str, message: str) -> None:
    if is_windows():
        try:
            MB_OK = 0x00000000
            MB_ICONERROR = 0x00000010
            ctypes.windll.user32.MessageBoxW(0, message, title, MB_OK | MB_ICONERROR)
            return
        except Exception:
            pass
    print(f"{title}: {message}")


def _open_browser_after_delay(url: str, delay: float) -> None:
    def _target() -> None:
        time.sleep(delay)
        try:
            webbrowser.open(url, new=2)
        except Exception:
            pass

    thread = threading.Thread(target=_target, daemon=True)
    thread.start()


def acquire_single_instance_mutex() -> bool:
    global instance_mutex
    if not is_windows():
        return True

    try:
        kernel32 = ctypes.windll.kernel32
        instance_mutex = kernel32.CreateMutexW(None, False, MUTEX_NAME)
        if not instance_mutex:
            return True
        ERROR_ALREADY_EXISTS = 183
        if kernel32.GetLastError() == ERROR_ALREADY_EXISTS:
            return False
    except Exception:
        return True
    return True


def get_app_root() -> str:
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def get_tray_icon_path() -> Optional[str]:
    root = Path(get_app_root())
    for icon_name in ("THMS.ico", "thms.ico"):
        candidate = root / icon_name
        if candidate.exists():
            return str(candidate)

    if not getattr(sys, "frozen", False):
        candidate = root.parent / "THMS installer" / "THMS.ico"
        if candidate.exists():
            return str(candidate)
    return None


class FlaskServerController:
    def __init__(self, app, host: str, port: int):
        self.app = app
        self.host = host
        self.port = port
        self._server = None
        self._thread = None
        self._lock = threading.Lock()

    def start(self) -> None:
        with self._lock:
            if self.running:
                return

            try:
                from werkzeug.serving import make_server
            except ImportError as exc:
                raise RuntimeError("Werkzeug is required to start the THMS server") from exc

            self._server = make_server(self.host, self.port, self.app, threaded=True)
            self._thread = threading.Thread(target=self._serve, daemon=True, name="THMSServer")
            self._thread.start()

    def _serve(self) -> None:
        try:
            if self._server is not None:
                self._server.serve_forever()
        except Exception:
            pass
        finally:
            with self._lock:
                self._server = None
                self._thread = None

    def stop(self, timeout: float = 5.0) -> None:
        with self._lock:
            if self._server is None:
                return
            try:
                self._server.shutdown()
            except Exception:
                pass

        if self._thread is not None:
            self._thread.join(timeout)

        with self._lock:
            if self._server is not None:
                try:
                    self._server.server_close()
                except Exception:
                    pass
                self._server = None
            self._thread = None

    def restart(self) -> None:
        self.stop()
        self.start()

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()


def create_system_tray(server_controller: FlaskServerController):
    try:
        from PIL import Image
        from pystray import Icon, Menu, MenuItem
    except ImportError:
        return None

    icon_path = get_tray_icon_path()
    if icon_path is None:
        raise FileNotFoundError("THMS icon was not found for the system tray.")

    icon_image = Image.open(icon_path)

    def open_thms(icon=None, item=None):
        _open_browser_after_delay(LOCAL_URL, 0)

    def restart_thms(icon=None, item=None):
        try:
            server_controller.restart()
        except Exception as exc:
            show_error_message("THMS Restart Error", str(exc))

    def exit_thms(icon=None, item=None):
        try:
            server_controller.stop()
        finally:
            icon.stop()

    menu = Menu(
        MenuItem("Open THMS", open_thms, default=True),
        MenuItem("Restart THMS", restart_thms),
        MenuItem("Exit THMS", exit_thms),
    )

    icon = Icon("THMS", icon_image, "Transport Hire Management System", menu)
    return icon


def run_with_tray(app, host: str, port: int, open_browser: bool) -> None:
    server_controller = FlaskServerController(app, host, port)
    server_controller.start()

    if open_browser:
        _open_browser_after_delay(LOCAL_URL, BROWSER_DELAY_SECONDS)

    tray_icon = create_system_tray(server_controller)
    if tray_icon is None:
        show_error_message(
            "THMS Tray Error",
            "The Windows tray experience requires pystray and Pillow. Please install them or start THMS normally.",
        )
        server_controller.stop()
        return

    try:
        tray_icon.run()
    finally:
        server_controller.stop()


def main() -> None:
    is_frozen = getattr(sys, "frozen", False)
    if is_frozen:
        hide_console_window()
        if not acquire_single_instance_mutex():
            _open_browser_after_delay(LOCAL_URL, BROWSER_DELAY_SECONDS)
            return

    flask_env = os.getenv("FLASK_ENV", "development")
    app_env = "production" if is_frozen else flask_env

    try:
        app = create_app(app_env)
    except Exception as exc:
        show_error_message(
            "THMS Startup Error",
            f"Unable to start THMS because the database connection is not configured.\n\n{exc}",
        )
        return

    if is_frozen:
        app.config["DEBUG"] = False
        app.config["ENV"] = "production"

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "5000"))
    debug = app.config["DEBUG"]
    use_reloader = debug and not is_frozen

    should_open_browser = not debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true" or is_frozen
    if is_windows() and not use_reloader:
        try:
            run_with_tray(app, host, port, should_open_browser)
            return
        except Exception as exc:
            show_error_message(
                "THMS Startup Error",
                f"Unable to start the Windows system tray experience:\n\n{exc}\n\nStarting THMS normally.",
            )

    if should_open_browser:
        _open_browser_after_delay(LOCAL_URL, BROWSER_DELAY_SECONDS)
    app.run(host=host, port=port, debug=debug, use_reloader=use_reloader)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        show_error_message(
            "THMS Startup Error",
            f"Failed to start Transport Hire Management System:\n\n{exc}",
        )
        raise
