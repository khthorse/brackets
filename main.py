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
from translations import t


def find_time():
    year = str(time.localtime().tm_year)
    month = time.localtime().tm_mon

    if month <= 6:
        sem = t("spring")
    else:
        sem = t("autumn")

    return f"{sem} {year}"


ctk.set_appearance_mode('dark')
#ctk.set_default_color_theme('green')



#root window
root = ctk.CTk()
root.title(t("app_title").format(semester=find_time()))
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
    text=t("app_title").format(semester=find_time()),
    font=("Arial", 40)
)
brackets_label.pack(pady=12, padx=10)

tournament_model = TournamentModel()

bracket_frame = TournamentBracketCanvas(master=main_frame, tournament_model=tournament_model)

# Timer 1
timer_label = ctk.CTkLabel(master=timer_frame, text=t("countdown_timer"), font=("Arial", 40))
timer_label.pack(pady=12, padx=10)

timer1 = Timer(
    master=timer_frame,
    initial_time=60 * 15,
    timer_label=t("table_label").format(index=1),
    show_controls=False
)

timer2 = Timer(
    master=timer_frame,
    initial_time=60 * 15,
    timer_label=t("table_label").format(index=2),
    show_controls=False
)


control_window = ControlWindow(
    master=main_frame,
    tournament_model=tournament_model,
    bracket_canvas=bracket_frame,
    timers=[timer1, timer2]
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