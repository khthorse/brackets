
import csv

import customtkinter as ctk
import tkinter.filedialog as fd
import tkinter as tk

from PIL import Image, ImageTk
from pathlib import Path

from models import TournamentModel, GroupStageModel, Team


class TournamentBracketCanvas(ctk.CTkFrame):
    """
    Hovedvinduet som viser braketten på en Canvas i pyramideform.
    Kampene tegnes som rektangler med linjer som forbinder rundene.
    Linjene trekkes i tre segmenter: horisontalt fra barnets boks, så vertikalt,
    og horisontalt til den nye boksen.
    """
    def __init__(self, master, tournament_model, *args, **kwargs):
        super().__init__(master, *args, border_width=0, fg_color="#2b2b2b", **kwargs)
        self.tournament_model = tournament_model
        self.pack(fill="both", expand=True)

        canvas_bg = "#2B2B2B"
        self.canvas = tk.Canvas(self, bg=canvas_bg, highlightthickness=0, bd=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda event: self.draw_bracket())

        self.images = []
        self.draw_bracket()

    def show_winner_popup(self, winner):
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        self.canvas.delete("all")
        self.canvas.create_text(
            canvas_width / 2,
            canvas_height / 2 - 300,
            text="🏆 Vinner av turnering! 🏆",
            font=("Arial", 60),
            fill="white",
        )
        self.canvas.create_text(
            canvas_width / 2,
            canvas_height / 2 - 200,
            text=winner.name,
            font=("Arial", 60),
            fill="white",
        )

        if winner.logo:
            try:
                img = Image.open(winner.logo)
                img.thumbnail((canvas_height / 3, canvas_height / 3), Image.LANCZOS)
                logo_img = ImageTk.PhotoImage(img)
                self.canvas.create_image(
                    canvas_width / 2,
                    canvas_height / 2 + canvas_height / 6,
                    image=logo_img,
                )
                self.images.append(logo_img)
            except Exception as e:
                print(f"Feil ved lasting av logo: {e}")

    def show_group_stage(self, group_stage_model):
        self.canvas.delete("all")
        self.images.clear()

        standings = group_stage_model.standings()
        matches = group_stage_model.matches

        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        self.canvas.create_text(
            canvas_width / 2, 30, text="Gruppespill", font=("Arial", 30), fill="white"
        )

        start_y = 80
        box_pady = 5
        box_padx = 10
        box_height = (canvas_height - start_y - 2 * box_pady) / len(standings)
        box_width = (canvas_width / 2) - 2 * box_padx
        box2_width = (canvas_width * 4 / 10) - 2 * box_padx
        thumbnail_size = box_height - 4 * box_pady

        self.canvas.create_text(
            canvas_width / 4,
            start_y - 6 * box_pady,
            text="Tabell",
            font=("Arial", 24),
            fill="white",
        )

        for idx, team in enumerate(standings, start=1):
            box_x0, box_y0 = box_padx, start_y + box_pady + (idx - 1) * box_height
            box_x1, box_y1 = box_width - box_padx, box_y0 - box_pady + box_height

            self.canvas.create_rectangle(box_x0, box_y0, box_x1, box_y1, fill="#333333")
            text_ypos = box_y1 + box_pady - box_height / 2
            teamname_x = box_width / 4
            results_x = 3 * box_width / 4
            fontsize = int(box_height / 4)

            self.canvas.create_text(
                teamname_x,
                text_ypos,
                text=f"{idx}. {team.name}",
                font=("Arial", fontsize),
                fill="white",
                anchor="w",
            )
            self.canvas.create_text(
                results_x,
                text_ypos,
                text=f"P    |    T    |    D\n{team.points}    |    {team.cups_hit}    |    {team.total_cups_diff}",
                font=("Arial", fontsize),
                fill="white",
                justify="left",
            )

            if team.logo:
                try:
                    img = Image.open(team.logo)
                    img.thumbnail((thumbnail_size, thumbnail_size), Image.LANCZOS)
                    logo_img = ImageTk.PhotoImage(img)
                    self.canvas.create_image(box_width / 8, text_ypos - box_pady / 2, image=logo_img)
                    self.images.append(logo_img)
                except Exception as e:
                    print(f"Feil ved lasting av logo: {e}")

        matches_start_y = 80
        matches_start_x = box_width + 0.5 * box_width + 2 * box_padx - box2_width / 2

        self.canvas.create_text(
            3 * canvas_width / 4,
            matches_start_y - 6 * box_pady,
            text="Kamper",
            font=("Arial", 24),
            fill="white",
        )

        for idx, match in enumerate(matches, start=1):
            box_x0, box_y0 = matches_start_x + box_padx, start_y + box_pady + (idx - 1) * box_height
            box_x1, box_y1 = matches_start_x + box2_width - box_padx, box_y0 - box_pady + box_height

            self.canvas.create_rectangle(box_x0, box_y0, box_x1, box_y1, fill="#333333")

            time_ypos = box_y1 + box_pady - box_height / 2 - box_height / 4
            text_ypos = box_y1 + box_pady - box_height / 2
            teamname1_x = matches_start_x + box2_width / 4 + thumbnail_size
            teamname2_x = matches_start_x + 3 * box2_width / 4 - thumbnail_size

            team1_name = match.team1.name if match.team1 else "TBD"
            team2_name = match.team2.name if match.team2 else "TBD"

            if match.time:
                if match.played:
                    self.canvas.create_text(
                        teamname1_x,
                        text_ypos + box_height / 6,
                        text=team1_name,
                        font=("Arial overstrike", int(fontsize * 3 / 4)),
                        fill="white",
                        justify="left",
                    )
                    self.canvas.create_text(
                        matches_start_x + box2_width / 2,
                        text_ypos + box_height / 6,
                        text="vs",
                        font=("Arial", fontsize),
                        fill="white",
                    )
                    self.canvas.create_text(
                        teamname2_x,
                        text_ypos + box_height / 6,
                        text=team2_name,
                        font=("Arial", int(fontsize * 3 / 4)),
                        fill="white",
                        justify="right",
                    )
                else:
                    self.canvas.create_text(
                        teamname1_x,
                        text_ypos + box_height / 6,
                        text=team1_name,
                        font=("Arial", int(fontsize * 3 / 4)),
                        fill="white",
                        justify="left",
                    )
                    self.canvas.create_text(
                        matches_start_x + box2_width / 2,
                        text_ypos + box_height / 6,
                        text="vs",
                        font=("Arial", fontsize),
                        fill="white",
                    )
                    self.canvas.create_text(
                        teamname2_x,
                        text_ypos + box_height / 6,
                        text=team2_name,
                        font=("Arial", int(fontsize * 3 / 4)),
                        fill="white",
                        justify="right",
                    )

                self.canvas.create_text(
                    matches_start_x + box2_width / 2,
                    time_ypos,
                    text=f"Starter: {match.time}",
                    font=("Arial", int(fontsize * 4 / 5)),
                    fill="white",
                )
            else:
                self.canvas.create_text(
                    teamname1_x,
                    text_ypos,
                    text=team1_name,
                    font=("Arial", int(fontsize * 3 / 4)),
                    fill="white",
                    justify="left",
                )
                self.canvas.create_text(
                    matches_start_x + box2_width / 2,
                    text_ypos,
                    text="vs",
                    font=("Arial", fontsize),
                    fill="white",
                )
                self.canvas.create_text(
                    teamname2_x,
                    text_ypos,
                    text=team2_name,
                    font=("Arial", int(fontsize * 3 / 4)),
                    fill="white",
                    justify="right",
                )

            if match.team1 and match.team1.logo:
                try:
                    img = Image.open(match.team1.logo)
                    img.thumbnail((thumbnail_size, thumbnail_size), Image.LANCZOS)
                    logo_img = ImageTk.PhotoImage(img)
                    self.canvas.create_image(
                        matches_start_x + box2_width / 8,
                        text_ypos - box_pady / 2,
                        image=logo_img,
                    )
                    self.images.append(logo_img)
                except Exception as e:
                    print(f"Feil ved lasting av logo: {e}")

            if match.team2 and match.team2.logo:
                try:
                    img = Image.open(match.team2.logo)
                    img.thumbnail((thumbnail_size, thumbnail_size), Image.LANCZOS)
                    logo_img = ImageTk.PhotoImage(img)
                    self.canvas.create_image(
                        matches_start_x + box2_width * 7 / 8,
                        text_ypos - box_pady / 2,
                        image=logo_img,
                    )
                    self.images.append(logo_img)
                except Exception as e:
                    print(f"Feil ved lasting av logo: {e}")

    def draw_bracket(self):
        self.canvas.delete("all")
        rounds = self.tournament_model.get_rounds()

        if not rounds:
            return

        num_rounds = len(rounds)

        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        left_margin = 50
        right_margin = 50
        top_margin = 50
        bottom_margin = 50

        box_width = 300
        box_height = 80

        horizontal_spacing = (
            (canvas_width - left_margin - right_margin - num_rounds * box_width) / (num_rounds - 1)
            if num_rounds > 1 else 0
        )

        num_matches_r0 = len(rounds[0])
        vertical_spacing = (
            (canvas_height - top_margin - bottom_margin - num_matches_r0 * box_height) / (num_matches_r0 - 1)
            if num_matches_r0 > 1 else 0
        )

        positions = []
        round0_positions = []

        for i in range(num_matches_r0):
            y = top_margin + i * (box_height + vertical_spacing) + box_height / 2
            x = left_margin + box_width / 2
            round0_positions.append((x, y))
        positions.append(round0_positions)

        for r in range(1, num_rounds):
            prev_positions = positions[r - 1]
            current_positions = []
            num_matches = len(rounds[r])

            for i in range(num_matches):
                if 2 * i + 1 < len(prev_positions):
                    y = (prev_positions[2 * i][1] + prev_positions[2 * i + 1][1]) / 2
                else:
                    y = prev_positions[2 * i][1]

                x = left_margin + r * (box_width + horizontal_spacing) + box_width / 2
                current_positions.append((x, y))

            positions.append(current_positions)

        self.images.clear()

        for r, round_matches in enumerate(rounds):
            for i, match in enumerate(round_matches):
                x, y = positions[r][i]
                x0, y0 = x - box_width / 2, y - box_height / 2
                x1, y1 = x + box_width / 2, y + box_height / 2

                self.canvas.create_rectangle(x0, y0, x1, y1, fill="gray20", outline="black")

                team1_name = match.team1.name if match.team1 else "TBD"
                team2_name = match.team2.name if match.team2 else "TBD"
                text = f"{team1_name}\nvs\n{team2_name}"

                self.canvas.create_text(
                    x, y, text=text, font=("Helvetica", 16), fill="white", justify="center"
                )

                logo_size = 40
                padding = 5

                if match.team1 and match.team1.logo:
                    try:
                        img1 = Image.open(match.team1.logo).resize((logo_size, logo_size))
                        img1_tk = ImageTk.PhotoImage(img1)
                        self.canvas.create_image(x0 + logo_size / 2 + padding, y, image=img1_tk)
                        self.images.append(img1_tk)
                    except Exception as e:
                        print(f"Feil ved lasting av logo for {team1_name}: {e}")

                if match.team2 and match.team2.logo:
                    try:
                        img2 = Image.open(match.team2.logo).resize((logo_size, logo_size))
                        img2_tk = ImageTk.PhotoImage(img2)
                        self.canvas.create_image(x1 - logo_size / 2 - padding, y, image=img2_tk)
                        self.images.append(img2_tk)
                    except Exception as e:
                        print(f"Feil ved lasting av logo for {team2_name}: {e}")

                if r > 0:
                    child_index = i * 2
                    parent_x_left = x0

                    for idx_offset in [0, 1]:
                        child_idx = child_index + idx_offset
                        if child_idx < len(positions[r - 1]):
                            child_x, child_y = positions[r - 1][child_idx]
                            child_x_right = child_x + box_width / 2
                            mid_x = (child_x_right + parent_x_left) / 2

                            self.canvas.create_line(child_x_right, child_y, mid_x, child_y, fill="white")
                            self.canvas.create_line(mid_x, child_y, mid_x, y, fill="white")
                            self.canvas.create_line(mid_x, y, parent_x_left, y, fill="white")

                            child_match = rounds[r - 1][child_idx]
                            if child_match.start_time:
                                text_x = (child_x_right + mid_x) / 2
                                text_y = child_y - 14
                                self.canvas.create_text(
                                    text_x,
                                    text_y,
                                    text=f"Starter: {child_match.start_time}",
                                    font=("Helvetica", 11),
                                    fill="white",
                                )

        self.canvas.config(scrollregion=self.canvas.bbox("all"))

        last_round = rounds[-1]
        if len(last_round) == 1 and last_round[0].winner:
            self.show_winner_popup(last_round[0].winner)

    def refresh(self):
        self.draw_bracket()

