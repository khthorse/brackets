import customtkinter as ctk
from timer import Timer
from paths import resource_path
from PIL import Image, ImageTk
import time
import sys
import os

from models import TournamentModel
from bracket_canvas import TournamentBracketCanvas
from control_window import ControlWindow
from translations import t, set_language
from settings import AppSettings


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

def build_timers(timer_frame, settings):
    timers = []
    timer_count = settings.get_timer_count()

    if timer_count <= 2:
        scale = 1.0
    elif timer_count == 3:
        scale = 0.82
    elif timer_count == 4:
        scale = 0.70
    else:
        scale = 0.58

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
        )
        timers.append(timer)

    return timers


ctk.set_appearance_mode('dark')
#ctk.set_default_color_theme('green')

settings = AppSettings()

settings.default_muted = True
settings.alarm_enabled = False
settings.pulse_enabled = False
settings.blink_enabled = False
settings.ask_for_logos = True
settings.shuffle_teams = False
settings.table_count = 3
settings.timer_mode = "per_table"
settings.language = "en"

set_language(settings.language)

#root window
root = ctk.CTk()
root.title(get_tournament_title(settings))
root.geometry('1920x1280')

#root.state('zoomed')

#configure grid
root.columnconfigure(0, weight=1)
root.columnconfigure(1, weight=100)
root.rowconfigure(0, weight=1)


# left frame timer
timer_frame = ctk.CTkFrame(master=root)
timer_frame.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)

# right frame brackets
main_frame = ctk.CTkFrame(master=root)
main_frame.grid(row=0, column=1, sticky='nsew', padx=10, pady=10)



# brackets

brackets_label = ctk.CTkLabel(
    master=main_frame,
    text=get_tournament_title(settings),
    font=("Arial", 40)
)
brackets_label.pack(pady=12, padx=10)

tournament_model = TournamentModel(settings=settings)

bracket_frame = TournamentBracketCanvas(
    master=main_frame,
    tournament_model=tournament_model,
    settings=settings,
)

# Timer 1
timer_label = ctk.CTkLabel(master=timer_frame, text=t("countdown_timer"), font=("Arial", 40))
timer_label.pack(pady=12, padx=10)

timers = build_timers(timer_frame, settings)


control_window = ControlWindow(
    master=main_frame,
    tournament_model=tournament_model,
    bracket_canvas=bracket_frame,
    timers=timers,
    settings=settings,
)

#fullscreen_button = ctk.CTkButton(master=timer_frame, text='Fullskjerm', command=fullscreen())
#fullscreen_button.pack(pady=12, padx=10)

# logo
image_path = resource_path('graphics/menageriet_logo.png')
image_light = Image.open(image_path)
#image_dark = Image.open('menageriet_logo_dark.png')
logo = ctk.CTkImage(light_image=image_light, dark_image=image_light, size=(200, 200))

logo_label = ctk.CTkLabel(master=timer_frame, image=logo, text='')
logo_label.pack(pady=12, padx=10, anchor='s')


root.mainloop()