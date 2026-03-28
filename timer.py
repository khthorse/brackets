import time
import customtkinter as ctk

from time_utils import normalize_time_input, is_valid_hhmm, hhmm_to_seconds


class Timer:
    def __init__(self, master, initial_time, timer_label, show_controls=True):
        self.master = master
        self.initial_time = initial_time
        self.current_time = initial_time
        self.paused = False
        self.timer_id = None
        self.show_controls = show_controls

        self._pulse_phase = 0.0
        self._blink_on = True
        self._blink_job = None

        self._observers = []
        self._start_timestamp = None
        self._remaining_before_start = float(initial_time)

        self.frame = ctk.CTkFrame(master)
        self.frame.pack(pady=20, padx=20)

        self._timer_label = ctk.CTkLabel(self.frame, text=timer_label, font=("Helvetica", 50))
        self._timer_label.pack(pady=10, padx=5)

        self.canvas_size = 250
        pad = 10

        bg_color = "#2b2b2b"
        self.canvas = ctk.CTkCanvas(
            self.frame,
            width=self.canvas_size,
            height=self.canvas_size,
            bg=bg_color,
            highlightthickness=0,
        )
        self.canvas.pack(pady=5)

        self.arc = self.canvas.create_arc(
            pad,
            pad,
            self.canvas_size - pad,
            self.canvas_size - pad,
            start=90,
            extent=0,
            style="arc",
            width=15,
            outline="#4682B4",
        )
 
        self.canvas_text = self.canvas.create_text(
            self.canvas_size / 2,
            self.canvas_size / 2,
            text="",
            font=("Helvetica", 40),
            fill="white",
        )

        if self.show_controls:
            self.buttonframe = ctk.CTkFrame(self.frame)
            self.buttonframe.pack(pady=10, padx=10)

            self.start_button = ctk.CTkButton(self.buttonframe, text="Start", command=self.countdown)
            self.start_button.grid(row=0, column=0, padx=10, pady=5)

            self.pause_button = ctk.CTkButton(self.buttonframe, text="Pause", command=self.toggle_pause)
            self.pause_button.grid(row=0, column=1, padx=10, pady=5)

            self.reset_button = ctk.CTkButton(self.buttonframe, text="Reset", command=self.reset_timer)
            self.reset_button.grid(row=1, column=0, padx=10, pady=5)

            self.change_time_button = ctk.CTkButton(
                self.buttonframe,
                text="Change Time",
                command=self.open_change_time_popup,
            )
            self.change_time_button.grid(row=1, column=1, padx=10, pady=5)

        self.update_label()

    def add_observer(self, callback):
        self._observers.append(callback)

    def _notify_observers(self):
        for callback in self._observers:
            callback()  

    def update_label(self):
        """Oppdaterer tekst og progress-bue basert på gjenværende tid."""
        remaining = max(self.current_time, 0)
        total_seconds = int(remaining)
        minutes, seconds = divmod(total_seconds, 60)
        time_str = f"{minutes:02d}:{seconds:02d}"

        if self.initial_time > 0:
            progress = (self.initial_time - remaining) / self.initial_time
        else:
            progress = 0

        ext = -progress * 360

        color = self.get_time_color()


        pulse = self._pulse_factor()
        arc_width = 15 + pulse * 3

        self.canvas.itemconfig(self.arc, extent=ext, outline=color, width=arc_width)
        self.canvas.itemconfig(self.canvas_text, text=time_str, fill=color)


        self._notify_observers()

    def countdown(self):
        """Starter nedtellingen med jevne, glatte oppdateringer."""
        if self.paused:
            return

        if self.timer_id is not None:
            return

        if self.current_time < 0:
            self.reset_timer()

        if hasattr(self, "start_button"):
            self.start_button.configure(state=ctk.DISABLED)

        self._stop_finished_blink()

        self._start_timestamp = time.time()
        self._remaining_before_start = float(self.current_time)
        self._pulse_phase = 0.0

        self.current_time = self._remaining_before_start
        self.update_label()
        self.timer_id = self.master.after(50, self._tick)

    def _tick(self):
        if self.paused:
            self.timer_id = None
            return

        elapsed = time.time() - self._start_timestamp
        self.current_time = self._remaining_before_start - elapsed
        self._pulse_phase += 0.35

        if self.current_time > 0:
            self.update_label()
            self.timer_id = self.master.after(50, self._tick)
        else:
            self.current_time = -1
            self._finish_timer()

    def _finish_timer(self):
        self.timer_id = None
        self.current_time = -1
        self._pulse_phase = 0.0

        color = self.get_time_color()

        self.canvas.itemconfig(self.canvas_text, text="Ferdig!", fill=color)
        self.canvas.itemconfig(self.arc, extent=-359.999, outline=color, width=15)

        self._start_finished_blink()

        self._notify_observers()

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

        self._notify_observers()

    
    def _start_finished_blink(self):
        if self._blink_job is not None:
            return
        self._blink_on = True
        self._blink_once()


    def _blink_once(self):
        color = self.get_time_color()

        if self._blink_on:
            self.canvas.itemconfig(self.canvas_text, text="Ferdig!", fill=color)
            self.canvas.itemconfig(self.arc, outline=color, width=15)
        else:
            self.canvas.itemconfig(self.canvas_text, text="Ferdig!", fill="#2b2b2b")
            self.canvas.itemconfig(self.arc, outline="#2b2b2b", width=15)

        self._blink_on = not self._blink_on
        self._notify_observers()
        self._blink_job = self.master.after(400, self._blink_once)

    def reset_timer(self):
        """Resetter timeren til startverdien."""
        self.set_time_seconds(self.initial_time)

    def _stop_finished_blink(self):
        if self._blink_job is not None:
            self.master.after_cancel(self._blink_job)
            self._blink_job = None

        self._blink_on = True

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
        self._stop_finished_blink()

        if hasattr(self, "start_button"):
            self.start_button.configure(state=ctk.NORMAL)

        if self.timer_id:
            self.master.after_cancel(self.timer_id)
            self.timer_id = None

        self.current_time = float(seconds)
        self.initial_time = float(seconds)
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
        remaining = max(self.current_time, 0)
        total_seconds = int(remaining)
        minutes, seconds = divmod(total_seconds, 60)
        return f"{minutes:02d}:{seconds:02d}"

    def get_status_text(self) -> str:
        if self.current_time < 0:
            return "Ferdig"
        if self.paused:
            return "Pause"
        if self.timer_id is not None:
            return "Kjører"
        return "Klar"

    def get_primary_button_text(self) -> str:
        if self.current_time < 0:
            return "Start"
        if self.paused:
            return "Resume"
        if self.timer_id is not None:
            return "Pause"
        return "Start"

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

    def get_time_color(self) -> str:
        if self.initial_time > 0:
            remaining = max(self.current_time, 0)
            fraction_left = remaining / self.initial_time
        else:
            fraction_left = 0.0

        blue   = "#6CA0DC"
        yellow = "#E6C229"
        red    = "#D1495B"  

        #white  = "#EAEAEA"
        #yellow = "#FFC857"
        #red    = "#FF5A5F"

        # Hold blå lenge
        if fraction_left > 0.35:
            return blue

        # Myk overgang blå -> gul
        if 0.25 < fraction_left <= 0.35:
            t = (0.35 - fraction_left) / 0.10
            return self._lerp_color(blue, yellow, t)

        # Hold gul en stund
        if 0.10 < fraction_left <= 0.25:
            return yellow

        # Myk overgang gul -> rød
        t = (0.10 - fraction_left) / 0.10 if fraction_left >= 0 else 1.0
        return self._lerp_color(yellow, red, t)

    def _lerp_color(self, start_hex: str, end_hex: str, t: float) -> str:
        t = max(0.0, min(1.0, t))

        s = start_hex.lstrip("#")
        e = end_hex.lstrip("#")

        sr, sg, sb = int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)
        er, eg, eb = int(e[0:2], 16), int(e[2:4], 16), int(e[4:6], 16)

        r = round(sr + (er - sr) * t)
        g = round(sg + (eg - sg) * t)
        b = round(sb + (eb - sb) * t)

        return f"#{r:02x}{g:02x}{b:02x}"
    
    def _pulse_factor(self) -> float:
        if self.initial_time <= 0:
            return 0.0

        remaining = max(self.current_time, 0)
        fraction_left = remaining / self.initial_time

        if fraction_left > 0.10:
            return 0.0

        import math
        return 0.5 + 0.5 * math.sin(self._pulse_phase)


if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    root = ctk.CTk()
    root.title("Timer")
    timer = Timer(master=root, initial_time=20, timer_label="Timer")
    root.mainloop()