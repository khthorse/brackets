import customtkinter as ctk
from timer import Timer
from paths import resource_path
from PIL import Image
import time

from models import TournamentModel
from bracket_canvas import TournamentBracketCanvas
from control_window import ControlWindow
from translations import t, set_language
from settings import AppSettings
from tournament_state import TournamentState
from display_utils import (
    get_monitor_by_index,
    get_secondary_monitor,
    get_centered_window_geometry,
    apply_borderless_fullscreen,
    apply_main_windowed_on_monitor,
    apply_control_window_on_monitor,
    apply_dark_title_bar,
)

def on_resize(event):
    if event.widget != root:
        return

    width = root.winfo_width()
    height = root.winfo_height()

    if width < 100 or height < 100:
        return

    resolution_scale = min(height / 1080, width / 1920)
    resolution_scale = max(0.9, min(1.5, resolution_scale))

    timer_count = settings.get_timer_count()

    if timer_count <= 2:
        count_scale = 1.0
    elif timer_count == 3:
        count_scale = 0.82
    elif timer_count == 4:
        count_scale = 0.70
    else:
        count_scale = 0.58

    new_scale = resolution_scale * count_scale

    for t in timers:
        if t.frame.winfo_exists():
            t.set_scale(new_scale)

def get_title_font_size(screen_height: int) -> int:
    base = 40  # størrelse for 1080p
    scale = screen_height / 1080

    # clamp så det ikke blir for ekstremt
    scale = max(0.8, min(1.8, scale))

    return int(base * scale)

def apply_root_window_mode():
    if settings.fullscreen_enabled:
        apply_borderless_fullscreen(root, monitor)
    else:
        apply_main_windowed_on_monitor(root, monitor)
        apply_dark_title_bar(root)


def toggle_root_fullscreen():
    settings.fullscreen_enabled = not settings.fullscreen_enabled
    apply_root_window_mode()

    if "control_window" in globals():
        control_window.update_fullscreen_button_text()

def find_time():
    year = str(time.localtime().tm_year)
    month = time.localtime().tm_mon

    if month <= 6:
        sem = t("spring")
    else:
        sem = t("autumn")

    return f"{sem} {year}"


def get_tournament_title(settings):
    custom = settings.custom_title.strip()
    if custom:
        return custom

    return t("app_title").format(semester=find_time())

def build_timers(timer_frame, settings, screen_height):
    timers = []
    timer_count = settings.get_timer_count()

    if timer_count <= 2:
        count_scale = 1.0
    elif timer_count == 3:
        count_scale = 0.82
    elif timer_count == 4:
        count_scale = 0.70
    else:
        count_scale = 0.58

    resolution_scale = screen_height / 1080
    resolution_scale = max(0.90, min(1.50, resolution_scale))

    scale = count_scale * resolution_scale

    for i in range(timer_count):
        label = (
            t("table_label").format(index=i + 1)
            if timer_count > 1
            else t("countdown_timer")
        )

        timer = Timer(
            master=timer_frame,
            initial_time=settings.default_timer_seconds,
            timer_label=label,
            show_controls=False,
            settings=settings,
            scale=scale,
            timer_index=i + 1 if timer_count > 1 else None,
            use_table_label=(timer_count > 1),
        )
        timers.append(timer)

    return timers

def refresh_language_ui():
    app_state.title = get_tournament_title(settings)
    root.title(app_state.title)

    brackets_label.configure(text=app_state.title)
    timer_label.configure(text=t("countdown_timer"))

    for timer in timers:
        timer.refresh_texts()

    bracket_frame.refresh_language()

    control_window.refresh_texts()

ctk.set_appearance_mode('dark')
#ctk.set_default_color_theme('green')

settings = AppSettings()

set_language(settings.language)

app_state = TournamentState(settings=settings)
app_state.title = get_tournament_title(settings)

# root window
monitor = get_monitor_by_index(settings.fullscreen_monitor_index)

root = ctk.CTk()
root.title(app_state.title)

apply_root_window_mode()

#configure grid
root.columnconfigure(0, weight=0)
root.columnconfigure(1, weight=1)
root.rowconfigure(0, weight=1)

# left frame timer
timer_frame = ctk.CTkFrame(master=root)
timer_frame.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)

# right frame brackets
main_frame = ctk.CTkFrame(master=root)
main_frame.grid(row=0, column=1, sticky='nsew', padx=10, pady=10)



# brackets

title_font_size = get_title_font_size(monitor.work_height)

brackets_label = ctk.CTkLabel(
    master=main_frame,
    text=app_state.title,
    font=("Helvetica", title_font_size)
)
pad_y = int(12 * (monitor.work_height / 1080))
pad_x = int(10 * (monitor.work_height / 1080))

brackets_label.pack(pady=pad_y, padx=pad_x)

app_state.bracket_model = TournamentModel(settings=settings)
tournament_model = app_state.bracket_model

bracket_frame = TournamentBracketCanvas(
    master=main_frame,
    tournament_model=tournament_model,
    settings=settings,
)

image_path = resource_path("graphics/menageriet_logo.png")
image_light = Image.open(image_path)
logo_size = max(80, min(180, int(120 * (monitor.work_height / 1080))))
main_logo = ctk.CTkImage(light_image=image_light, dark_image=image_light, size=(logo_size, logo_size))

main_logo_label = ctk.CTkLabel(master=main_frame, image=main_logo, text="")
main_logo_label.image = main_logo
logo_margin = max(12, int(20 * (monitor.work_height / 1080)))
main_logo_label.place(relx=1.0, rely=1.0, anchor="se", x=-logo_margin, y=-logo_margin)

# Timers
timer_title_font_size = get_title_font_size(monitor.work_height)

timer_label = ctk.CTkLabel(
    master=timer_frame,
    text=t("countdown_timer"),
    font=("Helvetica", timer_title_font_size)
)
timer_label.pack(pady=pad_y, padx=pad_x)

timers = build_timers(timer_frame, settings, monitor.work_height)

root.bind("<Configure>", on_resize)
root.update_idletasks()
on_resize(type("Event", (), {"widget": root})())

control_window = ControlWindow(
    master=main_frame,
    tournament_state=app_state,
    bracket_canvas=bracket_frame,
    timers=timers,
    settings=settings,
    toggle_fullscreen_callback=toggle_root_fullscreen,
    language_changed_callback=refresh_language_ui,
)

control_monitor = get_secondary_monitor(settings.fullscreen_monitor_index)

control_window.update_idletasks()
apply_control_window_on_monitor(control_window, control_monitor)

root.mainloop()