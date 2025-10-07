import customtkinter as ctk
from PIL import Image, ImageTk
import tkinter.filedialog as fd
import tkinter as tk
import math
import random
import os, csv
from pathlib import Path

class TournamentModel:
    def __init__(self):
        self.loaded_teams = []  # [{"name": ..., "logo": ...}, ...]
        self.teams = []
        self.rounds = []  # Hver runde er en liste med kamper

    def build_bracket(self, teams_input):

        team_objs = []
        for item in teams_input:
            if isinstance(item, dict):
                name = str(item.get("name", "")).strip()
                logo = item.get("logo")
            else:
                name = str(item).strip()
                logo = None
            if not name:
                continue
            team_objs.append({"name": name, "logo": logo})

        teams_shuffled = team_objs[:]
        random.shuffle(teams_shuffled)
        self.teams = teams_shuffled

        n = len(self.teams)
        size = 1
        while size < n:
            size *= 2

        seeds = self.teams + [None] * (size - n)
        first_round = []
        for i in range(0, size, 2):
            first_round.append({"team1": seeds[i], "team2": seeds[i+1], "winner": None, "start_time": None})
        self.rounds = [first_round]

        rsize = size // 2
        while rsize >= 1:
            matches = []
            for _ in range(rsize // 2):
                matches.append({"team1": None, "team2": None, "winner": None, "start_time": None})
            if rsize // 2 > 0:
                self.rounds.append(matches)
            rsize //= 2


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

class GroupStageModel:
    def __init__(self, teams):
        self.teams = []
        for team in teams:
            self.teams.append({
                "name": team["name"],
                "logo": team.get("logo"),
                "wins": 0,
                "cups_hit": 0,
                "cups_missed": 0,
                "total_cups_diff": 0
            })
        self.matches = []

    def generate_matches(self):
        teams_shuffled = self.teams[:]
        random.shuffle(teams_shuffled)
        
        n = len(teams_shuffled)
        assert n % 2 == 0, "Antall lag bør være partall for dette oppsettet."
        
        # Sørg for at ingen møter samme motstander to ganger
        round1 = []
        for i in range(0, n, 2):
            round1.append({"team1": teams_shuffled[i], "team2": teams_shuffled[i+1], 
                           "team1_cups_left": None, "team2_cups_left": None, "time": None, "played":False})

        # Lag en ny tilfeldig rekkefølge og sørg for unike kamper
        round2 = []
        valid_round = False
        while not valid_round:
            random.shuffle(teams_shuffled)
            round2 = [{"team1": teams_shuffled[i], "team2": teams_shuffled[i+1],
                       "team1_cups_left": None, "team2_cups_left": None, "time": None, "played":False}
                      for i in range(0, n, 2)]
            # sjekk at ingen par går igjen fra runde 1
            valid_round = all(
                set((m["team1"]["name"], m["team2"]["name"])) not in 
                [set((m1["team1"]["name"], m1["team2"]["name"])) for m1 in round1]
                for m in round2
            )

        self.matches = round1 + round2

    def update_match_result(self, match_index, cups_left_team1, cups_left_team2, winner):
        match = self.matches[match_index]

        # Rull tilbake gammelt resultat hvis kampen var spilt
        if match.get("played"):
            prev_c1 = match.get("team1_cups_left")
            prev_c2 = match.get("team2_cups_left")
            prev_w  = match.get("winner")
            if prev_c1 is not None and prev_c2 is not None and prev_w in (1, 2):
                self._apply_result(match, prev_c1, prev_c2, prev_w, sign=-1)

        # Lagre nytt resultat og påfør
        match["team1_cups_left"] = cups_left_team1
        match["team2_cups_left"] = cups_left_team2
        match["winner"] = winner
        self._apply_result(match, cups_left_team1, cups_left_team2, winner, sign=+1)
        match["played"] = True


    def standings(self):
        return sorted(self.teams, key=lambda x: (
            -x["wins"], -x["cups_hit"], -x["total_cups_diff"]
        ))
    
    def _apply_result(self, match, cups_left_team1, cups_left_team2, winner, sign=+1):
        """Påfør (sign=+1) eller rull tilbake (sign=-1) et resultat i tabellen."""
        team1 = next(t for t in self.teams if t["name"] == match["team1"]["name"])
        team2 = next(t for t in self.teams if t["name"] == match["team2"]["name"])

        cups_hit_team1 = 10 - cups_left_team2
        cups_hit_team2 = 10 - cups_left_team1

        # Poeng
        if cups_left_team1 != cups_left_team2:
            if cups_left_team1 > cups_left_team2 and winner == 1:
                team1['wins'] += 2 * sign
            elif cups_left_team1 < cups_left_team2 and winner == 2:
                team2['wins'] += 2 * sign
            else:
                raise ValueError("Ugyldig kombinasjon av kopper/vinner")
        else:
            team1['wins'] += 1 * sign
            team2['wins'] += 1 * sign
            if winner == 1 and cups_left_team1 == cups_hit_team2:
                team1['wins'] += 1 * sign
            elif winner == 2 and cups_left_team1 == cups_hit_team2:
                team2['wins'] += 1 * sign
            else:
                raise ValueError("Ugyldig tie-break kombinasjon")

        # Statistikk
        team1["cups_hit"]    += cups_hit_team1 * sign
        team1["cups_missed"] += cups_hit_team2 * sign
        team1["total_cups_diff"] = team1["cups_hit"] - team1["cups_missed"]

        team2["cups_hit"]    += cups_hit_team2 * sign
        team2["cups_missed"] += cups_hit_team1 * sign
        team2["total_cups_diff"] = team2["cups_hit"] - team2["cups_missed"]

    def clear_match_result(self, match_index):
        match = self.matches[match_index]
        if not match.get("played"):
            return
        prev_c1 = match.get("team1_cups_left")
        prev_c2 = match.get("team2_cups_left")
        prev_w  = match.get("winner")
        if prev_c1 is not None and prev_c2 is not None and prev_w in (1, 2):
            self._apply_result(match, prev_c1, prev_c2, prev_w, sign=-1)

        match["team1_cups_left"] = None
        match["team2_cups_left"] = None
        match["winner"] = None
        match["played"] = False



class TournamentBracketCanvas(ctk.CTkFrame):
    """
    Hovedvinduet som viser braketten på en Canvas i pyramideform.
    Kampene tegnes som rektangler med linjer som forbinder rundene.
    Linjene trekkes i tre segmenter: horisontalt fra barnets boks, så vertikalt, og horisontalt til den nye boksen.
    """
    def __init__(self, master, tournament_model, *args, **kwargs):
        super().__init__(master, *args, border_width=0, fg_color='#2b2b2b', **kwargs)
        self.tournament_model = tournament_model
        self.pack(fill="both", expand=True)
        canvas_bg = "#2B2B2B"
            
        self.canvas = tk.Canvas(self, bg=canvas_bg, highlightthickness=0, bd=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda event: self.draw_bracket())

        self.images = []  # Holder referanser til bilder

        self.draw_bracket()
        
    def show_winner_popup(self, winner):
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        self.canvas.delete('all')
        self.canvas.create_text(canvas_width/2, canvas_height/2 - 300, text= f'🏆 Vinner av turnering! 🏆', font=('Arial', 60), fill='white')
        self.canvas.create_text(canvas_width/2, canvas_height/2 - 200, text= f'{winner['name']}', font=('Arial', 60), fill='white')
        if winner["logo"]:
            try:
                img = Image.open(winner["logo"])
                img.thumbnail((canvas_height/3, canvas_height/3), Image.LANCZOS)
                logo_img = ImageTk.PhotoImage(img)
                self.canvas.create_image(canvas_width / 2, canvas_height/2 + canvas_height/6, image=logo_img)
                self.images.append(logo_img)
            except Exception as e:
                print(f"Feil ved lasting av logo: {e}")

    def show_group_stage(self, group_stage_model):
        self.canvas.delete("all")  # tøm eksisterende brackets
        self.images.clear()
        
        standings = group_stage_model.standings()
        matches = group_stage_model.matches

        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        

        # Vis tittel
        self.canvas.create_text(canvas_width / 2, 30, text="Gruppespill", font=("Arial", 30), fill="White")

        # Verdier for bokser som brukes i tabellene
        start_y = 80
        box_pady = 5
        box_padx = 10
        box_height = ((canvas_height-start_y-2*box_pady)/len(standings))
        box_width = (canvas_width/2) - 2*box_padx
        box2_width = (canvas_width*4/10) - 2*box_padx
        thumbnail_size = box_height-4*box_pady
        
        # Vis tabellen til venstre
        
        self.canvas.create_text(canvas_width / 4, start_y - 6*box_pady, text="Tabell", font=("Arial", 24), fill="white")
        for idx, team in enumerate(standings, start=1):
            
            box_x0, box_y0 = box_padx, start_y + box_pady + (idx-1)*box_height
            box_x1, box_y1 = box_width - box_padx, box_y0-box_pady + box_height
            
            self.canvas.create_rectangle(box_x0, box_y0, box_x1, box_y1, fill='#333333')
            text_ypos = box_y1 + box_pady - box_height/2
            teamname_x = box_width/4
            results_x = 3*box_width/4
            fontsize = int(box_height/4)
            
            self.canvas.create_text(teamname_x, text_ypos, text=f'{idx}. {team['name']}', font=('Arial', fontsize), fill='white', anchor='w')
            self.canvas.create_text(results_x, text_ypos, text=f'V    |    T    |    D\n{team['wins']}    |    {team['cups_hit']}    |    {team['total_cups_diff']}', font=('Arial', fontsize), fill='white', justify='left')

            
            # Logoer
            if team["logo"]:
                try:
                    img = Image.open(team["logo"])
                    img.thumbnail((thumbnail_size, thumbnail_size), Image.LANCZOS)
                    logo_img = ImageTk.PhotoImage(img)
                    self.canvas.create_image(box_width/8, text_ypos-box_pady/2, image=logo_img)
                    self.images.append(logo_img)
                except Exception as e:
                    print(f"Feil ved lasting av logo: {e}")

        # Vis kamper til høyre
        matches_start_y = 80
        matches_start_x = box_width + 1/2*box_width + 2*box_padx - box2_width/2
        
        
        self.canvas.create_text(3 * canvas_width / 4, matches_start_y - 6*box_pady, text="Kamper", font=("Arial", 24), fill="white")
        for idx, match in enumerate(matches, start=1):
            
            box_x0, box_y0 = matches_start_x + box_padx, start_y + box_pady + (idx-1)*box_height
            box_x1, box_y1 = matches_start_x + box2_width - box_padx, box_y0-box_pady + box_height
            
            self.canvas.create_rectangle(box_x0, box_y0, box_x1, box_y1, fill='#333333')
            time_ypos = box_y1 + box_pady - box_height/2 - box_height/4
            text_ypos = box_y1 + box_pady - box_height/2
            teamname1_x = matches_start_x + box2_width/4 + thumbnail_size
            teamname2_x = matches_start_x + 3*box2_width/4 - thumbnail_size
            
            if match['time']:
                if match['played']:
                    self.canvas.create_text(teamname1_x, text_ypos + box_height/6, text=f'{match['team1']['name']}', font=('Arial overstrike', int(fontsize*3/4)), fill='white', justify='left')
                    self.canvas.create_text(matches_start_x + box2_width/2, text_ypos + box_height/6, text=f'vs', font=('Arial', fontsize), fill='white')
                    self.canvas.create_text(teamname2_x, text_ypos + box_height/6, text=f'{match['team2']['name']}', font=('Arial', int(fontsize*3/4)), fill='white', justify='right')
                else:
                    self.canvas.create_text(teamname1_x, text_ypos + box_height/6, text=f'{match['team1']['name']}', font=('Arial', int(fontsize*3/4)), fill='white', justify='left')
                    self.canvas.create_text(matches_start_x + box2_width/2, text_ypos + box_height/6, text=f'vs', font=('Arial', fontsize), fill='white')
                    self.canvas.create_text(teamname2_x, text_ypos + box_height/6, text=f'{match['team2']['name']}', font=('Arial', int(fontsize*3/4)), fill='white', justify='right')

                # Legg inn tidspunkt
                self.canvas.create_text(matches_start_x + box2_width/2, time_ypos, text=f'Starter: {match['time']}', font=('Arial', int(fontsize*4/5)), fill='white')
                
            else:
                # Tegn kamper
                self.canvas.create_text(teamname1_x, text_ypos, text=f'{match['team1']['name']}', font=('Arial', int(fontsize*3/4)), fill='white', justify='left')
                self.canvas.create_text(matches_start_x + box2_width/2, text_ypos, text=f'vs', font=('Arial', fontsize), fill='white')
                self.canvas.create_text(teamname2_x, text_ypos, text=f'{match['team2']['name']}', font=('Arial', int(fontsize*3/4)), fill='white', justify='right')
                    
                    
                    
                    
            # Logoer
            if match['team1']['logo']:
                try:
                    img = Image.open(match['team1']['logo'])
                    img.thumbnail((thumbnail_size, thumbnail_size), Image.LANCZOS)
                    logo_img = ImageTk.PhotoImage(img)
                    self.canvas.create_image(matches_start_x + box2_width/8, text_ypos-box_pady/2, image=logo_img)
                    self.images.append(logo_img)
                except Exception as e:
                    print(f"Feil ved lasting av logo: {e}")
            
            if match['team2']['logo']:
                try:
                    img = Image.open(match['team2']['logo'])
                    img.thumbnail((thumbnail_size, thumbnail_size), Image.LANCZOS)
                    logo_img = ImageTk.PhotoImage(img)
                    self.canvas.create_image(matches_start_x + box2_width*7/8, text_ypos-box_pady/2, image=logo_img)
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

                start_text = f"Starter: {match['start_time']}" if match["start_time"] else ""
                self.canvas.create_text(x, y0 - 20, text=start_text, font=("Helvetica", 12), fill="white")

                team1_name = match["team1"]["name"] if match["team1"] else "TBD"
                team2_name = match["team2"]["name"] if match["team2"] else "TBD"
                text = f"{team1_name}\nvs\n{team2_name}"
                self.canvas.create_text(x, y, text=text, font=("Helvetica", 16), fill="white", justify='center')

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

        last_round = rounds[-1]
        if len(last_round) == 1 and last_round[0]["winner"]:
            self.show_winner_popup(last_round[0]["winner"])
            

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
        self.team_text.insert("1.0", "Lag 1\nLag 2\nLag 3\nLag 4\nLag 5\nLag 6\nLag 7\nLag 8\nLag 9\nLag 10\nLag 11\nLag 12\nLag 13\nLag 14\nLag 15\nLag 16")  
        
        set_teams_button = ctk.CTkButton(self, text="Bygg Brakett", command=self.build_bracket)
        set_teams_button.pack(pady=5)

        load_from_file_btn = ctk.CTkButton(self, text="Last lag fra fil...", command=self.load_teams_from_file)
        load_from_file_btn.pack(pady=5)

        
        self.logo_switch = False
        load_logo_checkbox = ctk.CTkCheckBox(self, text="Legg til laglogoer", command=self.toggle_load_logo)
        load_logo_checkbox.pack(pady=5)
        
        self.start_group_button = ctk.CTkButton(self, text="Start Gruppespill", command=self.start_group_stage)
        self.start_bracket_button = ctk.CTkButton(self, text="Start Sluttspill", command=self.build_final_bracket)
        self.start_bracket_button.pack_forget()  # skjul til å starte med

        self.start_group_button.pack(pady=5)
        self.match_controls_frame = ctk.CTkScrollableFrame(self)
        self.match_controls_frame.pack(fill="both", expand=True, pady=10)
        self.draw_match_controls()
        self.teams = []

    def build_final_bracket(self):
        standings = self.group_stage_model.standings()
        top_4 = standings[:4]
        self.tournament_model.build_bracket([team["name"] for team in top_4])

        # lagre logoer og statistikk
        for i, team in enumerate(self.tournament_model.teams):
            team["logo"] = top_4[i]["logo"]
            team["wins"] = top_4[i]["wins"]
            team["cups_hit"] = top_4[i]["cups_hit"]
            team["total_cups_diff"] = top_4[i]["total_cups_diff"]

        self.bracket_canvas.refresh()
        self.draw_match_controls()
        # skjul sluttspillknappen når brackets er laget
        self.start_bracket_button.pack_forget()

    def toggle_load_logo(self):
        if self.logo_switch:
            self.logo_switch = False
        else:
            self.logo_switch = True
            
    def check_allowed_cup_number(self, cups):
        if cups > 10 or cups < 0:
            raise ValueError
            
            
    def set_group_winner_popup(self, match_index, winner):
        match = self.group_stage_model.matches[match_index]
        team1_name = match['team1']['name']
        team2_name = match['team2']['name']

        # Én dialog med to inputfelt
        top = ctk.CTkToplevel(self)
        top.title("Antall kopper igjen")
        top.geometry("320x240")

        ctk.CTkLabel(top, text=f"{team1_name} kopper igjen (0–10):").pack(pady=(12, 4))
        e1 = ctk.CTkEntry(top, width=120)
        e1.pack(pady=4)

        ctk.CTkLabel(top, text=f"{team2_name} kopper igjen (0–10):").pack(pady=(12, 4))
        e2 = ctk.CTkEntry(top, width=120)
        e2.pack(pady=4)

        # Feilmelding-etikett (vises ved behov)
        err_lbl = ctk.CTkLabel(top, text="", text_color="tomato")
        err_lbl.pack(pady=(6, 0))

        # Hjelper: forsøk å lagre
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
                # (valgfritt) oppdater kontrollrader hvis du viser “rediger/angre”-knapper:
                if hasattr(self, "draw_group_match_controls"):
                    self.draw_group_match_controls()

                top.destroy()
            except ValueError:
                err_lbl.configure(text="Ugyldig antall/kombo. Prøv igjen.")

        # Knapper
        btn_row = ctk.CTkFrame(top)
        btn_row.pack(pady=12)
        ctk.CTkButton(btn_row, text="Avbryt", command=top.destroy).pack(side="left", padx=6)
        ctk.CTkButton(btn_row, text="Lagre", command=do_save).pack(side="left", padx=6)

        # Enter = lagre, Esc = avbryt
        e1.bind("<Return>", do_save)
        e2.bind("<Return>", do_save)
        top.bind("<Escape>", lambda _e: top.destroy())

        # Gjør dialogen modal
        top.grab_set()
        top.focus()
        e1.focus()
        top.wait_window()


    def _parse_team_file(self, filepath: str):
        """Leser fil med lag og valgfrie logostier. Støtter CSV (name,logo) og linjer med , ; | TAB."""
        teams = []
        base = Path(filepath).parent

        def split_smart(line: str):
            # Prøv CSV først
            try:
                for row in csv.reader([line]):
                    return [s.strip() for s in row]
            except Exception:
                pass
            # Fallback: manuell splitting på vanlige delimitere
            for delim in [",", ";", "|", "\t"]:
                if delim in line:
                    return [s.strip() for s in line.split(delim)]
            return [line.strip()]

        with open(filepath, "r", encoding="utf-8-sig") as f:
            lines = f.read().splitlines()

        # Hopp over header hvis den ser ut som "name,logo"
        if lines and ("name" in lines[0].lower() and "logo" in lines[0].lower()):
            lines = lines[1:]

        for raw in lines:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            parts = split_smart(line)
            if len(parts) == 1:
                name = parts[0]
                logo = None
            else:
                name, logo = parts[0], (parts[1] or None)

            if not name:
                continue

            # Normaliser/absolutt sti til logo hvis oppgitt
            if logo:
                p = Path(logo).expanduser()
                if not p.is_absolute():
                    p = (base / p).resolve()
                logo = str(p)
                # (valgfritt) ikke krav: sjekk om fila finnes
                # if not Path(logo).is_file(): logo = None

            teams.append({"name": name, "logo": logo})
        return teams

    def _teams_from_textbox(self):
        """Fallback når bruker har skrevet navn i tekstfeltet – ingen logo."""
        names = [ln.strip() for ln in self.team_text.get("1.0", "end").splitlines() if ln.strip()]
        return [{"name": n, "logo": None} for n in names]
    
    def load_teams_from_file(self):
        path = fd.askopenfilename(
            title="Velg lag-fil",
            filetypes=[("CSV/Tekst", "*.csv *.txt *.tsv"), ("Alle filer", "*.*")]
        )
        if not path:
            return
        try:
            # Les inn og lagre i self.teams
            self.teams = self._parse_team_file(path)
            if not self.teams:
                raise ValueError("Fant ingen lag i fila.")

            # Vis bare navnene i tekstboksen som en “preview”
            self.team_text.delete("1.0", "end")
            self.team_text.insert("1.0", "\n".join(t["name"] for t in self.teams))

            # Liten bekreftelse
            ok = ctk.CTkToplevel(self)
            ok.title("Lag lastet")
            ctk.CTkLabel(ok, text=f"Lastet {len(self.teams)} lag fra fil.").pack(padx=20, pady=14)
            try:
                # Hvis du har plasseringshjelperen fra tidligere:
                self._place_dialog_over(ok, width=260, height=90)
            except Exception:
                pass
        except Exception as e:
            err = ctk.CTkToplevel(self)
            err.title("Feil")
            ctk.CTkLabel(err, text=f"Kunne ikke lese filen.\n{e}").pack(padx=20, pady=20)
            try:
                self._place_dialog_over(err, width=320, height=120)
            except Exception:
                pass



    def start_group_stage(self):
        # Sørg for at listen med teams fylles først
        if not self.teams: 
            self.fill_team_list()

        team_list = [{"name": team["name"], "logo": team["logo"]} for team in self.teams]
        self.group_stage_model = GroupStageModel(team_list)
        self.group_stage_model.generate_matches()

        # Vis gruppespillet direkte i bracket_canvas
        self.bracket_canvas.show_group_stage(self.group_stage_model)

        # Tegn riktige kampkontroller for gruppespill (du må lage denne!)
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

            t1 = match['team1']['name']
            t2 = match['team2']['name']
            ctk.CTkLabel(row, text=f"{t1} vs {t2}").pack(side="left", padx=6)

            # Knappene lages alltid, men evt. deaktiveres hvis match er spilt
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

            # Rediger/angre vises kun når kampen er spilt
            if match.get("played"):
                ctk.CTkButton(
                    row, text="Rediger resultat",
                    command=lambda i=idx: self.edit_group_result(i)
                ).pack(side="right", padx=4)

                ctk.CTkButton(
                    row, text="Angre resultat",
                    command=lambda i=idx: self.clear_group_result(i)
                ).pack(side="right", padx=4)

                # Deaktiver innsending av nytt resultat på samme kamp
                btn_t1.configure(state="disabled")
                btn_t2.configure(state="disabled")
                btn_time.configure(state="disabled")


        update_standings_btn = ctk.CTkButton(self.match_controls_frame, text="Oppdater tabell",
                                            command=lambda: self.bracket_canvas.show_group_stage(self.group_stage_model))
        update_standings_btn.pack(pady=10)

    def edit_group_result(self, match_index):
        match = self.group_stage_model.matches[match_index]
        top = ctk.CTkToplevel(self)
        top.title("Rediger resultat")
        self._place_dialog_over(top, width=320, height = 300)

        t1 = match['team1']['name']
        t2 = match['team2']['name']
        prev_c1 = match.get("team1_cups_left") or 0
        prev_c2 = match.get("team2_cups_left") or 0
        prev_w  = match.get("winner") or 1

        ctk.CTkLabel(top, text=f"{t1} kopper igjen (0–10):").pack(pady=(10, 4))
        e1 = ctk.CTkEntry(top, width=120); e1.insert(0, str(prev_c1)); e1.pack(pady=4)

        ctk.CTkLabel(top, text=f"{t2} kopper igjen (0–10):").pack(pady=(10, 4))
        e2 = ctk.CTkEntry(top, width=120); e2.insert(0, str(prev_c2)); e2.pack(pady=4)

        ctk.CTkLabel(top, text="Vinner:").pack(pady=(10, 4))
        winner_var = tk.IntVar(value=prev_w)
        ctk.CTkRadioButton(top, text=t1, variable=winner_var, value=1).pack()
        ctk.CTkRadioButton(top, text=t2, variable=winner_var, value=2).pack()

        err_lbl = ctk.CTkLabel(top, text="", text_color="tomato")
        err_lbl.pack(pady=6)

        def save(event=None):
            try:
                c1 = int(e1.get().strip()); c2 = int(e2.get().strip())
                self.check_allowed_cup_number(c1)
                self.check_allowed_cup_number(c2)
                self.group_stage_model.update_match_result(match_index, c1, c2, winner_var.get())
                self.bracket_canvas.show_group_stage(self.group_stage_model)
                self.draw_group_match_controls()  # oppdatér knapper (deaktiver “vant”)
                top.destroy()
            except Exception:
                err_lbl.configure(text="Ugyldig antall/kombo. Prøv igjen.")

        btn_row = ctk.CTkFrame(top); btn_row.pack(pady=10)
        ctk.CTkButton(btn_row, text="Avbryt", command=top.destroy).pack(side="left", padx=6)
        ctk.CTkButton(btn_row, text="Lagre", command=save).pack(side="left", padx=6)

        top.grab_set(); top.focus(); e1.focus()
        top.bind("<Return>", save)

    def clear_group_result(self, match_index):
        self.group_stage_model.clear_match_result(match_index)
        self.bracket_canvas.show_group_stage(self.group_stage_model)
        self.draw_group_match_controls()  # aktiver “vant”-knappene igjen

    
    def set_group_match_result(self, match_index):
        popup = ctk.CTkInputDialog(title="Kopper igjen", 
                                text="Angi gjenstående kopper (Lag1,Lag2) f.eks 3,1")
        result = popup.get_input()
        try:
            cups1, cups2 = map(int, result.split(","))
            self.group_stage_model.update_match_result(match_index, cups1, cups2, None)
        except:
            pass
        
    def set_group_match_time(self, match_index):
        popup = ctk.CTkInputDialog(title="Sett tidspunkt", text="Tidspunkt (HH:MM)")
        time = popup.get_input()
        if time:
            self.group_stage_model.matches[match_index]["time"] = time

    def show_standings(self):
        standings_window = ctk.CTkToplevel(self)
        standings_window.title("Tabell etter gruppespill")
        standings_window.geometry("700x800")

        for idx, team in enumerate(self.group_stage_model.standings(), start=1):
            frame = ctk.CTkFrame(standings_window)
            frame.pack(fill="x", pady=2, padx=10)

            if team["logo"]:
                img = Image.open(team["logo"])
                img.thumbnail((40, 40), Image.LANCZOS)
                logo_img = ImageTk.PhotoImage(img)
                logo_label = ctk.CTkLabel(frame, image=logo_img, text="")
                logo_label.image = logo_img
                logo_label.pack(side="left", padx=10)

            stats = (f"{idx}. {team['name']} | Wins: {team['wins']} | "
                    f"Hit: {team['cups_hit']} | Diff: {team['total_cups_diff']}")

            ctk.CTkLabel(frame, text=stats, font=("Helvetica", 16)).pack(side="left")

    import sys

    def _place_dialog_over(self, top, width=None, height=None):
        """Plasser Toplevel 'top' over dette vinduet (self) – riktig skjerm, riktig z-order."""
        top.update_idletasks()
        self.update_idletasks()

        # Bestem størrelse først
        w = int(width) if width else max(top.winfo_reqwidth(), 280)
        h = int(height) if height else max(top.winfo_reqheight(), 160)

        # Sett størrelse før posisjon (viktig for noen WM)
        top.geometry(f"{w}x{h}")

        if sys.platform == "win32":
            try:
                import ctypes
                from ctypes import wintypes

                user32 = ctypes.windll.user32

                # Hent HWND-er
                hwnd_parent = self.winfo_id()
                hwnd_child  = top.winfo_id()

                # Strukturer
                class RECT(ctypes.Structure):
                    _fields_ = [("left",   wintypes.LONG),
                                ("top",    wintypes.LONG),
                                ("right",  wintypes.LONG),
                                ("bottom", wintypes.LONG)]

                class MONITORINFO(ctypes.Structure):
                    _fields_ = [("cbSize",   wintypes.DWORD),
                                ("rcMonitor", RECT),
                                ("rcWork",    RECT),
                                ("dwFlags",   wintypes.DWORD)]

                MONITOR_DEFAULTTONEAREST = 2

                # Finn monitor for parent
                hmon = user32.MonitorFromWindow(hwnd_parent, MONITOR_DEFAULTTONEAREST)
                mi = MONITORINFO()
                mi.cbSize = ctypes.sizeof(MONITORINFO)
                user32.GetMonitorInfoW(hmon, ctypes.byref(mi))

                # Parent-rect
                pr = RECT()
                user32.GetWindowRect(hwnd_parent, ctypes.byref(pr))
                pw = pr.right - pr.left
                ph = pr.bottom - pr.top

                # Center over parent
                x = pr.left + (pw - w) // 2
                y = pr.top  + (ph - h) // 2

                # Klamp til arbeidsområde på aktuell monitor
                x = max(mi.rcWork.left,  min(x, mi.rcWork.right  - w))
                y = max(mi.rcWork.top,   min(y, mi.rcWork.bottom - h))

                SWP_NOZORDER   = 0x0004
                SWP_NOACTIVATE = 0x0010
                user32.SetWindowPos(hwnd_child, None, int(x), int(y), int(w), int(h), SWP_NOZORDER | SWP_NOACTIVATE)

                # Sørg for at den ligger over og får fokus
                try:
                    top.attributes("-topmost", True)
                    top.after(200, lambda: top.attributes("-topmost", False))
                except Exception:
                    pass

                top.lift()
                top.focus_set()
                top.grab_set()
                return
            except Exception:
                # Fallback til ren Tk-geo nedenfor
                pass

        # Fallback: center m/ Tk-geo (macOS/Linux eller hvis ctypes feiler)
        px, py = self.winfo_rootx(), self.winfo_rooty()
        pw, ph = self.winfo_width(), self.winfo_height()
        if pw <= 1 or ph <= 1:
            self.update_idletasks()
            pw, ph = max(self.winfo_width(), 600), max(self.winfo_height(), 400)

        x = px + (pw - w) // 2
        y = py + (ph - h) // 2
        top.geometry(f"{w}x{h}+{x}+{y}")
        top.transient(self)
        top.lift()
        top.focus_set()
        top.grab_set()


    

    def fill_team_list(self):
        self.teams = []  # <-- viktig: ikke akkumulér
        team_names = self.team_text.get("1.0", "end").strip().splitlines()
        ...

        
        logo_path = False
        for name in team_names:
            if self.logo_switch:
                logo_path = fd.askopenfilename(title=f"Velg logo for {name}", filetypes=[("Image files", ".png .jpg .jpeg .gif")])
            self.teams.append({"name": name, "logo": logo_path if logo_path else None})

    def build_bracket(self):
        # Hvis vi ikke har lastet lag fra fil, les fra tekstboksen (og ev. spør om logo)
        if not self.teams:
            self.fill_team_list()

        # Bygg turnering med bare navn (som før)
        self.tournament_model.build_bracket([team["name"] for team in self.teams])

        # Koble logoer til de shufflade teamene ETTER bygging – ved navn (ikke indeks)
        logo_by_name = {t["name"]: t.get("logo") for t in self.teams}
        for t in self.tournament_model.teams:
            t["logo"] = logo_by_name.get(t["name"])

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
            if len(new_time) == 2:
                new_time = '00:' + new_time
            
            if len(new_time) == 3:
                new_time = new_time[:1] + ':' + new_time[2:]
            
            if len(new_time) == 4:
                if new_time[1] == ':':
                    new_time = '0' + new_time
                else:
                    new_time = new_time[:2] + ':' + new_time[2:]
            
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
