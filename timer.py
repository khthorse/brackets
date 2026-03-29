import time
import threading

import customtkinter as ctk

from tkinter import TclError

from paths import resource_path
from time_utils import normalize_time_input, is_valid_mmss, mmss_to_seconds
from translations import t

try:
    import winsound
except ImportError:
    winsound = None

class Timer:
    def __init__(self, master, initial_time, timer_label, show_controls=True, settings=None, scale=1.0):
        self.master = master
        self.settings = settings
        self.scale = scale
        self.base_arc_width = max(6, int(15 * self.scale))
        self.initial_time = initial_time
        self.current_time = initial_time
        self.muted = settings.default_muted if settings is not None else False
        self.paused = False
        self.timer_id = None
        self.show_controls = show_controls

        self._pulse_phase = 0.0
        self._blink_on = True
        self._blink_job = None

        self._observers = []
        self._start_timestamp = None
        self._remaining_before_start = float(initial_time)

        outer_pad_y = max(6, int(20 * self.scale))
        outer_pad_x = max(6, int(20 * self.scale))

        self.frame = ctk.CTkFrame(master)
        self.frame.pack(pady=outer_pad_y, padx=outer_pad_x)

        title_font_size = max(18, int(50 * self.scale))
        title_pad_y = max(4, int(10 * self.scale))
        title_pad_x = max(2, int(5 * self.scale))

        self._timer_label = ctk.CTkLabel(self.frame, text=timer_label, font=("Helvetica", title_font_size))
        self._timer_label.pack(pady=title_pad_y, padx=title_pad_x)

        self.canvas_size = max(120, int(250 * self.scale))
        pad = max(4, int(10 * self.scale))

        bg_color = "#2b2b2b"
        self.canvas = ctk.CTkCanvas(
            self.frame,
            width=self.canvas_size,
            height=self.canvas_size,
            bg=bg_color,
            highlightthickness=0,
        )
        canvas_pad_y = max(2, int(5 * self.scale))
        self.canvas.pack(pady=canvas_pad_y)

        self.arc = self.canvas.create_arc(
            pad,
            pad,
            self.canvas_size - pad,
            self.canvas_size - pad,
            start=90,
            extent=0,
            style="arc",
            width=self.base_arc_width,
            outline="#4682B4",
        )
 
        time_font_size = max(18, int(40 * self.scale))

        self.canvas_text = self.canvas.create_text(
            self.canvas_size / 2,
            self.canvas_size / 2,
            text="",
            font=("Helvetica", time_font_size),
            fill="white",
        )

        if self.show_controls:
            button_frame_pad_y = max(4, int(10 * self.scale))
            button_frame_pad_x = max(4, int(10 * self.scale))

            self.buttonframe = ctk.CTkFrame(self.frame)
            self.buttonframe.pack(pady=button_frame_pad_y, padx=button_frame_pad_x)

            button_font_size = max(11, int(13 * self.scale))
            button_width = max(70, int(140 * self.scale))
            button_height = max(28, int(36 * self.scale))
            button_pad_x = max(3, int(10 * self.scale))
            button_pad_y = max(3, int(5 * self.scale))

            self.start_button = ctk.CTkButton(
                self.buttonframe,
                text=t("start"),
                command=self.countdown,
                width=button_width,
                height=button_height,
                font=("Helvetica", button_font_size),
            )
            self.start_button.grid(row=0, column=0, padx=button_pad_x, pady=button_pad_y)

            self.pause_button = ctk.CTkButton(
                self.buttonframe,
                text=t("pause"),
                command=self.toggle_pause,
                width=button_width,
                height=button_height,
                font=("Helvetica", button_font_size),
            )
            self.pause_button.grid(row=0, column=1, padx=button_pad_x, pady=button_pad_y)

            self.reset_button = ctk.CTkButton(
                self.buttonframe,
                text=t("reset"),
                command=self.reset_timer,
                width=button_width,
                height=button_height,
                font=("Helvetica", button_font_size),
            )
            self.reset_button.grid(row=1, column=0, padx=button_pad_x, pady=button_pad_y)

            self.change_time_button = ctk.CTkButton(
                self.buttonframe,
                text=t("change_time"),
                command=self.open_change_time_popup,
                width=button_width,
                height=button_height,
                font=("Helvetica", button_font_size),
            )
            self.change_time_button.grid(row=1, column=1, padx=button_pad_x, pady=button_pad_y)

        self.update_label()

    def add_observer(self, callback):
        self._observers.append(callback)

    def _notify_observers(self):
        alive_callbacks = []

        for callback in self._observers:
            try:
                callback()
                alive_callbacks.append(callback)
            except TclError:
                pass

        self._observers = alive_callbacks

    def toggle_mute(self):
        self.muted = not self.muted
        self._notify_observers()

    def get_mute_text(self):
        return t("mute_on") if self.muted else t("mute_off")

    def _play_alarm(self):
        if self.settings is not None and not self.settings.alarm_enabled:
            return

        if self.muted:
            return
            
        if winsound is None:
            return

        try:
            sound_path = resource_path("sounds/bottle_alarm.wav")
            winsound.PlaySound(sound_path, winsound.SND_FILENAME)
        except Exception as e:
            print("Could not play sound:", e)


    def _play_alarm_async(self):
        threading.Thread(target=self._play_alarm, daemon=True).start()

    def update_label(self):
        """Oppdaterer tekst og progress-bue basert på gjenværende tid."""
        remaining = max(self.current_time, 0)
        total_seconds = int(remaining)
        minutes, seconds = divmod(total_seconds, 60)
        time_str = f"{minutes:02d}:{seconds:02d}"

        if self.initial_time > 0:
            progress = (self.initial_time - remaining) / self.initial_time
        else:
            progress = 0.0

        progress = max(0.0, min(1.0, progress))
        ext = -progress * 360

        color = self.get_time_color()

        pulse = self._pulse_factor() if (self.settings is None or self.settings.pulse_enabled) else 0.0
        pulse_extra = max(1, int(3 * self.scale))
        arc_width = self.base_arc_width + pulse * pulse_extra

        # Ikke tegn bue før den er stor nok til å se pen ut
        if self.initial_time > 30:
            if abs(ext) < 0.3:
                self.canvas.itemconfig(self.arc, extent=0, outline="#2b2b2b", width=self.base_arc_width)
            else:
                self.canvas.itemconfig(self.arc, extent=ext, outline=color, width=arc_width)
        else:
            if progress == 0:
                self.canvas.itemconfig(self.arc, extent=0, outline="#2b2b2b", width=self.base_arc_width)
            elif abs(ext) < 8:
                self.canvas.itemconfig(self.arc, extent=-8, outline=color, width=arc_width)
            else:
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

        self.canvas.itemconfig(self.canvas_text, text=t("finished"), fill=color)
        self.canvas.itemconfig(self.arc, extent=-359.999, outline=color, width=self.base_arc_width)

        self._play_alarm_async()

        if self.settings is None or self.settings.blink_enabled:
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
                self.pause_button.configure(text=t("resume"))
        else:
            self.paused = False
            if hasattr(self, "pause_button"):
                self.pause_button.configure(text=t("pause"))
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
            self.canvas.itemconfig(self.canvas_text, text=t("finished"), fill=color)
            self.canvas.itemconfig(self.arc, outline=color, width=self.base_arc_width)
        else:
            self.canvas.itemconfig(self.canvas_text, text=t("finished"), fill="#2b2b2b")
            self.canvas.itemconfig(self.arc, outline="#2b2b2b", width=self.base_arc_width)

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
        popup = ctk.CTkInputDialog(
            title=t("change_time_title"),
            text=t("enter_new_time_mmss")
        )
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
            self.pause_button.configure(text=t("pause"))

        self.canvas.itemconfig(self.canvas_text, fill="white")
        self.update_label()

    def set_time_from_input(self, value: str):
        normalized = normalize_time_input(value)
        if not is_valid_mmss(normalized):
            raise ValueError(t("invalid_mmss_time"))
        self.set_time_seconds(mmss_to_seconds(normalized))

    def get_display_time(self) -> str:
        remaining = max(self.current_time, 0)
        total_seconds = int(remaining)
        minutes, seconds = divmod(total_seconds, 60)
        return f"{minutes:02d}:{seconds:02d}"

    def get_status_text(self) -> str:
        if self.current_time < 0:
            return t("finished")
        if self.paused:
            return t("pause")
        if self.timer_id is not None:
            return t("running")
        return t("ready")

    def get_primary_button_text(self) -> str:
        if self.current_time < 0:
            return t("start")
        if self.paused:
            return t("resume")
        if self.timer_id is not None:
            return t("pause")
        return t("start")

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
    root.title(t("countdown_timer"))
    timer = Timer(master=root, initial_time=20, timer_label=t("countdown_timer"))
    root.mainloop()