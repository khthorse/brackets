import time
import math
import threading

import customtkinter as ctk

from tkinter import TclError

from paths import resource_path
from time_utils import normalize_time_input, is_valid_mmss, mmss_to_seconds
from translations import t
from ui_theme import get_dark_theme

try:
    import winsound
except ImportError:
    winsound = None

class Timer:
    def __init__(
        self,
        master,
        initial_time,
        show_controls=True,
        settings=None,
        scale=1.0,
        timer_index=None,
        use_table_label=False,
    ):  
        self.ui = get_dark_theme()
        self.timer_index = timer_index
        self.use_table_label = use_table_label
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

        metrics = self._calc_timer_metrics()

        outer_pad_y = metrics["outer_pad_y"]
        outer_pad_x = metrics["outer_pad_x"]

        self.frame = ctk.CTkFrame(master, fg_color=self.ui.timer_bg)
        self.frame.pack(pady=outer_pad_y, padx=outer_pad_x)

        title_font_size = metrics["title_font_size"]
        title_pad_y = metrics["title_pad_y"]
        title_pad_x = metrics["title_pad_x"]

        self._timer_label = ctk.CTkLabel(
            self.frame,
            text=self.get_timer_title_text(),
            font=(self.ui.font_timer, title_font_size),
            text_color=self.ui.timer_text,
        )
        self._timer_label.pack(pady=title_pad_y, padx=title_pad_x)

        self.canvas_size = metrics["canvas_size"]
        pad = metrics["arc_pad"]

        self.canvas = ctk.CTkCanvas(
            self.frame,
            width=self.canvas_size,
            height=self.canvas_size,
            bg=self.ui.timer_bg,
            highlightthickness=0,
        )
        canvas_pad_y = metrics["canvas_pad_y"]
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
            outline=self.ui.timer_arc_idle,
        )
 
        time_font_size = metrics["time_font_size"]

        self.canvas_text = self.canvas.create_text(
            self.canvas_size / 2,
            self.canvas_size / 2,
            text="",
            font=(self.ui.font_timer, time_font_size),
            fill=self.ui.timer_text,
        )

        if self.show_controls:
            button_frame_pad_y = metrics["button_frame_pad_y"]
            button_frame_pad_x = metrics["button_frame_pad_x"]

            self.buttonframe = ctk.CTkFrame(self.frame, fg_color="transparent")
            self.buttonframe.pack(pady=button_frame_pad_y, padx=button_frame_pad_x)



            button_font_size = metrics["button_font_size"]
            button_width = metrics["button_width"]
            button_height = metrics["button_height"]
            button_pad_x = metrics["button_pad_x"]
            button_pad_y = metrics["button_pad_y"]

            self.start_button = ctk.CTkButton(
                self.buttonframe,
                text=t("start"),
                command=self.countdown,
                width=button_width,
                height=button_height,
                fg_color=self.ui.button_fg,
                hover_color=self.ui.button_hover,
                font=(self.ui.font_timer, button_font_size),
                text_color=self.ui.button_text,
            )
            self.start_button.grid(row=0, column=0, padx=button_pad_x, pady=button_pad_y)

            self.pause_button = ctk.CTkButton(
                self.buttonframe,
                text=t("pause"),
                command=self.toggle_pause,
                width=button_width,
                height=button_height,
                fg_color=self.ui.button_fg,
                hover_color=self.ui.button_hover,
                font=(self.ui.font_timer, button_font_size),
                text_color=self.ui.button_text,
            )
            self.pause_button.grid(row=0, column=1, padx=button_pad_x, pady=button_pad_y)

            self.reset_button = ctk.CTkButton(
                self.buttonframe,
                text=t("reset"),
                command=self.reset_timer,
                width=button_width,
                height=button_height,
                fg_color=self.ui.button_fg,
                hover_color=self.ui.button_hover,
                font=(self.ui.font_timer, button_font_size),
                text_color=self.ui.button_text,
            )
            self.reset_button.grid(row=1, column=0, padx=button_pad_x, pady=button_pad_y)

            self.change_time_button = ctk.CTkButton(
                self.buttonframe,
                text=t("change_time"),
                command=self.open_change_time_popup,
                width=button_width,
                height=button_height,
                fg_color=self.ui.button_fg,
                hover_color=self.ui.button_hover,
                font=(self.ui.font_timer, button_font_size),
                text_color=self.ui.button_text,
            )
            self.change_time_button.grid(row=1, column=1, padx=button_pad_x, pady=button_pad_y)

        self.update_label()

    def _calc_timer_metrics(self):
        ui = self.ui
        s = self.scale

        return {
            "outer_pad_y": max(ui.timer_min_outer_pad, int(20 * s)),
            "outer_pad_x": max(ui.timer_min_outer_pad, int(20 * s)),
            "title_font_size": max(ui.timer_min_title_font, int(50 * s)),
            "title_pad_y": max(4, int(10 * s)),
            "title_pad_x": max(2, int(5 * s)),
            "canvas_size": max(ui.timer_min_canvas_size, int(250 * s)),
            "arc_pad": max(ui.timer_min_arc_pad, int(10 * s)),
            "arc_width": max(ui.timer_min_arc_width, int(15 * s)),
            "canvas_pad_y": max(2, int(5 * s)),
            "time_font_size": max(ui.timer_min_time_font, int(40 * s)),
            "button_font_size": max(ui.timer_min_button_font, int(13 * s)),
            "button_width": max(ui.timer_min_button_width, int(140 * s)),
            "button_height": max(ui.timer_min_button_height, int(36 * s)),
            "button_pad_x": max(ui.timer_min_button_pad_x, int(10 * s)),
            "button_pad_y": max(ui.timer_min_button_pad_y, int(5 * s)),
            "button_frame_pad_y": max(4, int(10 * s)),
            "button_frame_pad_x": max(4, int(10 * s)),
        }

    def set_scale(self, new_scale: float):
        self.scale = new_scale
        metrics = self._calc_timer_metrics()
        self.base_arc_width = metrics["arc_width"]

        # oppdater canvas størrelse
        self.canvas_size = metrics["canvas_size"]
        self.canvas.configure(width=self.canvas_size, height=self.canvas_size)

        pad = metrics["arc_pad"]

        self.canvas.coords(
            self.arc,
            pad,
            pad,
            self.canvas_size - pad,
            self.canvas_size - pad,
        )

        self.canvas.coords(
            self.canvas_text,
            self.canvas_size / 2,
            self.canvas_size / 2,
        )

        # oppdater fonter
        title_font_size = metrics["title_font_size"]
        time_font_size = metrics["time_font_size"]

        self._timer_label.configure(font=(self.ui.font_timer, title_font_size))
        self.canvas.itemconfig(self.canvas_text, font=(self.ui.font_timer, time_font_size))

        self.update_label()

    def add_observer(self, callback):
        self._observers.append(callback)
    
    def get_timer_title_text(self) -> str:
        if self.use_table_label and self.timer_index is not None:
            return t("table_label").format(index=self.timer_index)
        return t("countdown_timer")

    def refresh_texts(self):
        if hasattr(self, "_timer_label") and self._timer_label.winfo_exists():
            self._timer_label.configure(text=self.get_timer_title_text())

        if hasattr(self, "start_button"):
            self.start_button.configure(text=t("start"))

        if hasattr(self, "pause_button"):
            if self.paused:
                self.pause_button.configure(text=t("resume"))
            else:
                self.pause_button.configure(text=t("pause"))

        if hasattr(self, "reset_button"):
            self.reset_button.configure(text=t("reset"))

        if hasattr(self, "change_time_button"):
            self.change_time_button.configure(text=t("change_time"))

        self._notify_observers()

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
                self.canvas.itemconfig(self.arc, extent=0, outline=self.ui.timer_arc_idle, width=self.base_arc_width)
            else:
                self.canvas.itemconfig(self.arc, extent=ext, outline=color, width=arc_width)
        else:
            if progress == 0:
                self.canvas.itemconfig(self.arc, extent=0, outline=self.ui.timer_arc_idle, width=self.base_arc_width)
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
            self.canvas.itemconfig(self.canvas_text, text=t("finished"), fill=self.ui.timer_text_dim)
            self.canvas.itemconfig(self.arc, outline=self.ui.timer_arc_idle, width=self.base_arc_width)

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

        self.canvas.itemconfig(self.canvas_text, fill=self.ui.timer_text)
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

        ok_color = self.ui.timer_arc_ok
        warning_color = self.ui.timer_arc_warning
        danger_color = self.ui.timer_arc_danger

        if fraction_left > 0.35:
            return ok_color

        if 0.25 < fraction_left <= 0.35:
            t = (0.35 - fraction_left) / 0.10
            return self._lerp_color(ok_color, warning_color, t)

        if 0.10 < fraction_left <= 0.25:
            return warning_color

        t = (0.10 - fraction_left) / 0.10 if fraction_left >= 0 else 1.0
        return self._lerp_color(warning_color, danger_color, t)

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

        return 0.5 + 0.5 * math.sin(self._pulse_phase)


if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    root = ctk.CTk()
    root.title(t("countdown_timer"))
    timer = Timer(master=root, initial_time=20)
    root.mainloop()