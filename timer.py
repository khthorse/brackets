import customtkinter as ctk

from time_utils import normalize_time_input, is_valid_hhmm, hhmm_to_seconds

class Timer:
    def __init__(self, master, initial_time, timer_label, show_controls=True):
        self.master = master
        self.initial_time = initial_time  # Starttid i sekunder
        self.current_time = initial_time
        self.paused = False
        self.timer_id = None  # For å holde styr på etter-kall
        self.show_controls = show_controls

        # Opprett en ramme for hver timer
        self.frame = ctk.CTkFrame(master)
        self.frame.pack(pady=20, padx=20)
        
        # Timer label
        self._timer_label = ctk.CTkLabel(self.frame, text=timer_label, font=('Helvetica', 50))
        self._timer_label.pack(pady=10, padx=5)
        
        # Opprett en Canvas for sirkulær progress bar
        self.canvas_size = 250
        pad = 10

        bg_color = "#2b2b2b"
        self.canvas = ctk.CTkCanvas(self.frame, width=self.canvas_size, height=self.canvas_size,
                                bg=bg_color, highlightthickness=0)
        self.canvas.pack(pady=5)
        # Tegn en bue (arc) som viser progresjonen
        self.arc = self.canvas.create_arc(pad, pad, self.canvas_size - pad, self.canvas_size - pad,
                                          start=90, extent=0, style="arc", width=15, outline="#4682B4")
        # Tekst i midten av progress baren som viser nedtellingsformatet
        self.canvas_text = self.canvas.create_text(self.canvas_size/2, self.canvas_size/2,
                                                    text="", font=("Helvetica", 40), fill="white")
        if self.show_controls:
            # Frame for buttons
            self.buttonframe = ctk.CTkFrame(self.frame)
            self.buttonframe.pack(pady=10, padx=10)
            # Start-knapp
            self.start_button = ctk.CTkButton(self.buttonframe, text="Start", command=self.countdown)
            self.start_button.grid(row=0, column=0, padx=10, pady=5)

            # Pause/Resume-knapp
            self.pause_button = ctk.CTkButton(self.buttonframe, text="Pause", command=self.toggle_pause)
            self.pause_button.grid(row=0, column=1, padx=10, pady=5)

            # Reset-knapp
            self.reset_button = ctk.CTkButton(self.buttonframe, text="Reset", command=self.reset_timer)
            self.reset_button.grid(row=1, column=0, padx=10, pady=5)
            
            # Change time button
            self.change_time_button = ctk.CTkButton(self.buttonframe, text="Change Time", command=self.open_change_time_popup)
            self.change_time_button.grid(row=1, column=1, padx=10, pady=5)

        self.update_label()

    def update_label(self):
        """Oppdaterer teksten i progress baren og buens extent basert på gjenværende tid."""
        minutes, seconds = divmod(self.current_time, 60)
        time_str = f"{minutes:02d}:{seconds:02d}"
        self.canvas.itemconfig(self.canvas_text, text=time_str)
        # Kalkuler progresjon: 0 ved start, 1 når tiden er ute
        if self.initial_time > 0:
            progress = (self.initial_time - self.current_time) / self.initial_time
        else:
            progress = 0
        # Oppdater buens extent (negativ for med klokka)
        ext = -progress * 360
        self.canvas.itemconfig(self.arc, extent=ext, outline='#4682B4')
        if progress > 8/10:
            self.canvas.itemconfig(self.arc, outline='#C00020')
        elif progress > 3/4:
            self.canvas.itemconfig(self.arc, outline='#C0A000')
        

    def countdown(self):
        """Kjører nedtellingen og planlegger oppdateringer hvert sekund."""
        if hasattr(self, "start_button"):
            self.start_button.configure(state=ctk.DISABLED)

        if self.current_time >= 0 and not self.paused:
            self.update_label() 
            self.current_time -= 1
            self.timer_id = self.master.after(1000, self.countdown)

        if self.current_time < 0:
            self.timer_id = None
            self.canvas.itemconfig(self.canvas_text, text="Ferdig!", fill="#B46246")
            self.canvas.itemconfig(self.arc, extent=-359.999)

    def toggle_pause(self):
        """Bytter mellom pause og fortsett."""
        if not self.paused:
            self.paused = True
            if self.timer_id:
                self.master.after_cancel(self.timer_id)
                self.timer_id = None
            if hasattr(self, "pause_button"):
                self.pause_button.configure(text="Resume")
        else:
            self.paused = False
            if hasattr(self, "pause_button"):
                self.pause_button.configure(text="Pause")
            self.countdown()

    def reset_timer(self):
        """Resetter timeren til startverdien."""
        if hasattr(self, "start_button"):
            self.start_button.configure(state=ctk.NORMAL)

        if self.timer_id:
            self.master.after_cancel(self.timer_id)
            self.timer_id = None

        self.current_time = self.initial_time
        self.paused = False

        if hasattr(self, "pause_button"):
            self.pause_button.configure(text="Pause")

        self.canvas.itemconfig(self.canvas_text, fill="white")
        self.update_label()
        
    def open_change_time_popup(self):
        popup = ctk.CTkInputDialog(title="Change Time", text="enter new time:  mm:ss")
        new_time = popup.get_input()

        if new_time is None:
            return

        new_time = new_time.strip()
        if not new_time:
            return

        try:
            self.set_time_from_input(new_time)
        except ValueError:
            self.open_change_time_popup()
            
    def set_time_seconds(self, seconds: int):
        if hasattr(self, "start_button"):
            self.start_button.configure(state=ctk.NORMAL)

        if self.timer_id:
            self.master.after_cancel(self.timer_id)
            self.timer_id = None

        self.current_time = seconds
        self.initial_time = seconds
        self.paused = False

        if hasattr(self, "pause_button"):
            self.pause_button.configure(text="Pause")

        self.canvas.itemconfig(self.canvas_text, fill="white")
        self.update_label()


    def set_time_from_input(self, value: str):
        normalized = normalize_time_input(value)
        if not is_valid_hhmm(normalized):
            raise ValueError("Ugyldig tid. Bruk MM:SS.")
        self.set_time_seconds(hhmm_to_seconds(normalized))

    def get_display_time(self) -> str:
        minutes, seconds = divmod(max(self.current_time, 0), 60)
        return f"{minutes:02d}:{seconds:02d}"


    def get_status_text(self) -> str:
        if self.current_time < 0:
            return "Ferdig"
        if self.paused:
            return "Pause"
        if self.timer_id is not None:
            return "Kjører"
        return "Klar"
    
    def primary_action(self):
        if self.current_time < 0:
            self.reset_timer()
            self.countdown()
        elif self.paused:
            self.toggle_pause()
        elif self.timer_id is not None:
            self.toggle_pause()
        else:
            self.countdown()


    def get_primary_button_text(self) -> str:
        if self.current_time < 0:
            return "Start"
        if self.paused:
            return "Resume"
        if self.timer_id is not None:
            return "Pause"
        return "Start"
    
if __name__ == "__main__":
    ctk.set_appearance_mode('dark')
    root = ctk.CTk()
    root.title('Timer')
    timer = Timer(master=root, initial_time=20, timer_label='Timer')
    root.mainloop()