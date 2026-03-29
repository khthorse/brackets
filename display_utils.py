import ctypes
from dataclasses import dataclass


@dataclass
class MonitorInfo:
    index: int
    left: int
    top: int
    width: int
    height: int

    @property
    def right(self) -> int:
        return self.left + self.width

    @property
    def bottom(self) -> int:
        return self.top + self.height


def get_monitors() -> list[MonitorInfo]:
    monitors = []

    user32 = ctypes.windll.user32

    MONITORENUMPROC = ctypes.WINFUNCTYPE(
        ctypes.c_int,
        ctypes.c_ulong,
        ctypes.c_ulong,
        ctypes.POINTER(ctypes.wintypes.RECT),
        ctypes.c_double,
    )

    def _callback(hMonitor, hdcMonitor, lprcMonitor, dwData):
        rect = lprcMonitor.contents
        monitors.append(
            MonitorInfo(
                index=len(monitors),
                left=rect.left,
                top=rect.top,
                width=rect.right - rect.left,
                height=rect.bottom - rect.top,
            )
        )
        return 1

    user32.EnumDisplayMonitors(0, 0, MONITORENUMPROC(_callback), 0)
    return monitors


def get_monitor_by_index(index: int) -> MonitorInfo:
    monitors = get_monitors()
    if not monitors:
        return MonitorInfo(index=0, left=0, top=0, width=1920, height=1080)

    if index < 0 or index >= len(monitors):
        return monitors[0]

    return monitors[index]


def apply_windowed_on_monitor(window, monitor: MonitorInfo):
    window.overrideredirect(False)
    window.attributes("-fullscreen", False)
    window.geometry(f"{monitor.width}x{monitor.height}+{monitor.left}+{monitor.top}")


def apply_borderless_fullscreen(window, monitor: MonitorInfo):
    window.overrideredirect(True)
    window.attributes("-fullscreen", False)
    window.geometry(f"{monitor.width}x{monitor.height}+{monitor.left}+{monitor.top}")
    window.lift()
    window.focus_force()