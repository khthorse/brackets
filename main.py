import customtkinter as ctk
from timer import Timer
from PIL import Image, ImageTk
import time


from brackets import TournamentModel, TournamentBracketCanvas, ControlWindow

def find_time():
    year = str(time.localtime().tm_year)
    month = time.localtime().tm_mon
    
    if month <= 6:
        sem = 'Vår '
    else:
        sem = 'Høst '
        
    return sem + year


ctk.set_appearance_mode('dark')
#ctk.set_default_color_theme('green')


#root window
root = ctk.CTk()
root.title('Beerpong Turnering ' + find_time())
root.geometry('1920x1280')
#root.attributes('-fullscreen', True)
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

brackets_label = ctk.CTkLabel(master=main_frame, text='Beerpong Turnering '+ find_time(), font=('Arial', 40))
brackets_label.pack(pady=12, padx=10)

tournament_model = TournamentModel()

bracket_frame = TournamentBracketCanvas(master=main_frame, tournament_model=tournament_model)

control_window = ControlWindow(master=main_frame, tournament_model=tournament_model, bracket_canvas=bracket_frame)


# Timer 1
timer_label = ctk.CTkLabel(master=timer_frame, text='Countdown Timer', font=('Arial', 40))
timer_label.pack(pady=12, padx=10)

timer1 = Timer(master=timer_frame, initial_time=2, timer_label='Bord 1')

timer2 = Timer(master=timer_frame, initial_time=120, timer_label='Bord 2')


# logo
image_light = Image.open('menageriet_logo.png')
#image_dark = Image.open('menageriet_logo_dark.png')
logo = ctk.CTkImage(light_image=image_light, dark_image=image_light, size=(200, 200))

logo_label = ctk.CTkLabel(master=timer_frame, image=logo, text='')
logo_label.pack(pady=12, padx=10, anchor='s')


root.mainloop()