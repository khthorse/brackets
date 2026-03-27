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
