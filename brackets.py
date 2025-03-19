import customtkinter as ctk
from PIL import Image, ImageTk
import tkinter.filedialog as fd
import tkinter as tk
import math
import random

class TournamentModel:
    def __init__(self):
        self.teams = []
        self.rounds = []  # Hver runde er en liste med kamper

    def build_bracket(self, teams):
        teams_shuffled = teams[:]
        random.shuffle(teams_shuffled)
        self.teams = [{"name": team, "logo": None} for team in teams_shuffled]  # lagres med logo=None foreløpig
        n = len(self.teams)
        power = 2 ** math.ceil(math.log2(n))
        padded_teams = self.teams + [{"name": "BYE", "logo": None}] * (power - n)

        round1 = []
        for i in range(0, len(padded_teams), 2):
            match = {
                "team1": padded_teams[i],
                "team2": padded_teams[i + 1],
                "winner": None,
                "start_time": None
            }
            round1.append(match)
        self.rounds = [round1]

        total_rounds = int(math.log2(power))
        for r in range(2, total_rounds + 1):
            num_matches = power // (2 ** r)
            matches = []
            for i in range(num_matches):
                match = {
                    "team1": None,
                    "team2": None,
                    "winner": None,
                    "start_time": None
                }
                matches.append(match)
            self.rounds.append(matches)


    def set_winner(self, round_index, match_index, winner):
        self.rounds[round_index][match_index]["winner"] = winner
        if round_index + 1 < len(self.rounds):
            next_match_index = match_index // 2
            match = self.rounds[round_index + 1][next_match_index]
            if match["team1"] is None:
                match["team1"] = winner
            elif match["team2"] is None:
                match["team2"] = winner

    def set_start_time(self, round_index, match_index, start_time):
        self.rounds[round_index][match_index]["start_time"] = start_time

    def set_match_teams(self, round_index, match_index, team1, team2):
        self.rounds[round_index][match_index]["team1"] = team1
        self.rounds[round_index][match_index]["team2"] = team2
        self.rounds[round_index][match_index]["winner"] = None
        self.rounds[round_index][match_index]["start_time"] = None

    def get_rounds(self):
        return self.rounds

