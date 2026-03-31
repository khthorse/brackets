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
    name_label: ctk.CTkLabel
    points_label: ctk.CTkLabel
    hit_label: ctk.CTkLabel
    diff_label: ctk.CTkLabel
    points_box: Optional[ctk.CTkFrame] = None
    hit_box: Optional[ctk.CTkFrame] = None
    diff_box: Optional[ctk.CTkFrame] = None
    logo_label: Optional[tk.Label] = None

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

        for child in standings_frame.winfo_children():
            child.destroy()
        for child in matches_frame.winfo_children():
            child.destroy()

        standings = self.group_stage_model.standings()
        matches = self.group_stage_model.matches

        self.build_group_stage_standings(standings_frame, standings, matches)
        self.build_group_stage_matches(matches_frame, matches)

    def show_group_stage(self, group_stage_model):
        self.group_stage_model = group_stage_model
        self.show_group_stage_view()

        for child in self.group_stage_view.winfo_children():
            child.destroy()

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

        # Rebuild når layout er klar
        self._schedule_group_stage_rebuild(delay=30)

        # Rebuild ved resize, men debounce-et
        standings_frame.bind("<Configure>", lambda _e: self._schedule_group_stage_rebuild(delay=60))
        matches_frame.bind("<Configure>", lambda _e: self._schedule_group_stage_rebuild(delay=60))
        
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
        row.pack(fill="both", padx=4, pady=row_gap, expand=True)
        row.pack_propagate(False)
        #row.grid_propagate(False)

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

        logo_label = None
        if team.logo and row_height >= 18:
            try:
                img = Image.open(team.logo)
                img.thumbnail((logo_size, logo_size), Image.LANCZOS)
                logo_img = ImageTk.PhotoImage(img)
                self.images.append(logo_img)

                logo_label = tk.Label(
                    name_wrap,
                    image=logo_img,
                    bg=row_color,
                    bd=0,
                    highlightthickness=0,
                )
                logo_label.image = logo_img
                logo_label.pack(side="left", padx=(0, 4))
            except Exception as e:
                print(f"Error loading logo: {e}")

        name_label = ctk.CTkLabel(
            name_wrap,
            text=team.name,
            font=("Arial", row_font_size),
        )
        name_label.pack(side="left")

        points_label = self._create_stat_box(
            row, 0, 3, str(team.points),
            font_size=stat_font_size, corner_radius=stat_corner, padx=stat_box_padx, pady=stat_box_pady
        )
        hit_label = self._create_stat_box(
            row, 0, 4, str(team.cups_hit),
            font_size=stat_font_size, corner_radius=stat_corner, padx=stat_box_padx, pady=stat_box_pady
        )
        diff_label = self._create_stat_box(
            row, 0, 5, str(team.total_cups_diff),
            font_size=stat_font_size, corner_radius=stat_corner, padx=stat_box_padx, pady=stat_box_pady
        )

        return StandingsRowView(
            frame=row,
            position_label=position_label,
            name_label=name_label,
            points_label=points_label,
            hit_label=hit_label,
            diff_label=diff_label,
            logo_label=logo_label,
        )
    
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

    def build_group_stage_standings(self, parent, standings, matches):
        self.standings_parent = parent
        self.standings_rows = []

        available_height = parent.winfo_height()
        row_count = max(1, len(standings))

        # Toppområde
        title_font_size = max(12, min(20, int(available_height * 0.022)))
        header_font_size = max(8, min(13, int(available_height * 0.013)))
        header_block_height = max(18, int(header_font_size * 1.9))

        # Vertikal spacing
        outer_padding = 1
        row_gap = 2

        # Hold høydeberegningen enkel og stabil
        top_area = 50
        usable_height = max(60, available_height - top_area)

        row_height = usable_height // row_count
        row_height = max(9, min(100, row_height))
        row_height = row_height

        # Alt inni radene skaleres fra row_height
        row_font_size = max(8, min(14, int(row_height * 0.42)))
        stat_font_size = max(7, min(11, int(row_height * 0.32)))

        row_corner = max(4, int(row_height * 0.22))
        stat_corner = max(2, int(row_height * 0.14))

        row_inner_pady = max(0, int(row_height * 0.05))
        row_inner_padx = max(2, int(row_height * 0.12))

        stat_box_padx = max(1, int(row_height * 0.05))
        stat_box_pady = max(2, int(row_height * 0.12))

        logo_size = max(10, int(row_height * 0.62))

        title = ctk.CTkLabel(
            parent,
            text=t("standings"),
            font=("Arial", title_font_size, "bold"),
        )
        title.pack(pady=(2, 2))

        self._build_standings_header(parent, header_font_size, header_block_height)

        rows = ctk.CTkFrame(parent, fg_color="transparent")
        rows.pack(fill="both", expand=True, padx=4, pady=0)

        for idx, team in enumerate(standings, start=1):
            row_view = self._build_standings_row(
                rows,
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
            )
            self.standings_rows.append(row_view)
            
    def build_group_stage_matches(self, parent, matches):
        available_height = parent.winfo_height()
        row_count = max(1, len(matches))

        title_font_size = max(12, min(20, int(available_height * 0.022)))
        title_block_height = max(22, int(title_font_size * 1.5))

        outer_padding = 4
        row_gap = 1

        reserved_height = (
            title_block_height
            + outer_padding * 2
            + row_count * (row_gap * 2)
        )

        usable_height = max(60, available_height - reserved_height)
        row_height = usable_height // row_count
        row_height = max(14, min(52, row_height))

        time_font_size = max(7, min(11, int(row_height * 0.28)))
        team_font_size = max(7, min(13, int(row_height * 0.36)))
        vs_font_size = max(7, min(13, int(row_height * 0.34)))
        row_corner = max(4, int(row_height * 0.22))
        row_inner_pady = max(0, int(row_height * 0.10))
        print("Matches")
        print("available_height:", available_height)
        print("title_block_height:", title_block_height)
        print("reserved_height:", reserved_height)
        print("usable_height:", max(60, available_height - reserved_height))
        print("row_count: ", row_count)
        print("row height: ", row_height)

        title = ctk.CTkLabel(
            parent,
            text=t("matches"),
            font=("Arial", title_font_size, "bold"),
        )
        title.pack(pady=(2, 2))

        rows = ctk.CTkFrame(parent, fg_color="transparent")
        rows.pack(fill="both", expand=True, padx=4, pady=0)

        for match in matches:
            row = ctk.CTkFrame(
                rows,
                fg_color="#333333",
                corner_radius=row_corner,
                height=row_height,
            )
            row.pack(fill="x", padx=4, pady=row_gap, expand=True)
            row.pack_propagate(False)

            row.grid_columnconfigure(0, weight=2)
            row.grid_columnconfigure(1, weight=4)
            row.grid_columnconfigure(2, weight=1)
            row.grid_columnconfigure(3, weight=4)

            team1_name = match.team1.name if match.team1 else t("tbd")
            team2_name = match.team2.name if match.team2 else t("tbd")
            time_text = match.time if match.time else ""

            font1 = ("Arial", team_font_size, "overstrike") if match.played and match.winner == 2 else ("Arial", team_font_size)
            font2 = ("Arial", team_font_size, "overstrike") if match.played and match.winner == 1 else ("Arial", team_font_size)

            ctk.CTkLabel(
                row,
                text=time_text,
                font=("Arial", time_font_size),
                text_color="#cccccc",
            ).grid(row=0, column=0, padx=4, pady=row_inner_pady, sticky="w")

            ctk.CTkLabel(
                row,
                text=team1_name,
                font=font1,
            ).grid(row=0, column=1, padx=4, pady=row_inner_pady, sticky="e")

            ctk.CTkLabel(
                row,
                text=t("vs"),
                font=("Arial", vs_font_size, "bold"),
            ).grid(row=0, column=2, padx=4, pady=row_inner_pady)

            ctk.CTkLabel(
                row,
                text=team2_name,
                font=font2,
            ).grid(row=0, column=3, padx=4, pady=row_inner_pady, sticky="w")

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