import customtkinter as ctk
import tkinter as tk

from dataclasses import dataclass
from typing import Optional
from PIL import Image, ImageTk

from translations import t

@dataclass
class StandingsRowView:
    frame: ctk.CTkFrame
    position_label: ctk.CTkLabel
    name_wrap: ctk.CTkFrame
    name_label: ctk.CTkLabel
    points_label: ctk.CTkLabel
    hit_label: ctk.CTkLabel
    diff_label: ctk.CTkLabel
    points_box: Optional[ctk.CTkFrame] = None
    hit_box: Optional[ctk.CTkFrame] = None
    diff_box: Optional[ctk.CTkFrame] = None
    logo_label: Optional[tk.Label] = None

@dataclass
class MatchRowView:
    frame: ctk.CTkFrame
    time_label: ctk.CTkLabel
    team1_label: ctk.CTkLabel
    vs_label: ctk.CTkLabel
    team2_label: ctk.CTkLabel


class TournamentBracketCanvas(ctk.CTkFrame):
    """
    Hovedvinduet som viser braketten på en Canvas i pyramideform.
    Kampene tegnes som rektangler med linjer som forbinder rundene.
    Linjene trekkes i tre segmenter: horisontalt fra barnets boks, så vertikalt,
    og horisontalt til den nye boksen.
    """
    def __init__(self, master, tournament_model, settings=None, *args, **kwargs):
        super().__init__(master, *args, border_width=0, fg_color="#2b2b2b", **kwargs)
        self.tournament_model = tournament_model
        self.settings = settings

        self.pack(fill="both", expand=True)

        self.images = []
        self.logo_cache = {}
        self.group_stage_model = None
        self._group_stage_rebuild_job = None
        self._group_stage_frames = None
        self.previous_standings_positions = {}

        self.standings_rows = []
        self.standings_layout = None
        self.standings_title_label = None
        self.standings_header = None
        self.standings_rows_container = None
        self.matches_title_label = None
        self.matches_rows_container = None
        self.matches_row_views = []

        self.loading_window = None
        self.loading_canvas = None
        self.loading_circle = None
        self.loading_text_item = None
        self.loading_text_base = None
        self._loading_job = None
        self._loading_step = 0

        self.bracket_view = ctk.CTkFrame(self, fg_color="#2b2b2b")
        self.bracket_view.pack(fill="both", expand=True)

        canvas_bg = "#2B2B2B"
        self.canvas = tk.Canvas(self.bracket_view, bg=canvas_bg, highlightthickness=0, bd=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda event: self.draw_bracket())

        self.group_stage_view = ctk.CTkFrame(self, fg_color="#2b2b2b")


    def show_bracket_view(self):
        if self.group_stage_view.winfo_manager():
            self.group_stage_view.pack_forget()

        if not self.bracket_view.winfo_manager():
            self.bracket_view.pack(fill="both", expand=True)


    def show_group_stage_view(self):
        if self.bracket_view.winfo_manager():
            self.bracket_view.pack_forget()

        if not self.group_stage_view.winfo_manager():
            self.group_stage_view.pack(fill="both", expand=True)

    def show_loading_overlay(self, text=None):
        self.hide_loading_overlay()

        root = self.winfo_toplevel()
        root.update_idletasks()

        x = root.winfo_rootx()
        y = root.winfo_rooty()
        w = root.winfo_width()
        h = root.winfo_height()

        self.loading_window = tk.Toplevel(root)
        self.loading_window.overrideredirect(True)
        self.loading_window.geometry(f"{w}x{h}+{x}+{y}")
        self.loading_window.configure(bg="#2b2b2b")
        self.loading_window.attributes("-topmost", True)

        size = 220
        pad = 18
        line_width = 10

        self.loading_canvas = tk.Canvas(
            self.loading_window,
            width=size,
            height=size,
            bg="#2b2b2b",
            highlightthickness=0,
            bd=0,
        )
        self.loading_canvas.place(relx=0.5, rely=0.5, anchor="center")

        self.loading_circle = self.loading_canvas.create_oval(
            pad,
            pad,
            size - pad,
            size - pad,
            width=line_width,
            outline="#4682B4",
        )

        self.loading_text_base = text if text is not None else t("loading")
        self._loading_step = 0

        self.loading_text_item = self.loading_canvas.create_text(
            size / 2,
            size / 2,
            text=self.loading_text_base,
            font=("Helvetica", 18, "bold"),
            fill="white",
        )

        self.loading_window.update()
        self._loading_job = self.after(100, self._animate_loading_text)

    def _animate_loading_text(self):
        if self.loading_canvas is None or self.loading_text_item is None:
            return

        try:
            if not self.loading_canvas.winfo_exists():
                return
        except Exception:
            return

        states = [
            self.loading_text_base,
            self.loading_text_base + ".",
            self.loading_text_base + "..",
            self.loading_text_base + "...",
        ]

        self._loading_step = (self._loading_step + 1) % len(states)
        self.loading_canvas.itemconfigure(
            self.loading_text_item,
            text=states[self._loading_step]
        )

        self._loading_job = self.after(350, self._animate_loading_text)

    def hide_loading_overlay(self):
        if self._loading_job is not None:
            try:
                self.after_cancel(self._loading_job)
            except Exception:
                pass
            self._loading_job = None

        if self.loading_window is not None:
            try:
                if self.loading_window.winfo_exists():
                    self.loading_window.destroy()
            except Exception:
                pass

        self.loading_window = None
        self.loading_canvas = None
        self.loading_circle = None
        self.loading_text_item = None
        self.loading_text_base = None
        self._loading_step = 0

    def show_winner_popup(self, winner):
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        self.canvas.delete("all")
        self.canvas.create_text(
            canvas_width / 2,
            canvas_height / 2 - 300,
            text=t("winner_of_tournament"),
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
                print(f"Error when loading logo: {e}")
    ''' 
        Deprecated

    def draw_standings_table(self, x, y, width, row_height, standings, scale):
        headers = ["#", t("team_label"), t("points_short"), t("hit_short"), t("diff_short")]

        # Kolonnebredder som andel av total bredde
        col_widths = [0.08, 0.52, 0.13, 0.13, 0.14]

        header_font = ("Arial", max(10, int(14 * scale)), "bold")
        cell_font = ("Arial", max(9, int(13 * scale)))

        # Regn ut x-posisjoner for kolonnene
        col_x = [x]
        for fraction in col_widths:
            col_x.append(col_x[-1] + fraction * width)

        # Header-rad
        for i, header in enumerate(headers):
            self.canvas.create_rectangle(
                col_x[i],
                y,
                col_x[i + 1],
                y + row_height,
                fill="#2b2b2b",
                outline="#444444",
            )

            self.canvas.create_text(
                (col_x[i] + col_x[i + 1]) / 2,
                y + row_height / 2,
                text=header,
                fill="white",
                font=header_font,
            )

        # Datarader
        for row_idx, team in enumerate(standings):
            row_y0 = y + row_height * (row_idx + 1)
            row_y1 = row_y0 + row_height

            values = [
                str(row_idx + 1),
                team.name,
                str(team.points),
                str(team.cups_hit),
                str(team.total_cups_diff),
            ]

            for i, value in enumerate(values):
                self.canvas.create_rectangle(
                    col_x[i],
                    row_y0,
                    col_x[i + 1],
                    row_y1,
                    fill="#333333",
                    outline="#444444",
                )

                # Venstrejuster bare lagnavn
                if i == 1:
                    text_x = col_x[i] + 10
                    anchor = "w"
                else:
                    text_x = (col_x[i] + col_x[i + 1]) / 2
                    anchor = "center"

                self.canvas.create_text(
                    text_x,
                    (row_y0 + row_y1) / 2,
                    text=value,
                    fill="white",
                    font=cell_font,
                    anchor=anchor,
                )
    '''

    def _schedule_group_stage_rebuild(self, delay=30):
        if self._group_stage_rebuild_job is not None:
            try:
                self.after_cancel(self._group_stage_rebuild_job)
            except Exception:
                pass

        self._group_stage_rebuild_job = self.after(delay, self._rebuild_group_stage_view)


    def _rebuild_group_stage_view(self):
        self._group_stage_rebuild_job = None

        if self.group_stage_model is None:
            return

        if self._group_stage_frames is None:
            return

        standings_frame, matches_frame = self._group_stage_frames

        if not standings_frame.winfo_exists() or not matches_frame.winfo_exists():
            return

        # Vent til layout faktisk er klar
        if standings_frame.winfo_width() <= 10 or standings_frame.winfo_height() <= 10:
            self._schedule_group_stage_rebuild(delay=30)
            return

        if matches_frame.winfo_width() <= 10 or matches_frame.winfo_height() <= 10:
            self._schedule_group_stage_rebuild(delay=30)
            return

        standings = self.group_stage_model.standings()
        matches = self.group_stage_model.matches

        self.refresh_group_stage_standings(standings_frame, standings, matches)
        self.refresh_group_stage_matches(matches_frame, matches)
        self.after(120, self.hide_loading_overlay)

    def refresh_group_stage_standings(self, parent, standings, matches):
        if self.standings_rows_container is None or not self.standings_rows_container.winfo_exists():
            self.build_group_stage_standings(parent, standings, matches)
            return

        current_count = len(self.standings_rows)
        new_count = len(standings)

        # Hvis antall lag har endret seg, bygg på nytt
        if current_count != new_count:
            for child in parent.winfo_children():
                child.destroy()

            self.standings_rows = []
            self.standings_title_label = None
            self.standings_header = None
            self.standings_rows_container = None

            self.build_group_stage_standings(parent, standings, matches)
            return

        self.update_group_stage_standings(standings, matches)

    def update_group_stage_standings(self, standings, matches):
        for idx, (team, row_view) in enumerate(zip(standings, self.standings_rows), start=1):
            row_view.position_label.configure(text=str(idx))
            row_view.name_label.configure(text=team.name)
            row_view.points_label.configure(text=str(team.points))
            row_view.hit_label.configure(text=str(team.cups_hit))
            row_view.diff_label.configure(text=str(team.total_cups_diff))

            row_color = "#3a3a3a" if idx <= 4 else "#333333"
            row_view.frame.configure(fg_color=row_color)

            if row_view.logo_label is not None:
                try:
                    row_view.logo_label.configure(bg=row_color)
                except Exception:
                    pass

        self.after(10, self._update_standings_row_styles)


    def show_group_stage(self, group_stage_model):
        self.group_stage_model = group_stage_model
        self.show_group_stage_view()
        self.show_loading_overlay()

        self.after(50, self._build_group_stage_layout)

    def _build_group_stage_layout(self):
        for child in self.group_stage_view.winfo_children():
            child.destroy()

        self.standings_rows = []
        self.standings_title_label = None
        self.standings_header = None
        self.standings_rows_container = None

        self.matches_title_label = None
        self.matches_rows_container = None
        self.matches_row_views = []

        content = ctk.CTkFrame(self.group_stage_view, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        content.grid_columnconfigure(0, weight=1)
        content.grid_columnconfigure(1, weight=4)
        content.grid_columnconfigure(2, weight=1)
        content.grid_columnconfigure(3, weight=4)
        content.grid_columnconfigure(4, weight=1)
        content.grid_rowconfigure(0, weight=1)

        standings_frame = ctk.CTkFrame(content, fg_color="#2b2b2b")
        standings_frame.grid(row=0, column=1, sticky="nsew", padx=(0, 10))

        matches_frame = ctk.CTkFrame(content, fg_color="#2b2b2b")
        matches_frame.grid(row=0, column=3, sticky="nsew", padx=(10, 0))

        self._group_stage_frames = (standings_frame, matches_frame)

        self._schedule_group_stage_rebuild(delay=30)

        standings_frame.bind("<Configure>", lambda _e: self._schedule_group_stage_rebuild(delay=60))
        matches_frame.bind("<Configure>", lambda _e: self._schedule_group_stage_rebuild(delay=60))

    def refresh_group_stage(self):
        if self.group_stage_model is None:
            return
        self._schedule_group_stage_rebuild(delay=10)
        
    def get_position_trend(self, team_name, current_position):
        previous_position = self.previous_standings_positions.get(team_name)

        if previous_position is None:
            return "–", "#aaaaaa"

        if current_position < previous_position:
            return "↑", "#2faa6a"

        if current_position > previous_position:
            return "↓", "#d9534f"

        return "–", "#aaaaaa"
    
    def get_team_form(self, team_name, matches, limit=3):
        results = []

        for match in matches:
            if not match.played:
                continue

            if not match.team1 or not match.team2:
                continue

            if match.team1.name != team_name and match.team2.name != team_name:
                continue

            winner = match.winner

            if winner == 1:
                winning_name = match.team1.name
            elif winner == 2:
                winning_name = match.team2.name
            else:
                winning_name = None

            if winning_name is None:
                results.append("U")
            elif winning_name == team_name:
                results.append("V")
            else:
                results.append("T")

        return results[-limit:]
    
    def _create_form_boxes(self, parent, row, column, form_list, row_height):
        wrapper = ctk.CTkFrame(parent, fg_color="transparent")
        wrapper.grid(row=row, column=column, padx=6, pady=max(2, int(row_height * 0.12)))

        colors = {
            "V": "#2faa6a",
            "T": "#d9534f",
            "U": "#c9a227",
        }

        if not form_list:
            ctk.CTkLabel(wrapper, text="–", text_color="#aaaaaa", font=("Arial", max(9, int(row_height * 0.26)))).pack()
            return

        box_size = max(18, int(row_height * 0.5))

        for result in form_list:
            color = colors.get(result, "#666666")
            box = ctk.CTkFrame(
                wrapper,
                fg_color=color,
                corner_radius=max(5, int(box_size * 0.28)),
                width=box_size,
                height=box_size,
            )
            box.pack(side="left", padx=2)
            box.pack_propagate(False)

            ctk.CTkLabel(
                box,
                text=result,
                font=("Arial", max(8, int(box_size * 0.42)), "bold"),
                text_color="white",
            ).pack(expand=True)

    def _build_standings_header(self, parent, header_font_size, header_block_height):
        header = ctk.CTkFrame(parent, fg_color="transparent", height=header_block_height)
        header.pack(fill="x", padx=6, pady=(0, 2))
        header.pack_propagate(False)

        header.grid_columnconfigure(0, weight=1, minsize=26)
        header.grid_columnconfigure(1, weight=1, minsize=34)
        header.grid_columnconfigure(2, weight=6)
        header.grid_columnconfigure(3, weight=1, minsize=34)
        header.grid_columnconfigure(4, weight=1, minsize=34)
        header.grid_columnconfigure(5, weight=1, minsize=34)

        ctk.CTkLabel(
            header,
            text="",
            font=("Arial", header_font_size, "bold"),
        ).grid(row=0, column=0, padx=3, pady=1)

        ctk.CTkLabel(
            header,
            text="#",
            font=("Arial", header_font_size, "bold"),
        ).grid(row=0, column=1, padx=3, pady=1)

        ctk.CTkLabel(
            header,
            text=t("team_label"),
            font=("Arial", header_font_size, "bold"),
        ).grid(row=0, column=2, padx=4, pady=1, sticky="w")

        ctk.CTkLabel(
            header,
            text=t("points_label"),
            font=("Arial", header_font_size, "bold"),
        ).grid(row=0, column=3, padx=2, pady=1)

        ctk.CTkLabel(
            header,
            text=t("hit_label"),
            font=("Arial", header_font_size, "bold"),
        ).grid(row=0, column=4, padx=2, pady=1)

        ctk.CTkLabel(
            header,
            text=t("diff_label"),
            font=("Arial", header_font_size, "bold"),
        ).grid(row=0, column=5, padx=2, pady=1)

        return header

    def _set_team_name_and_logo(self, row_view, team, row_color, logo_size):
        for child in row_view.name_wrap.winfo_children():
            child.destroy()

        logo_label = None

        if team.logo:
            try:
                cache_key = (team.logo, logo_size)

                if cache_key in self.logo_cache:
                    logo_img = self.logo_cache[cache_key]
                else:
                    img = Image.open(team.logo)
                    img.thumbnail((logo_size, logo_size), Image.LANCZOS)
                    logo_img = ImageTk.PhotoImage(img)
                    self.logo_cache[cache_key] = logo_img

                self.images.append(logo_img)

                logo_label = tk.Label(
                    row_view.name_wrap,
                    image=logo_img,
                    bg=row_color,
                    bd=0,
                    highlightthickness=0,
                )
                logo_label.image = logo_img
                logo_label.pack(side="left", padx=(0, 4))
            except Exception as e:
                print(f"Error loading logo: {e}")

        row_view.name_label = ctk.CTkLabel(
            row_view.name_wrap,
            text=team.name,
            font=("Arial", 12),  # blir overskrevet i style-update
        )
        row_view.name_label.pack(side="left")

        row_view.logo_label = logo_label

    def _build_standings_row(
        self,
        parent,
        idx,
        team,
        row_gap,
        row_height,
        row_corner,
        row_font_size,
        row_inner_padx,
        row_inner_pady,
        stat_box_padx,
        stat_box_pady,
        stat_font_size,
        stat_corner,
        logo_size,
    ):
        row_color = "#3a3a3a" if idx <= 4 else "#333333"

        row = ctk.CTkFrame(
            parent,
            fg_color=row_color,
            corner_radius=row_corner,
        )
        row.grid_propagate(False)

        row.grid_columnconfigure(0, weight=1, minsize=26)
        row.grid_columnconfigure(1, weight=1, minsize=34)
        row.grid_columnconfigure(2, weight=6)
        row.grid_columnconfigure(3, weight=1, minsize=34)
        row.grid_columnconfigure(4, weight=1, minsize=34)
        row.grid_columnconfigure(5, weight=1, minsize=34)
        row.grid_rowconfigure(0, weight=1)

        ctk.CTkLabel(
            row,
            text="",
            font=("Arial", row_font_size),
        ).grid(row=0, column=0, padx=row_inner_padx, pady=row_inner_pady, sticky="ns")

        position_label = ctk.CTkLabel(
            row,
            text=str(idx),
            font=("Arial", row_font_size),
        )
        position_label.grid(row=0, column=1, padx=row_inner_padx, pady=row_inner_pady)

        name_wrap = ctk.CTkFrame(row, fg_color="transparent")
        name_wrap.grid(row=0, column=2, padx=row_inner_padx, pady=row_inner_pady, sticky="w")

        placeholder_name_label = ctk.CTkLabel(
            name_wrap,
            text=team.name,
            font=("Arial", row_font_size),
        )
        placeholder_name_label.pack(side="left")

        points_box, points_label = self._create_stat_box(
            row, 0, 3, str(team.points),
            font_size=stat_font_size, corner_radius=stat_corner, padx=stat_box_padx, pady=stat_box_pady
        )
        hit_box, hit_label = self._create_stat_box(
            row, 0, 4, str(team.cups_hit),
            font_size=stat_font_size, corner_radius=stat_corner, padx=stat_box_padx, pady=stat_box_pady
        )
        diff_box, diff_label = self._create_stat_box(
            row, 0, 5, str(team.total_cups_diff),
            font_size=stat_font_size, corner_radius=stat_corner, padx=stat_box_padx, pady=stat_box_pady
        )

        row_view = StandingsRowView(
            frame=row,
            position_label=position_label,
            name_wrap=name_wrap,
            name_label=placeholder_name_label,
            points_label=points_label,
            hit_label=hit_label,
            diff_label=diff_label,
            points_box=points_box,
            hit_box=hit_box,
            diff_box=diff_box,
            logo_label=None,
        )

        self._set_team_name_and_logo(row_view, team, row_color, logo_size)

        return row_view
    
    def _create_stat_box(self, parent, row, column, value, font_size, corner_radius, padx, pady):
        box = ctk.CTkFrame(
            parent,
            fg_color="#1f1f1f",
            corner_radius=corner_radius,
        )
        box.grid(row=row, column=column, padx=padx, pady=pady, sticky="nsew")

        label = ctk.CTkLabel(
            box,
            text=value,
            fg_color="transparent",
            font=("Consolas", font_size, "bold"),
        )
        label.pack(expand=True, fill="both", padx=4, pady=2)

        return box, label
    
    def _update_standings_row_styles(self):
        self.update_idletasks()

        for row_view in self.standings_rows:
            row_height = row_view.frame.winfo_height()

            if row_height <= 1:
                continue

            row_font_size = max(8, min(14, int(row_height * 0.42)))
            stat_font_size = max(7, min(11, int(row_height * 0.32)))
            row_corner = max(4, int(row_height * 0.22))
            stat_corner = max(4, int(row_height * 0.14))

            row_view.frame.configure(corner_radius=row_corner)

            row_view.position_label.configure(font=("Arial", row_font_size))
            row_view.name_label.configure(font=("Arial", row_font_size))
            row_view.points_label.configure(font=("Consolas", stat_font_size, "bold"))
            row_view.hit_label.configure(font=("Consolas", stat_font_size, "bold"))
            row_view.diff_label.configure(font=("Consolas", stat_font_size, "bold"))

            if row_view.points_box is not None:
                row_view.points_box.configure(corner_radius=stat_corner)

            if row_view.hit_box is not None:
                row_view.hit_box.configure(corner_radius=stat_corner)

            if row_view.diff_box is not None:
                row_view.diff_box.configure(corner_radius=stat_corner)

            if row_view.logo_label is not None:
                try:
                    row_view.logo_label.configure(bg=row_view.frame.cget("fg_color"))
                except Exception:
                    pass

    def build_group_stage_standings(self, parent, standings, matches):
        self.standings_parent = parent
        self.standings_rows = []

        available_height = parent.winfo_height()
        row_count = max(1, len(standings))

        title_font_size = max(12, min(20, int(available_height * 0.022)))
        header_font_size = max(8, min(13, int(available_height * 0.013)))
        header_block_height = max(18, int(header_font_size * 1.9))

        # Disse er bare startverdier før vi kjenner faktisk radhøyde
        estimated_row_height = max(24, int(available_height / max(6, row_count + 2)))

        row_font_size = max(8, min(14, int(estimated_row_height * 0.42)))
        stat_font_size = max(7, min(11, int(estimated_row_height * 0.32)))

        row_corner = max(4, int(estimated_row_height * 0.22))
        stat_corner = max(4, int(estimated_row_height * 0.14))

        row_inner_pady = max(0, int(estimated_row_height * 0.05))
        row_inner_padx = max(2, int(estimated_row_height * 0.12))

        stat_box_padx = max(1, int(estimated_row_height * 0.05))
        stat_box_pady = max(2, int(estimated_row_height * 0.12))

        logo_size = max(10, int(estimated_row_height * 0.62))

        self.standings_title_label = ctk.CTkLabel(
            parent,
            text=t("standings"),
            font=("Arial", title_font_size, "bold"),
        )
        self.standings_title_label.pack(pady=(2, 2))

        self.standings_header = self._build_standings_header(parent, header_font_size, header_block_height)

        self.standings_rows_container = ctk.CTkFrame(parent, fg_color="transparent")
        self.standings_rows_container.pack(fill="both", expand=True, padx=4, pady=0)

        rows = self.standings_rows_container

        rows.grid_columnconfigure(0, weight=1)
        for i in range(len(standings)):
            rows.grid_rowconfigure(i, weight=1)

        for idx, team in enumerate(standings, start=1):
            row_view = self._build_standings_row(
                rows,
                idx,
                team,
                row_gap=2,
                row_height=estimated_row_height,
                row_corner=row_corner,
                row_font_size=row_font_size,
                row_inner_padx=row_inner_padx,
                row_inner_pady=row_inner_pady,
                stat_box_padx=stat_box_padx,
                stat_box_pady=stat_box_pady,
                stat_font_size=stat_font_size,
                stat_corner=stat_corner,
                logo_size=logo_size,
            )

            row_view.frame.grid(row=idx - 1, column=0, sticky="nsew", padx=4, pady=2)

            self.standings_rows.append(row_view)

        self.after(10, self._update_standings_row_styles)
        parent.bind("<Configure>", lambda _e: self.after(10, self._update_standings_row_styles))

    def refresh_group_stage_matches(self, parent, matches):
        if self.matches_rows_container is None or not self.matches_rows_container.winfo_exists():
            self.build_group_stage_matches(parent, matches)
            return

        current_count = len(self.matches_row_views)
        new_count = len(matches)

        if current_count != new_count:
            for child in parent.winfo_children():
                child.destroy()

            self.matches_title_label = None
            self.matches_rows_container = None
            self.matches_row_views = []

            self.build_group_stage_matches(parent, matches)
            return

        self.update_group_stage_matches(matches)


    def update_group_stage_matches(self, matches):
        for match, row_view in zip(matches, self.matches_row_views):
            team1_name = match.team1.name if match.team1 else t("tbd")
            team2_name = match.team2.name if match.team2 else t("tbd")
            time_text = match.time if match.time else ""

            row_view.time_label.configure(text=time_text)
            row_view.team1_label.configure(text=team1_name)
            row_view.team2_label.configure(text=team2_name)
            row_view.vs_label.configure(text=t("vs"))

        self.after(10, self._update_match_row_styles)


    def _update_match_row_styles(self):
        self.update_idletasks()

        if self.group_stage_model is None:
            return

        matches = self.group_stage_model.matches

        for match, row_view in zip(matches, self.matches_row_views):
            row_height = row_view.frame.winfo_height()

            if row_height <= 1:
                continue

            time_font_size = max(7, min(11, int(row_height * 0.28)))
            team_font_size = max(7, min(13, int(row_height * 0.36)))
            vs_font_size = max(7, min(13, int(row_height * 0.34)))
            row_corner = max(4, int(row_height * 0.22))
            row_inner_pady = max(0, int(row_height * 0.10))

            row_view.frame.configure(corner_radius=row_corner)
            row_view.time_label.configure(font=("Arial", time_font_size))
            row_view.vs_label.configure(font=("Arial", vs_font_size, "bold"))

            font1 = ("Arial", team_font_size, "overstrike") if match.played and match.winner == 2 else ("Arial", team_font_size)
            font2 = ("Arial", team_font_size, "overstrike") if match.played and match.winner == 1 else ("Arial", team_font_size)

            row_view.team1_label.configure(font=font1, pady=row_inner_pady)
            row_view.team2_label.configure(font=font2, pady=row_inner_pady)


    def _build_match_row(self, parent, match, row_index, estimated_row_height):
        row_corner = max(4, int(estimated_row_height * 0.22))
        row_inner_pady = max(0, int(estimated_row_height * 0.10))
        time_font_size = max(7, min(11, int(estimated_row_height * 0.28)))
        team_font_size = max(7, min(13, int(estimated_row_height * 0.36)))
        vs_font_size = max(7, min(13, int(estimated_row_height * 0.34)))

        row = ctk.CTkFrame(
            parent,
            fg_color="#333333",
            corner_radius=row_corner,
        )
        row.grid(row=row_index, column=0, sticky="nsew", padx=4, pady=1)
        row.grid_columnconfigure(0, weight=2)
        row.grid_columnconfigure(1, weight=4)
        row.grid_columnconfigure(2, weight=1)
        row.grid_columnconfigure(3, weight=4)
        row.grid_rowconfigure(0, weight=1)

        team1_name = match.team1.name if match.team1 else t("tbd")
        team2_name = match.team2.name if match.team2 else t("tbd")
        time_text = match.time if match.time else ""

        font1 = ("Arial", team_font_size, "overstrike") if match.played and match.winner == 2 else ("Arial", team_font_size)
        font2 = ("Arial", team_font_size, "overstrike") if match.played and match.winner == 1 else ("Arial", team_font_size)

        time_label = ctk.CTkLabel(
            row,
            text=time_text,
            font=("Arial", time_font_size),
            text_color="#cccccc",
        )
        time_label.grid(row=0, column=0, padx=4, pady=row_inner_pady, sticky="w")

        team1_label = ctk.CTkLabel(
            row,
            text=team1_name,
            font=font1,
        )
        team1_label.grid(row=0, column=1, padx=4, pady=row_inner_pady, sticky="e")

        vs_label = ctk.CTkLabel(
            row,
            text=t("vs"),
            font=("Arial", vs_font_size, "bold"),
        )
        vs_label.grid(row=0, column=2, padx=4, pady=row_inner_pady)

        team2_label = ctk.CTkLabel(
            row,
            text=team2_name,
            font=font2,
        )
        team2_label.grid(row=0, column=3, padx=4, pady=row_inner_pady, sticky="w")

        return MatchRowView(
            frame=row,
            time_label=time_label,
            team1_label=team1_label,
            vs_label=vs_label,
            team2_label=team2_label,
        )

    def build_group_stage_matches(self, parent, matches):
        self.matches_row_views = []

        available_height = parent.winfo_height()
        row_count = max(1, len(matches))

        title_font_size = max(12, min(20, int(available_height * 0.022)))
        estimated_row_height = max(24, int(available_height / max(6, row_count + 1)))

        self.matches_title_label = ctk.CTkLabel(
            parent,
            text=t("matches"),
            font=("Arial", title_font_size, "bold"),
        )
        self.matches_title_label.pack(pady=(2, 2))

        self.matches_rows_container = ctk.CTkFrame(parent, fg_color="transparent")
        self.matches_rows_container.pack(fill="both", expand=True, padx=4, pady=0)

        rows = self.matches_rows_container
        rows.grid_columnconfigure(0, weight=1)

        for i in range(len(matches)):
            rows.grid_rowconfigure(i, weight=1)

        for row_index, match in enumerate(matches):
            row_view = self._build_match_row(rows, match, row_index, estimated_row_height)
            self.matches_row_views.append(row_view)

        self.after(10, self._update_match_row_styles)
        parent.bind("<Configure>", lambda _e: self.after(10, self._update_match_row_styles))

    def draw_bracket(self):
        self.show_bracket_view()
        self.canvas.delete("all")
        rounds = self.tournament_model.get_rounds()

        if not rounds:
            return

        num_rounds = len(rounds)

        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        if canvas_width < 10 or canvas_height < 10:
            return

        # Skaler etter faktisk canvas-høyde
        scale = canvas_height / 1080
        scale = max(0.75, min(1.6, scale))

        left_margin = int(50 * scale)
        right_margin = int(50 * scale)
        top_margin = int(50 * scale)
        bottom_margin = int(50 * scale)

        box_width = int(300 * scale)
        box_height = int(80 * scale)

        match_font_size = max(10, int(16 * scale))
        logo_size = max(20, int(40 * scale))
        padding = max(2, int(5 * scale))
        line_width = max(1, int(1.4 * scale))
        time_font_size = max(8, int(11 * scale))
        time_offset_y = max(8, int(14 * scale))

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

                team1_name = match.team1.name if match.team1 else t("tbd")
                team2_name = match.team2.name if match.team2 else t("tbd")
                text = f"{team1_name}\n{t('vs')}\n{team2_name}"

                self.canvas.create_text(
                    x,
                    y,
                    text=text,
                    font=("Helvetica", match_font_size),
                    fill="white",
                    justify="center",
                )

                if match.team1 and match.team1.logo:
                    try:
                        img1 = Image.open(match.team1.logo).resize((logo_size, logo_size))
                        img1_tk = ImageTk.PhotoImage(img1)
                        self.canvas.create_image(x0 + logo_size / 2 + padding, y, image=img1_tk)
                        self.images.append(img1_tk)
                    except Exception as e:
                        print(f"Error loading logo {team1_name}: {e}")

                if match.team2 and match.team2.logo:
                    try:
                        img2 = Image.open(match.team2.logo).resize((logo_size, logo_size))
                        img2_tk = ImageTk.PhotoImage(img2)
                        self.canvas.create_image(x1 - logo_size / 2 - padding, y, image=img2_tk)
                        self.images.append(img2_tk)
                    except Exception as e:
                        print(f"Error loading logo {team2_name}: {e}")

                if r > 0:
                    child_index = i * 2
                    parent_x_left = x0

                    for idx_offset in [0, 1]:
                        child_idx = child_index + idx_offset
                        if child_idx < len(positions[r - 1]):
                            child_x, child_y = positions[r - 1][child_idx]
                            child_x_right = child_x + box_width / 2
                            mid_x = (child_x_right + parent_x_left) / 2

                            self.canvas.create_line(
                                child_x_right, child_y, mid_x, child_y,
                                fill="white", width=line_width
                            )
                            self.canvas.create_line(
                                mid_x, child_y, mid_x, y,
                                fill="white", width=line_width
                            )
                            self.canvas.create_line(
                                mid_x, y, parent_x_left, y,
                                fill="white", width=line_width
                            )

                            child_match = rounds[r - 1][child_idx]
                            if child_match.start_time:
                                text_x = (child_x_right + mid_x) / 2
                                text_y = child_y - time_offset_y
                                self.canvas.create_text(
                                    text_x,
                                    text_y,
                                    text=t("starts_at").format(time=child_match.start_time),
                                    font=("Helvetica", time_font_size),
                                    fill="white",
                                )

        self.canvas.config(scrollregion=self.canvas.bbox("all"))

        last_round = rounds[-1]
        if len(last_round) == 1 and last_round[0].winner:
            self.show_winner_popup(last_round[0].winner)

    def refresh_language(self):
        if hasattr(self, "group_stage_model") and self.group_stage_model is not None:
            self.show_group_stage(self.group_stage_model)
        else:
            self.refresh()

    def refresh(self):
        self.draw_bracket()