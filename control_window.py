import customtkinter as ctk
import tkinter.filedialog as fd
import tkinter as tk

from PIL import Image, ImageTk

from models import GroupStageModel, Team
from team_io import parse_team_file, teams_from_text
from time_utils import normalize_time_input, is_valid_hhmm

class ControlWindow(ctk.CTkToplevel):
    """
    Kontrollvinduet der du kan legge inn lag, sette vinnere, angi starttidspunkt
    og redigere kampoppsettet.
    """
    def __init__(self, master, tournament_model, bracket_canvas, timers=None, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.tournament_model = tournament_model
        self.bracket_canvas = bracket_canvas
        self.title("Kontrollvindu")
        self.geometry("1000x1200")
        self.timers = timers or []

        team_entry_label = ctk.CTkLabel(self, text="Skriv inn lag (én per linje):")
        team_entry_label.pack(pady=5)

        self.team_text = tk.Text(self, height=20, width=60)
        self.team_text.pack(pady=5)
        self.team_text.insert(
            "1.0",
            "Lag 1\nLag 2\nLag 3\nLag 4\nLag 5\nLag 6\nLag 7\nLag 8\n"
            "Lag 9\nLag 10\nLag 11\nLag 12\nLag 13\nLag 14\nLag 15\nLag 16"
        )

        set_teams_button = ctk.CTkButton(self, text="Bygg Brakett", command=self.build_bracket)
        set_teams_button.pack(pady=5)

        load_from_file_btn = ctk.CTkButton(self, text="Last lag fra fil...", command=self.load_teams_from_file)
        load_from_file_btn.pack(pady=5)

        self.logo_switch = False
        load_logo_checkbox = ctk.CTkCheckBox(self, text="Legg til laglogoer", command=self.toggle_load_logo)
        load_logo_checkbox.pack(pady=5)

        self.start_group_button = ctk.CTkButton(self, text="Start Gruppespill", command=self.start_group_stage)
        self.start_bracket_button = ctk.CTkButton(self, text="Start Sluttspill", command=self.build_final_bracket)
        self.start_group_button.pack(pady=5)

        self._build_timer_controls()

        self.match_controls_frame = ctk.CTkScrollableFrame(self)
        self.match_controls_frame.pack(fill="both", expand=True, pady=10)

        self.draw_match_controls()
        self.teams = []

    def _build_timer_controls(self):
        if not self.timers:
            return

        timer_section = ctk.CTkFrame(self)
        timer_section.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(timer_section, text="Timerkontroll", font=("Arial", 20)).pack(pady=6)

        for i, timer in enumerate(self.timers, start=1):
            row = ctk.CTkFrame(timer_section)
            row.pack(fill="x", padx=6, pady=4)

            ctk.CTkLabel(row, text=f"Bord {i}").pack(side="left", padx=8)

            time_frame = ctk.CTkFrame(
                    row,
                    fg_color="#1f1f1f",   # mørkere bakgrunn
                    corner_radius=8
                )
            time_frame.pack(side="left", padx=8, pady=2)

            time_label = ctk.CTkLabel(
                time_frame,
                text="00:00",
                font=("Consolas", 22)  # monospace + større
            )
            time_label.pack(padx=10, pady=4)

            status_label = ctk.CTkLabel(row, text="")
            status_label.pack(side="left", padx=8)

            primary_button = ctk.CTkButton(
                row,
                text=timer.get_primary_button_text(),
                command=lambda t=timer: t.primary_action()
            )
            primary_button.pack(side="right", padx=4)

            ctk.CTkButton(
                row,
                text="Reset",
                command=lambda t=timer: t.reset_timer()
            ).pack(side="right", padx=4)

            ctk.CTkButton(
                row,
                text="Endre tid",
                command=lambda t=timer: self.change_timer_time(t)
            ).pack(side="right", padx=4)

            mute_button = ctk.CTkButton(
                row,
                text=timer.get_mute_text(),
                command=lambda t=timer: t.toggle_mute()
            )
            mute_button.pack(side="right", padx=4)

            def update_timer_info(t=timer, tl=time_label, sl=status_label, pb=primary_button, mb=mute_button):
                if not (tl.winfo_exists() and sl.winfo_exists() and pb.winfo_exists()):
                    return

                tl.configure(
                    text=t.get_display_time(),
                    text_color=(t.get_time_color(), t.get_time_color())
                )
                sl.configure(text=t.get_status_text())
                pb.configure(text=t.get_primary_button_text())
                mb.configure(text=t.get_mute_text())
            timer.add_observer(update_timer_info)
            update_timer_info()

    def change_timer_time(self, timer):
        top = self._make_dialog("Endre tid", width=360, height=220)

        ctk.CTkLabel(top, text="Skriv inn ny tid (MM:SS):").pack(pady=(20, 8))

        entry = ctk.CTkEntry(top, width=140)
        entry.pack(pady=6)

        err_lbl = ctk.CTkLabel(top, text="", text_color="tomato")
        err_lbl.pack(pady=(6, 0))

        def save(event=None):
            try:
                timer.set_time_from_input(entry.get())
                top.destroy()
            except ValueError as e:
                err_lbl.configure(text=str(e))

        btn_row = ctk.CTkFrame(top)
        btn_row.pack(pady=16)

        ctk.CTkButton(btn_row, text="Avbryt", command=top.destroy).pack(side="left", padx=6)
        ctk.CTkButton(btn_row, text="Lagre", command=save).pack(side="left", padx=6)

        entry.bind("<Return>", save)
        top.bind("<Escape>", lambda _e: top.destroy())
        top.after(50, lambda: entry.focus_force())

    def _make_dialog(self, title, width=350, height=220):
        top = ctk.CTkToplevel(self)
        top.title(title)
        top.transient(self)
        top.configure(fg_color="#2b2b2b")

        top.geometry(f"{width}x{height}")
        top.update_idletasks()
        self.update_idletasks()

        parent_x = self.winfo_rootx()
        parent_y = self.winfo_rooty()
        parent_w = self.winfo_width()
        parent_h = self.winfo_height()

        x = parent_x + (parent_w - width) // 2
        y = parent_y + (parent_h - height) // 2
        top.geometry(f"{width}x{height}+{x}+{y}")

        top.wait_visibility()

        self._set_dark_title_bar(top)

        top.attributes("-topmost", True)
        top.lift(self)
        top.focus_force()
        top.grab_set()
        top.after(150, lambda: top.attributes("-topmost", False))

        return top
    
    def _show_message_dialog(self, title, message, width=320, height=140):
        top = self._make_dialog(title, width=width, height=height)
        ctk.CTkLabel(top, text=message, justify="center").pack(padx=20, pady=20)
        ctk.CTkButton(top, text="OK", command=top.destroy).pack(pady=(0, 12))
    
    def _set_dark_title_bar(self, window):
        try:
            import ctypes

            hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
            value = ctypes.c_int(1)

            # Windows 11 / nyere Windows 10
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_USE_IMMERSIVE_DARK_MODE,
                ctypes.byref(value),
                ctypes.sizeof(value)
            )
        except Exception:
            pass

    def build_final_bracket(self):
        standings = self.group_stage_model.standings()
        top_4 = standings[:4]

        self.tournament_model.build_bracket(top_4)

        top_4_by_name = {team.name: team for team in top_4}
        for team in self.tournament_model.teams:
            src = top_4_by_name.get(team.name)
            if src:
                team.logo = src.logo
                team.points = src.points
                team.cups_hit = src.cups_hit
                team.total_cups_diff = src.total_cups_diff

        self.bracket_canvas.refresh()
        self.draw_match_controls()
        self.start_bracket_button.pack_forget()

    def toggle_load_logo(self):
        self.logo_switch = not self.logo_switch

    def check_allowed_cup_number(self, cups):
        if cups > 10 or cups < 0:
            raise ValueError

    def set_group_winner_popup(self, match_index, winner):
        match = self.group_stage_model.matches[match_index]
        team1_name = match.team1.name
        team2_name = match.team2.name

        top = self._make_dialog("Antall kopper igjen", width=320, height=420)

        ctk.CTkLabel(top, text=f"{team1_name} kopper igjen (0–10):").pack(pady=(12, 4))
        e1 = ctk.CTkEntry(top, width=120)
        e1.pack(pady=4)

        ctk.CTkLabel(top, text=f"{team2_name} kopper igjen (0–10):").pack(pady=(12, 4))
        e2 = ctk.CTkEntry(top, width=120)
        e2.pack(pady=4)

        err_lbl = ctk.CTkLabel(top, text="", text_color="tomato")
        err_lbl.pack(pady=(6, 0))

        def do_save(event=None):
            c1_str = e1.get().strip()
            c2_str = e2.get().strip()

            if c1_str == "" or c2_str == "":
                err_lbl.configure(text="Fyll inn begge feltene.")
                return

            try:
                c1 = int(c1_str)
                c2 = int(c2_str)
                self.check_allowed_cup_number(c1)
                self.check_allowed_cup_number(c2)

                self.group_stage_model.update_match_result(match_index, c1, c2, winner)
                self.bracket_canvas.show_group_stage(self.group_stage_model)

                if hasattr(self, "draw_group_match_controls"):
                    self.draw_group_match_controls()

                top.destroy()
            except ValueError as e:
                err_lbl.configure(text=str(e))

        btn_row = ctk.CTkFrame(top)
        btn_row.pack(pady=12)
        ctk.CTkButton(btn_row, text="Avbryt", command=top.destroy).pack(side="left", padx=6)
        ctk.CTkButton(btn_row, text="Lagre", command=do_save).pack(side="left", padx=6)

        e1.bind("<Return>", do_save)
        e2.bind("<Return>", do_save)
        top.bind("<Escape>", lambda _e: top.destroy())

        top.grab_set()
        top.after(50, lambda: e1.focus_force())
        top.wait_window()

    def load_teams_from_file(self):
        path = fd.askopenfilename(
            title="Velg lag-fil",
            filetypes=[("CSV/Tekst", "*.csv *.txt *.tsv"), ("Alle filer", "*.*")]
        )
        if not path:
            return

        try:
            self.teams = parse_team_file(path)
            if not self.teams:
                raise ValueError("Fant ingen lag i fila.")

            self.team_text.delete("1.0", "end")
            self.team_text.insert("1.0", "\n".join(t.name for t in self.teams))

            self._show_message_dialog("Lag lastet", f"Lastet {len(self.teams)} lag fra fil.", 280, 120)

        except Exception as e:
            print(f"Feil ved lasting av lag: {e}")
            self._show_message_dialog("Feil", f"Kunne ikke lese filen.\n{e}", 360, 160)

    def start_group_stage(self):
        if not self.teams:
            self.fill_team_list()

        self.group_stage_model = GroupStageModel(self.teams)
        self.group_stage_model.generate_matches()

        self.bracket_canvas.show_group_stage(self.group_stage_model)
        self.draw_group_match_controls()

        self.start_group_button.pack_forget()
        self.start_bracket_button.pack(pady=5)

    def draw_group_match_controls(self):
        for widget in self.match_controls_frame.winfo_children():
            widget.destroy()

        ctk.CTkLabel(self.match_controls_frame, text="Gruppespillkontroller", font=("Arial", 20)).pack(pady=5)

        for idx, match in enumerate(self.group_stage_model.matches):
            row = ctk.CTkFrame(self.match_controls_frame)
            row.pack(fill="x", padx=6, pady=4)

            t1 = match.team1.name
            t2 = match.team2.name
            ctk.CTkLabel(row, text=f"{t1} vs {t2}").pack(side="left", padx=6)

            btn_t1 = ctk.CTkButton(
                row, text=f"{t1} vant",
                command=lambda i=idx: self.set_group_winner_popup(i, 1)
            )
            btn_t1.pack(side="right", padx=4)

            btn_t2 = ctk.CTkButton(
                row, text=f"{t2} vant",
                command=lambda i=idx: self.set_group_winner_popup(i, 2)
            )
            btn_t2.pack(side="right", padx=4)

            btn_time = ctk.CTkButton(
                row, text="Sett tidspunkt",
                command=lambda i=idx: self.set_group_match_time(i)
            )
            btn_time.pack(side="right", padx=4)

            if match.played:
                ctk.CTkButton(
                    row, text="Rediger resultat",
                    command=lambda i=idx: self.edit_group_result(i)
                ).pack(side="right", padx=4)

                ctk.CTkButton(
                    row, text="Angre resultat",
                    command=lambda i=idx: self.clear_group_result(i)
                ).pack(side="right", padx=4)

                btn_t1.configure(state="disabled")
                btn_t2.configure(state="disabled")
                btn_time.configure(state="disabled")

        update_standings_btn = ctk.CTkButton(
            self.match_controls_frame,
            text="Oppdater tabell",
            command=lambda: self.bracket_canvas.show_group_stage(self.group_stage_model)
        )
        update_standings_btn.pack(pady=10)

    def edit_group_result(self, match_index):
        match = self.group_stage_model.matches[match_index]
        top = self._make_dialog("Rediger resultat", width=320, height=340)

        t1 = match.team1.name
        t2 = match.team2.name
        prev_c1 = match.team1_cups_left or 0
        prev_c2 = match.team2_cups_left or 0
        prev_w = match.winner or 1

        ctk.CTkLabel(top, text=f"{t1} kopper igjen (0–10):").pack(pady=(10, 4))
        e1 = ctk.CTkEntry(top, width=120)
        e1.insert(0, str(prev_c1))
        e1.pack(pady=4)

        ctk.CTkLabel(top, text=f"{t2} kopper igjen (0–10):").pack(pady=(10, 4))
        e2 = ctk.CTkEntry(top, width=120)
        e2.insert(0, str(prev_c2))
        e2.pack(pady=4)

        ctk.CTkLabel(top, text="Vinner:").pack(pady=(10, 4))
        winner_var = tk.IntVar(value=prev_w)
        ctk.CTkRadioButton(top, text=t1, variable=winner_var, value=1).pack()
        ctk.CTkRadioButton(top, text=t2, variable=winner_var, value=2).pack()

        err_lbl = ctk.CTkLabel(top, text="", text_color="tomato")
        err_lbl.pack(pady=6)

        def save(event=None):
            try:
                c1 = int(e1.get().strip())
                c2 = int(e2.get().strip())
                self.check_allowed_cup_number(c1)
                self.check_allowed_cup_number(c2)
                self.group_stage_model.update_match_result(match_index, c1, c2, winner_var.get())
                self.bracket_canvas.show_group_stage(self.group_stage_model)
                self.draw_group_match_controls()
                top.destroy()
            except ValueError as e:
                err_lbl.configure(text=str(e))

        btn_row = ctk.CTkFrame(top)
        btn_row.pack(pady=10)
        ctk.CTkButton(btn_row, text="Avbryt", command=top.destroy).pack(side="left", padx=6)
        ctk.CTkButton(btn_row, text="Lagre", command=save).pack(side="left", padx=6)

        top.grab_set()
        top.focus()
        e1.focus()
        top.bind("<Return>", save)
        top.bind("<Escape>", lambda _e: top.destroy())
        top.after(50, lambda: e1.focus_force())

    def clear_group_result(self, match_index):
        self.group_stage_model.clear_match_result(match_index)
        self.bracket_canvas.show_group_stage(self.group_stage_model)
        self.draw_group_match_controls()

    def set_group_match_time(self, match_index):
        top = self._make_dialog("Sett tidspunkt", width=360, height=220)

        ctk.CTkLabel(top, text="Tidspunkt (HH:MM):").pack(pady=(20, 8))

        entry = ctk.CTkEntry(top, width=140)
        entry.pack(pady=6)

        err_lbl = ctk.CTkLabel(top, text="", text_color="tomato")
        err_lbl.pack(pady=(6, 0))

        def save(event=None):
            new_time = normalize_time_input(entry.get())
            if not is_valid_hhmm(new_time):
                err_lbl.configure(text="Ugyldig klokkeslett. Bruk HH:MM.")
                return

            self.group_stage_model.matches[match_index].time = new_time
            self.bracket_canvas.show_group_stage(self.group_stage_model)
            self.draw_group_match_controls()
            top.destroy()

        btn_row = ctk.CTkFrame(top)
        btn_row.pack(pady=16)

        ctk.CTkButton(btn_row, text="Avbryt", command=top.destroy).pack(side="left", padx=6)
        ctk.CTkButton(btn_row, text="Lagre", command=save).pack(side="left", padx=6)

        entry.bind("<Return>", save)
        top.bind("<Escape>", lambda _e: top.destroy())
        top.after(50, lambda: entry.focus_force())

    def show_standings(self):
        standings_window = ctk.CTkToplevel(self)
        standings_window.title("Tabell etter gruppespill")
        standings_window.geometry("700x800")

        for idx, team in enumerate(self.group_stage_model.standings(), start=1):
            frame = ctk.CTkFrame(standings_window)
            frame.pack(fill="x", pady=2, padx=10)

            if team.logo:
                img = Image.open(team.logo)
                img.thumbnail((40, 40), Image.LANCZOS)
                logo_img = ImageTk.PhotoImage(img)
                logo_label = ctk.CTkLabel(frame, image=logo_img, text="")
                logo_label.image = logo_img
                logo_label.pack(side="left", padx=10)

            stats = f"{idx}. {team.name} | Points: {team.points} | Hit: {team.cups_hit} | Diff: {team.total_cups_diff}"
            ctk.CTkLabel(frame, text=stats, font=("Helvetica", 16)).pack(side="left")

    def fill_team_list(self):
        self.teams = []

        base_teams = teams_from_text(self.team_text.get("1.0", "end"))

        for team in base_teams:
            logo_path = None
            if self.logo_switch:
                logo_path = fd.askopenfilename(
                    title=f"Velg logo for {team.name}",
                    filetypes=[("Image files", ".png .jpg .jpeg .gif")]
                )

            self.teams.append(Team(name=team.name, logo=logo_path))

    def build_bracket(self):
        if not self.teams:
            self.fill_team_list()

        self.tournament_model.build_bracket(self.teams)

        logo_by_name = {t.name: t.logo for t in self.teams}
        for t in self.tournament_model.teams:
            t.logo = logo_by_name.get(t.name)

        self.draw_match_controls()
        self.bracket_canvas.refresh()

    def draw_match_controls(self):
        for widget in self.match_controls_frame.winfo_children():
            widget.destroy()

        rounds = self.tournament_model.get_rounds()
        for r, matches in enumerate(rounds):
            round_label = ctk.CTkLabel(self.match_controls_frame, text=f"Runde {r+1} Kontroller")
            round_label.pack(pady=5)

            for mi, match in enumerate(matches):
                frame = ctk.CTkFrame(self.match_controls_frame)
                frame.pack(pady=5, fill="x")

                team1 = match.team1.name if match.team1 else "TBD"
                team2 = match.team2.name if match.team2 else "TBD"

                info_label = ctk.CTkLabel(frame, text=f"Kamp {mi+1}: {team1} vs {team2}")
                info_label.pack(side="left", padx=5)

                if match.winner:
                    btn1 = ctk.CTkButton(frame, text=team1, state="disabled")
                    btn2 = ctk.CTkButton(frame, text=team2, state="disabled")
                else:
                    btn1 = ctk.CTkButton(
                        frame,
                        text=team1,
                        command=lambda r=r, mi=mi, t=team1: self.set_winner(r, mi, t)
                    )
                    btn2 = ctk.CTkButton(
                        frame,
                        text=team2,
                        command=lambda r=r, mi=mi, t=team2: self.set_winner(r, mi, t)
                    )

                start_time = match.start_time if match.start_time else "Ikke satt"
                btn_time = ctk.CTkButton(
                    frame,
                    text=f"Sett starttid ({start_time})",
                    command=lambda r=r, mi=mi: self.set_start_time(r, mi)
                )
                btn_time.pack(side="right", padx=5)

                btn_edit = ctk.CTkButton(frame, text="Rediger", command=lambda r=r, mi=mi: self.edit_match(r, mi))
                btn_edit.pack(side="right", padx=5)

                btn2.pack(side="right", padx=5)
                btn1.pack(side="right", padx=5)

    def set_winner(self, round_index, match_index, winner_name):
        match = self.tournament_model.rounds[round_index][match_index]

        if match.team1 and match.team1.name == winner_name:
            winner = match.team1
        elif match.team2 and match.team2.name == winner_name:
            winner = match.team2
        else:
            winner = Team(name=winner_name)

        self.tournament_model.set_winner(round_index, match_index, winner)
        self.draw_match_controls()
        self.bracket_canvas.refresh()

    def set_start_time(self, round_index, match_index):
        top = self._make_dialog("Sett starttid", width=360, height=220)

        ctk.CTkLabel(top, text="Skriv inn starttid (f.eks. HH:MM):").pack(pady=(20, 8))

        entry = ctk.CTkEntry(top, width=140)
        entry.pack(pady=6)

        err_lbl = ctk.CTkLabel(top, text="", text_color="tomato")
        err_lbl.pack(pady=(6, 0))

        def save(event=None):
            new_time = normalize_time_input(entry.get())
            if not is_valid_hhmm(new_time):
                err_lbl.configure(text="Ugyldig klokkeslett. Bruk HH:MM.")
                return

            self.tournament_model.set_start_time(round_index, match_index, new_time)
            self.draw_match_controls()
            self.bracket_canvas.refresh()
            top.destroy()

        btn_row = ctk.CTkFrame(top)
        btn_row.pack(pady=16)

        ctk.CTkButton(btn_row, text="Avbryt", command=top.destroy).pack(side="left", padx=6)
        ctk.CTkButton(btn_row, text="Lagre", command=save).pack(side="left", padx=6)

        entry.bind("<Return>", save)
        top.bind("<Escape>", lambda _e: top.destroy())

        top.after(50, lambda: entry.focus_force())

    def edit_match(self, round_index, match_index):
        edit_window = self._make_dialog("Rediger kamp")

        match = self.tournament_model.get_rounds()[round_index][match_index]
        team1_current = match.team1.name if match.team1 is not None else ""
        team2_current = match.team2.name if match.team2 is not None else ""

        label1 = ctk.CTkLabel(edit_window, text="Lag 1:")
        label1.pack(pady=5)
        entry1 = ctk.CTkEntry(edit_window, width=200)
        entry1.insert(0, team1_current)
        entry1.pack(pady=5)

        label2 = ctk.CTkLabel(edit_window, text="Lag 2:")
        label2.pack(pady=5)
        entry2 = ctk.CTkEntry(edit_window, width=200)
        entry2.insert(0, team2_current)
        entry2.pack(pady=5)

        def save_edits():
            new_team1 = entry1.get().strip() or "TBD"
            new_team2 = entry2.get().strip() or "TBD"
            self.tournament_model.set_match_teams(round_index, match_index, new_team1, new_team2)
            edit_window.destroy()
            self.draw_match_controls()
            self.bracket_canvas.refresh()

        save_button = ctk.CTkButton(edit_window, text="Lagre", command=save_edits)
        save_button.pack(pady=10)
        edit_window.after(50, lambda: entry1.focus_force())