class ControlWindow(ctk.CTkToplevel):
    """
    Kontrollvinduet der du kan legge inn lag, sette vinnere, angi starttidspunkt
    og redigere kampoppsettet.
    """
    def __init__(self, master, tournament_model, bracket_canvas, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.tournament_model = tournament_model
        self.bracket_canvas = bracket_canvas
        self.title("Kontrollvindu")
        self.geometry("1000x1200")

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
        self.start_bracket_button.pack_forget()

        self.start_group_button.pack(pady=5)

        self.match_controls_frame = ctk.CTkScrollableFrame(self)
        self.match_controls_frame.pack(fill="both", expand=True, pady=10)

        self.draw_match_controls()
        self.teams = []

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

    def _parse_team_file(self, filepath: str):
        teams = []
        base = Path(filepath).parent

        def split_smart(line: str):
            # Bruk csv.reader bare hvis linjen faktisk ser komma-separert ut
            if "," in line:
                try:
                    for row in csv.reader([line]):
                        if len(row) > 1:
                            return [s.strip() for s in row]
                except Exception:
                    pass

            # Fallback for andre skilletegn
            for delim in [";", "|", "\t"]:
                if delim in line:
                    return [s.strip() for s in line.split(delim)]

            return [line.strip()]

        with open(filepath, "r", encoding="utf-8-sig") as f:
            lines = f.read().splitlines()

        if lines and ("name" in lines[0].lower() and "logo" in lines[0].lower()):
            lines = lines[1:]

        for raw in lines:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue

            parts = split_smart(line)

            if len(parts) == 1:
                name = parts[0].strip()
                logo = None
            else:
                name = parts[0].strip()
                logo = parts[1].strip() if parts[1] else None

            if logo:
                logo = logo.strip('"').strip("'")

            if not name:
                continue

            if logo:
                p = Path(logo).expanduser()
                if not p.is_absolute():
                    p = (base / p).resolve()
                logo = str(p)

            teams.append(Team(name=name, logo=logo))

        return teams

    def _teams_from_textbox(self):
        names = [ln.strip() for ln in self.team_text.get("1.0", "end").splitlines() if ln.strip()]
        return [Team(name=n) for n in names]

    def load_teams_from_file(self):
        path = fd.askopenfilename(
            title="Velg lag-fil",
            filetypes=[("CSV/Tekst", "*.csv *.txt *.tsv"), ("Alle filer", "*.*")]
        )
        if not path:
            return

        try:
            self.teams = self._parse_team_file(path)
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
                command=lambda i=idx: self.set_group_match_timer(i)
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

    def set_group_match_timer(self, match_index):
        top = self._make_dialog("Sett tidspunkt", width=360, height=220)

        ctk.CTkLabel(top, text="Tidspunkt (HH:MM):").pack(pady=(20, 8))

        entry = ctk.CTkEntry(top, width=140)
        entry.pack(pady=6)

        err_lbl = ctk.CTkLabel(top, text="", text_color="tomato")
        err_lbl.pack(pady=(6, 0))

        def save(event=None):
            new_time = self._normalize_time(entry.get())
            if not self._is_valid_time(new_time):
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
        team_names = [name.strip() for name in self.team_text.get("1.0", "end").splitlines() if name.strip()]

        for name in team_names:
            logo_path = None
            if self.logo_switch:
                logo_path = fd.askopenfilename(
                    title=f"Velg logo for {name}",
                    filetypes=[("Image files", ".png .jpg .jpeg .gif")]
                )

            self.teams.append(Team(name=name, logo=logo_path))

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

    def _normalize_time(self, value: str) -> str:
        value = value.strip()

        # Hvis allerede format HH:MM → returner direkte
        if ":" in value:
            return value

        # Kun tall → tolk smart
        if value.isdigit():
            if len(value) <= 2:
                # "8" → "08:00"
                return f"{int(value):02d}:00"

            elif len(value) == 3:
                # "800" → "08:00", "930" → "09:30"
                h = int(value[0])
                m = int(value[1:])
                return f"{h:02d}:{m:02d}"

            elif len(value) == 4:
                # "1330" → "13:30"
                h = int(value[:2])
                m = int(value[2:])
                return f"{h:02d}:{m:02d}"

        return value

    def _is_valid_time(self, value: str) -> bool:
        if len(value) != 5 or value[2] != ":":
            return False
        hh, mm = value.split(":")
        if not (hh.isdigit() and mm.isdigit()):
            return False
        hh = int(hh)
        mm = int(mm)
        return 0 <= hh <= 23 and 0 <= mm <= 59

    def set_start_time(self, round_index, match_index):
        top = self._make_dialog("Sett starttid", width=360, height=220)

        ctk.CTkLabel(top, text="Skriv inn starttid (f.eks. HH:MM):").pack(pady=(20, 8))

        entry = ctk.CTkEntry(top, width=140)
        entry.pack(pady=6)

        err_lbl = ctk.CTkLabel(top, text="", text_color="tomato")
        err_lbl.pack(pady=(6, 0))

        def save(event=None):
            new_time = self._normalize_time(entry.get())
            if not self._is_valid_time(new_time):
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

if __name__ == "__main__":
    ctk.set_appearance_mode("Dark")
    root = ctk.CTk()
    root.title("Turneringsbrakett - Hovedvindu")
    tournament_model = TournamentModel()
    bracket_canvas = TournamentBracketCanvas(root, tournament_model)
    control_window = ControlWindow(root, tournament_model, bracket_canvas)
    root.mainloop()