class TournamentBracketCanvas(ctk.CTkFrame):
    """
    Hovedvinduet som viser braketten på en Canvas i pyramideform.
    Kampene tegnes som rektangler med linjer som forbinder rundene.
    Linjene trekkes i tre segmenter: horisontalt fra barnets boks, så vertikalt, og horisontalt til den nye boksen.
    """
    def __init__(self, master, tournament_model, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.tournament_model = tournament_model
        self.pack(fill="both", expand=True)
        if ctk.get_appearance_mode() == "Dark":
            canvas_bg = "#2B2B2B"
        else:
            canvas_bg = "#FFFFFF"
        self.canvas = tk.Canvas(self, bg=canvas_bg)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda event: self.draw_bracket())

        self.images = []  # Holder referanser til bilder

        self.draw_bracket()
        
    def show_winner_popup(self, winner):
        popup = ctk.CTkToplevel(self)
        popup.title("🏆 Vinner av turnering! 🏆")
        popup.geometry("400x400")

        name_label = ctk.CTkLabel(popup, text=f"Vinneren er:\n{winner['name']}",
                                font=("Arial", 30), pady=20)
        name_label.pack()



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

        box_width = 250
        box_height = 80

        horizontal_spacing = ((canvas_width - left_margin - right_margin - num_rounds * box_width) /
                              (num_rounds - 1)) if num_rounds > 1 else 0

        num_matches_r0 = len(rounds[0])
        vertical_spacing = ((canvas_height - top_margin - bottom_margin - num_matches_r0 * box_height) /
                            (num_matches_r0 - 1)) if num_matches_r0 > 1 else 0

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
                (x, y) = positions[r][i]
                x0, y0 = x - box_width / 2, y - box_height / 2
                x1, y1 = x + box_width / 2, y + box_height / 2
                self.canvas.create_rectangle(x0, y0, x1, y1, fill="gray20", outline="black")

                start_text = f"Start: {match['start_time']}" if match["start_time"] else ""
                self.canvas.create_text(x, y0 - 20, text=start_text, font=("Helvetica", 12), fill="white")

                team1_name = match["team1"]["name"] if match["team1"] else "TBD"
                team2_name = match["team2"]["name"] if match["team2"] else "TBD"
                text = f"{team1_name}\nvs\n{team2_name}"
                self.canvas.create_text(x, y, text=text, font=("Helvetica", 16), fill="white")

                # Tegne logoer
                logo_size = 40
                padding = 5
                if match["team1"] and match["team1"]["logo"]:
                    try:
                        img1 = Image.open(match["team1"]["logo"]).resize((logo_size, logo_size))
                        img1_tk = ImageTk.PhotoImage(img1)
                        self.canvas.create_image(x0 + logo_size / 2 + padding, y, image=img1_tk)
                        self.images.append(img1_tk)
                    except Exception as e:
                        print(f"Feil ved lasting av logo for {team1_name}: {e}")

                if match["team2"] and match["team2"]["logo"]:
                    try:
                        img2 = Image.open(match["team2"]["logo"]).resize((logo_size, logo_size))
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

        self.canvas.config(scrollregion=self.canvas.bbox("all"))

        
        

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
        self.geometry("800x1200")
        team_entry_label = ctk.CTkLabel(self, text="Skriv inn lag (én per linje):")
        team_entry_label.pack(pady=5)
        self.team_text = tk.Text(self, height=20, width=60)
        self.team_text.pack(pady=5)
        self.team_text.insert("1.0", "Lag 1\nLag 2\nLag 3\nLag 4") #\nLag 5\nLag 6\nLag 7\nLag 8\nLag 9\nLag 10\nLag 11\nLag 12\nLag 13\nLag 14\nLag 15\nLag 16
        set_teams_button = ctk.CTkButton(self, text="Bygg Brakett", command=self.build_bracket)
        set_teams_button.pack(pady=5)
        self.match_controls_frame = ctk.CTkFrame(self)
        self.match_controls_frame.pack(fill="both", expand=True, pady=10)
        self.draw_match_controls()



    def build_bracket(self):
        team_names = self.team_text.get("1.0", "end").strip().splitlines()
        teams = []
        for name in team_names:
            logo_path = False #fd.askopenfilename(title=f"Velg logo for {name}", filetypes=[("Image files", ".png .jpg .jpeg .gif")])
            teams.append({"name": name, "logo": logo_path if logo_path else None})

        self.tournament_model.build_bracket([team["name"] for team in teams])

        # Lagre logoene separat
        for i, team in enumerate(self.tournament_model.teams):
            team["logo"] = teams[i]["logo"]

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
                team1 = match["team1"]['name'] if match["team1"] else "TBD"
                team2 = match["team2"]['name'] if match["team2"] else "TBD"
                info_label = ctk.CTkLabel(frame, text=f"Kamp {mi+1}: {team1} vs {team2}")
                info_label.pack(side="left", padx=5)
                if match["winner"]:
                    btn1 = ctk.CTkButton(frame, text=team1, state="disabled")
                    btn2 = ctk.CTkButton(frame, text=team2, state="disabled")
                else:
                    btn1 = ctk.CTkButton(frame, text=team1, command=lambda r=r, mi=mi, t=team1: self.set_winner(r, mi, t))
                    btn2 = ctk.CTkButton(frame, text=team2, command=lambda r=r, mi=mi, t=team2: self.set_winner(r, mi, t))

                start_time = match["start_time"] if match["start_time"] else "Ikke satt"
                btn_time = ctk.CTkButton(frame, text=f"Sett starttid ({start_time})", command=lambda r=r, mi=mi: self.set_start_time(r, mi))
                btn_time.pack(side="right", padx=5)
                btn_edit = ctk.CTkButton(frame, text="Rediger", command=lambda r=r, mi=mi: self.edit_match(r, mi))
                btn_edit.pack(side="right", padx=5)

                btn2.pack(side="right", padx=5)
                btn1.pack(side="right", padx=5)

    def set_winner(self, round_index, match_index, winner_name):
        match = self.tournament_model.rounds[round_index][match_index]

        if match["team1"] and match["team1"]["name"] == winner_name:
            winner = match["team1"]
        elif match["team2"] and match["team2"]["name"] == winner_name:
            winner = match["team2"]
        else:
            winner = {"name": winner_name, "logo": None}

        self.tournament_model.set_winner(round_index, match_index, winner)
        self.draw_match_controls()
        self.bracket_canvas.refresh()


    def set_start_time(self, round_index, match_index):
        popup = ctk.CTkInputDialog(title="Sett starttid", text="Skriv inn starttid (f.eks. HH:MM):")
        new_time = popup.get_input()
        if new_time:
            self.tournament_model.set_start_time(round_index, match_index, new_time)
            self.draw_match_controls()
            self.bracket_canvas.refresh()

    def edit_match(self, round_index, match_index):
        edit_window = ctk.CTkToplevel(self)
        edit_window.title("Rediger kamp")
        match = self.tournament_model.get_rounds()[round_index][match_index]
        team1_current = match["team1"] if match["team1"] is not None else ""
        team2_current = match["team2"] if match["team2"] is not None else ""
        
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

if __name__ == "__main__":
    ctk.set_appearance_mode("Dark")
    root = ctk.CTk()
    root.title("Turneringsbrakett - Hovedvindu")
    tournament_model = TournamentModel()
    bracket_canvas = TournamentBracketCanvas(root, tournament_model)
    control_window = ControlWindow(root, tournament_model, bracket_canvas)
    root.mainloop()
