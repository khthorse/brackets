import customtkinter as ctk
import tkinter as tk

from PIL import Image, ImageTk

from translations import t

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

    def show_group_stage(self, group_stage_model):
        self.canvas.delete("all")
        self.images.clear()

        standings = group_stage_model.standings()
        matches = group_stage_model.matches

        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        if canvas_width < 10 or canvas_height < 10 or not standings:
            return

        scale = canvas_height / 1080
        scale = max(0.75, min(1.6, scale))

        title_font = max(18, int(30 * scale))
        section_font = max(14, int(24 * scale))

        start_y = int(80 * scale)
        box_pady = max(3, int(5 * scale))
        box_padx = max(6, int(10 * scale))

        box_height = (canvas_height - start_y - 2 * box_pady) / len(standings)
        box_width = (canvas_width / 2) - 2 * box_padx
        box2_width = (canvas_width * 4 / 10) - 2 * box_padx

        thumbnail_size = max(18, int(box_height - 4 * box_pady))
        fontsize = max(10, int(min(box_height / 4, 22 * scale)))
        small_fontsize = max(8, int(fontsize * 3 / 4))
        time_fontsize = max(8, int(fontsize * 4 / 5))

        self.canvas.create_text(
            canvas_width / 2,
            int(30 * scale),
            text=t("group_stage"),
            font=("Arial", title_font),
            fill="white",
        )

        self.canvas.create_text(
            canvas_width / 4,
            start_y - 6 * box_pady,
            text=t("standings"),
            font=("Arial", section_font),
            fill="white",
        )

        for idx, team in enumerate(standings, start=1):
            box_x0 = box_padx
            box_y0 = start_y + box_pady + (idx - 1) * box_height
            box_x1 = box_width - box_padx
            box_y1 = box_y0 - box_pady + box_height

            self.canvas.create_rectangle(box_x0, box_y0, box_x1, box_y1, fill="#333333")

            text_ypos = box_y1 + box_pady - box_height / 2
            teamname_x = box_width / 4
            results_x = 3 * box_width / 4

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
                text=f"{t('points_hit_diff_header')}\n{team.points}    |    {team.cups_hit}    |    {team.total_cups_diff}",
                font=("Arial", fontsize),
                fill="white",
                justify="left",
            )

            if team.logo:
                try:
                    img = Image.open(team.logo)
                    img.thumbnail((thumbnail_size, thumbnail_size), Image.LANCZOS)
                    logo_img = ImageTk.PhotoImage(img)
                    self.canvas.create_image(
                        box_width / 8,
                        text_ypos - box_pady / 2,
                        image=logo_img,
                    )
                    self.images.append(logo_img)
                except Exception as e:
                    print(f"Error loading logo: {e}")

        matches_start_y = start_y
        matches_start_x = box_width + 0.5 * box_width + 2 * box_padx - box2_width / 2

        self.canvas.create_text(
            3 * canvas_width / 4,
            matches_start_y - 6 * box_pady,
            text=t("matches"),
            font=("Arial", section_font),
            fill="white",
        )

        for idx, match in enumerate(matches, start=1):
            box_x0 = matches_start_x + box_padx
            box_y0 = start_y + box_pady + (idx - 1) * box_height
            box_x1 = matches_start_x + box2_width - box_padx
            box_y1 = box_y0 - box_pady + box_height

            self.canvas.create_rectangle(box_x0, box_y0, box_x1, box_y1, fill="#333333")

            time_ypos = box_y1 + box_pady - box_height / 2 - box_height / 4
            text_ypos = box_y1 + box_pady - box_height / 2
            teamname1_x = matches_start_x + box2_width / 4 + thumbnail_size
            teamname2_x = matches_start_x + 3 * box2_width / 4 - thumbnail_size
            center_x = matches_start_x + box2_width / 2

            team1_name = match.team1.name if match.team1 else t("tbd")
            team2_name = match.team2.name if match.team2 else t("tbd")

            if match.time:
                y_match = text_ypos + box_height / 6

                if match.played:
                    self.canvas.create_text(
                        teamname1_x,
                        y_match,
                        text=team1_name,
                        font=("Arial", small_fontsize, "overstrike"),
                        fill="white",
                        justify="left",
                    )
                    self.canvas.create_text(
                        center_x,
                        y_match,
                        text=t("vs"),
                        font=("Arial", fontsize),
                        fill="white",
                    )
                    self.canvas.create_text(
                        teamname2_x,
                        y_match,
                        text=team2_name,
                        font=("Arial", small_fontsize),
                        fill="white",
                        justify="right",
                    )
                else:
                    self.canvas.create_text(
                        teamname1_x,
                        y_match,
                        text=team1_name,
                        font=("Arial", small_fontsize),
                        fill="white",
                        justify="left",
                    )
                    self.canvas.create_text(
                        center_x,
                        y_match,
                        text=t("vs"),
                        font=("Arial", fontsize),
                        fill="white",
                    )
                    self.canvas.create_text(
                        teamname2_x,
                        y_match,
                        text=team2_name,
                        font=("Arial", small_fontsize),
                        fill="white",
                        justify="right",
                    )

                self.canvas.create_text(
                    center_x,
                    time_ypos,
                    text=t("starts_at").format(time=match.time),
                    font=("Arial", time_fontsize),
                    fill="white",
                )
            else:
                self.canvas.create_text(
                    teamname1_x,
                    text_ypos,
                    text=team1_name,
                    font=("Arial", small_fontsize),
                    fill="white",
                    justify="left",
                )
                self.canvas.create_text(
                    center_x,
                    text_ypos,
                    text=t("vs"),
                    font=("Arial", fontsize),
                    fill="white",
                )
                self.canvas.create_text(
                    teamname2_x,
                    text_ypos,
                    text=team2_name,
                    font=("Arial", small_fontsize),
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
                    print(f"Error loading logo: {e}")

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
                    print(f"Error loading logo: {e}")

    def draw_bracket(self):
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

    def refresh(self):
        self.draw_bracket()