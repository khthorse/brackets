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


def apply_windowed_on_monitor(
    window,
    monitor: MonitorInfo,
    desired_width: int | None = None,
    desired_height: int | None = None,
):
    window.overrideredirect(False)
    window.attributes("-fullscreen", False)

    if desired_width is None:
        desired_width = monitor.work_width
    if desired_height is None:
        desired_height = monitor.work_height

    width, height, x, y = get_centered_window_geometry(
        monitor,
        desired_width=desired_width,
        desired_height=desired_height,
    )
    window.geometry(f"{width}x{height}+{x}+{y}")


def apply_borderless_fullscreen(window, monitor: MonitorInfo):
    window.overrideredirect(True)
    window.attributes("-fullscreen", False)
    window.geometry(
        f"{monitor.width}x{monitor.height}+{monitor.left}+{monitor.top}"
    )
    window.lift()
    window.focus_force()

def get_control_window_geometry(
    monitor: MonitorInfo,
    desired_width: int = 900,
    width_fraction: float = 0.6,
    frame_margin_x: int = 0,
    frame_margin_y: int = 40,
    min_width: int = 700,
    min_height: int = 500,
) -> tuple[int, int, int, int]:
    width = min(desired_width, int(monitor.work_width * width_fraction))
    width = max(min_width, width)

    height = max(min_height, monitor.work_height - frame_margin_y)

    x = monitor.work_left + (monitor.work_width - width) // 2
    y = monitor.work_top + frame_margin_y // 2

    return width, height, x, y

def get_centered_window_geometry(
    monitor: MonitorInfo,
    desired_width: int,
    desired_height: int,
    min_width: int = 400,
    min_height: int = 300,
    frame_margin_y: int = 32,
    top_offset: int = 0,
) -> tuple[int, int, int, int]:
    max_width = max(min_width, monitor.work_width)
    max_height = max(min_height, monitor.work_height - frame_margin_y)

    width = min(desired_width, max_width)
    height = min(desired_height, max_height)

    width = max(min_width, width)
    height = max(min_height, height)

    x = monitor.work_left + (monitor.work_width - width) // 2
    y = monitor.work_top + top_offset

    return width, height, x, y

def apply_main_windowed_on_monitor(
    window,
    monitor: MonitorInfo,
    frame_margin_x: int = 5,
    frame_margin_y: int = 32,
    x_offset: int = -5,
):
    width = monitor.work_width - frame_margin_x
    height = monitor.work_height - frame_margin_y

    x = monitor.work_left + x_offset
    y = monitor.work_top

    window.overrideredirect(False)
    window.attributes("-fullscreen", False)
    window.geometry(f"{width}x{height}+{x}+{y}")

def apply_control_window_on_monitor(
    window,
    monitor: MonitorInfo,
    desired_width: int = 900,
    min_width: int = 700,
    min_height: int = 500,
    frame_margin_y: int = 32,
):
    width, height, x, y = get_centered_window_geometry(
        monitor,
        desired_width=desired_width,
        desired_height=monitor.work_height,
        min_width=min_width,
        min_height=min_height,
        frame_margin_y=frame_margin_y,
        top_offset=0,
    )
    window.geometry(f"{width}x{height}+{x}+{y}")