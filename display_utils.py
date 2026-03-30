import ctypes
from dataclasses import dataclass


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]


class MONITORINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.c_ulong),
        ("rcMonitor", RECT),
        ("rcWork", RECT),
        ("dwFlags", ctypes.c_ulong),
    ]


@dataclass
class MonitorInfo:
    index: int
    left: int
    top: int
    width: int
    height: int
    work_left: int
    work_top: int
    work_width: int
    work_height: int

    @property
    def right(self) -> int:
        return self.left + self.width

    @property
    def bottom(self) -> int:
        return self.top + self.height

    @property
    def work_right(self) -> int:
        return self.work_left + self.work_width

    @property
    def work_bottom(self) -> int:
        return self.work_top + self.work_height


def _fallback_monitor() -> MonitorInfo:
    return MonitorInfo(
        index=0,
        left=0,
        top=0,
        width=1920,
        height=1080,
        work_left=0,
        work_top=0,
        work_width=1920,
        work_height=1040,
    )


def get_monitors() -> list[MonitorInfo]:
    monitors: list[MonitorInfo] = []
    user32 = ctypes.windll.user32

    MONITORENUMPROC = ctypes.WINFUNCTYPE(
        ctypes.c_int,
        ctypes.c_ulong,
        ctypes.c_ulong,
        ctypes.POINTER(RECT),
        ctypes.c_double,
    )

    def _callback(hMonitor, hdcMonitor, lprcMonitor, dwData):
        info = MONITORINFO()
        info.cbSize = ctypes.sizeof(MONITORINFO)

        user32.GetMonitorInfoW(hMonitor, ctypes.byref(info))

        mon = info.rcMonitor
        work = info.rcWork

        monitors.append(
            MonitorInfo(
                index=len(monitors),
                left=mon.left,
                top=mon.top,
                width=mon.right - mon.left,
                height=mon.bottom - mon.top,
                work_left=work.left,
                work_top=work.top,
                work_width=work.right - work.left,
                work_height=work.bottom - work.top,
            )
        )
        return 1

    user32.EnumDisplayMonitors(0, 0, MONITORENUMPROC(_callback), 0)
    return monitors


def get_monitor_by_index(index: int) -> MonitorInfo:
    monitors = get_monitors()

    if not monitors:
        return _fallback_monitor()

    if index < 0 or index >= len(monitors):
        return monitors[0]

    return monitors[index]


def get_secondary_monitor(primary_index: int) -> MonitorInfo:
    monitors = get_monitors()

    if not monitors:
        return _fallback_monitor()

    if len(monitors) == 1:
        return monitors[0]

    for monitor in monitors:
        if monitor.index != primary_index:
            return monitor

    return monitors[0]


def apply_windowed_on_monitor(window, monitor: MonitorInfo):
    window.overrideredirect(False)
    window.attributes("-fullscreen", False)
    window.geometry(
        f"{monitor.width}x{monitor.height}+{monitor.left}+{monitor.top}"
    )


def apply_borderless_fullscreen(window, monitor: MonitorInfo):
    window.overrideredirect(True)
    window.attributes("-fullscreen", False)
    window.geometry(
        f"{monitor.width}x{monitor.height}+{monitor.left}+{monitor.top}"
    )
    window.lift()
    window.focus_force()